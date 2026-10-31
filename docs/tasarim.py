# -*- coding: utf-8 -*-
"""Kesit tasarımı ve tahkikleri (Dilim 3–4): TS 500:2000 betonarme kiriş/kolon/eğik eleman, ÇYTHYE 2018 çelik eleman,
çelik çekme/basınç çubuğu (çapraz, kafes), basit kesitler (kutu, boru, korniyer, çift korniyer, UPN) ve kesit önerisi.

Bölümler: A) TS 500 betonarme; B) ÇYTHYE çelik I/H; C) basit çelik kesitler (``kesit_ozellik``, ``celik_cubuk_kontrol``;
kapalı form parça toplama: dikdörtgen + üçgen + köşe dolgusu, kutu köşe yarıçaplı, standart boy listeleri
``STANDART_KESITLER``); D) kesit önerisi (``celik_kesit_oner``, ``betonarme_kesit_oner``) ve betonarme birleştirici
``betonarme_eleman_kontrol`` (kiriş / kolon / eğik: |N_d| ≤ 0,1 f_ck A_c ise eğilme, değilse N–M).

Saf hesap + öğretici anlatım. Her işlev isteğe bağlı ``anl`` (``matris_ogren.Anlatim``) alır; verilirse adımları,
formülleri (LaTeX, sayılar yerine konmuş), yönetmelik maddelerini ve SVG şemalarını oraya yazar. ``*_anlatimli(...)``
sarmalayıcıları ``mo.Sonuc`` döndürür (``.deger`` ve ``.veri`` sonuç sözlüğü, ``.anlatim`` adımlar).

Birimler
--------
* Girdi: kuvvet kN, moment kN·m, uzunluk m (kesit boyutları da m: 0.30 × 0.50); donatı alanı cm²; malzeme MPa.
* İçeride N–mm çalışılır (1 kN = 10³ N, 1 kN·m = 10⁶ N·mm, 1 m = 10³ mm, 1 MPa = 1 N/mm²); dönüşüm anlatımda bir kez
  açıkça gösterilir.
* Çıktı sözlükleri JSON uyumludur (yalnız float/int/str/bool/None/list/dict); kuvvet kN, moment kN·m, boy m ya da mm
  (alan adında birim yazılıdır: ``As_gerekli_cm2``, ``d_mm``, ``Lp_m`` …).
* İşaret: betonarme kolonda ve çelik elemanda eksenel kuvvet **basınç pozitif** (TS 500 N_d kuralı); çekme negatif.

Ortak çıktı alanları: ``dc`` (talep/kapasite, en elverişsiz), ``durum`` ("yeterli" | "donatı artır" | "kesit büyüt"
| "yetersiz"), ``kontroller: [{ad, talep, kapasite, dc, birim, kaynak, saglandi}]``, ``uyarilar: [...]``.

Kaynaklar (yalnız araştırma dosyalarında doğrulanmış madde numaraları yazılır):
* TS 500:2000 (+T1/T2/T3): Çizelge 3.2, md. 6.2.5, md. 6.3.10 (Denk. 6.16), md. 7.1 + Çizelge 7.1, md. 7.3
  (Denk. 7.2–7.5), md. 7.4.1 (Denk. 7.7–7.9), md. 8.1.3–8.1.6 (Denk. 8.1, 8.4–8.7).
* TBDY 2018: md. 7.3.1.1, 7.3.1.2, 7.3.2, 7.4.1.1, 7.4.1.2, 7.4.2.4, 7.4.4; çelik çapraz md. 9.6.3.1, 9.6.4.2–9.6.4.3,
  9.7.3.1, 9.7.4.2–9.7.4.3, Tablo 9.3.
* ÇYTHYE 2018 Esaslar (RG 15.02.2018/30333 Mük.): Tablo 2.1A, 5.4.1 Tablo 5.1A/5.1B (+5.4.1.2(d)), 5.4.2, Bölüm 7
  (7.1.1), 8 (8.1.1, 8.2.1, 8.2.2 Denk. 8.5–8.14, 8.3 Denk. 8.15–8.18, 8.4 Denk. 8.19–8.21), 9 (9.2, 9.3.2, 9.6),
  10.2.1, 11.1.1–11.1.2.
* Profil boyları: EN 10210-2 / EN 10219-2 (kutu, boru), EN 10056-1 (korniyer), EN 10279 / DIN 1026-1 (UPN) — seçki.
"""
from __future__ import annotations

import functools
import html as _html
import math

import numpy as np

import matris_ogren as mo
import sonlu_eleman as se
from matris_ogren import MatrisHatasi

try:  # yapi_veri.py: malzeme ve profil kütüphanesi (salt veri)
    import yapi_veri as yv
except ImportError:  # pragma: no cover - yalnız kütüphane dosyası olmayan dallarda
    yv = None

__all__ = [
    "beton_malzeme", "donati_malzeme", "kiris_egilme", "kiris_kesme", "kolon_etkilesim", "kolon_kontrol",
    "celik_malzeme", "kesit_sinifi", "cb_katsayisi", "celik_egilme", "celik_basinc", "celik_kesme", "celik_cekme",
    "celik_etkilesim", "celik_eleman_kontrol",
    "kiris_egilme_anlatimli", "kiris_kesme_anlatimli", "kolon_etkilesim_anlatimli", "kolon_kontrol_anlatimli",
    "kesit_sinifi_anlatimli", "celik_egilme_anlatimli", "celik_basinc_anlatimli", "celik_kesme_anlatimli",
    "celik_cekme_anlatimli", "celik_eleman_kontrol_anlatimli",
    "kesit_ozellik", "STANDART_KESITLER", "celik_cubuk_kontrol", "celik_kesit_oner", "betonarme_eleman_kontrol",
    "betonarme_kesit_oner", "celik_cubuk_kontrol_anlatimli", "celik_kesit_oner_anlatimli",
    "betonarme_eleman_kontrol_anlatimli", "betonarme_kesit_oner_anlatimli",
]

# ============================================================================
# Yönetmelik sabitleri (kaynaklı)
# ============================================================================
EPS_CU = 0.003            # TS 500 md. 7.1
ES = 200000.0             # MPa, TS 500 md. 7.1
GAMMA_MC = 1.5            # TS 500 md. 6.2.5 (yerinde döküm)
GAMMA_MS = 1.15           # TS 500 md. 6.2.5
E_CELIK = 200000.0        # MPa, ÇYTHYE simgeler listesi / md. 8.2.2
G_CELIK = 77200.0         # MPa
CUBUK_CAPLARI = (12, 14, 16, 18, 20, 22, 24, 26)   # mm; TS 500 md. 7.3: kirişte en küçük Φ12 (araştırma)
ETRIYE_CAPLARI = (8, 10, 12)
DC_UST = 99.0             # sonsuz D/C yerine (JSON uyumu)

K_TS500 = {
    "malzeme": "TS 500 Çizelge 3.2; md. 6.2.5 (γmc = 1,5, γms = 1,15)",
    "blok": "TS 500 md. 7.1, Çizelge 7.1",
    "rho_min": "TS 500 md. 7.3, Denk. 7.3 (TBDY Denk. 7.8 aynı)",
    "rho_085": "TS 500 md. 7.3, Denk. 7.4",
    "rho_002": "TS 500 Denk. 7.5; TBDY 2018 md. 7.4.2.4",
    "rho_b": "TS 500 md. 7.1 varsayımlarından türetilmiştir (TS 500 kapalı form vermez; md. 0.2.5 yalnız tanım)",
    "kiris_boyut": "TS 500 md. 7.3 (h ≥ 300 mm, bw ≥ 200 mm)",
    "kiris_boyut_tbdy": "TBDY 2018 md. 7.4.1.1 (bw ≥ 250 mm, h ≤ 3,5 bw)",
    "aralik": "TS 500 md. 7.3 (net aralık ≥ 20 mm ve ≥ Φ)",
    "Vcr": "TS 500 md. 8.1.3, Denk. 8.1",
    "Vc": "TS 500 md. 8.1.4, Denk. 8.4",
    "Vw": "TS 500 md. 8.1.4, Denk. 8.5",
    "Vmin": "TS 500 md. 8.1.5a, Denk. 8.6",
    "Vmax": "TS 500 md. 8.1.5b, Denk. 8.7",
    "s": "TS 500 md. 8.1.6",
    "s_tbdy": "TBDY 2018 md. 7.4.4 (sarılma bölgesi)",
    "N09": "TS 500 md. 7.4.1, Denk. 7.7",
    "N040": "TBDY 2018 md. 7.3.1.2",
    "rho_kolon": "TS 500 md. 7.4.1, Denk. 7.8–7.9; TBDY 2018 md. 7.3.2",
    "kolon_boyut": "TS 500 md. 7.4.1 (en küçük boyut 250 mm)",
    "kolon_boyut_tbdy": "TBDY 2018 md. 7.3.1.1 (en küçük boyut 300 mm)",
    "emin": "TS 500 md. 6.3.10, Denk. 6.16",
    "iki_eksen": "Öğretici yaklaşım (Bresler ters yük formülü); TS 500 iki eksenli eğilme için etkileşim formülü "
                 "vermez (md. 7.6.2.6 yalnız iki doğrultudaki momentlerin ayrı ayrı büyütülmesini ister)",
}
K_CYT = {
    "malzeme": "ÇYTHYE 2018 md. 2.1.1, Tablo 2.1A",
    "sinif_egilme": "ÇYTHYE 2018 md. 5.4.1, Tablo 5.1B (Durum 10 başlık, Durum 15 gövde)",
    "sinif_basinc": "ÇYTHYE 2018 md. 5.4.1, Tablo 5.1A (Durum 1 başlık, Durum 5 gövde)",
    "Mp": "ÇYTHYE 2018 md. 9.2.1, Denk. 9.2",
    "YBB": "ÇYTHYE 2018 md. 9.2.2, Denk. 9.3–9.6 (c = 1: Denk. 9.7a; i_ts: Denk. 9.8a)",
    "FLB": "ÇYTHYE 2018 md. 9.3.2, Denk. 9.9",
    "Cb": "ÇYTHYE 2018 md. 9.1, Denk. 9.1",
    "zayif": "ÇYTHYE 2018 md. 9.6.1, Denk. 9.39 (başlık kompakt değilse md. 9.6.2, Denk. 9.40)",
    "phi_b": "ÇYTHYE 2018 md. 9.1 (φb = 0,90; Ωb = 1,67)",
    "basinc": "ÇYTHYE 2018 md. 8.2, Denk. 8.1–8.4 (φc = 0,90; Ωc = 1,67)",
    "burulmali": "ÇYTHYE 2018 md. 8.2.2, Denk. 8.5",
    "narinlik_basinc": "ÇYTHYE 2018 md. 8.1.1 (L_c/i ≤ 200, zorunlu; RG s.192)",
    "kesme": "ÇYTHYE 2018 md. 10.2.1, Denk. 10.1–10.3",
    "cekme_akma": "ÇYTHYE 2018 md. 7.2.1, Denk. 7.2 (φt = 0,90; Ωt = 1,67)",
    "cekme_kirilma": "ÇYTHYE 2018 md. 7.2.2, Denk. 7.3; A_e = U A_n Denk. 7.1 (φt = 0,75; Ωt = 2,00)",
    "narinlik_cekme": "ÇYTHYE 2018 md. 7.1.1 (L/i ≤ 300; kablo ve miller hariç)",
    "etkilesim": "ÇYTHYE 2018 md. 11.1.1, Denk. 11.1a/11.1b (çekmede md. 11.1.2)",
}


# ============================================================================
# Küçük yardımcılar
# ============================================================================
def _sayi(v, ad, pozitif=False, sifir_olur=True) -> float:
    if isinstance(v, bool) or v is None or (isinstance(v, str) and not v.strip()):
        raise MatrisHatasi(f"{ad} verilmedi (sayı bekleniyor).")
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"{ad} sayı olmalı (girilen: {v!r}).") from None
    if x != x or math.isinf(x):
        raise MatrisHatasi(f"{ad} sonlu bir sayı olmalı (girilen: {v!r}).")
    if pozitif and (x < 0 or (x == 0 and not sifir_olur)):
        raise MatrisHatasi(f"{ad} {'pozitif' if not sifir_olur else 'negatif olmayan'} olmalı (girilen: {v!r}).")
    return x


def _boyut(v, ad, en_buyuk=5.0) -> float:
    """Kesit boyutu (m) → mm; birim karışıklığına öğretici hata."""
    x = _sayi(v, ad, pozitif=True, sifir_olur=False)
    if x > en_buyuk:
        raise MatrisHatasi(f"{ad} = {x} m çok büyük; kesit boyutları metre girilir (30 cm → 0.30).")
    return x * 1000.0


def _json(o):
    """numpy/float/tuple → JSON uyumlu yalın Python."""
    if isinstance(o, dict):
        return {str(k): _json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        x = float(o)
        if x != x:
            return None
        if math.isinf(x):
            return DC_UST if x > 0 else -DC_UST
        return x
    return o


def _dc(talep, kapasite) -> float:
    talep, kapasite = float(talep), float(kapasite)
    if kapasite <= 0:
        return 0.0 if talep <= 0 else DC_UST
    return min(max(talep / kapasite, 0.0), DC_UST)


def _kontrol(ad, talep, kapasite, kaynak, birim="", dc=None) -> dict:
    d = _dc(talep, kapasite) if dc is None else min(float(dc), DC_UST)
    return {"ad": ad, "talep": float(talep), "kapasite": float(kapasite), "dc": d, "birim": birim,
            "kaynak": kaynak, "saglandi": bool(d <= 1.0 + 1e-9)}


def _f(x, b=2) -> str:
    """Tablo sayısı (nokta ondalık, ondalık kısmın sondaki sıfırları atılır)."""
    s = f"{float(x):.{b}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _g(x) -> str:
    """Tablo sayısı, 4 anlamlı basamak (küçük oranlar için)."""
    x = float(x)
    if x != 0 and abs(x) < 0.1:
        return f"{x:.4g}"
    return _f(x, 3)


def _L(x, b=2) -> str:
    """LaTeX sayısı: virgül ondalık ({,}); büyük sayılar a·10^k."""
    x = float(x)
    if x != 0 and (abs(x) >= 1e6 or abs(x) < 10 ** (-b)):
        k = int(math.floor(math.log10(abs(x)) / 3.0) * 3) if abs(x) >= 1e6 else int(math.floor(math.log10(abs(x))))
        m = x / 10 ** k
        return f"{_L(m, 3)} \\cdot 10^{{{k}}}"
    s = f"{x:.{b}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("", "-0"):
        s = "0"
    return s.replace(".", "{,}")


def _basla(anl, baslik, ne, seviye=3):
    if anl is None:
        return
    anl.baslik(baslik, seviye)
    anl.metin("**Ne yapıyoruz, neden?** " + ne)


def _birim_notu(anl):
    if anl is not None:
        anl.metin("**Birimler:** girdiler kN, kN·m ve m; hesap N ve mm ile yapılır. Dönüşüm: "
                  "1 kN = 10³ N, 1 kN·m = 10⁶ N·mm, 1 m = 10³ mm, 1 MPa = 1 N/mm², 1 cm² = 100 mm².")


def _durum_ozet(anl, sonuc):
    if anl is None:
        return
    satir = [[k["ad"], _g(k["talep"]), _g(k["kapasite"]), k.get("birim", ""), _f(k["dc"], 3),
              "✓" if k["saglandi"] else "✗", k["kaynak"]] for k in sonuc["kontroller"]]
    if satir:
        anl.metin("**Kontroller** (D/C = talep / kapasite; alt sınır denetimlerinde gerekli / sağlanan):\n\n"
                  + se._tablo(["Kontrol", "Talep", "Kapasite", "Birim", "D/C", "", "Kaynak"], satir))
    for u in sonuc.get("uyarilar", []):
        anl.uyari(u)
    anl.sonuc(rf"\text{{D/C}}_{{max}} = {_L(sonuc['dc'], 3)}", f"Durum: **{sonuc['durum']}**")


def _anlatimli(islev, ad, goster, args, kw):
    anl = mo.Anlatim()
    r = islev(*args, anl=anl, **kw)
    mo.son_anlatim = anl
    anl.goster(goster)
    s = mo.Sonuc(r, anl, ad)
    s.veri = r
    return s


# ============================================================================
# Küçük SVG üretici (renkler sonlu_eleman şemalarıyla aynı --sema-* değişkenleri)
# ============================================================================
class _Svg:
    def __init__(self):
        self.parca = []
        self._k = [math.inf, math.inf, -math.inf, -math.inf]

    def kapsa(self, x0, y0, x1=None, y1=None):
        x1 = x0 if x1 is None else x1
        y1 = y0 if y1 is None else y1
        k = self._k
        k[0], k[1] = min(k[0], x0, x1), min(k[1], y0, y1)
        k[2], k[3] = max(k[2], x0, x1), max(k[3], y0, y1)

    @staticmethod
    def _renk(aile, dolgu):
        if aile is None:
            return ('fill="none" ' if not dolgu else 'fill="currentColor" ') + 'stroke="currentColor"'
        if aile == "n":
            return se._st(None if not dolgu else se._KART, se._NOTR) + ("" if dolgu else ' fill="none"')
        d, c = se._AILE[aile]
        return se._st(d if dolgu else None, c) + ("" if dolgu else ' fill="none"')

    def cizgi(self, a, b, aile=None, kalin=1.5, kesik=None):
        oz = f' stroke-dasharray="{kesik}"' if kesik else ""
        self.parca.append(f'<line x1="{se._n(a[0])}" y1="{se._n(a[1])}" x2="{se._n(b[0])}" y2="{se._n(b[1])}" '
                          f'{self._renk(aile, False)} stroke-width="{kalin}" stroke-linecap="round"{oz}/>')
        self.kapsa(a[0], a[1], b[0], b[1])

    def dikdortgen(self, x, y, w, h, aile=None, dolgu=True, kalin=1.5, kesik=None):
        oz = f' stroke-dasharray="{kesik}"' if kesik else ""
        self.parca.append(f'<rect x="{se._n(x)}" y="{se._n(y)}" width="{se._n(w)}" height="{se._n(h)}" '
                          f'{self._renk(aile, dolgu)} stroke-width="{kalin}"{oz}/>')
        self.kapsa(x, y, x + w, y + h)

    def daire(self, x, y, r, aile="a", dolgu=True):
        self.parca.append(f'<circle cx="{se._n(x)}" cy="{se._n(y)}" r="{se._n(max(r, 1.5))}" '
                          f'{self._renk(aile, dolgu)} stroke-width="1.2"/>')
        self.kapsa(x - r, y - r, x + r, y + r)

    def yol(self, pts, aile=None, kalin=1.8, kapali=False, dolgu=False, kesik=None):
        if len(pts) < 2:
            return
        d = "M" + " L".join(f"{se._n(x)} {se._n(y)}" for x, y in pts) + (" Z" if kapali else "")
        oz = f' stroke-dasharray="{kesik}"' if kesik else ""
        self.parca.append(f'<path d="{d}" {self._renk(aile, dolgu)} stroke-width="{kalin}" '
                          f'stroke-linejoin="round" stroke-linecap="round"{oz}/>')
        for x, y in pts:
            self.kapsa(x, y)

    def yazi(self, x, y, metin, anchor="middle", boyut=11, kalin=False, aile=None):
        renk = se._st(se._AILE[aile][1]) if aile in se._AILE else 'fill="currentColor"'
        kl = ' font-weight="600"' if kalin else ""
        self.parca.append(f'<text x="{se._n(x)}" y="{se._n(y)}" text-anchor="{anchor}" font-size="{boyut}" '
                          f'{renk}{kl}>{_html.escape(str(metin))}</text>')
        g = 0.55 * boyut * len(str(metin))
        x0 = x - g / 2 if anchor == "middle" else (x - g if anchor == "end" else x)
        self.kapsa(x0, y - boyut, x0 + g, y + 3)

    def svg(self, baslik, pay=10.0) -> str:
        k = self._k if self._k[0] != math.inf else [0, 0, 10, 10]
        x0, y0, w, h = k[0] - pay, k[1] - pay, k[2] - k[0] + 2 * pay, k[3] - k[1] + 2 * pay
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{se._n(x0)} {se._n(y0)} {se._n(w)} {se._n(h)}" '
                f'width="{se._n(w)}" height="{se._n(h)}" style="max-width:100%;height:auto" '
                f'font-family="{se._YAZI_AILESI}" font-size="11" role="img" '
                f'aria-label="{_html.escape(baslik, quote=True)}">' + "".join(self.parca) + "</svg>")


def _sema(anl, baslik, kareler):
    if anl is not None:
        anl.sema(baslik, [{"baslik": b, "svg": s} for b, s in kareler])


def _svg_kiris_kesit(b, h, d, d2, alt, ust, a, c, eps_s, baslik):
    """b, h, d, d2, a, c mm; alt/ust: [(adet, çap)]; eps_s: çekme donatısı birim uzaması."""
    S = _Svg()
    s = 200.0 / h
    W, H = b * s, h * s
    S.dikdortgen(0, 0, W, H, "n")
    if a > 0:
        S.dikdortgen(0, 0, W, min(a, h) * s, "b", kalin=1.0)
        S.yazi(W / 2, min(a, h) * s / 2 + 4, f"0,85 fcd · a = {_f(a, 1)} mm", boyut=10)
    if 0 < c < h:
        S.cizgi((-8, c * s), (W + 8, c * s), "sil", kalin=1.2, kesik="5 3")
        S.yazi(-10, c * s + 4, f"t.e. c = {_f(c, 1)}", anchor="end", boyut=10, aile="sil")

    def sira(cubuklar, y):
        tum = [cap for adet, cap in cubuklar for _ in range(int(adet))]
        if not tum:
            return
        tum = sorted(tum, reverse=True)
        # iri çubuklar köşelere
        sirali = [None] * len(tum)
        sol, sag = 0, len(tum) - 1
        for i, cap in enumerate(tum):
            if i % 2 == 0:
                sirali[sol] = cap
                sol += 1
            else:
                sirali[sag] = cap
                sag -= 1
        n = len(sirali)
        for i, cap in enumerate(sirali):
            x = d2 + (b - 2 * d2) * (i / (n - 1) if n > 1 else 0.5)
            S.daire(x * s, y * s, cap / 2 * s, "a")

    sira(alt, d)
    sira(ust, d2)
    S.yazi(W / 2, -6, f"b = {_f(b, 0)} mm", boyut=10)
    S.yazi(W + 6, H / 2, f"h = {_f(h, 0)}", anchor="start", boyut=10)
    S.yazi(W + 6, d * s + 4, f"d = {_f(d, 0)}", anchor="start", boyut=10, aile="a")
    # birim uzama diyagramı
    x0 = W + 90
    S.cizgi((x0, 0), (x0, H), "n", kalin=1.0)
    if 0 < c:
        olc = 40.0 / EPS_CU
        es = min(abs(eps_s), 0.012) * olc
        S.yol([(x0, 0), (x0 - EPS_CU * olc, 0), (x0, min(c, h) * s)], "b", kalin=1.2, kapali=True, dolgu=True)
        if c < d:
            S.yol([(x0, c * s), (x0 + es, d * s), (x0, d * s)], "a", kalin=1.2, kapali=True, dolgu=True)
            S.yazi(x0 + es + 4, d * s + 4, f"εs = {eps_s * 1000:.2f}‰", anchor="start", boyut=10, aile="a")
        S.yazi(x0 - EPS_CU * olc, -6, "εcu = 3‰", boyut=10, aile="b")
    return S.svg(baslik)


def _svg_kolon_kesit(bx, by, cubuklar, baslik, eksen="x"):
    """bx (yatay), by (düşey) mm; cubuklar: [(x, y, alan)] merkezden mm."""
    S = _Svg()
    s = 180.0 / max(bx, by)
    W, H = bx * s, by * s
    S.dikdortgen(0, 0, W, H, "n")
    for x, y, A in cubuklar:
        S.daire(W / 2 + x * s, H / 2 - y * s, math.sqrt(4 * A / math.pi) / 2 * s, "a")
    S.yazi(W / 2, -6, f"b = {_f(bx, 0)} mm", boyut=10)
    S.yazi(W + 6, H * 0.3, f"h = {_f(by, 0)} mm", anchor="start", boyut=10)
    if eksen == "x":
        S.cizgi((-10, H / 2), (W + 10, H / 2), "sil", kalin=1.0, kesik="6 3")
        S.yazi(-12, H / 2 + 4, "x", anchor="end", boyut=10, aile="sil")
    else:
        S.cizgi((W / 2, -2), (W / 2, H + 10), "sil", kalin=1.0, kesik="6 3")
        S.yazi(W / 2, H + 22, "y", boyut=10, aile="sil")
    return S.svg(baslik)


def _svg_nm(egri, baslik, noktalar=(), dengeli=None, N_cizgiler=(), M_etiket="M"):
    """egri: [(N kN, M kN·m)] (M ≥ 0); noktalar: [(ad, N, M, dc)]; N_cizgiler: [(etiket, N)]."""
    S = _Svg()
    Ns = [p[0] for p in egri] + [p[1] for p in noktalar] + [n for _, n in N_cizgiler]
    Ms = [p[1] for p in egri] + [abs(p[2]) for p in noktalar]
    Nmin, Nmax = min(Ns + [0.0]), max(Ns)
    Mmax = max(Ms) if max(Ms) > 0 else 1.0
    W, H = 300.0, 260.0
    sx = W / (1.15 * Mmax)
    sy = H / ((Nmax - Nmin) * 1.08 if Nmax > Nmin else 1.0)

    def P(N, M):
        return M * sx, (Nmax * 1.04 - N) * sy

    o = P(0, 0)
    S.cizgi((0, 0), (0, H), "n", kalin=1.0)
    S.cizgi((0, o[1]), (W, o[1]), "n", kalin=1.0)
    S.yazi(W, o[1] - 4, f"{M_etiket} (kN·m)", anchor="end", boyut=10)
    S.yazi(4, 10, "N (kN, basınç +)", anchor="start", boyut=10)
    S.yol([P(n, m) for n, m in egri], "a", kalin=2.0)
    for et, n in N_cizgiler:
        y = P(n, 0)[1]
        S.cizgi((0, y), (W * 0.85, y), "b", kalin=1.0, kesik="5 3")
        S.yazi(W * 0.86, y + 4, et, anchor="start", boyut=9, aile="b")
    n0, nt = egri[-1][0], egri[0][0]
    S.yazi(-4, P(n0, 0)[1] + 4, f"N0 = {_f(n0, 0)}", anchor="end", boyut=9)
    S.yazi(-4, P(nt, 0)[1] + 4, f"Nt = {_f(nt, 0)}", anchor="end", boyut=9)
    if dengeli is not None:
        x, y = P(dengeli[0], dengeli[1])
        S.daire(x, y, 3.5, "c")
        S.yazi(x + 6, y - 4, f"dengeli ({_f(dengeli[1], 0)}; {_f(dengeli[0], 0)})", anchor="start", boyut=9, aile="c")
    for ad, n, m, dc in noktalar:
        x, y = P(n, abs(m))
        aile = "c" if dc <= 1.0 else "sil"
        S.cizgi(o, (x, y), aile, kalin=0.8, kesik="2 3")
        S.daire(x, y, 3.5, aile)
        S.yazi(x + 6, y + 4, f"{ad}: D/C = {dc:.2f}", anchor="start", boyut=9, aile=aile)
    return S.svg(baslik)


def _svg_profil(p, baslik, Fy=None, sinif=None):
    S = _Svg()
    s = 200.0 / max(p["h"], p["b"])
    h, b, tw, tf = p["h"] * s, p["b"] * s, p["tw"] * s, p["tf"] * s
    x0 = 0.0
    xc = x0 + b / 2
    pts = [(x0, 0), (x0 + b, 0), (x0 + b, tf), (xc + tw / 2, tf), (xc + tw / 2, h - tf), (x0 + b, h - tf),
           (x0 + b, h), (x0, h), (x0, h - tf), (xc - tw / 2, h - tf), (xc - tw / 2, tf), (x0, tf)]
    S.yol(pts, "a", kalin=1.4, kapali=True, dolgu=True)
    S.yazi(xc, -6, f"b = {_f(p['b'], 0)} mm", boyut=10)
    S.yazi(x0 + b + 8, h / 2, f"h = {_f(p['h'], 0)}", anchor="start", boyut=10)
    S.yazi(x0 + b + 8, h / 2 + 14, f"tw = {_f(p['tw'], 1)}", anchor="start", boyut=10)
    S.yazi(x0 + b + 8, tf + 8, f"tf = {_f(p['tf'], 1)}", anchor="start", boyut=10)
    if sinif is not None:
        S.yazi(xc, h + 16, f"b/2tf = {sinif['baslik']['oran']:.2f}  h/tw = {sinif['govde']['oran']:.2f}", boyut=10)
        S.yazi(xc, h + 30, f"eğilme: {sinif['egilme']}; basınç: {sinif['basinc']}", boyut=10, kalin=True)
    return S.svg(baslik)


# ============================================================================
# A) TS 500 malzeme
# ============================================================================
def _kutuphane(tablo_adi):
    if yv is None:
        raise MatrisHatasi("yapi_veri.py (malzeme/profil kütüphanesi) bulunamadı; malzemeyi sözlük olarak verin.")
    return getattr(yv, tablo_adi)


def _beton_kart(sinif):
    if isinstance(sinif, dict):
        return dict(sinif)
    ad = str(sinif).strip().upper().replace(" ", "")
    tablo = _kutuphane("BETONLAR")
    for anahtar, kart in tablo.items():
        if ad == anahtar.upper() or ad == anahtar.upper().split("/")[0]:
            k = dict(kart)
            k["sinif"] = anahtar
            return k
    raise MatrisHatasi(f"Beton sınıfı {sinif!r} tanımsız. TS 500 Çizelge 3.2 sınıfları: {', '.join(tablo)} "
                       "(\"C30\" ya da \"C30/37\" yazılabilir).")


def beton_malzeme(sinif="C30", gamma_mc=GAMMA_MC) -> dict:
    """TS 500 beton kartı: fck, fcd = fck/γmc, fctk, fctd = fctk/γmc, Ec, k1 (Çizelge 7.1), εcu = 0,003 (MPa).

    ``sinif``: "C30" / "C30/37" (kütüphane) ya da sözlük {"fck", "k1", ["fctk", "Ec"]}; sözlükte fctk verilmezse
    0,35√fck (TS 500 Denk. 3.1), Ec verilmezse 3250√fck + 14000 (Denk. 3.2) alınır."""
    gamma_mc = _sayi(gamma_mc, "γmc", pozitif=True, sifir_olur=False)
    k = _beton_kart(sinif)
    if "fck" not in k:
        raise MatrisHatasi("Beton sözlüğünde 'fck' (MPa) olmalı.")
    fck = _sayi(k["fck"], "fck", pozitif=True, sifir_olur=False)
    fctk = float(k.get("fctk", 0.35 * math.sqrt(fck)))
    Ec = float(k.get("Ec", 3250.0 * math.sqrt(fck) + 14000.0))
    if "k1" not in k:
        raise MatrisHatasi("Beton sözlüğünde 'k1' (TS 500 Çizelge 7.1) olmalı.")
    k1 = _sayi(k["k1"], "k1", pozitif=True, sifir_olur=False)
    return _json({"sinif": k.get("sinif", f"C{_f(fck, 0)}"), "fck": fck, "fcd": fck / gamma_mc, "fctk": fctk,
                  "fctd": fctk / gamma_mc, "Ec": Ec, "k1": k1, "eps_cu": EPS_CU, "gamma_mc": gamma_mc,
                  "kaynak": f"{K_TS500['malzeme']}; k1: {K_TS500['blok']}",
                  "dogrulandi": bool(k.get("dogrulandi", True))})


def donati_malzeme(sinif="B420C", gamma_ms=GAMMA_MS) -> dict:
    """Donatı kartı: fyk, fyd = fyk/γms, Es = 2·10⁵ MPa, εyd = fyd/Es."""
    gamma_ms = _sayi(gamma_ms, "γms", pozitif=True, sifir_olur=False)
    if isinstance(sinif, dict):
        k = dict(sinif)
        if "fyk" not in k:
            raise MatrisHatasi("Donatı sözlüğünde 'fyk' (MPa) olmalı.")
        k.setdefault("sinif", f"S{_f(k['fyk'], 0)}")
    else:
        ad = str(sinif).strip().upper().replace(" ", "")
        tablo = _kutuphane("DONATILAR")
        if ad not in tablo:
            raise MatrisHatasi(f"Donatı sınıfı {sinif!r} tanımsız. Seçenekler: {', '.join(tablo)}.")
        k = dict(tablo[ad])
        k["sinif"] = ad
    fyk = _sayi(k["fyk"], "fyk", pozitif=True, sifir_olur=False)
    Es = float(k.get("Es", ES))
    fyd = fyk / gamma_ms
    return _json({"sinif": k["sinif"], "fyk": fyk, "fyd": fyd, "Es": Es, "eps_yd": fyd / Es, "gamma_ms": gamma_ms,
                  "kaynak": "TS 500 md. 6.2.5 (γms = 1,15), md. 7.1 (Es = 2·10⁵ MPa); TBDY 7.2.5.3b B420C/B500C"})


def _malzemeler(beton, donati):
    bm = beton if isinstance(beton, dict) and "fcd" in beton else beton_malzeme(beton)
    dm = donati if isinstance(donati, dict) and "fyd" in donati else donati_malzeme(donati)
    return bm, dm


def _rho_b(bm, dm):
    return 0.85 * bm["k1"] * bm["fcd"] / dm["fyd"] * (EPS_CU * dm["Es"]) / (EPS_CU * dm["Es"] + dm["fyd"])


def _anlat_malzeme(anl, bm, dm):
    if anl is None:
        return
    anl.metin(f"**Malzeme:** beton {bm['sinif']}, donatı {dm['sinif']} ({K_TS500['malzeme']}).")
    anl.mat(rf"f_{{cd}} = \frac{{f_{{ck}}}}{{\gamma_{{mc}}}} = \frac{{{_L(bm['fck'])}}}{{{_L(bm['gamma_mc'])}}} = "
            rf"{_L(bm['fcd'], 3)}\ \text{{MPa}},\quad f_{{ctd}} = \frac{{{_L(bm['fctk'])}}}{{{_L(bm['gamma_mc'])}}} = "
            rf"{_L(bm['fctd'], 3)}\ \text{{MPa}},\quad f_{{yd}} = \frac{{{_L(dm['fyk'])}}}{{{_L(dm['gamma_ms'])}}} = "
            rf"{_L(dm['fyd'], 2)}\ \text{{MPa}}")
    anl.mat(rf"k_1 = {_L(bm['k1'])}\ (\text{{Çizelge 7.1}}),\quad \varepsilon_{{cu}} = 0{{,}}003,\quad "
            rf"E_s = 2\cdot 10^{{5}}\ \text{{MPa}},\quad \varepsilon_{{yd}} = \frac{{f_{{yd}}}}{{E_s}} = {_L(dm['eps_yd'], 5)}")


# ============================================================================
# A2) Kiriş eğilme (TS 500)
# ============================================================================
def _cubuk_alani(cap):
    return math.pi * cap ** 2 / 4.0


def _cubuk_metin(cubuklar):
    return " + ".join(f"{adet}Φ{cap}" for adet, cap in cubuklar if adet > 0)


def _cubuk_oner(As, b, pas, en_az_adet=2):
    """As (mm²) için çubuk önerisi: tek çap ya da 2Φbüyük + kΦküçük; tek sıra sığma denetimi (kabaca).

    Çubuk merkezleri yanlarda da ``pas`` uzaklığında varsayılır: net aralık = (b − 2·pas)/(n − 1) − Φmax."""
    adaylar = []
    for cap in CUBUK_CAPLARI:
        n = max(en_az_adet, math.ceil(As / _cubuk_alani(cap) - 1e-9))
        adaylar.append(([(n, cap)], n * _cubuk_alani(cap)))
    for i, buyuk in enumerate(CUBUK_CAPLARI):
        for kucuk in (c for c in CUBUK_CAPLARI[:i] if c >= buyuk - 6):   # çaplar birbirine yakın kalsın
            for k in range(1, 7):
                alan = 2 * _cubuk_alani(buyuk) + k * _cubuk_alani(kucuk)
                if alan >= As - 1e-9:
                    adaylar.append(([(2, buyuk), (k, kucuk)], alan))
                    break

    def bilgi(aday):
        cubuklar, alan = aday
        n = sum(a for a, _ in cubuklar)
        capmax = max(c for _, c in cubuklar)
        net = (b - 2 * pas) / (n - 1) - capmax if n > 1 else b - 2 * pas
        gerek = max(20.0, capmax)
        return {"cubuklar": [{"adet": a, "cap": c} for a, c in cubuklar], "metin": _cubuk_metin(cubuklar),
                "As_mm2": alan, "As_cm2": alan / 100.0, "adet": n, "net_aralik_mm": net,
                "gerekli_aralik_mm": gerek, "sigar": bool(net >= gerek - 1e-9)}

    bilgiler = [bilgi(a) for a in adaylar if a[1] >= As - 1e-9]
    sigan = [x for x in bilgiler if x["sigar"]]
    havuz = sigan or bilgiler
    # en az fazlalık; %2 içinde eşitse az çubuk, sonra tek çap
    enaz = min(x["As_mm2"] for x in havuz)
    yakin = [x for x in havuz if x["As_mm2"] <= enaz * 1.02 + 1e-9]
    yakin.sort(key=lambda x: (x["adet"], len(x["cubuklar"]), x["As_mm2"]))
    return yakin[0]


def _kiris_Mr(As, As2, b, d, d2, bm, dm):
    """Şekil değiştirme uygunluğuyla Mr (N·mm): c'yi denge ile bulur (ikiye bölme)."""
    fcd, k1, fyd, Es = bm["fcd"], bm["k1"], dm["fyd"], dm["Es"]

    def kuvvetler(c):
        a = k1 * c
        Cc = 0.85 * fcd * b * a
        es2 = EPS_CU * (c - d2) / c
        ss2 = max(-fyd, min(fyd, Es * es2))
        es = EPS_CU * (d - c) / c
        ss = max(-fyd, min(fyd, Es * es))
        return Cc, As2 * ss2, As * ss, a, es, es2, ss, ss2

    def f(c):
        Cc, Cs, T, *_ = kuvvetler(c)
        return Cc + Cs - T

    lo, hi = 1e-6, max(d, 1.0) * 1.0
    while f(hi) < 0:
        hi *= 2.0
    for _ in range(200):
        orta = 0.5 * (lo + hi)
        if f(orta) > 0:
            hi = orta
        else:
            lo = orta
    c = 0.5 * (lo + hi)
    Cc, Cs, T, a, es, es2, ss, ss2 = kuvvetler(c)
    Mr = Cc * (d - a / 2.0) + Cs * (d - d2)
    return {"Mr": Mr, "c": c, "a": a, "eps_s": es, "eps_s2": es2, "sigma_s": ss, "sigma_s2": ss2}


def kiris_egilme(Md, b, h, paspayi, beton="C30", donati="B420C", As_mevcut=None, As_ust=None, paspayi_ust=None,
                 tbdy=True, anl=None) -> dict:
    """TS 500 dikdörtgen kiriş eğilme tasarımı/tahkiki.

    Md (kN·m, pozitif: alt lif çekme), b, h, paspayi (m; ``paspayi`` çekme donatısı ağırlık merkezinin dış yüze
    uzaklığı, d = h − paspayi), ``As_mevcut`` / ``As_ust`` (cm², verilirse tahkik edilir; verilmezse önerilen
    donatıyla), ``paspayi_ust`` basınç donatısı için (varsayılan ``paspayi``). ``tbdy``: TBDY 7.4 boyut koşulları.

    Dönüş: d_mm, k1, rho_b, rho_min, rho_max, tek_donatili, a_mm, c_mm, As_gerekli_cm2, As_ust_gerekli_cm2,
    sigma_s_ust_MPa, ust_akiyor, oneri {metin, cubuklar, As_cm2, net_aralik_mm, sigar}, As_saglanan_cm2,
    As_ust_saglanan_cm2, Mr_kNm, dc, durum, kontroller, uyarilar."""
    Md_kNm = _sayi(Md, "Md (kN·m)")
    bmm = _boyut(b, "b (kiriş genişliği)")
    hmm = _boyut(h, "h (kiriş yüksekliği)")
    pas = _sayi(paspayi, "paspayı (m)", pozitif=True, sifir_olur=False) * 1000.0
    if pas >= hmm / 2:
        raise MatrisHatasi(f"Paspayı {pas:.0f} mm, h/2 = {hmm / 2:.0f} mm'den küçük olmalı (d = h − paspayı; "
                           "paspayı donatı ağırlık merkezinin dış yüze uzaklığıdır, m girilir: 4 cm → 0.04).")
    d2 = pas if paspayi_ust is None else _sayi(paspayi_ust, "üst paspayı (m)", pozitif=True, sifir_olur=False) * 1000.0
    if d2 >= hmm / 2:
        raise MatrisHatasi("Üst paspayı h/2'den küçük olmalı.")
    bm, dm = _malzemeler(beton, donati)
    fcd, fyd, k1, Es = bm["fcd"], dm["fyd"], bm["k1"], dm["Es"]
    d = hmm - pas
    M = abs(Md_kNm) * 1e6
    uyarilar = []
    if Md_kNm < 0:
        uyarilar.append("Md negatif verildi; mutlak değeriyle (çekme yüzü 'alt' kabul edilerek) hesaplandı. "
                        "Mesnet momentinde çekme donatısı üsttedir.")
    R = 0.85 * fcd * bmm
    rho_b = _rho_b(bm, dm)
    rho_085 = 0.85 * rho_b
    rho_min = 0.8 * bm["fctd"] / fyd
    rho_lim = min(rho_085, 0.02)
    As_lim = rho_lim * bmm * d
    a_lim = As_lim * fyd / R
    M_lim = As_lim * fyd * (d - a_lim / 2.0)

    tek = M <= M_lim * (1 + 1e-12)
    As2 = 0.0
    sigma2 = None
    ust_akiyor = None
    kesit_kucuk = False
    if tek:
        a = d - math.sqrt(max(d * d - 2.0 * M / R, 0.0))
        As = R * a / fyd
        c = a / k1
    else:
        a = a_lim
        c = a / k1
        es2 = EPS_CU * (c - d2) / c
        sigma2 = min(Es * es2, fyd)
        ust_akiyor = bool(Es * es2 >= fyd)
        M2 = M - M_lim
        if sigma2 <= 0:
            kesit_kucuk = True
            As2 = math.inf
            As = math.inf
            uyarilar.append("Basınç donatısı tarafsız eksenin altında kalıyor; çift donatı işe yaramaz — kesit büyütülmeli.")
        else:
            As2 = M2 / (sigma2 * (d - d2))
            As = As_lim + As2 * sigma2 / fyd
    As_gerekli = max(As, rho_min * bmm * d) if not kesit_kucuk else As
    rho_gerekli = As_gerekli / (bmm * d) if not kesit_kucuk else math.inf
    if rho_gerekli > 0.02 + 1e-12:
        kesit_kucuk = True
    if not tek and not kesit_kucuk:
        uyarilar.append(f"Tek donatılı sınır aşıldı (ρ − ρ' ≤ min(0,85ρb; 0,02) = {rho_lim:.4f}); çift donatılı "
                        f"tasarlandı. Basınç donatısı {'akıyor' if ust_akiyor else 'akmıyor (σs′ < fyd)'}.")

    # öneri ve sağlanan donatı
    if not kesit_kucuk:
        oneri = _cubuk_oner(As_gerekli, bmm, pas)
        oneri_ust = _cubuk_oner(As2, bmm, d2) if As2 > 0 else None
    else:
        oneri = oneri_ust = None
    if As_mevcut is not None:
        As_s = _sayi(As_mevcut, "As_mevcut (cm²)", pozitif=True, sifir_olur=False) * 100.0
    else:
        As_s = oneri["As_mm2"] if oneri else 0.0
    if As_ust is not None:
        As2_s = _sayi(As_ust, "As_ust (cm²)", pozitif=True) * 100.0
    else:
        As2_s = oneri_ust["As_mm2"] if (oneri_ust and As_mevcut is None) else 0.0
    if As_s > 0:
        r = _kiris_Mr(As_s, As2_s, bmm, d, d2, bm, dm)
    else:
        r = {"Mr": 0.0, "c": 0.0, "a": 0.0, "eps_s": 0.0, "eps_s2": 0.0, "sigma_s": 0.0, "sigma_s2": 0.0}
    Mr = r["Mr"]

    rho_s = As_s / (bmm * d)
    rho2_s = As2_s / (bmm * d)
    kontroller = [_kontrol("Eğilme taşıma gücü Md ≤ Mr", M / 1e6, Mr / 1e6, K_TS500["blok"], "kN·m")]
    kontroller.append(_kontrol("En az donatı ρ ≥ ρmin", rho_min, rho_s, K_TS500["rho_min"]))
    kontroller.append(_kontrol("ρ − ρ′ ≤ 0,85ρb", rho_s - rho2_s, rho_085, K_TS500["rho_085"]))
    kontroller.append(_kontrol("ρ ≤ 0,02", rho_s, 0.02, K_TS500["rho_002"]))
    kontroller.append(_kontrol("Kiriş yüksekliği h ≥ 300 mm", 300.0, hmm, K_TS500["kiris_boyut"], "mm"))
    kontroller.append(_kontrol("Gövde genişliği bw ≥ 200 mm", 200.0, bmm, K_TS500["kiris_boyut"], "mm"))
    if tbdy:
        kontroller.append(_kontrol("TBDY: bw ≥ 250 mm", 250.0, bmm, K_TS500["kiris_boyut_tbdy"], "mm"))
        kontroller.append(_kontrol("TBDY: h ≤ 3,5 bw", hmm, 3.5 * bmm, K_TS500["kiris_boyut_tbdy"], "mm"))
    if As_mevcut is None and oneri is not None:
        kontroller.append(_kontrol("Çubuk net aralığı (tek sıra)", oneri["gerekli_aralik_mm"],
                                   max(oneri["net_aralik_mm"], 1e-9), K_TS500["aralik"], "mm"))
        if not oneri["sigar"]:
            uyarilar.append(f"Önerilen {oneri['metin']} tek sıraya sığmıyor (net aralık {oneri['net_aralik_mm']:.0f} mm < "
                            f"{oneri['gerekli_aralik_mm']:.0f} mm); iki sıra donatı ya da daha geniş kesit düşünün.")

    dc = max(k["dc"] for k in kontroller)
    boyut_yetersiz = any(not k["saglandi"] for k in kontroller if "mm" == k["birim"] and "aralığı" not in k["ad"])
    if kesit_kucuk or boyut_yetersiz or rho_s > 0.02 + 1e-12:
        durum = "kesit büyüt"
    elif dc > 1.0 + 1e-9:
        durum = "donatı artır"
    else:
        durum = "yeterli"
    if kesit_kucuk:
        dc = max(dc, _dc(rho_gerekli if math.isfinite(rho_gerekli) else DC_UST, 0.02))

    sonuc = _json({
        "tur": "kiris_egilme", "beton": bm["sinif"], "donati": dm["sinif"],
        "Md_kNm": Md_kNm, "b_mm": bmm, "h_mm": hmm, "d_mm": d, "d2_mm": d2,
        "fcd": fcd, "fyd": fyd, "fctd": bm["fctd"], "k1": k1,
        "rho_b": rho_b, "rho_085b": rho_085, "rho_min": rho_min, "rho_max": rho_lim,
        "tek_donatili": tek, "a_mm": a, "c_mm": c,
        "As_gerekli_cm2": As_gerekli / 100.0 if math.isfinite(As_gerekli) else None,
        "As_ust_gerekli_cm2": As2 / 100.0 if math.isfinite(As2) else None,
        "rho_gerekli": rho_gerekli if math.isfinite(rho_gerekli) else None,
        "sigma_s_ust_MPa": sigma2, "ust_akiyor": ust_akiyor,
        "oneri": oneri, "oneri_ust": oneri_ust,
        "As_saglanan_cm2": As_s / 100.0, "As_ust_saglanan_cm2": As2_s / 100.0,
        "rho_saglanan": rho_s, "Mr_kNm": Mr / 1e6, "c_r_mm": r["c"], "a_r_mm": r["a"], "eps_s_r": r["eps_s"],
        "dc": dc, "durum": durum, "kontroller": kontroller, "uyarilar": uyarilar,
    })
    if anl is not None:
        _anlat_kiris_egilme(anl, sonuc, bm, dm, M, R, M_lim, As_lim, a_lim)
    return sonuc


def _anlat_kiris_egilme(anl, s, bm, dm, M, R, M_lim, As_lim, a_lim):
    b, h, d = s["b_mm"], s["h_mm"], s["d_mm"]
    _basla(anl, "Kiriş eğilme tasarımı (TS 500)",
           "Kirişin kesitinde tasarım momenti Md'yi taşıyacak çekme donatısını buluyoruz. Beton basıncı eşdeğer "
           "dikdörtgen blokla (0,85 fcd, derinlik a = k₁c), çelik akma gerilmesiyle (fyd) temsil edilir; iç kuvvet "
           "çifti dış momente eşitlenir. Sonra donatının çok az (gevrek kırılma) ya da çok fazla (sünek olmayan "
           "kırılma) olmadığını yönetmelik sınırlarıyla denetleriz.")
    _birim_notu(anl)
    anl.mat(rf"M_d = {_L(s['Md_kNm'])}\ \text{{kN·m}} = {_L(M)}\ \text{{N·mm}},\quad b = {_L(b, 0)}\ \text{{mm}},\quad "
            rf"h = {_L(h, 0)}\ \text{{mm}},\quad d = h - d' = {_L(h, 0)} - {_L(h - d, 0)} = {_L(d, 0)}\ \text{{mm}}")
    _anlat_malzeme(anl, bm, dm)
    anl.kural("TS 500 md. 7.1 varsayımları: betonun çekme dayanımı ihmal edilir, düzlem kesitler düzlem kalır, "
              "en dış basınç lifinde εcu = 0,003; çelik elasto-plastik (σs = Es·εs ≤ fyd); beton basıncı 0,85 fcd "
              "şiddetinde, a = k₁c derinliğinde dikdörtgen blok.")
    anl.metin("**Donatı sınırları.** Dengeli donatı oranı ρb, çeliğin aktığı anda betonun ezildiği orandır. "
              "TS 500 ρb için kapalı form vermez (md. 0.2.5 yalnız tanım); md. 7.1 varsayımlarından "
              "(εcu = 0,003, Es = 2·10⁵ MPa) türetilir:")
    anl.mat(rf"\rho_b = 0{{,}}85\,k_1\,\frac{{f_{{cd}}}}{{f_{{yd}}}}\cdot\frac{{600}}{{600 + f_{{yd}}}} = "
            rf"0{{,}}85 \cdot {_L(s['k1'])} \cdot \frac{{{_L(s['fcd'], 3)}}}{{{_L(s['fyd'])}}} \cdot "
            rf"\frac{{600}}{{600 + {_L(s['fyd'])}}} = {_L(s['rho_b'], 5)}")
    anl.mat(rf"\rho_{{min}} = 0{{,}}8\frac{{f_{{ctd}}}}{{f_{{yd}}}} = 0{{,}}8\cdot\frac{{{_L(s['fctd'], 3)}}}{{{_L(s['fyd'])}}}"
            rf" = {_L(s['rho_min'], 5)}\ (\text{{Denk. 7.3}}),\qquad \rho - \rho' \le 0{{,}}85\rho_b = {_L(s['rho_085b'], 5)}"
            rf"\ (\text{{Denk. 7.4}}),\qquad \rho \le 0{{,}}02\ (\text{{Denk. 7.5; TBDY 7.4.2.4}})")
    anl.metin(f"Tek donatılı kesitte üst sınır ρmax = min(0,85ρb; 0,02) = {s['rho_max']:.5f}. Bu orana karşılık gelen "
              "moment, tek donatıyla taşınabilecek en büyük momenttir:")
    anl.mat(rf"A_{{s,lim}} = \rho_{{max}}\,b\,d = {_L(As_lim, 1)}\ \text{{mm}}^2,\quad a_{{lim}} = \frac{{A_{{s,lim}} f_{{yd}}}}"
            rf"{{0{{,}}85 f_{{cd}} b}} = {_L(a_lim, 1)}\ \text{{mm}},\quad M_{{lim}} = A_{{s,lim}} f_{{yd}}\left(d - \frac{{a_{{lim}}}}{{2}}\right)"
            rf" = {_L(M_lim / 1e6)}\ \text{{kN·m}}")
    if s["tek_donatili"]:
        anl.metin(f"Md = {_f(s['Md_kNm'])} kN·m ≤ M_lim → **tek donatılı** kesit yeterli. Denge "
                  "0,85 fcd·b·a = As·fyd ve moment Md = As·fyd·(d − a/2) birlikte çözülürse:")
        anl.mat(rf"a = d - \sqrt{{d^2 - \frac{{2M_d}}{{0{{,}}85 f_{{cd}} b}}}} = {_L(d, 0)} - \sqrt{{{_L(d, 0)}^2 - "
                rf"\frac{{2\cdot {_L(M)}}}{{{_L(R, 1)}}}}} = {_L(s['a_mm'], 2)}\ \text{{mm}}")
        As_hes = R * s["a_mm"] / s["fyd"]
        anl.mat(rf"A_s = \frac{{0{{,}}85 f_{{cd}}\,b\,a}}{{f_{{yd}}}} = \frac{{{_L(R, 1)} \cdot {_L(s['a_mm'], 2)}}}"
                rf"{{{_L(s['fyd'])}}} = {_L(As_hes, 1)}\ \text{{mm}}^2 = {_L(As_hes / 100, 2)}\ \text{{cm}}^2")
        if As_hes < s["rho_min"] * b * d:
            anl.metin(f"Bulunan donatı ρmin·b·d = {_f(s['rho_min'] * b * d, 1)} mm²'den az; en az donatı esas alınır.")
    elif s["As_ust_gerekli_cm2"] is not None:
        anl.metin(f"Md = {_f(s['Md_kNm'])} kN·m > M_lim → **çift donatılı** kesit: fazla moment M₂ = Md − M_lim "
                  "basınç donatısı As′ ile ona eşit ek çekme donatısının oluşturduğu kuvvet çiftine verilir.")
        c = s["c_mm"]
        anl.mat(rf"c = \frac{{a_{{lim}}}}{{k_1}} = {_L(c, 1)}\ \text{{mm}},\quad \varepsilon_s' = 0{{,}}003\,\frac{{c - d'}}{{c}} = "
                rf"{_L(EPS_CU * (c - s['d2_mm']) / c, 5)},\quad \sigma_s' = \min(E_s\varepsilon_s',\ f_{{yd}}) = "
                rf"{_L(s['sigma_s_ust_MPa'], 1)}\ \text{{MPa}}")
        anl.mat(rf"A_s' = \frac{{M_d - M_{{lim}}}}{{\sigma_s'(d - d')}} = {_L(s['As_ust_gerekli_cm2'] * 100, 1)}\ \text{{mm}}^2,"
                rf"\quad A_s = A_{{s,lim}} + A_s'\frac{{\sigma_s'}}{{f_{{yd}}}} = {_L(s['As_gerekli_cm2'] * 100, 1)}\ \text{{mm}}^2")
    else:
        anl.uyari("Gerekli donatı ρ ≤ 0,02 sınırını aşıyor: kesit büyütülmeli.")
    if s["oneri"]:
        o = s["oneri"]
        anl.metin(f"**Donatı önerisi:** {o['metin']} (As = {_f(o['As_cm2'])} cm²); tek sırada net aralık ≈ "
                  f"{_f(o['net_aralik_mm'], 0)} mm (gerekli ≥ {_f(o['gerekli_aralik_mm'], 0)} mm, {K_TS500['aralik']}).")
        if s["oneri_ust"]:
            anl.metin(f"Basınç donatısı önerisi: {s['oneri_ust']['metin']} (As′ = {_f(s['oneri_ust']['As_cm2'])} cm²).")
    if s["As_saglanan_cm2"] > 0:
        anl.metin(f"**Taşıma gücü (sağlanan As = {_f(s['As_saglanan_cm2'])} cm², As′ = {_f(s['As_ust_saglanan_cm2'])} cm²).** "
                  "Tarafsız eksen derinliği c, kuvvet dengesinden şekil değiştirme uygunluğuyla bulunur; çeliklerin "
                  "akıp akmadığı birim uzamadan okunur:")
        anl.mat(rf"0{{,}}85 f_{{cd}} b\,k_1 c + A_s'\sigma_s'(c) = A_s\sigma_s(c) \Rightarrow c = {_L(s['c_r_mm'], 1)}\ \text{{mm}},"
                rf"\quad \varepsilon_s = 0{{,}}003\frac{{d - c}}{{c}} = {_L(s['eps_s_r'], 5)}"
                rf"\ (" + ("\\ge" if s["eps_s_r"] >= dm["eps_yd"] else "<") + r"\ \varepsilon_{yd})")
        anl.mat(rf"M_r = 0{{,}}85 f_{{cd}} b\,a\left(d - \frac{{a}}{{2}}\right) + A_s'\sigma_s'(d - d') = {_L(s['Mr_kNm'])}"
                rf"\ \text{{kN·m}},\qquad \frac{{M_d}}{{M_r}} = {_L(s['Md_kNm'] / max(s['Mr_kNm'], 1e-9), 3)}")
        alt = [(c["adet"], c["cap"]) for c in s["oneri"]["cubuklar"]] if (s["oneri"] and s["As_saglanan_cm2"] ==
                                                                         s["oneri"]["As_cm2"]) else []
        ust = [(c["adet"], c["cap"]) for c in s["oneri_ust"]["cubuklar"]] if s["oneri_ust"] else []
        _sema(anl, "Kiriş kesiti, basınç bloğu ve birim uzama",
              [("Kesit: basınç bloğu (amber), tarafsız eksen (kesikli), donatı (mavi); sağda birim uzama dağılımı",
                _svg_kiris_kesit(b, h, d, s["d2_mm"], alt, ust, s["a_r_mm"], s["c_r_mm"], s["eps_s_r"],
                                 "Kiriş kesiti"))])
    _durum_ozet(anl, s)


# ============================================================================
# A3) Kiriş kesme (TS 500)
# ============================================================================
def kiris_kesme(Vd, b, h, paspayi, beton="C30", etriye="B420C", Nd=0.0, etriye_cap=None, kol=2, sarilma=False,
                boyuna_cap=None, anl=None) -> dict:
    """TS 500 md. 8.1 kesme tasarımı. Vd (kN, mesnet yüzünden d uzaklıkta), Nd (kN, basınç +, çekme −).

    ``etriye_cap`` verilmezse Φ8 → Φ10 → Φ12 denenir; ``kol`` etriye kol sayısı; ``sarilma=True`` ise TBDY 7.4.4
    sarılma bölgesi aralık koşulları (s ≤ d/4, 8Φl, 150 mm) da uygulanır (``boyuna_cap`` mm verilirse 8Φl).

    Dönüş: d_mm, V_cr_kN, V_c_kN, V_max_kN, Asw_s_gerekli (mm²/mm), Asw_s_min, Asw_s_tasarim, hesap_gerekli,
    s_max_mm, oneri {cap, kol, s_mm, metin, Asw_s}, V_w_kN, V_r_kN, dc, durum, kontroller, uyarilar."""
    Vd_kN = _sayi(Vd, "Vd (kN)")
    bmm = _boyut(b, "b (kiriş genişliği)")
    hmm = _boyut(h, "h (kiriş yüksekliği)")
    pas = _sayi(paspayi, "paspayı (m)", pozitif=True, sifir_olur=False) * 1000.0
    if pas >= hmm / 2:
        raise MatrisHatasi(f"Paspayı {pas:.0f} mm, h/2 = {hmm / 2:.0f} mm'den küçük olmalı.")
    Nd_kN = _sayi(Nd, "Nd (kN)")
    kol = int(_sayi(kol, "etriye kol sayısı", pozitif=True, sifir_olur=False))
    bm = beton if isinstance(beton, dict) and "fcd" in beton else beton_malzeme(beton)
    em = etriye if isinstance(etriye, dict) and "fyd" in etriye else donati_malzeme(etriye)
    fctd, fcd, fywd = bm["fctd"], bm["fcd"], em["fyd"]
    d = hmm - pas
    V = abs(Vd_kN) * 1e3
    N = Nd_kN * 1e3
    Ac = bmm * hmm
    if N > 0:
        gamma = 0.07
    elif N < 0 and abs(N) / Ac >= 0.5:
        gamma = -0.3
    else:
        gamma = 0.0
    Vcr = 0.65 * fctd * bmm * d * (1.0 + gamma * abs(N) / Ac)
    Vc = 0.8 * Vcr
    Vmax = 0.22 * fcd * bmm * d
    Asw_min = 0.3 * fctd * bmm / fywd
    hesap = V > Vcr
    Asw_ger = max((V - Vc) / (fywd * d), 0.0) if hesap else 0.0
    Asw_tas = max(Asw_ger, Asw_min)
    s_max = d / 2.0
    s_kaynak = "s ≤ d/2"
    if V > 3.0 * Vcr:
        s_max = d / 4.0
        s_kaynak = "Vd > 3Vcr → s ≤ d/4"
    if sarilma:
        sinir = [d / 4.0, 150.0] + ([8.0 * _sayi(boyuna_cap, "boyuna_cap (mm)", pozitif=True)] if boyuna_cap else [])
        s_max = min([s_max] + sinir)
        s_kaynak += "; sarılma: s ≤ d/4, 150 mm" + (", 8Φl" if boyuna_cap else "")
    caplar = (int(etriye_cap),) if etriye_cap else ETRIYE_CAPLARI
    oneri = None
    for cap in caplar:
        Ao = kol * _cubuk_alani(cap)
        s = min(Ao / Asw_tas, s_max)
        s_yuv = math.floor(s / 10.0 + 1e-9) * 10.0
        if s_yuv >= 50.0:
            oneri = {"cap": cap, "kol": kol, "s_mm": s_yuv, "metin": f"Φ{cap}/{s_yuv / 10:.0f} ({kol} kollu)",
                     "Asw_s": Ao / s_yuv}
            break
    uyarilar = []
    if oneri is None:
        cap = caplar[-1]
        Ao = kol * _cubuk_alani(cap)
        oneri = {"cap": cap, "kol": kol, "s_mm": 50.0, "metin": f"Φ{cap}/5 ({kol} kollu)", "Asw_s": Ao / 50.0}
        uyarilar.append("Etriye 50 mm'den sık çıkıyor; kol sayısını artırın ya da kesiti büyütün.")
    Vw = oneri["Asw_s"] * fywd * d
    Vr = Vc + Vw
    if sarilma:
        uyarilar.append("Sarılma bölgesinde deprem kesmesi toplam kesmenin yarısından büyükse TBDY 7.4.5.3'e göre "
                        "Vc = 0 alınmalıdır (bu hesapta Vc korunmuştur).")
    kontroller = [
        _kontrol("Kesme üst sınırı Vd ≤ 0,22 fcd bw d", V / 1e3, Vmax / 1e3, K_TS500["Vmax"], "kN"),
        _kontrol("Kesme dayanımı Vd ≤ Vc + Vw", V / 1e3, Vr / 1e3, f"{K_TS500['Vc']}; {K_TS500['Vw']}", "kN"),
        _kontrol("En az etriye Asw/s ≥ 0,3 fctd bw / fywd", Asw_min, oneri["Asw_s"], K_TS500["Vmin"], "mm²/mm"),
        _kontrol(f"Etriye aralığı ({s_kaynak})", oneri["s_mm"], s_max,
                 K_TS500["s"] + ("; " + K_TS500["s_tbdy"] if sarilma else ""), "mm"),
    ]
    dc = max(k["dc"] for k in kontroller)
    if V > Vmax:
        durum = "kesit büyüt"
    elif dc > 1.0 + 1e-9:
        durum = "donatı artır"
    else:
        durum = "yeterli"
    sonuc = _json({
        "tur": "kiris_kesme", "beton": bm["sinif"], "etriye": em["sinif"], "Vd_kN": Vd_kN, "Nd_kN": Nd_kN,
        "b_mm": bmm, "h_mm": hmm, "d_mm": d, "fctd": fctd, "fcd": fcd, "fywd": fywd, "gamma": gamma,
        "V_cr_kN": Vcr / 1e3, "V_c_kN": Vc / 1e3, "V_max_kN": Vmax / 1e3, "hesap_gerekli": hesap,
        "Asw_s_gerekli": Asw_ger, "Asw_s_min": Asw_min, "Asw_s_tasarim": Asw_tas,
        "Asw_s_gerekli_cm2_m": Asw_ger * 10.0, "Asw_s_min_cm2_m": Asw_min * 10.0,
        "s_max_mm": s_max, "oneri": oneri, "V_w_kN": Vw / 1e3, "V_r_kN": Vr / 1e3,
        "dc": dc, "durum": durum, "kontroller": kontroller, "uyarilar": uyarilar,
    })
    if anl is not None:
        _basla(anl, "Kiriş kesme tasarımı (TS 500 md. 8.1)",
               "Kesme kuvveti betonda eğik çatlaklar açar. Çatlamaya kadar kesmeyi beton taşır (Vcr); çatlak "
               "sonrası betonun katkısı Vc = 0,8 Vcr kabul edilir, kalanını etriyeler taşır. Beton basınç "
               "dikmelerinin ezilmemesi için kesmeye bir üst sınır (0,22 fcd bw d) konur.")
        _birim_notu(anl)
        anl.mat(rf"V_d = {_L(Vd_kN)}\ \text{{kN}} = {_L(V, 0)}\ \text{{N}},\quad b_w = {_L(bmm, 0)},\ d = {_L(d, 0)}\ \text{{mm}},"
                rf"\quad f_{{ctd}} = {_L(fctd, 3)},\ f_{{cd}} = {_L(fcd, 3)},\ f_{{ywd}} = {_L(fywd)}\ \text{{MPa}}")
        anl.metin(f"Eksenel kuvvet katsayısı γ = {gamma} (basınçta 0,07; çekmede −0,3; çekme gerilmesi 0,5 MPa'dan "
                  f"küçükse 0) — {K_TS500['Vcr']}.")
        anl.mat(rf"V_{{cr}} = 0{{,}}65 f_{{ctd}} b_w d\left(1 + \gamma\frac{{N_d}}{{A_c}}\right) = 0{{,}}65\cdot{_L(fctd, 3)}"
                rf"\cdot{_L(bmm, 0)}\cdot{_L(d, 0)}\cdot\left(1 + {_L(gamma)}\cdot\frac{{{_L(abs(N), 0)}}}{{{_L(Ac, 0)}}}\right)"
                rf" = {_L(Vcr / 1e3)}\ \text{{kN}}")
        anl.mat(rf"V_c = 0{{,}}8V_{{cr}} = {_L(Vc / 1e3)}\ \text{{kN}},\qquad V_{{max}} = 0{{,}}22 f_{{cd}} b_w d = "
                rf"{_L(Vmax / 1e3)}\ \text{{kN}}\ (\text{{Denk. 8.7}})")
        if hesap:
            anl.mat(rf"\frac{{A_{{sw}}}}{{s}} = \frac{{V_d - V_c}}{{f_{{ywd}}\,d}} = \frac{{{_L(V, 0)} - {_L(Vc, 0)}}}"
                    rf"{{{_L(fywd)}\cdot{_L(d, 0)}}} = {_L(Asw_ger, 4)}\ \text{{mm}}^2/\text{{mm}}")
        else:
            anl.metin("Vd ≤ Vcr: hesap gerekmez, en az etriye konur.")
        anl.mat(rf"\left(\frac{{A_{{sw}}}}{{s}}\right)_{{min}} = 0{{,}}3\frac{{f_{{ctd}}}}{{f_{{ywd}}}}b_w = {_L(Asw_min, 4)}"
                rf"\ \text{{mm}}^2/\text{{mm}}\ (\text{{Denk. 8.6}})")
        anl.metin(f"Aralık sınırı ({K_TS500['s']}): {s_kaynak} → s_max = {_f(s_max, 0)} mm. Öneri: **{oneri['metin']}** "
                  f"(Asw/s = {_f(oneri['Asw_s'], 4)} mm²/mm).")
        anl.mat(rf"V_w = \frac{{A_{{sw}}}}{{s}} f_{{ywd}} d = {_L(Vw / 1e3)}\ \text{{kN}},\qquad V_r = V_c + V_w = {_L(Vr / 1e3)}"
                rf"\ \text{{kN}}")
        _durum_ozet(anl, sonuc)
    return sonuc


# ============================================================================
# A4) Kolon N–M etkileşimi (TS 500)
# ============================================================================
def _kolon_cubuklari(bx, by, As, pas, yerlesim, n_cubuk):
    """Çubuklar [(x, y, alan)] (mm, kesit merkezinden; x genişlik bx yönünde, y yükseklik by yönünde)."""
    if yerlesim not in ("iki_yuz", "dort_yuz"):
        raise MatrisHatasi(f"yerlesim {yerlesim!r} tanımsız; 'iki_yuz' ya da 'dort_yuz' olmalı.")
    xa, ya = bx / 2 - pas, by / 2 - pas
    if yerlesim == "iki_yuz":
        n = 4 if n_cubuk is None else int(n_cubuk)
        if n < 4 or n % 2:
            raise MatrisHatasi("iki_yuz yerleşimde çubuk sayısı çift ve en az 4 olmalı (her yüzde en az 2).")
        m = n // 2
        xs = [-xa + 2 * xa * i / (m - 1) for i in range(m)]
        noktalar = [(x, ya) for x in xs] + [(x, -ya) for x in xs]
    else:
        n = 8 if n_cubuk is None else int(n_cubuk)
        if n < 4 or n % 2:
            raise MatrisHatasi("dort_yuz yerleşimde çubuk sayısı çift ve en az 4 olmalı (4 köşe + yüzlere eşit).")
        ek = (n - 4) // 2
        eb = int(round(ek * bx / (bx + by)))
        eh = ek - eb
        noktalar = [(-xa, ya), (xa, ya), (-xa, -ya), (xa, -ya)]
        for i in range(1, eb + 1):
            x = -xa + 2 * xa * i / (eb + 1)
            noktalar += [(x, ya), (x, -ya)]
        for i in range(1, eh + 1):
            y = -ya + 2 * ya * i / (eh + 1)
            noktalar += [(-xa, y), (xa, y)]
    A1 = As / len(noktalar)
    return [(x, y, A1) for x, y in noktalar]


def _katmanlar(cubuklar, eksen, bx, by):
    """Eğilme eksenine göre (derinlik, alan, çap) katmanları; derinlik basınç yüzünden ölçülür."""
    kat = {}
    for x, y, A in cubuklar:
        dd = by / 2 - y if eksen == "x" else bx / 2 - x
        anahtar = round(dd, 6)
        kat.setdefault(anahtar, [0.0, 0])
        kat[anahtar][0] += A
        kat[anahtar][1] += 1
    cap = math.sqrt(4 * cubuklar[0][2] / math.pi)
    return [(dd, A, n, cap) for dd, (A, n) in sorted(kat.items())]


def _nm_nokta(c, gen, yuk, katmanlar, bm, dm):
    """Tarafsız eksen derinliği c (mm) için (N [N], M [N·mm], katman bilgisi). Basınç +."""
    fcd, k1, fyd, Es = bm["fcd"], bm["k1"], dm["fyd"], dm["Es"]
    a = min(k1 * c, yuk)
    Cc = 0.85 * fcd * gen * a
    N = Cc
    Mm = Cc * (yuk / 2 - a / 2)
    bilgi = []
    for dd, A, n, cap in katmanlar:
        eps = EPS_CU * (c - dd) / c
        sig = max(-fyd, min(fyd, Es * eps))
        # blok içindeki çubuğun yerini aldığı beton (çubuk çapı boyunca sürekli geçiş)
        oran = min(max((a - (dd - cap / 2)) / cap, 0.0), 1.0)
        F = A * sig - oran * 0.85 * fcd * A
        N += F
        Mm += F * (yuk / 2 - dd)
        bilgi.append({"derinlik_mm": dd, "As_mm2": A, "adet": n, "eps": eps, "sigma_MPa": sig, "F_kN": F / 1e3})
    return N, Mm, a, bilgi


def _egri(gen, yuk, katmanlar, bm, dm, n):
    As = sum(k[1] for k in katmanlar)
    N0 = 0.85 * bm["fcd"] * (gen * yuk - As) + As * dm["fyd"]
    Nt = -As * dm["fyd"]
    dmax = max(k[0] for k in katmanlar)
    cb = EPS_CU * dmax / (EPS_CU + dm["eps_yd"])
    n = max(int(n), 12)
    n1 = n // 2
    # c_dolu: blok tüm kesiti kapladı ve en uzak çubuk da basınçta aktı → N = N0 (daha büyük c yeni nokta vermez)
    dmin = min(k[0] for k in katmanlar)
    c_dolu = yuk / bm["k1"]
    if dm["eps_yd"] < EPS_CU:
        c_dolu = max(c_dolu, EPS_CU * dmax / (EPS_CU - dm["eps_yd"]))
    else:  # pragma: no cover - fyd/Es ≥ 0,003 olan donatı yok
        c_dolu = max(c_dolu, 3.0 * yuk)
    c_dolu = max(c_dolu, 0.6 * yuk * 1.01, dmin)
    cs = list(yuk * np.geomspace(0.01, 0.6, n1)) + list(np.linspace(0.6 * yuk, c_dolu, n - n1 + 1)[1:-1])
    cs.append(cb)
    cs = sorted(set(float(c) for c in cs))
    noktalar = [{"c_mm": None, "N_kN": Nt / 1e3, "M_kNm": 0.0, "uc": "saf çekme"}]
    for c in cs:
        N, Mm, a, _ = _nm_nokta(c, gen, yuk, katmanlar, bm, dm)
        if N <= Nt + 1e-6 or N >= N0 - 1e-6:
            continue
        noktalar.append({"c_mm": c, "N_kN": N / 1e3, "M_kNm": Mm / 1e6, "a_mm": a})
    noktalar.append({"c_mm": None, "N_kN": N0 / 1e3, "M_kNm": 0.0, "uc": "saf basınç"})
    Nb, Mb, ab, bilgi_b = _nm_nokta(cb, gen, yuk, katmanlar, bm, dm)
    dengeli = {"c_mm": cb, "a_mm": ab, "N_kN": Nb / 1e3, "M_kNm": Mb / 1e6, "eps_s": bilgi_b[-1]["eps"] * -1.0,
               "eps_yd": dm["eps_yd"], "katmanlar": bilgi_b}
    return noktalar, N0, Nt, dengeli


def _isin_kesisim(egri, Nd, Md):
    """Orijinden (Nd, Md) yönündeki ışının eğriyi kestiği nokta: (dc, N, M). egri: [(N, M)] (M ≥ 0)."""
    Md = abs(Md)
    if abs(Nd) < 1e-12 and Md < 1e-12:
        return 0.0, None, None
    for i in range(len(egri) - 1):
        (n1, m1), (n2, m2) = egri[i], egri[i + 1]
        # t·(Nd, Md) = P1 + u(P2 − P1)
        dx, dy = n2 - n1, m2 - m1
        # çöz: t*Nd - u*dx = n1 ; t*Md - u*dy = m1
        D = Nd * (-dy) - (-dx) * Md
        if abs(D) < 1e-15:
            continue
        t = (n1 * (-dy) - (-dx) * m1) / D
        u = (Nd * m1 - Md * n1) / D
        if -1e-9 <= u <= 1 + 1e-9 and t > 0:
            return 1.0 / t, n1 + u * dx, m1 + u * dy
    return DC_UST, None, None


def _isin_kesisim_cok(eg, Nds, Mds):
    """``_isin_kesisim``'in çok ışınlı vektörel karşılığı (numpy; sonuç bit bit aynı: aynı işlem sırası, ilk kesişen parça).
    eg: (k × 2) dizi [(N, M)]; Nds, Mds: ışın listeleri. Dönüş [(dc, N, M)] (Python float ya da None)."""
    m = len(Nds)
    if m == 0:
        return []
    Nd = np.asarray(Nds, dtype=float)[:, None]
    Md = np.abs(np.asarray(Mds, dtype=float))[:, None]
    n1, m1 = eg[:-1, 0], eg[:-1, 1]
    dx, dy = eg[1:, 0] - n1, eg[1:, 1] - m1
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        D = Nd * (-dy) - (-dx) * Md
        t = (n1 * (-dy) - (-dx) * m1) / D
        u = (Nd * m1 - Md * n1) / D
        ok = (np.abs(D) >= 1e-15) & (u >= -1e-9) & (u <= 1 + 1e-9) & (t > 0)
    var = ok.any(axis=1)
    ilk = ok.argmax(axis=1)
    out = []
    for r in range(m):
        N_, M_ = float(Nd[r, 0]), float(Md[r, 0])
        if abs(N_) < 1e-12 and M_ < 1e-12:
            out.append((0.0, None, None))
        elif not var[r]:
            out.append((DC_UST, None, None))
        else:
            i = int(ilk[r])
            uu = float(u[r, i])
            out.append((1.0 / float(t[r, i]), float(n1[i]) + uu * float(dx[i]), float(m1[i]) + uu * float(dy[i])))
    return out


def _M_kapasite(egri, N):
    """Eğri üzerinde verilen N için M kapasitesi (N aralık dışındaysa 0)."""
    Ns = [p[0] for p in egri]
    if N <= Ns[0] or N >= Ns[-1]:
        return 0.0
    for i in range(len(egri) - 1):
        (n1, m1), (n2, m2) = egri[i], egri[i + 1]
        if n1 <= N <= n2 and n2 > n1:
            return m1 + (m2 - m1) * (N - n1) / (n2 - n1)
    return 0.0


def _kolon_hazirla(b, h, As_toplam, paspayi, beton, donati, yerlesim, n_cubuk):
    bmm = _boyut(b, "b (kolon genişliği)")
    hmm = _boyut(h, "h (kolon yüksekliği)")
    pas = _sayi(paspayi, "paspayı (m)", pozitif=True, sifir_olur=False) * 1000.0
    if pas >= min(bmm, hmm) / 2:
        raise MatrisHatasi(f"Paspayı {pas:.0f} mm, kesitin en küçük boyutunun yarısından ({min(bmm, hmm) / 2:.0f} mm) "
                           "küçük olmalı (m girilir: 5 cm → 0.05).")
    As = _sayi(As_toplam, "As_toplam (cm²)", pozitif=True, sifir_olur=False) * 100.0
    if As >= bmm * hmm:
        raise MatrisHatasi("Donatı alanı beton alanından büyük olamaz (As cm² girilir).")
    bm, dm = _malzemeler(beton, donati)
    cubuklar = _kolon_cubuklari(bmm, hmm, As, pas, yerlesim, n_cubuk)
    return bmm, hmm, pas, As, bm, dm, cubuklar


def kolon_etkilesim(b, h, As_toplam, paspayi, beton="C30", donati="B420C", eksen="x", n=60, yerlesim="dort_yuz",
                    n_cubuk=None, anl=None, ham=False) -> dict:
    """TS 500 dikdörtgen kolon N–M etkileşim eğrisi (şekil değiştirme uygunluğu, md. 7.1 varsayımları).

    b (x yönü), h (y yönü), paspayi (m; boyuna çubuk merkezinin dış yüze uzaklığı), As_toplam (cm², simetrik).
    ``eksen="x"``: x ekseni etrafında eğilme (derinlik h); ``"y"``: y ekseni etrafında (derinlik b).
    ``yerlesim``: "dort_yuz" (varsayılan 8 çubuk) ya da "iki_yuz" (varsayılan 4 çubuk; eğilme yüzlerinde).
    c taranır (saf çekmeden saf basınca); blok a = k₁c ≤ derinlik; σs = Es εs ≤ fyd; bloktaki çubuğun yerini aldığı
    beton düşülür. N (kN, basınç +), M (kN·m, kesit ağırlık merkezine göre).

    Dönüş: noktalar [{c_mm, N_kN, M_kNm}] (N artan), N0_kN, Nt_kN, dengeli {c_mm, N_kN, M_kNm, eps_s, eps_yd},
    N_max_TS500_kN (0,9 fcd Ac), N_max_TBDY_kN (0,40 fck Ac), rho, cubuklar, katmanlar.

    ``ham=True`` (iç kullanım, ör. kesit önerisi taramaları): önbellekteki yalın sözlük döner (_json dönüşümü yok; salt okunur,
    değiştirilmemeli). Eğriler (b, h, As, paspayı, beton, donatı, eksen, n, yerleşim, çubuk sayısı) anahtarıyla önbellektedir."""
    sonuc, gen, yuk, katmanlar, _, bm, dm = _etkilesim_ham(b, h, As_toplam, paspayi, beton, donati, eksen, n, yerlesim, n_cubuk)
    if ham and anl is None:
        return sonuc
    sonuc = _json(sonuc)
    if anl is not None:
        _anlat_kolon_egri(anl, sonuc, bm, dm, gen, yuk, katmanlar)
    return sonuc


def _malz_anahtar(m):
    """Malzeme sözlüğü → önbellek anahtarı (sıralı (ad, değer) demeti); karılmayan değer varsa None (önbelleksiz hesap)."""
    try:
        k = tuple(sorted(m.items()))
        hash(k)
        return k
    except TypeError:
        return None


def _etkilesim_ham(b, h, As_toplam, paspayi, beton, donati, eksen, n, yerlesim, n_cubuk):
    """kolon_etkilesim'in denetimli, önbellekli iç hesabı → (yalın sonuç, genişlik, derinlik, katmanlar, eğri dizisi (k × 2:
    N, M), bm, dm). Dönen sözlük ve dizi önbellekte paylaşılır: değiştirilmez."""
    bmm, hmm, pas, As, bm, dm, cubuklar = _kolon_hazirla(b, h, As_toplam, paspayi, beton, donati, yerlesim, n_cubuk)
    if eksen not in ("x", "y"):
        raise MatrisHatasi(f"eksen {eksen!r} tanımsız; 'x' ya da 'y' olmalı.")
    bmk, dmk = _malz_anahtar(bm), _malz_anahtar(dm)
    try:
        anahtar = (bmm, hmm, pas, As, bmk, dmk, eksen, n, yerlesim, n_cubuk)
        hash(anahtar)
    except TypeError:
        anahtar = None
    if anahtar is None or bmk is None or dmk is None:
        r = _etkilesim_hesap(bmm, hmm, pas, As, bm, dm, cubuklar, eksen, n, yerlesim)
    else:
        r = _etkilesim_onbellek(*anahtar)
    return r + (bm, dm)


@functools.lru_cache(maxsize=512)
def _etkilesim_onbellek(bmm, hmm, pas, As, bmk, dmk, eksen, n, yerlesim, n_cubuk):
    cubuklar = _kolon_cubuklari(bmm, hmm, As, pas, yerlesim, n_cubuk)
    return _etkilesim_hesap(bmm, hmm, pas, As, dict(bmk), dict(dmk), cubuklar, eksen, n, yerlesim)


def _etkilesim_hesap(bmm, hmm, pas, As, bm, dm, cubuklar, eksen, n, yerlesim):
    gen, yuk = (bmm, hmm) if eksen == "x" else (hmm, bmm)
    katmanlar = _katmanlar(cubuklar, eksen, bmm, hmm)
    noktalar, N0, Nt, dengeli = _egri(gen, yuk, katmanlar, bm, dm, n)
    Ac = bmm * hmm
    sonuc = ({
        "tur": "kolon_etkilesim", "eksen": eksen, "beton": bm["sinif"], "donati": dm["sinif"],
        "b_mm": bmm, "h_mm": hmm, "derinlik_mm": yuk, "genislik_mm": gen, "paspayi_mm": pas,
        "As_mm2": As, "As_cm2": As / 100.0, "rho": As / Ac, "yerlesim": yerlesim, "n_cubuk": len(cubuklar),
        "fcd": bm["fcd"], "fck": bm["fck"], "fyd": dm["fyd"], "k1": bm["k1"],
        "noktalar": noktalar, "N0_kN": N0 / 1e3, "Nt_kN": Nt / 1e3, "dengeli": dengeli,
        "N_max_TS500_kN": 0.9 * bm["fcd"] * Ac / 1e3, "N_max_TBDY_kN": 0.40 * bm["fck"] * Ac / 1e3,
        "cubuklar": [{"x_mm": x, "y_mm": y, "As_mm2": A} for x, y, A in cubuklar],
        "katmanlar": [{"derinlik_mm": dd, "As_mm2": A, "adet": k} for dd, A, k, _ in katmanlar],
        "kaynak": f"{K_TS500['blok']}; uç noktalar: N0 = 0,85fcd(Ac − As) + As·fyd, Nt = −As·fyd",
    })
    eg = np.array([(p["N_kN"], p["M_kNm"]) for p in noktalar], dtype=float)
    eg.setflags(write=False)
    return sonuc, gen, yuk, katmanlar, eg


def _anlat_kolon_egri(anl, s, bm, dm, gen, yuk, katmanlar):
    e = s["eksen"]
    _basla(anl, f"Kolon N–M etkileşim eğrisi ({e} ekseni, TS 500)",
           "Kolon aynı anda eksenel kuvvet (N) ve moment (M) taşır. Tarafsız eksen derinliği c'yi saf çekmeden saf "
           "basınca kaydırıp her konumda kesitin taşıdığı (N, M) çiftini hesaplarsak kesitin taşıma sınırını çizeriz; "
           "eğrinin içinde kalan her (Nd, Md) güvenlidir.")
    _birim_notu(anl)
    _anlat_malzeme(anl, bm, dm)
    anl.metin(f"Kesit {_f(s['b_mm'], 0)} × {_f(s['h_mm'], 0)} mm, As = {_f(s['As_cm2'])} cm² ({s['n_cubuk']} çubuk, "
              f"{'dört yüze' if s['yerlesim'] == 'dort_yuz' else 'iki yüze'} dağıtılmış), ρ = {s['rho']:.4f}. "
              f"Eğilme {e} ekseni etrafında: derinlik {_f(yuk, 0)} mm, genişlik {_f(gen, 0)} mm.")
    anl.metin("Donatı katmanları (derinlik basınç yüzünden):\n\n" + se._tablo(
        ["Katman", "Derinlik (mm)", "Çubuk", "As (mm²)"],
        [[i + 1, _f(dd, 1), k, _f(A, 1)] for i, (dd, A, k, _) in enumerate(katmanlar)]))
    anl.kural("Her c için: a = k₁c (≤ derinlik), εsi = 0,003(c − di)/c, σsi = Es·εsi ile ±fyd arasında; "
              "N = 0,85 fcd·b·a + Σ Asi(σsi − 0,85fcd·[blok içinde]); M = 0,85 fcd·b·a(h/2 − a/2) + Σ Fsi(h/2 − di). "
              "Momentler kesitin ağırlık merkezine göredir (simetrik donatıda plastik merkez ile aynı).")
    Ac = s["b_mm"] * s["h_mm"]
    anl.mat(rf"N_0 = 0{{,}}85 f_{{cd}}(A_c - A_s) + A_s f_{{yd}} = 0{{,}}85\cdot{_L(bm['fcd'], 3)}\cdot({_L(Ac, 0)} - "
            rf"{_L(s['As_mm2'], 0)}) + {_L(s['As_mm2'], 0)}\cdot{_L(dm['fyd'])} = {_L(s['N0_kN'], 1)}\ \text{{kN}}")
    anl.mat(rf"N_t = -A_s f_{{yd}} = -{_L(s['As_mm2'], 0)}\cdot{_L(dm['fyd'])} = {_L(s['Nt_kN'], 1)}\ \text{{kN}}")
    dg = s["dengeli"]
    dmax = max(k[0] for k in katmanlar)
    anl.metin("**Dengeli nokta:** en dıştaki çekme donatısı tam akma birim uzamasına (εyd) ulaşırken beton ezilir.")
    anl.mat(rf"c_b = \frac{{0{{,}}003\,d}}{{0{{,}}003 + \varepsilon_{{yd}}}} = \frac{{0{{,}}003\cdot{_L(dmax, 0)}}}"
            rf"{{0{{,}}003 + {_L(dm['eps_yd'], 5)}}} = {_L(dg['c_mm'], 1)}\ \text{{mm}}\ \Rightarrow\ N_b = {_L(dg['N_kN'], 1)}"
            rf"\ \text{{kN}},\ M_b = {_L(dg['M_kNm'], 1)}\ \text{{kN·m}}")
    anl.metin("Dengeli noktadaki katmanlar:\n\n" + se._tablo(
        ["Derinlik (mm)", "ε (‰)", "σ (MPa)", "F (kN)"],
        [[_f(k["derinlik_mm"], 1), _f(k["eps"] * 1000, 3), _f(k["sigma_MPa"], 1), _f(k["F_kN"], 1)]
         for k in dg["katmanlar"]]))
    sec = s["noktalar"][:: max(1, len(s["noktalar"]) // 10)]
    anl.metin("Eğriden seçilmiş noktalar:\n\n" + se._tablo(
        ["c (mm)", "N (kN)", "M (kN·m)"],
        [["–" if p["c_mm"] is None else _f(p["c_mm"], 1), _f(p["N_kN"], 1), _f(p["M_kNm"], 1)] for p in sec]))
    anl.metin(f"Eksenel sınırlar: TS 500 Nd ≤ 0,9 fcd Ac = {_f(s['N_max_TS500_kN'], 1)} kN ({K_TS500['N09']}); "
              f"TBDY Ndm ≤ 0,40 fck Ac = {_f(s['N_max_TBDY_kN'], 1)} kN ({K_TS500['N040']}).")
    egri = [(p["N_kN"], p["M_kNm"]) for p in s["noktalar"]]
    _sema(anl, f"Kolon kesiti ve N–M eğrisi ({e})", [
        ("Kesit ve donatı yerleşimi", _svg_kolon_kesit(s["b_mm"], s["h_mm"],
                                                       [(c["x_mm"], c["y_mm"], c["As_mm2"]) for c in s["cubuklar"]],
                                                       "Kolon kesiti", e)),
        ("N–M etkileşim eğrisi (M ≥ 0 yarısı; simetrik)",
         _svg_nm(egri, "N–M eğrisi", dengeli=(dg["N_kN"], dg["M_kNm"]),
                 N_cizgiler=[("0,9 fcd Ac", s["N_max_TS500_kN"]), ("0,40 fck Ac", s["N_max_TBDY_kN"])],
                 M_etiket=f"M{e}"))])


def _liste(v, ad):
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_sayi(x, ad) for x in v]
    return [_sayi(v, ad)]


def kolon_kontrol(Nd, Mdx, Mdy, b, h, As_toplam, paspayi, beton="C30", donati="B420C", yerlesim="dort_yuz",
                  n_cubuk=None, adlar=None, tbdy=False, n=60, anl=None, deprem=None, ham=False) -> dict:
    """TS 500 kolon tahkiki: her kombinasyon (Nd kN basınç +, Mdx, Mdy kN·m) için radyal D/C.

    ``tbdy=True``: TBDY 2018 kolon koşulları da denetlenir — en küçük boyut ≥ 300 mm (md. 7.3.1.1) ve Ndm ≤ 0,40 fck Ac
    (md. 7.3.1.2). Ndm deprem birleşimindeki eksenel kuvvettir: ``deprem`` (bool ya da noktalar kadar bool listesi) hangi
    noktaların deprem birleşimi olduğunu söyler; verilmezse bütün noktalar deprem birleşimi sayılır (güvenli taraf, uyarılır).
    Varsayılan ``tbdy=False``: yalnız TS 500 (deprem içermeyen birleşimlere 0,40 fck Ac sınırı uygulanmaz).

    Nd, Mdx, Mdy sayı ya da eşit uzunlukta listeler. Her doğrultuda en küçük dışmerkezlik
    e_min = 15 mm + 0,03h (TS 500 md. 6.3.10) uygulanır (tek eksenli kontrollerde, doğrultu başına ayrı ayrı).
    İki eksenli eğilmede (iki moment de sıfırdan farklı): Nd ≥ 0,1 fck Ac ise Bresler ters yük formülü
    1/Nr = 1/Nrx + 1/Nry − 1/N0; değilse doğrusal moment toplamı Mx/Mrx + My/Mry ≤ 1 (öğretici yaklaşımlar; TS 500
    iki eksenli etkileşim formülü vermez).

    Dönüş: noktalar [{ad, Nd_kN, Mdx_kNm, Mdy_kNm, Mx_tasarim_kNm, My_tasarim_kNm, dc_x, dc_y, dc_iki_eksen,
    iki_eksen_yontemi, N_rx_kN, N_ry_kN, N_r_kN, dc, kontroller}], egri_x, egri_y (etkileşim sonuçları), rho,
    dc, durum, kontroller (en elverişsiz nokta + genel), uyarilar.

    ``ham=True`` (iç kullanım; ``anl`` yokken): egri_x / egri_y yazılmaz ve _json dönüşümü yapılmaz (aynı sayılar)."""
    Ns, Mxs, Mys = _liste(Nd, "Nd (kN)"), _liste(Mdx, "Mdx (kN·m)"), _liste(Mdy, "Mdy (kN·m)")
    m = max(len(Ns), len(Mxs), len(Mys))
    for L_, ad in ((Ns, "Nd"), (Mxs, "Mdx"), (Mys, "Mdy")):
        if len(L_) not in (1, m):
            raise MatrisHatasi(f"{ad} listesinin uzunluğu diğerleriyle aynı olmalı ({m}).")
    Ns, Mxs, Mys = [L_ * m if len(L_) == 1 else L_ for L_ in (Ns, Mxs, Mys)]
    if adlar is None:
        adlar = [f"K{i + 1}" for i in range(m)]
    elif len(adlar) != m:
        raise MatrisHatasi("adlar listesinin uzunluğu kombinasyon sayısına eşit olmalı.")
    if deprem is None or isinstance(deprem, bool):
        dep_liste = [True if deprem is None else deprem] * m
    else:
        dep_liste = [bool(x) for x in deprem]
        if len(dep_liste) != m:
            raise MatrisHatasi("deprem listesinin uzunluğu kombinasyon sayısına eşit olmalı.")
    ex, _, _, _, egx_d, bm, dm = _etkilesim_ham(b, h, As_toplam, paspayi, beton, donati, "x", n, yerlesim, n_cubuk)
    ey, _, _, _, egy_d, _, _ = _etkilesim_ham(b, h, As_toplam, paspayi, beton, donati, "y", n, yerlesim, n_cubuk)
    bmm, hmm = ex["b_mm"], ex["h_mm"]
    Ac = bmm * hmm
    egx = [(p["N_kN"], p["M_kNm"]) for p in ex["noktalar"]]
    egy = [(p["N_kN"], p["M_kNm"]) for p in ey["noktalar"]]
    N0 = ex["N0_kN"]
    emin_x = 15.0 + 0.03 * hmm   # x ekseni etrafında eğilme: derinlik h
    emin_y = 15.0 + 0.03 * bmm
    N09 = ex["N_max_TS500_kN"]
    N040 = ex["N_max_TBDY_kN"]
    rho = ex["rho"]
    genel = [
        _kontrol("Boyuna donatı ρ ≥ 0,01", 0.01, rho, K_TS500["rho_kolon"]),
        _kontrol("Boyuna donatı ρ ≤ 0,04", rho, 0.04, K_TS500["rho_kolon"]),
        _kontrol("Kolon en küçük boyutu ≥ 250 mm", 250.0, min(bmm, hmm), K_TS500["kolon_boyut"], "mm"),
    ]
    if tbdy:
        genel.append(_kontrol("TBDY: kolon en küçük boyutu ≥ 300 mm", 300.0, min(bmm, hmm), K_TS500["kolon_boyut_tbdy"], "mm"))
    noktalar = []
    # ışın kesişimleri bütün noktalar için birlikte (vektörel; _isin_kesisim ile bit bit aynı)
    Mx_tl = [max(abs(Mx), N * emin_x / 1e3) if N > 0 else abs(Mx) for N, Mx in zip(Ns, Mxs)]
    My_tl = [max(abs(My), N * emin_y / 1e3) if N > 0 else abs(My) for N, My in zip(Ns, Mys)]
    kes_x, kes_y = _isin_kesisim_cok(egx_d, Ns, Mx_tl), _isin_kesisim_cok(egy_d, Ns, My_tl)
    iki = [i for i, (N, Mx, My) in enumerate(zip(Ns, Mxs, Mys))
           if abs(Mx) > 1e-9 and abs(My) > 1e-9 and N >= 0.1 * bm["fck"] * Ac / 1e3]
    br_x = dict(zip(iki, _isin_kesisim_cok(egx_d, [Ns[i] for i in iki], [abs(Mxs[i]) for i in iki])))
    br_y = dict(zip(iki, _isin_kesisim_cok(egy_d, [Ns[i] for i in iki], [abs(Mys[i]) for i in iki])))
    for i_n, (ad, N, Mx, My, dep_i) in enumerate(zip(adlar, Ns, Mxs, Mys, dep_liste)):
        Mx_t, My_t = Mx_tl[i_n], My_tl[i_n]
        dcx, Nrx_e, Mrx_e = kes_x[i_n]
        dcy, Nry_e, Mry_e = kes_y[i_n]
        k = [_kontrol("N–Mx etkileşimi (radyal, e_min dahil)", 1.0, 1.0, K_TS500["blok"] + "; " + K_TS500["emin"],
                      dc=dcx),
             _kontrol("N–My etkileşimi (radyal, e_min dahil)", 1.0, 1.0, K_TS500["blok"] + "; " + K_TS500["emin"],
                      dc=dcy)]
        # talep/kapasite: aynı ışın üzerinde moment (moment yoksa eksenel kuvvet) — oranları D/C'ye eşittir
        for kk, Mt, Ni, Mi in ((k[0], Mx_t, Nrx_e, Mrx_e), (k[1], My_t, Nry_e, Mry_e)):
            if Ni is None:
                continue
            if Mt > 1e-9:
                kk["talep"], kk["kapasite"], kk["birim"] = Mt, Mi, "kN·m"
            else:
                kk["talep"], kk["kapasite"], kk["birim"] = abs(N), abs(Ni), "kN"
        dc2 = None
        yontem = None
        Nrx = Nry = Nr = None
        if abs(Mx) > 1e-9 and abs(My) > 1e-9:
            if N >= 0.1 * bm["fck"] * Ac / 1e3:
                yontem = "Bresler ters yük"
                d1, Nrx, _ = br_x[i_n]
                d2, Nry, _ = br_y[i_n]
                if Nrx and Nry and Nrx > 0 and Nry > 0:
                    ters = 1.0 / Nrx + 1.0 / Nry - 1.0 / N0
                    Nr = 1.0 / ters if ters > 0 else N0
                    dc2 = _dc(N, Nr)
                else:
                    dc2 = DC_UST
                k.append(_kontrol("İki eksenli eğilme (Bresler: 1/Nr = 1/Nrx + 1/Nry − 1/N0)", N, Nr or 0.0,
                                  K_TS500["iki_eksen"], "kN", dc=dc2))
            else:
                yontem = "doğrusal moment toplamı"
                Mrx = _M_kapasite(egx, N)
                Mry = _M_kapasite(egy, N)
                dc2 = min((abs(Mx) / Mrx if Mrx > 0 else DC_UST) + (abs(My) / Mry if Mry > 0 else DC_UST), DC_UST)
                k.append(_kontrol("İki eksenli eğilme (Mx/Mrx + My/Mry ≤ 1)", dc2, 1.0, K_TS500["iki_eksen"], dc=dc2))
        if N > 0:
            k.append(_kontrol("Nd ≤ 0,9 fcd Ac", N, N09, K_TS500["N09"], "kN"))
            if tbdy and dep_i:
                k.append(_kontrol("TBDY: Ndm ≤ 0,40 fck Ac", N, N040, K_TS500["N040"], "kN"))
        noktalar.append({"ad": str(ad), "Nd_kN": N, "Mdx_kNm": Mx, "Mdy_kNm": My, "Mx_tasarim_kNm": Mx_t,
                         "My_tasarim_kNm": My_t, "e_min_x_mm": emin_x, "e_min_y_mm": emin_y,
                         "dc_x": dcx, "dc_y": dcy, "kesisim_x": {"N_kN": Nrx_e, "M_kNm": Mrx_e},
                         "kesisim_y": {"N_kN": Nry_e, "M_kNm": Mry_e}, "dc_iki_eksen": dc2,
                         "iki_eksen_yontemi": yontem, "N_rx_kN": Nrx, "N_ry_kN": Nry, "N_r_kN": Nr,
                         "dc": max(x["dc"] for x in k), "kontroller": k})
    en = max(noktalar, key=lambda p: p["dc"])
    kontroller = [dict(x, ad=f"{en['ad']}: {x['ad']}") for x in en["kontroller"]] + genel
    dc = max(x["dc"] for x in kontroller)
    uyarilar = []
    eksenel_asim = any(not x["saglandi"] for p in noktalar for x in p["kontroller"] if x["birim"] == "kN"
                       and "Nd" in x["ad"])
    if not all(x["saglandi"] for x in genel if x["birim"] == "mm") or eksenel_asim or rho > 0.04:
        durum = "kesit büyüt"
    elif dc > 1.0 + 1e-9:
        durum = "donatı artır"
    else:
        durum = "yeterli"
    if any(p["iki_eksen_yontemi"] for p in noktalar):
        uyarilar.append("İki eksenli eğilme öğretici yaklaşımla denetlendi: " + K_TS500["iki_eksen"] + ".")
    if tbdy and deprem is None:
        uyarilar.append("TBDY 7.3.1.2'deki Ndm, deprem birleşimi (G + Q + E) altındaki en büyük eksenel basınçtır; deprem "
                        "listesi verilmediği için her kombinasyona uygulandı (güvenli tarafta). Deprem içermeyen noktalar için "
                        "deprem=[...] ile işaretleyin ya da tbdy=False kullanın.")
    sonuc = {"tur": "kolon_kontrol", "beton": bm["sinif"], "donati": dm["sinif"], "b_mm": bmm, "h_mm": hmm,
             "As_cm2": ex["As_cm2"], "rho": rho, "N0_kN": N0, "noktalar": noktalar}
    if not (ham and anl is None):
        sonuc.update({"egri_x": ex, "egri_y": ey})
    sonuc.update({"dc": dc, "durum": durum, "kontroller": kontroller, "uyarilar": uyarilar, "tbdy": bool(tbdy),
                  "deprem": dep_liste})
    if ham and anl is None:
        return sonuc
    sonuc = _json(sonuc)
    if anl is not None:
        _anlat_kolon_kontrol(anl, sonuc, bm, dm)
    return sonuc


def _anlat_kolon_kontrol(anl, s, bm, dm):
    _basla(anl, "Kolon tahkiki (TS 500 + TBDY 2018)",
           "Her yük kombinasyonunun (Nd, Mdx, Mdy) noktasını kesitin N–M etkileşim eğrisiyle karşılaştırıyoruz. "
           "Orijinden noktaya bir ışın çizilir; ışının eğriyi kestiği nokta kapasitedir. D/C = |talep| / |kapasite| "
           "(aynı ışın üzerinde uzunluk oranı): 1'den küçükse nokta eğrinin içindedir.")
    _birim_notu(anl)
    _anlat_malzeme(anl, bm, dm)
    p0 = s["noktalar"][0]
    anl.kural(f"En küçük dışmerkezlik ({K_TS500['emin']}): e_min = 15 mm + 0,03h. Bu kesitte "
              f"e_min,x = {_f(p0['e_min_x_mm'], 1)} mm (h = {_f(s['h_mm'], 0)} mm), e_min,y = {_f(p0['e_min_y_mm'], 1)} mm. "
              "Tasarım momenti Md ≥ Nd·e_min alınır.")
    anl.mat(rf"\text{{D/C}} = \frac{{\sqrt{{N_d^2 + M_d^2}}}}{{\sqrt{{N_r^2 + M_r^2}}}}\Big|_{{\text{{aynı ışın}}}},\qquad "
            rf"N_d \le 0{{,}}9 f_{{cd}} A_c = {_L(s['egri_x']['N_max_TS500_kN'], 1)}\ \text{{kN}}"
            + (rf",\qquad N_{{dm}} \le 0{{,}}40 f_{{ck}} A_c = {_L(s['egri_x']['N_max_TBDY_kN'], 1)}\ \text{{kN (TBDY, deprem birleşimleri)}}"
               if s.get("tbdy") else ""))
    if not s.get("tbdy"):
        anl.metin("TBDY 7.3.1.2 sınırı N_dm ≤ 0,40 f_ck A_c yalnız deprem birleşimlerine uygulanır; bu tahkik `tbdy=False` "
                  "(TS 500, deprem içermeyen birleşimler). Deprem birleşimleri için `tbdy=True, deprem=[...]`.")
    if any(p["iki_eksen_yontemi"] == "Bresler ters yük" for p in s["noktalar"]):
        anl.metin("İki eksenli eğilme: TS 500 bir etkileşim formülü vermez; öğretici yaklaşım olarak Bresler ters yük "
                  "formülü kullanılır (Nd ≥ 0,1 fck Ac için):")
        anl.mat(r"\frac{1}{N_r} = \frac{1}{N_{rx}} + \frac{1}{N_{ry}} - \frac{1}{N_0}")
    satir = []
    for p in s["noktalar"]:
        satir.append([p["ad"], _f(p["Nd_kN"], 1), _f(p["Mdx_kNm"], 1), _f(p["Mdy_kNm"], 1), _f(p["Mx_tasarim_kNm"], 1),
                      _f(p["My_tasarim_kNm"], 1), _f(p["dc_x"], 3), _f(p["dc_y"], 3),
                      "–" if p["dc_iki_eksen"] is None else _f(p["dc_iki_eksen"], 3), _f(p["dc"], 3)])
    anl.metin("Kombinasyonlar:\n\n" + se._tablo(
        ["Ad", "Nd (kN)", "Mdx", "Mdy", "Mx,t", "My,t", "D/C x", "D/C y", "D/C 2 eksen", "D/C"], satir))
    egx = [(p["N_kN"], p["M_kNm"]) for p in s["egri_x"]["noktalar"]]
    egy = [(p["N_kN"], p["M_kNm"]) for p in s["egri_y"]["noktalar"]]
    nok_x = [(p["ad"], p["Nd_kN"], p["Mx_tasarim_kNm"], p["dc_x"]) for p in s["noktalar"]]
    nok_y = [(p["ad"], p["Nd_kN"], p["My_tasarim_kNm"], p["dc_y"]) for p in s["noktalar"]]
    cz = [("0,9 fcd Ac", s["egri_x"]["N_max_TS500_kN"]), ("0,40 fck Ac", s["egri_x"]["N_max_TBDY_kN"])]
    dgx, dgy = s["egri_x"]["dengeli"], s["egri_y"]["dengeli"]
    _sema(anl, "N–M eğrileri ve kombinasyon noktaları", [
        ("N–Mx: kombinasyon noktaları ve ışınlar", _svg_nm(egx, "N–Mx", nok_x, (dgx["N_kN"], dgx["M_kNm"]), cz, "Mx")),
        ("N–My: kombinasyon noktaları ve ışınlar", _svg_nm(egy, "N–My", nok_y, (dgy["N_kN"], dgy["M_kNm"]), cz, "My")),
    ])
    _durum_ozet(anl, s)


# ============================================================================
# B) ÇYTHYE 2018 çelik
# ============================================================================
def celik_malzeme(sinif="S275", t_mm=None) -> dict:
    """ÇYTHYE Tablo 2.1A: Fy, Fu (t ≤ 40 mm ya da 40 < t ≤ 80 mm bandı), E = 200000, G = 77200 MPa."""
    if isinstance(sinif, dict):
        k = dict(sinif)
        if "Fy" not in k or "Fu" not in k:
            raise MatrisHatasi("Çelik sözlüğünde 'Fy' ve 'Fu' (MPa) olmalı.")
        Fy, Fu = float(k["Fy"]), float(k["Fu"])
        ad = str(k.get("sinif", f"S{_f(Fy, 0)}"))
        bant = "verilen"
    else:
        ad = str(sinif).strip().upper().replace(" ", "")
        tablo = _kutuphane("CELIKLER")
        if ad not in tablo:
            raise MatrisHatasi(f"Çelik sınıfı {sinif!r} tanımsız. Seçenekler: {', '.join(tablo)} (ÇYTHYE Tablo 2.1A).")
        k = tablo[ad]
        t = 0.0 if t_mm is None else _sayi(t_mm, "kalınlık t (mm)", pozitif=True)
        if t > 80:
            raise MatrisHatasi(f"t = {t} mm: Tablo 2.1A en çok 80 mm kalınlık için değer verir.")
        if t <= 40:
            Fy, Fu, bant = float(k["Fy"]), float(k["Fu"]), "t ≤ 40 mm"
        else:
            Fy, Fu, bant = float(k["Fy_40_80"]), float(k["Fu_40_80"]), "40 < t ≤ 80 mm"
    return _json({"sinif": ad, "Fy": Fy, "Fu": Fu, "E": float(k.get("E", E_CELIK)), "G": float(k.get("G", G_CELIK)),
                  "t_mm": t_mm, "bant": bant, "kaynak": K_CYT["malzeme"]})


def _profil(profil):
    """Katalog profili → mm birimli sözlük (A mm², I mm⁴, W mm³, i mm, It mm⁴, Iw mm⁶)."""
    if isinstance(profil, dict):
        p = dict(profil)
        ad = str(p.get("ad", "profil"))
    else:
        ad = str(profil).strip().upper()
        ad = " ".join(ad.split())
        if " " not in ad:
            for on in ("IPE", "HEA", "HEB"):
                if ad.startswith(on):
                    ad = on + " " + ad[len(on):]
        tablo = _kutuphane("PROFILLER")
        if ad not in tablo:
            raise MatrisHatasi(f"Profil {profil!r} tabloda yok. IPE 80…600, HEA 100…600, HEB 100…600 yazılabilir "
                               "(örn. \"IPE 300\").")
        p = dict(tablo[ad])
    gerek = ("h", "b", "tw", "tf", "r", "A", "Iy", "Wely", "Wply", "iy", "Iz", "Welz", "Wplz", "iz", "It", "Iw")
    eksik = [g for g in gerek if g not in p]
    if eksik:
        raise MatrisHatasi(f"Profil sözlüğünde eksik alanlar: {', '.join(eksik)} (katalog birimleri: mm, cm², cm⁴, cm³, "
                           "cm, ×10³ cm⁶).")
    for g in ("h", "b", "tw", "tf", "A", "Iy", "Iz", "iy", "iz"):
        if float(p[g]) <= 0:
            raise MatrisHatasi(f"Profil {ad}: {g} pozitif olmalı.")
    return {"ad": ad, "h": float(p["h"]), "b": float(p["b"]), "tw": float(p["tw"]), "tf": float(p["tf"]),
            "r": float(p["r"]), "A": float(p["A"]) * 100.0, "Iy": float(p["Iy"]) * 1e4, "Wely": float(p["Wely"]) * 1e3,
            "Wply": float(p["Wply"]) * 1e3, "iy": float(p["iy"]) * 10.0, "Iz": float(p["Iz"]) * 1e4,
            "Welz": float(p["Welz"]) * 1e3, "Wplz": float(p["Wplz"]) * 1e3, "iz": float(p["iz"]) * 10.0,
            "It": float(p["It"]) * 1e4, "Iw": float(p["Iw"]) * 1e9}


def _Fy(Fy, p, E=None):
    """Fy sayı (MPa) ya da sınıf adı ("S275": başlık kalınlığına göre bant)."""
    if isinstance(Fy, str) or isinstance(Fy, dict):
        m = celik_malzeme(Fy, max(p["tf"], p["tw"]) if not isinstance(Fy, dict) else None)
        return m["Fy"], m
    return _sayi(Fy, "Fy (MPa)", pozitif=True, sifir_olur=False), None


def _katsayi(yontem, phi, omega):
    y = str(yontem).strip().upper()
    if y not in ("YDKT", "GKT"):
        raise MatrisHatasi(f"yontem {yontem!r} tanımsız; 'YDKT' (φ) ya da 'GKT' (Ω) olmalı.")
    return (phi, 1.0 / omega)[y == "GKT"], y


def _tasarim_metin(yontem, phi, omega):
    return f"φ = {phi:.2f}" if yontem == "YDKT" else f"Ω = {omega:.2f}"


def kesit_sinifi(profil, Fy=275.0, E=E_CELIK, anl=None) -> dict:
    """Enkesit sınıfı (ÇYTHYE 5.4.1): başlık λf = b/(2tf), gövde λw = h/tw (h = d − 2tf − 2r: eğrilik yarıçapları
    çıkarılmış başlıklar arası yükseklik). Eğilme (Tablo 5.1B): kompakt / kompakt olmayan / narin; basınç
    (Tablo 5.1A): narin olmayan / narin.

    Basit kesit adı (KUTU / BORU / L / 2L / UPN: ``_ad_coz``) tabloda yoksa Tablo 5.1A/B basit kesit kuralları uygulanır (C20):
    dönüş {tur, profil, egilme, basinc, parcalar, kaynak} (2L'de eğilme sınıfı yok: None).

    Dönüş: baslik {oran, lambda_p, lambda_r, egilme, basinc_lambda_r, basinc}, govde {...}, egilme, basinc."""
    try:
        p = _profil(profil)
    except MatrisHatasi:
        c = _ad_coz(profil) if isinstance(profil, str) else None
        if c is None:
            raise
        return _basit_kesit_sinifi(_kesit_hesap(*c), Fy, E, anl)
    Fy, _ = _Fy(Fy, p)
    E = _sayi(E, "E (MPa)", pozitif=True, sifir_olur=False)
    k = math.sqrt(E / Fy)
    hw = p["h"] - 2 * p["tf"] - 2 * p["r"]
    lf, lw = p["b"] / (2 * p["tf"]), hw / p["tw"]

    def sinif(l, lp, lr):
        return "kompakt" if l <= lp else ("kompakt olmayan" if l <= lr else "narin")

    bas = {"oran": lf, "lambda_p": 0.38 * k, "lambda_r": 1.00 * k, "basinc_lambda_r": 0.56 * k}
    bas["egilme"] = sinif(lf, bas["lambda_p"], bas["lambda_r"])
    bas["basinc"] = "narin olmayan" if lf <= bas["basinc_lambda_r"] else "narin"
    gov = {"oran": lw, "h_mm": hw, "lambda_p": 3.76 * k, "lambda_r": 5.70 * k, "basinc_lambda_r": 1.49 * k}
    gov["egilme"] = sinif(lw, gov["lambda_p"], gov["lambda_r"])
    gov["basinc"] = "narin olmayan" if lw <= gov["basinc_lambda_r"] else "narin"
    sira = ["kompakt", "kompakt olmayan", "narin"]
    eg = sira[max(sira.index(bas["egilme"]), sira.index(gov["egilme"]))]
    ba = "narin" if "narin" in (bas["basinc"], gov["basinc"]) else "narin olmayan"
    sonuc = _json({"tur": "kesit_sinifi", "profil": p["ad"], "Fy": Fy, "E": E, "baslik": bas, "govde": gov,
                   "egilme": eg, "basinc": ba,
                   "kaynak": f"{K_CYT['sinif_egilme']}; {K_CYT['sinif_basinc']}"})
    if anl is not None:
        _basla(anl, f"Enkesit sınıfı: {p['ad']} (ÇYTHYE 5.4.1)",
               "Kesitin ince parçaları (başlık, gövde) akmadan önce yerel olarak buruşabilir. Genişlik/kalınlık "
               "oranları sınırlarla karşılaştırılır: kompakt kesit tam plastik momente ulaşır; kompakt olmayan "
               "kesitte yerel burkulma dayanımı düşürür; narin kesit ayrı kurallar ister.")
        anl.mat(rf"\lambda_f = \frac{{b_f}}{{2t_f}} = \frac{{{_L(p['b'], 1)}}}{{2\cdot{_L(p['tf'], 1)}}} = {_L(lf, 2)},\qquad "
                rf"\lambda_w = \frac{{h}}{{t_w}} = \frac{{{_L(p['h'], 1)} - 2\cdot{_L(p['tf'], 1)} - 2\cdot{_L(p['r'], 1)}}}"
                rf"{{{_L(p['tw'], 1)}}} = {_L(lw, 2)}")
        anl.mat(rf"\sqrt{{E/F_y}} = \sqrt{{{_L(E, 0)}/{_L(Fy, 0)}}} = {_L(k, 3)}")
        anl.metin(se._tablo(["Parça", "Oran", "λp (eğilme)", "λr (eğilme)", "Eğilme sınıfı", "λr (basınç)", "Basınç"],
                            [["Başlık (Durum 10 / Durum 1)", _f(lf, 2), f"0,38√(E/Fy) = {_f(bas['lambda_p'], 2)}",
                              f"1,00√(E/Fy) = {_f(bas['lambda_r'], 2)}", bas["egilme"],
                              f"0,56√(E/Fy) = {_f(bas['basinc_lambda_r'], 2)}", bas["basinc"]],
                             ["Gövde (Durum 15 / Durum 5)", _f(lw, 2), f"3,76√(E/Fy) = {_f(gov['lambda_p'], 2)}",
                              f"5,70√(E/Fy) = {_f(gov['lambda_r'], 2)}", gov["egilme"],
                              f"1,49√(E/Fy) = {_f(gov['basinc_lambda_r'], 2)}", gov["basinc"]]]))
        anl.metin(f"Kaynak: {sonuc['kaynak']}.")
        _sema(anl, f"{p['ad']} enkesiti", [(f"{p['ad']}: oranlar ve sınıf", _svg_profil(p, p["ad"], Fy, sonuc))])
        anl.sonuc(rf"\text{{eğilme: {eg}}},\quad \text{{basınç: {ba}}}")
    return sonuc


def cb_katsayisi(M_maks, M_A, M_B, M_C) -> float:
    """C_b = 12,5 Mmaks / (2,5 Mmaks + 3 MA + 4 MB + 3 MC) (ÇYTHYE Denk. 9.1; momentlerin mutlak değerleri,
    MA, MB, MC desteklenmeyen boyun 1/4, 1/2, 3/4 noktalarında)."""
    Mm, A, B, C = (abs(_sayi(x, ad)) for x, ad in ((M_maks, "M_maks"), (M_A, "M_A"), (M_B, "M_B"), (M_C, "M_C")))
    if Mm <= 0:
        raise MatrisHatasi("M_maks sıfırdan büyük olmalı.")
    if max(A, B, C) > Mm * (1 + 1e-9):
        raise MatrisHatasi("M_maks, desteklenmeyen boydaki en büyük moment olmalı (MA, MB, MC'den küçük olamaz).")
    return 12.5 * Mm / (2.5 * Mm + 3 * A + 4 * B + 3 * C)


def _ybb(p, Fy, E, Lb, Cb):
    Mp = Fy * p["Wply"]
    Lp = 1.76 * p["iz"] * math.sqrt(E / Fy)
    ho = p["h"] - p["tf"]
    its = math.sqrt(math.sqrt(p["Iz"] * p["Iw"]) / p["Wely"])
    c = 1.0
    jc = p["It"] * c / (p["Wely"] * ho)
    Lr = 1.95 * its * E / (0.7 * Fy) * math.sqrt(jc + math.sqrt(jc ** 2 + 6.76 * (0.7 * Fy / E) ** 2))
    Fcr = None
    if Lb <= Lp:
        Mn, bolge = Mp, "akma (Lb ≤ Lp)"
    elif Lb <= Lr:
        Mn = min(Cb * (Mp - (Mp - 0.7 * Fy * p["Wely"]) * (Lb - Lp) / (Lr - Lp)), Mp)
        bolge = "elastik olmayan YBB (Lp < Lb ≤ Lr)"
    else:
        Fcr = Cb * math.pi ** 2 * E / (Lb / its) ** 2 * math.sqrt(1 + 0.078 * jc * (Lb / its) ** 2)
        Mn = min(Fcr * p["Wely"], Mp)
        bolge = "elastik YBB (Lb > Lr)"
    return {"Mp": Mp, "Lp": Lp, "Lr": Lr, "ho": ho, "its": its, "jc": jc, "Mn": Mn, "bolge": bolge, "Fcr": Fcr}


def celik_egilme(profil, Fy=275.0, Lb=0.0, Cb=1.0, yontem="YDKT", E=E_CELIK, M_talep=None, My_talep=None,
                 anl=None) -> dict:
    """ÇYTHYE Bölüm 9: güçlü eksen eğilmesi (kompakt/kompakt olmayan başlıklı hadde I) ve zayıf eksen (9.6).

    Lb (m) yanal desteksiz boy, Cb (``cb_katsayisi`` ile), ``yontem`` "YDKT" (φb = 0,90) ya da "GKT" (Ωb = 1,67).
    Mp = Fy·Wpl,y; Lp = 1,76 i_z √(E/Fy) (zayıf eksen atalet yarıçapı; ÇYTHYE simgesiyle i_y); Lr Denk. 9.6b
    (c = 1, h_o = d − tf, i_ts² = √(Iz Cw)/Wel,y). Kompakt olmayan başlıkta Denk. 9.9. Zayıf eksen
    Mny = min(Fy Wpl,z, 1,6 Fy Wel,z) (Denk. 9.39), kompakt olmayan başlıkta Denk. 9.40.

    Dönüş: Mp_kNm, Lp_m, Lr_m, bolge, Mn_YBB_kNm, Mn_FLB_kNm, Mn_kNm, Mc_kNm (tasarım dayanımı), Mny_kNm,
    Mcy_kNm, its_mm, ho_mm, Fcr_MPa, sinif, dc, durum, kontroller, uyarilar."""
    p = _profil(profil)
    Fy, _ = _Fy(Fy, p)
    E = _sayi(E, "E (MPa)", pozitif=True, sifir_olur=False)
    Lb_m = _sayi(Lb, "Lb (m)", pozitif=True)
    Cb = _sayi(Cb, "Cb", pozitif=True, sifir_olur=False)
    kat, y = _katsayi(yontem, 0.90, 1.67)
    sn = kesit_sinifi(_geri(p), Fy, E)
    r = _ybb(p, Fy, E, Lb_m * 1000.0, Cb)
    uyarilar = []
    Mp = r["Mp"]
    Mn_flb = None
    lf, lpf, lrf = sn["baslik"]["oran"], sn["baslik"]["lambda_p"], sn["baslik"]["lambda_r"]
    if sn["baslik"]["egilme"] == "kompakt olmayan":
        Mn_flb = Mp - (Mp - 0.7 * Fy * p["Wely"]) * (lf - lpf) / (lrf - lpf)
    elif sn["baslik"]["egilme"] == "narin":
        uyarilar.append("Narin başlık: ÇYTHYE Denk. 9.10 (k_c ile) gerekir; bu modülün kapsamı dışında.")
    if sn["govde"]["egilme"] != "kompakt":
        uyarilar.append("Gövde kompakt değil: ÇYTHYE 9.4/9.5 kuralları gerekir; bu modülde yalnız kompakt gövdeli "
                        "hadde I-profiller hesaplanır.")
    Mn = min(r["Mn"], Mn_flb) if Mn_flb is not None else r["Mn"]
    # zayıf eksen 9.6
    Mpy = min(Fy * p["Wplz"], 1.6 * Fy * p["Welz"])
    Mny = Mpy
    if sn["baslik"]["egilme"] == "kompakt olmayan":
        Mny = min(Mny, Mpy - (Mpy - 0.7 * Fy * p["Welz"]) * (lf - lpf) / (lrf - lpf))
    Mc, Mcy = kat * Mn, kat * Mny
    kontroller = []
    if M_talep is not None:
        kontroller.append(_kontrol("Güçlü eksen eğilmesi Mr ≤ Mc", abs(_sayi(M_talep, "M_talep (kN·m)")), Mc / 1e6,
                                   K_CYT["YBB"], "kN·m"))
    if My_talep is not None:
        kontroller.append(_kontrol("Zayıf eksen eğilmesi Mry ≤ Mcy", abs(_sayi(My_talep, "My_talep (kN·m)")),
                                   Mcy / 1e6, K_CYT["zayif"], "kN·m"))
    dc = max([k["dc"] for k in kontroller] + [0.0])
    sonuc = _json({
        "tur": "celik_egilme", "profil": p["ad"], "Fy": Fy, "E": E, "yontem": y, "katsayi": kat,
        "phi_b": 0.90, "Omega_b": 1.67, "Lb_m": Lb_m, "Cb": Cb,
        "Mp_kNm": Mp / 1e6, "Lp_m": r["Lp"] / 1e3, "Lr_m": r["Lr"] / 1e3, "bolge": r["bolge"],
        "its_mm": r["its"], "ho_mm": r["ho"], "J_mm4": p["It"], "Cw_mm6": p["Iw"], "Fcr_MPa": r["Fcr"],
        "Mn_YBB_kNm": r["Mn"] / 1e6, "Mn_FLB_kNm": None if Mn_flb is None else Mn_flb / 1e6,
        "Mn_kNm": Mn / 1e6, "Mc_kNm": Mc / 1e6, "Mny_kNm": Mny / 1e6, "Mcy_kNm": Mcy / 1e6,
        "sinif": sn, "dc": dc, "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt",
        "kontroller": kontroller, "uyarilar": uyarilar,
    })
    if anl is not None:
        _anlat_celik_egilme(anl, sonuc, p, Fy, E, r, kat, y)
    return sonuc


def _geri(p):
    """mm birimli profil → katalog birimli sözlük (kesit_sinifi'ne yeniden vermek için)."""
    return {"ad": p["ad"], "h": p["h"], "b": p["b"], "tw": p["tw"], "tf": p["tf"], "r": p["r"], "A": p["A"] / 100,
            "Iy": p["Iy"] / 1e4, "Wely": p["Wely"] / 1e3, "Wply": p["Wply"] / 1e3, "iy": p["iy"] / 10,
            "Iz": p["Iz"] / 1e4, "Welz": p["Welz"] / 1e3, "Wplz": p["Wplz"] / 1e3, "iz": p["iz"] / 10,
            "It": p["It"] / 1e4, "Iw": p["Iw"] / 1e9}


def _anlat_celik_egilme(anl, s, p, Fy, E, r, kat, y):
    _basla(anl, f"Çelik kiriş eğilmesi: {p['ad']} (ÇYTHYE Bölüm 9)",
           "Eğilen I-profilin basınç başlığı, yanal olarak desteklenmediği boy (Lb) uzadıkça yana kayıp burularak "
           "burkulabilir (yanal burulmalı burkulma, YBB). Kısa boyda kesit tam plastik momente (Mp) ulaşır; Lp ile Lr "
           "arasında dayanım doğrusal azalır; Lr'den sonra elastik burkulma belirler.")
    anl.metin("**Birimler:** katalog değerleri cm → mm çevrilir (1 cm³ = 10³ mm³, 1 cm⁴ = 10⁴ mm⁴, "
              "×10³ cm⁶ = 10⁹ mm⁶); 1 N·mm = 10⁻⁶ kN·m.")
    anl.mat(rf"M_p = F_y W_{{pl,y}} = {_L(Fy, 0)}\cdot{_L(p['Wply'], 0)} = {_L(s['Mp_kNm'] * 1e6)}\ \text{{N·mm}} = "
            rf"{_L(s['Mp_kNm'])}\ \text{{kN·m}}\quad (\text{{Denk. 9.2}})")
    anl.mat(rf"L_p = 1{{,}}76\,i_z\sqrt{{\frac{{E}}{{F_y}}}} = 1{{,}}76\cdot{_L(p['iz'], 1)}\cdot\sqrt{{\frac{{{_L(E, 0)}}}"
            rf"{{{_L(Fy, 0)}}}}} = {_L(r['Lp'], 0)}\ \text{{mm}}\quad (\text{{Denk. 9.6a; ÇYTHYE simgesiyle }} i_y)")
    anl.mat(rf"i_{{ts}} = \sqrt{{\frac{{\sqrt{{I_z C_w}}}}{{W_{{el,y}}}}}} = {_L(r['its'], 2)}\ \text{{mm}},\quad "
            rf"h_o = d - t_f = {_L(r['ho'], 1)}\ \text{{mm}},\quad \frac{{J c}}{{W_{{el,y}} h_o}} = {_L(r['jc'], 5)}\ (c = 1)")
    anl.mat(rf"L_r = 1{{,}}95\,i_{{ts}}\frac{{E}}{{0{{,}}7F_y}}\sqrt{{\frac{{Jc}}{{W_{{el}} h_o}} + \sqrt{{\left(\frac{{Jc}}"
            rf"{{W_{{el}} h_o}}\right)^2 + 6{{,}}76\left(\frac{{0{{,}}7F_y}}{{E}}\right)^2}}}} = {_L(r['Lr'], 0)}\ \text{{mm}}")
    anl.metin(f"Lb = {_f(s['Lb_m'], 3)} m → **{s['bolge']}** ({K_CYT['YBB']}).")
    if r["Fcr"] is not None:
        anl.mat(rf"F_{{cr}} = \frac{{C_b\pi^2E}}{{(L_b/i_{{ts}})^2}}\sqrt{{1 + 0{{,}}078\frac{{Jc}}{{W_{{el}}h_o}}\left("
                rf"\frac{{L_b}}{{i_{{ts}}}}\right)^2}} = {_L(r['Fcr'], 1)}\ \text{{MPa}},\quad M_n = F_{{cr}}W_{{el,y}} \le M_p")
    elif s["Lb_m"] * 1000 > r["Lp"]:
        anl.mat(r"M_n = C_b\left[M_p - (M_p - 0{,}7F_yW_{el,y})\frac{L_b - L_p}{L_r - L_p}\right] \le M_p\quad"
                r"(\text{Denk. 9.3})")
    anl.mat(rf"M_{{n,YBB}} = {_L(s['Mn_YBB_kNm'])}\ \text{{kN·m}}")
    if s["Mn_FLB_kNm"] is not None:
        anl.metin(f"Başlık kompakt değil → başlık yerel burkulması ({K_CYT['FLB']}):")
        anl.mat(rf"M_n = M_p - (M_p - 0{{,}}7F_yW_{{el,y}})\frac{{\lambda - \lambda_{{pf}}}}{{\lambda_{{rf}} - \lambda_{{pf}}}} = "
                rf"{_L(s['Mn_FLB_kNm'])}\ \text{{kN·m}}")
    t = r"\phi_b" if y == "YDKT" else r"1/\Omega_b"
    anl.mat(rf"M_c = {t} M_n = {_L(kat, 3)}\cdot{_L(s['Mn_kNm'])} = {_L(s['Mc_kNm'])}\ \text{{kN·m}}\quad ({y})")
    anl.mat(rf"M_{{ny}} = \min(F_yW_{{pl,z}},\ 1{{,}}6F_yW_{{el,z}}) = {_L(s['Mny_kNm'])}\ \text{{kN·m}}\ (\text{{Denk. 9.39}}),"
            rf"\quad M_{{cy}} = {_L(s['Mcy_kNm'])}\ \text{{kN·m}}")
    _sema(anl, f"{p['ad']} enkesiti", [(f"{p['ad']}", _svg_profil(p, p["ad"], Fy, s["sinif"]))])
    if s["kontroller"]:
        _durum_ozet(anl, s)
    else:
        for u in s["uyarilar"]:
            anl.uyari(u)
        anl.sonuc(rf"M_c = {_L(s['Mc_kNm'])}\ \text{{kN·m}}")


def _fcr_basinc(Fy, Fe, E, KLr):
    if KLr <= 4.71 * math.sqrt(E / Fy):
        return 0.658 ** (Fy / Fe) * Fy, "elastik olmayan (Denk. 8.2)"
    return 0.877 * Fe, "elastik (Denk. 8.3)"


def celik_basinc(profil, Fy=275.0, KLx=3.0, KLy=3.0, KLz=None, yontem="YDKT", E=E_CELIK, G=G_CELIK, P_talep=None,
                 anl=None) -> dict:
    """ÇYTHYE Bölüm 8: eğilmeli burkulma (her iki eksen, Denk. 8.4) ve burulmalı burkulma (Denk. 8.5; L_cz = KLz,
    verilmezse max(KLx, KLy)). F_cr: KL/i ≤ 4,71√(E/Fy) ise 0,658^(Fy/Fe)·Fy, değilse 0,877 Fe. Pn = Fcr·Ag.
    KLx: güçlü eksen (y–y, i_y) burkulma boyu, KLy: zayıf eksen (z–z, i_z) burkulma boyu (m).

    Dönüş: KLr_x, KLr_y, Fe_x_MPa, Fe_y_MPa, Fe_z_MPa, Fe_MPa, Fcr_MPa, bolge, Pn_kN, Pc_kN, sinif, dc, durum,
    kontroller, uyarilar."""
    p = _profil(profil)
    Fy, _ = _Fy(Fy, p)
    E = _sayi(E, "E (MPa)", pozitif=True, sifir_olur=False)
    Lx = _sayi(KLx, "KLx (m)", pozitif=True, sifir_olur=False) * 1000.0
    Ly = _sayi(KLy, "KLy (m)", pozitif=True, sifir_olur=False) * 1000.0
    Lz = max(Lx, Ly) if KLz is None else _sayi(KLz, "KLz (m)", pozitif=True, sifir_olur=False) * 1000.0
    kat, y = _katsayi(yontem, 0.90, 1.67)
    sn = kesit_sinifi(_geri(p), Fy, E)
    rx, ry = Lx / p["iy"], Ly / p["iz"]
    Fex = math.pi ** 2 * E / rx ** 2
    Fey = math.pi ** 2 * E / ry ** 2
    Fez = (math.pi ** 2 * E * p["Iw"] / Lz ** 2 + G * p["It"]) / (p["Iy"] + p["Iz"])
    Fe = min(Fex, Fey, Fez)
    KLr = max(rx, ry)
    if Fe == Fez and Fez < min(Fex, Fey):
        KLr_esd = math.pi * math.sqrt(E / Fez)
        Fcr, bolge = _fcr_basinc(Fy, Fe, E, KLr_esd)
        bolge += "; burulmalı burkulma belirleyici"
    else:
        Fcr, bolge = _fcr_basinc(Fy, Fe, E, KLr)
    Pn = Fcr * p["A"]
    Pc = kat * Pn
    uyarilar = []
    if sn["basinc"] == "narin":
        uyarilar.append("Kesit basınçta narin (Tablo 5.1A): ÇYTHYE 8.5 etkin alan yöntemi gerekir; burada brüt alanla "
                        "hesaplandı (güvensiz tarafta olabilir).")
    kontroller = [_kontrol("Narinlik KL/i ≤ 200", KLr, 200.0, K_CYT["narinlik_basinc"])]
    if P_talep is not None:
        kontroller.insert(0, _kontrol("Eksenel basınç Pr ≤ Pc", abs(_sayi(P_talep, "P_talep (kN)")), Pc / 1e3,
                                      K_CYT["basinc"], "kN"))
    dc = max(k["dc"] for k in kontroller)
    sonuc = _json({
        "tur": "celik_basinc", "profil": p["ad"], "Fy": Fy, "E": E, "yontem": y, "katsayi": kat,
        "phi_c": 0.90, "Omega_c": 1.67, "KLx_m": Lx / 1e3, "KLy_m": Ly / 1e3, "KLz_m": Lz / 1e3,
        "KLr_x": rx, "KLr_y": ry, "KLr": KLr, "sinir_471": 4.71 * math.sqrt(E / Fy),
        "Fe_x_MPa": Fex, "Fe_y_MPa": Fey, "Fe_z_MPa": Fez, "Fe_MPa": Fe, "Fcr_MPa": Fcr, "bolge": bolge,
        "A_mm2": p["A"], "Pn_kN": Pn / 1e3, "Pc_kN": Pc / 1e3, "sinif": sn,
        "dc": dc, "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller,
        "uyarilar": uyarilar,
    })
    if anl is not None:
        _basla(anl, f"Çelik basınç elemanı: {p['ad']} (ÇYTHYE Bölüm 8)",
               "Basınç çubuğu, akma yükünden önce burkulabilir. Her eksen için narinlik KL/i ve Euler gerilmesi Fe "
               "bulunur; en küçük Fe kritik gerilmeyi (Fcr) belirler. Kısa çubukta akma, uzun çubukta elastik "
               "burkulma baskındır.")
        anl.metin("**Birimler:** KL m → mm, katalog i cm → mm, A cm² → mm²; Pn N → kN (÷10³).")
        anl.mat(rf"\frac{{KL_x}}{{i_y}} = \frac{{{_L(Lx, 0)}}}{{{_L(p['iy'], 1)}}} = {_L(rx, 2)},\qquad "
                rf"\frac{{KL_y}}{{i_z}} = \frac{{{_L(Ly, 0)}}}{{{_L(p['iz'], 1)}}} = {_L(ry, 2)}")
        anl.mat(rf"F_e = \frac{{\pi^2 E}}{{(KL/i)^2}}:\quad F_{{e,x}} = {_L(Fex, 1)},\ F_{{e,y}} = {_L(Fey, 1)}\ \text{{MPa}}"
                rf"\ (\text{{Denk. 8.4}});\quad F_{{e,z}} = \frac{{\pi^2EC_w/L_{{cz}}^2 + GJ}}{{I_x + I_y}} = {_L(Fez, 1)}"
                rf"\ \text{{MPa}}\ (\text{{Denk. 8.5}})")
        anl.mat(rf"4{{,}}71\sqrt{{E/F_y}} = {_L(4.71 * math.sqrt(E / Fy), 2)}\ \Rightarrow\ F_{{cr}} = "
                + (rf"0{{,}}658^{{F_y/F_e}}F_y = 0{{,}}658^{{{_L(Fy / Fe, 4)}}}\cdot{_L(Fy, 0)}" if "Denk. 8.2" in bolge
                   else rf"0{{,}}877F_e = 0{{,}}877\cdot{_L(Fe, 1)}")
                + rf" = {_L(Fcr, 2)}\ \text{{MPa}}")
        tt = r"\phi_c" if y == "YDKT" else r"1/\Omega_c"
        anl.mat(rf"P_n = F_{{cr}}A_g = {_L(Fcr, 2)}\cdot{_L(p['A'], 0)} = {_L(Pn / 1e3, 1)}\ \text{{kN}},\quad "
                rf"P_c = {tt}P_n = {_L(Pc / 1e3, 1)}\ \text{{kN}}\quad (\text{{Denk. 8.1}})")
        _durum_ozet(anl, sonuc)
    return sonuc


def celik_kesme(profil, Fy=275.0, yontem="YDKT", E=E_CELIK, V_talep=None, anl=None) -> dict:
    """ÇYTHYE 10.2.1: Vn = 0,6 Fy Aw Cv1, Aw = d·tw. Hadde I gövdesinde h/tw ≤ 2,24√(E/Fy) ise Cv1 = 1,
    φv = 1,00 (Ωv = 1,50); değilse kv = 5,34 ile Cv1 (Denk. 10.2a/b), φv = 0,90 (Ωv = 1,67).

    Dönüş: Aw_mm2, h_tw, sinir_224, Cv1, phi_v, Omega_v, Vn_kN, Vc_kN, dc, durum, kontroller."""
    p = _profil(profil)
    Fy, _ = _Fy(Fy, p)
    E = _sayi(E, "E (MPa)", pozitif=True, sifir_olur=False)
    hw = p["h"] - 2 * p["tf"] - 2 * p["r"]
    htw = hw / p["tw"]
    sinir = 2.24 * math.sqrt(E / Fy)
    if htw <= sinir:
        Cv1, phi, om, dal = 1.0, 1.00, 1.50, "10.2.1(a)"
    else:
        kv = 5.34
        s2 = 1.10 * math.sqrt(kv * E / Fy)
        Cv1 = 1.0 if htw <= s2 else s2 / htw
        phi, om, dal = 0.90, 1.67, "10.2.1(b)"
    kat, y = _katsayi(yontem, phi, om)
    Aw = p["h"] * p["tw"]
    Vn = 0.6 * Fy * Aw * Cv1
    Vc = kat * Vn
    kontroller = []
    if V_talep is not None:
        kontroller.append(_kontrol("Kesme Vr ≤ Vc", abs(_sayi(V_talep, "V_talep (kN)")), Vc / 1e3, K_CYT["kesme"], "kN"))
    dc = max([k["dc"] for k in kontroller] + [0.0])
    sonuc = _json({"tur": "celik_kesme", "profil": p["ad"], "Fy": Fy, "yontem": y, "Aw_mm2": Aw, "h_mm": hw,
                   "h_tw": htw, "sinir_224": sinir, "dal": dal, "Cv1": Cv1, "phi_v": phi, "Omega_v": om,
                   "katsayi": kat, "Vn_kN": Vn / 1e3, "Vc_kN": Vc / 1e3, "dc": dc,
                   "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller, "uyarilar": []})
    if anl is not None:
        _basla(anl, f"Çelik kesme: {p['ad']} (ÇYTHYE 10.2.1)",
               "Kesmeyi I-profilde esas olarak gövde taşır. Gövde yeterince kalınsa (h/tw küçük) kayma akmasına kadar "
               "burkulmaz; o zaman Cv1 = 1 ve dayanım katsayısı daha elverişlidir.")
        anl.mat(rf"\frac{{h}}{{t_w}} = \frac{{{_L(hw, 1)}}}{{{_L(p['tw'], 1)}}} = {_L(htw, 2)}\ "
                + ("\\le" if htw <= sinir else ">") + rf"\ 2{{,}}24\sqrt{{E/F_y}} = {_L(sinir, 2)}\ \Rightarrow\ C_{{v1}} = {_L(Cv1, 3)},\ "
                + (rf"\phi_v = {_L(phi)}" if y == "YDKT" else rf"\Omega_v = {_L(om)}"))
        anl.mat(rf"V_n = 0{{,}}6F_yA_wC_{{v1}} = 0{{,}}6\cdot{_L(Fy, 0)}\cdot({_L(p['h'], 0)}\cdot{_L(p['tw'], 1)})\cdot"
                rf"{_L(Cv1, 3)} = {_L(Vn / 1e3, 1)}\ \text{{kN}},\quad V_c = {_L(Vc / 1e3, 1)}\ \text{{kN}}")
        if kontroller:
            _durum_ozet(anl, sonuc)
        else:
            anl.sonuc(rf"V_c = {_L(Vc / 1e3, 1)}\ \text{{kN}}")
    return sonuc


def celik_cekme(profil, Fy=275.0, Fu=430.0, An=None, U=1.0, L=None, yontem="YDKT", T_talep=None, anl=None) -> dict:
    """ÇYTHYE Bölüm 7: akma Tn = Fy·Ag (φt = 0,90 / Ωt = 1,67), kırılma Tn = Fu·Ae, Ae = U·An (φt = 0,75 / Ωt = 2,00).
    An (cm², verilmezse Ag), U (Tablo 7.1; varsayılan 1), L (m, verilirse L/i ≤ 300 denetimi).

    Dönüş: Tn_akma_kN, Tn_kirilma_kN, Tc_akma_kN, Tc_kirilma_kN, Tc_kN, belirleyici, dc, durum, kontroller."""
    p = _profil(profil)
    Fy, m = _Fy(Fy, p)
    if m is not None and (Fu is None or isinstance(Fu, str)):
        Fu = m["Fu"]
    Fu = _sayi(Fu, "Fu (MPa)", pozitif=True, sifir_olur=False)
    U = _sayi(U, "U", pozitif=True, sifir_olur=False)
    Ag = p["A"]
    An_mm = Ag if An is None else _sayi(An, "An (cm²)", pozitif=True, sifir_olur=False) * 100.0
    if An_mm > Ag * (1 + 1e-9):
        raise MatrisHatasi("Net alan An brüt alandan büyük olamaz.")
    Ae = U * An_mm
    ka, y = _katsayi(yontem, 0.90, 1.67)
    kk, _ = _katsayi(yontem, 0.75, 2.00)
    Ty, Tu = Fy * Ag, Fu * Ae
    Tcy, Tcu = ka * Ty, kk * Tu
    Tc = min(Tcy, Tcu)
    kontroller = []
    if T_talep is not None:
        kontroller.append(_kontrol("Eksenel çekme Tr ≤ Tc", abs(_sayi(T_talep, "T_talep (kN)")), Tc / 1e3,
                                   f"{K_CYT['cekme_akma']}; {K_CYT['cekme_kirilma']}", "kN"))
    if L is not None:
        Li = _sayi(L, "L (m)", pozitif=True) * 1000.0 / p["iz"]
        kontroller.append(_kontrol("Narinlik L/i ≤ 300", Li, 300.0, K_CYT["narinlik_cekme"]))
    dc = max([k["dc"] for k in kontroller] + [0.0])
    sonuc = _json({"tur": "celik_cekme", "profil": p["ad"], "Fy": Fy, "Fu": Fu, "yontem": y, "Ag_mm2": Ag,
                   "An_mm2": An_mm, "U": U, "Ae_mm2": Ae, "Tn_akma_kN": Ty / 1e3, "Tn_kirilma_kN": Tu / 1e3,
                   "Tc_akma_kN": Tcy / 1e3, "Tc_kirilma_kN": Tcu / 1e3, "Tc_kN": Tc / 1e3,
                   "belirleyici": "akma" if Tcy <= Tcu else "kırılma", "dc": dc,
                   "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller, "uyarilar": []})
    if anl is not None:
        _basla(anl, f"Çelik çekme elemanı: {p['ad']} (ÇYTHYE Bölüm 7)",
               "Çekme çubuğu iki biçimde göçer: brüt kesitin boyunca akması (aşırı uzama) ya da bulon delikleriyle "
               "zayıflamış net kesitin kopması. İkisinin küçüğü dayanımdır.")
        ta, tk = (r"\phi_t", r"\phi_t") if y == "YDKT" else (r"1/\Omega_t", r"1/\Omega_t")
        anl.mat(rf"T_{{n,akma}} = F_yA_g = {_L(Fy, 0)}\cdot{_L(Ag, 0)} = {_L(Ty / 1e3, 1)}\ \text{{kN}},\quad "
                rf"{ta}T_n = {_L(ka, 3)}\cdot{_L(Ty / 1e3, 1)} = {_L(Tcy / 1e3, 1)}\ \text{{kN}}\ (\text{{Denk. 7.2}})")
        anl.mat(rf"T_{{n,kırılma}} = F_uA_e = F_u\,U A_n = {_L(Fu, 0)}\cdot{_L(U, 2)}\cdot{_L(An_mm, 0)} = {_L(Tu / 1e3, 1)}"
                rf"\ \text{{kN}},\quad {tk}T_n = {_L(Tcu / 1e3, 1)}\ \text{{kN}}\ (\text{{Denk. 7.3}})")
        if kontroller:
            _durum_ozet(anl, sonuc)
        else:
            anl.sonuc(rf"T_c = {_L(Tc / 1e3, 1)}\ \text{{kN}}", f"({sonuc['belirleyici']} belirleyici)")
    return sonuc


def celik_etkilesim(Pr, Mrx, Mry, Pc, Mcx, Mcy) -> dict:
    """ÇYTHYE 11.1.1 (AISC H1-1a/b karşılığı). Pr/Pc ≥ 0,2: Pr/Pc + 8/9(Mrx/Mcx + Mry/Mcy) ≤ 1 (Denk. 11.1a);
    Pr/Pc < 0,2: Pr/(2Pc) + (Mrx/Mcx + Mry/Mcy) ≤ 1 (Denk. 11.1b). Mutlak değerler kullanılır.

    Dönüş: {oran_P, oran_Mx, oran_My, dal, dc, durum, kaynak}."""
    return _json(_celik_etkilesim(Pr, Mrx, Mry, Pc, Mcx, Mcy))


def _celik_etkilesim(Pr, Mrx, Mry, Pc, Mcx, Mcy):
    """celik_etkilesim'in yalın sözlüğü (_json'suz; celik_eleman_kontrol sonunda dönüştürür)."""
    Pr, Mrx, Mry = (abs(_sayi(v, ad)) for v, ad in ((Pr, "Pr"), (Mrx, "Mrx"), (Mry, "Mry")))
    Pc, Mcx, Mcy = (_sayi(v, ad, pozitif=True, sifir_olur=False) for v, ad in ((Pc, "Pc"), (Mcx, "Mcx"), (Mcy, "Mcy")))
    oP, ox, oy = Pr / Pc, Mrx / Mcx, Mry / Mcy
    if oP >= 0.2:
        dc, dal = oP + 8.0 / 9.0 * (ox + oy), "11.1a"
    else:
        dc, dal = oP / 2.0 + ox + oy, "11.1b"
    return {"oran_P": oP, "oran_Mx": ox, "oran_My": oy, "dal": dal, "dc": min(dc, DC_UST),
            "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kaynak": K_CYT["etkilesim"]}


def _kuvvet_listesi(kuvvetler):
    if kuvvetler is None:
        return []
    if isinstance(kuvvetler, dict):
        kuvvetler = [kuvvetler]
    liste = []
    for i, k in enumerate(kuvvetler):
        if not isinstance(k, dict):
            raise MatrisHatasi('Her kuvvet kaydı sözlük olmalı: {"ad": "K1", "N": 120, "Mx": 45, "My": 0, "V": 30} '
                               "(N kN, basınç +; M kN·m; V kN).")
        liste.append({"ad": str(k.get("ad", f"K{i + 1}")), "N": _sayi(k.get("N", 0.0), "N (kN)"),
                      "Mx": _sayi(k.get("Mx", 0.0), "Mx (kN·m)"), "My": _sayi(k.get("My", 0.0), "My (kN·m)"),
                      "V": _sayi(k.get("V", 0.0), "V (kN)")})
    return liste


def celik_eleman_kontrol(profil, malzeme="S275", L=3.0, Lb=None, K=1.0, kuvvetler=None, yontem="YDKT", Cb=1.0,
                         An=None, U=1.0, anl=None, kren=False, ham=False) -> dict:
    """Toplu çelik eleman tahkiki (ÇYTHYE): basınç/çekme, iki eksenli eğilme, güçlü eksen kesmesi, etkileşim.

    L (m) eleman boyu, Lb (m; varsayılan L), K sayı ya da (Kx, Ky), kuvvetler: sözlük ya da liste
    [{"ad", "N" (kN, basınç +, çekme −), "Mx" (güçlü eksen, kN·m), "My" (zayıf eksen), "V" (güçlü eksen kesmesi, kN)}].

    İki eksenli eğilme + eksenel kuvvet (aşık, eğik mertek, kren kirişi): her kombinasyonda ÇYTHYE 11.1.1/11.1.2
    (Denk. 11.1a/b) P_r/P_c + 8/9 (M_rx/M_cx + M_ry/M_cy) ya da P_r/(2P_c) + (M_rx/M_cx + M_ry/M_cy); M_cy zayıf eksen
    dayanımı 9.6 (Denk. 9.39/9.40). ``kren=True``: kren kirişi öğretici yaklaşımı — yanal tekerlek kuvvetinin momenti My
    yalnız üst başlıkça taşınır (W_z,üst ≈ W_z/2 → M_cy,üst = M_cy/2; ÇYTHYE'de ayrı kural yok), uyarı eklenir.
    Narinlik koşulları: KL/i ≤ 200 yalnız basınç alan kombinasyon varsa (md. 8.1.1), L/i ≤ 300 yalnız çekme varsa
    (md. 7.1.1); kuvvet verilmezse ikisi de.

    Dönüş: malzeme, sinif, basinc, cekme, egilme, kesme (alt sonuçlar), kombinasyonlar [{ad, ..., dc_etkilesim, dal,
    dc_kesme, dc}], Mcy_kullanilan_kNm, kren, dc, durum, kontroller (en elverişsiz kombinasyon), uyarilar."""
    p = _profil(profil)
    m = celik_malzeme(malzeme, max(p["tf"], p["tw"])) if not isinstance(malzeme, dict) else celik_malzeme(malzeme)
    Fy, Fu = m["Fy"], m["Fu"]
    L_m = _sayi(L, "L (m)", pozitif=True, sifir_olur=False)
    Lb_m = L_m if Lb is None else _sayi(Lb, "Lb (m)", pozitif=True)
    if isinstance(K, (list, tuple)):
        if len(K) != 2:
            raise MatrisHatasi("K bir sayı ya da (Kx, Ky) ikilisi olmalı.")
        Kx, Ky = (_sayi(k, "K", pozitif=True, sifir_olur=False) for k in K)
    else:
        Kx = Ky = _sayi(K, "K", pozitif=True, sifir_olur=False)
    pk = _geri(p)
    bas = celik_basinc(pk, Fy, Kx * L_m, Ky * L_m, None, yontem)
    cek = celik_cekme(pk, Fy, Fu, An, U, L_m, yontem)
    eg = celik_egilme(pk, Fy, Lb_m, Cb, yontem)
    ks = celik_kesme(pk, Fy, yontem)
    kombs = []
    Mcy = eg["Mcy_kNm"] / 2.0 if kren else eg["Mcy_kNm"]
    kay_y = f"{K_CYT['zayif']}; {K_CYT['kren']}" if kren else K_CYT["zayif"]
    for k in _kuvvet_listesi(kuvvetler):
        N = k["N"]
        if N >= 0:
            Pc, tur = bas["Pc_kN"], "basınç"
        else:
            Pc, tur = cek["Tc_kN"], "çekme"
        et = _celik_etkilesim(abs(N), k["Mx"], k["My"], Pc, eg["Mc_kNm"], Mcy)
        dck = _dc(abs(k["V"]), ks["Vc_kN"])
        kont = [
            _kontrol(f"Eksenel ({tur}) Pr ≤ Pc", abs(N), Pc, K_CYT["basinc"] if N >= 0 else K_CYT["cekme_akma"], "kN"),
            _kontrol("Güçlü eksen eğilmesi Mrx ≤ Mcx", abs(k["Mx"]), eg["Mc_kNm"], K_CYT["YBB"], "kN·m"),
            _kontrol("Zayıf eksen eğilmesi Mry ≤ Mcy" + (" (kren: yalnız üst başlık)" if kren else ""), abs(k["My"]),
                     Mcy, kay_y, "kN·m"),
            _kontrol(f"Bileşik etki (Denk. {et['dal']})", et["dc"], 1.0, K_CYT["etkilesim"], dc=et["dc"]),
            _kontrol("Kesme Vr ≤ Vc", abs(k["V"]), ks["Vc_kN"], K_CYT["kesme"], "kN"),
        ]
        kombs.append(dict(k, tur=tur, Pc_kN=Pc, etkilesim=et, dc_etkilesim=et["dc"], dal=et["dal"], dc_kesme=dck,
                          dc=max(x["dc"] for x in kont), kontroller=kont))
    var_bas = not kombs or any(c["N"] > 1e-9 for c in kombs)
    var_cek = not kombs or any(c["N"] < -1e-9 for c in kombs)
    genel = ([bas["kontroller"][-1]] if var_bas else []) + \
        ([x for x in cek["kontroller"] if "Narinlik" in x["ad"]] if var_cek else [])
    if kombs:
        en = max(kombs, key=lambda c: c["dc"])
        kontroller = [dict(x, ad=f"{en['ad']}: {x['ad']}") for x in en["kontroller"]] + genel
    else:
        kontroller = genel
    dc = max([x["dc"] for x in kontroller] + [0.0])
    uyarilar = list(dict.fromkeys(bas["uyarilar"] + eg["uyarilar"]))
    if kren:
        uyarilar.append("Kren kirişi (öğretici yaklaşım): yanal kuvvet momenti My yalnız üst başlıkta, M_cy,üst = M_cy/2 = "
                        f"{_f(Mcy, 2)} kN·m. Tekerlek yerel basıncı (gövde ezilmesi), yorulma ve dinamik katsayı bu "
                        "tahkikte yok (ÇYTHYE kren kuralı vermez; TS EN 1991-3 / EN 1993-6 teknik kural).")
    uyarilar.append("Pr ve Mr ikinci mertebe etkilerini içermelidir (ÇYTHYE Bölüm 6, B1/B2); bu tahkik verilen iç "
                    "kuvvetleri doğrudan kullanır.")
    sonuc = {"tur": "celik_eleman_kontrol", "profil": p["ad"], "malzeme": m, "yontem": bas["yontem"],
             "L_m": L_m, "Lb_m": Lb_m, "Kx": Kx, "Ky": Ky, "Cb": Cb, "sinif": eg["sinif"],
             "kren": bool(kren), "Mcy_kullanilan_kNm": Mcy,
             "basinc": bas, "cekme": cek, "egilme": eg, "kesme": ks, "kombinasyonlar": kombs,
             "dc": dc, "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller,
             "uyarilar": uyarilar}
    if ham and anl is None:          # iç kullanım (kesit önerisi taraması, §11 kaydı): _json dönüşümü yok, aynı sayılar
        return sonuc
    sonuc = _json(sonuc)
    if anl is not None:
        _basla(anl, f"Çelik eleman tahkiki: {p['ad']} {m['sinif']} ({sonuc['yontem']})",
               "Elemanın eksenel, eğilme ve kesme dayanımlarını ayrı ayrı bulup her kombinasyonda ÇYTHYE 11.1 "
               "etkileşim denklemiyle birleştiriyoruz.")
        anl.metin(f"Malzeme {m['sinif']} ({m['bant']}): Fy = {_f(Fy, 0)} MPa, Fu = {_f(Fu, 0)} MPa ({m['kaynak']}). "
                  f"L = {_f(L_m, 3)} m, Lb = {_f(Lb_m, 3)} m, Kx = {_f(Kx, 2)}, Ky = {_f(Ky, 2)}, Cb = {_f(Cb, 3)}.")
        kesit_sinifi(pk, Fy, anl=anl)
        celik_basinc(pk, Fy, Kx * L_m, Ky * L_m, None, yontem, anl=anl)
        celik_egilme(pk, Fy, Lb_m, Cb, yontem, anl=anl)
        celik_kesme(pk, Fy, yontem, anl=anl)
        if any(c["N"] < 0 for c in kombs):
            celik_cekme(pk, Fy, Fu, An, U, L_m, yontem, anl=anl)
        if kombs:
            anl.baslik("Bileşik etki (ÇYTHYE 11.1.1)", 3)
            anl.mat(r"\frac{P_r}{P_c}\ge 0{,}2:\ \frac{P_r}{P_c} + \frac{8}{9}\left(\frac{M_{rx}}{M_{cx}} + "
                    r"\frac{M_{ry}}{M_{cy}}\right) \le 1\ (11.1a);\qquad \frac{P_r}{P_c} < 0{,}2:\ \frac{P_r}{2P_c} + "
                    r"\left(\frac{M_{rx}}{M_{cx}} + \frac{M_{ry}}{M_{cy}}\right) \le 1\ (11.1b)")
            anl.metin(se._tablo(["Ad", "N (kN)", "Mx", "My", "V", "Pr/Pc", "Dal", "D/C etkileşim", "D/C kesme", "D/C"],
                                [[c["ad"], _f(c["N"], 1), _f(c["Mx"], 1), _f(c["My"], 1), _f(c["V"], 1),
                                  _f(c["etkilesim"]["oran_P"], 3), c["dal"], _f(c["dc_etkilesim"], 3),
                                  _f(c["dc_kesme"], 3), _f(c["dc"], 3)] for c in kombs]))
        _durum_ozet(anl, sonuc)
    return sonuc


# ============================================================================
# C) Basit çelik kesitler: kutu, boru, korniyer, çift korniyer, U (kapalı form özellikler)
# ============================================================================
K_CYT.update({
    "sinif_kutu": "ÇYTHYE 2018 Tablo 5.1A Durum 6 (basınç), Tablo 5.1B Durum 17 başlık / Durum 19 gövde (eğilme); "
                  "b = B − 3t, h = H − 3t (md. 5.4.1.2(d), köşe yarıçapı bilinmiyorsa)",
    "sinif_boru": "ÇYTHYE 2018 Tablo 5.1A Durum 9 (D/t ≤ 0,11E/Fy), Tablo 5.1B Durum 20 (0,07E/Fy; 0,31E/Fy)",
    "sinif_L": "ÇYTHYE 2018 Tablo 5.1A Durum 3 (tek korniyer kolu b/t ≤ 0,45√(E/Fy)), Tablo 5.1B Durum 12 (0,54; 0,91)",
    "sinif_2L_ara": "ÇYTHYE 2018 Tablo 5.1A Durum 3 (birbirine boşluklu bağlanan çift korniyer kolları)",
    "sinif_2L_bitisik": "ÇYTHYE 2018 Tablo 5.1A Durum 1 (boşluksuz sürekli birleştirilen çift korniyerin dış kolları); "
                        "bitişik kollar T gövdesi gibi Durum 4 (d/t ≤ 0,75√(E/Fy), t = 2t — yorum, doğrulanacak)",
    "sinif_U": "ÇYTHYE 2018 Tablo 5.1A Durum 1 (U başlığı) / Durum 5 (U gövdesi); Tablo 5.1B Durum 10 / Durum 15",
    "tasarim_et": "ÇYTHYE 2018 md. 5.4.2 (elektrik direnç kaynaklı boru/kutu: t_tasarım = 0,93t)",
    "ftb": "ÇYTHYE 2018 md. 8.2.2(b), Denk. 8.6, 8.10–8.12 (çift korniyer ve T: C_w ihmal, Denk. 8.14)",
    "tek_korniyer": "ÇYTHYE 2018 md. 8.3 (RG s.196–197), Denk. 8.15–8.18 (etkin narinlik; sabitler OCR'de bozuk, "
                    "AISC 360-10 E5 ile aynı yapıda alındı)",
    "yapma": "ÇYTHYE 2018 md. 8.4, Denk. 8.19–8.21 (K_i = 0,50: sırt sırta çift korniyer)",
    "narin_kesit": "ÇYTHYE 2018 md. 8.5 (narin enkesit, etkin alan) — bu modülde uygulanmadı",
    "tbdy_capraz": "TBDY 2018 md. 9.6.3.1 (SDY, KL/i ≤ 200), 9.6.4.2 (K düzeni yasak), 9.6.4.3 (yalnız çekme çaprazı "
                   "yasak); md. 9.7.3.1 (SDS, KL/i ≤ 200; V/ters V: KL/i ≤ 4,0√(E/Fy)), 9.7.4.2 (K yasak), 9.7.4.3 "
                   "(yalnız çekme: KL/i ≤ 300)",
    "tbdy_t93": "TBDY 2018 Tablo 9.3 (çapraz satırları, λhd SDY / λmd SDS): kutu b/t 0,55/0,64√(E/Fy); boru D/t "
                "0,038/0,044 E/Fy; I başlığı, korniyer, U, T b/t 0,30/0,38√(E/Fy); I gövdesi h/tw 1,49√(E/Fy)",
    "kren": "Öğretici yaklaşım (ÇYTHYE kren kirişi için ayrı kural vermez): yanal kuvvetin momenti M_y yalnız üst başlıkça "
            "taşınır, W_z,üst ≈ W_z/2 → M_cy,üst = M_cy/2",
})
CELIK_KUTLE = 7850.0      # kg/m³ — yalnız ağırlık sıralaması (kg/m) için (TS 498'de 78,5 kN/m³; araştırmada doğrulanamadı)

_STD_KAYNAK = {
    "KUTU": "EN 10210-2 (sıcak bitmiş) / EN 10219-2 (soğuk şekillendirilmiş) yaygın SHS/RHS boyları (seçki); hesap köşe "
            "yarıçaplı: sıcak r_o = 1,5t, r_i = t (EN 10210-2)",
    "BORU": "EN 10210-2 / EN 10219-2 yaygın CHS boyları (seçki); formüller kesin",
    "L": "EN 10056-1 eşit kollu korniyer yaygın boyları (seçki); kök yarıçapı r1 (EN 10056-1), uç yarıçapı r2 = r1/2",
    "2L": "EN 10056-1 korniyer çiftleri, sırt sırta (bayrak levhası aralığı s = 10 mm varsayılan)",
    "UPN": "EN 10279 / DIN 1026-1 nominal boyutlar (h, b, tw, t; r = t); konik başlık paralel kabul edilir",
}
_KUTU_STD = ((40, 40, 3), (50, 50, 3), (50, 50, 4), (60, 60, 4), (70, 70, 4), (80, 80, 4), (80, 80, 5), (90, 90, 5),
             (100, 100, 5), (100, 100, 6), (120, 120, 6), (140, 140, 6), (150, 150, 6), (160, 160, 8), (180, 180, 8),
             (200, 200, 8), (200, 200, 10), (250, 250, 10), (300, 300, 10),
             (100, 50, 4), (120, 60, 4), (120, 80, 5), (150, 100, 5), (160, 80, 5), (200, 100, 6), (250, 150, 8),
             (300, 200, 10))
_BORU_STD = ((48.3, 3.2), (60.3, 3.2), (76.1, 3.2), (88.9, 3.2), (88.9, 4), (101.6, 4), (114.3, 4), (114.3, 5),
             (139.7, 5), (168.3, 5), (168.3, 6.3), (193.7, 6.3), (219.1, 6.3), (219.1, 8), (244.5, 8), (273, 8),
             (323.9, 8), (323.9, 10), (355.6, 10), (406.4, 10))
_L_STD = ((40, 4, 6), (45, 5, 7), (50, 5, 7), (50, 6, 7), (60, 6, 8), (65, 7, 9), (70, 7, 9), (75, 8, 10), (80, 8, 10),
          (90, 9, 11), (100, 10, 12), (120, 12, 13), (150, 15, 16), (160, 16, 17), (180, 18, 18), (200, 20, 18))
_L_R1 = {(b, t): r for b, t, r in _L_STD}
_UPN_STD = {80: (45, 6, 8), 100: (50, 6, 8.5), 120: (55, 7, 9), 140: (60, 7, 10), 160: (65, 7.5, 10.5),
            180: (70, 8, 11), 200: (75, 8.5, 11.5), 220: (80, 9, 12.5), 240: (85, 9.5, 13), 260: (90, 10, 14),
            280: (95, 10, 15), 300: (100, 10, 16)}
_2L_ARA = 10.0            # mm, varsayılan bayrak (düğüm) levhası kalınlığı


def _sad(x):
    return _f(x, 2)


STANDART_KESITLER = {
    "KUTU": [f"KUTU {_sad(H)}x{_sad(B)}x{_sad(t)}" for H, B, t in _KUTU_STD],
    "BORU": [f"BORU {_sad(D)}x{_sad(t)}" for D, t in _BORU_STD],
    "L": [f"L {b}x{b}x{t}" for b, t, _ in _L_STD],
    "2L": [f"2L {b}x{b}x{t} s={_sad(_2L_ARA)}" for b, t, _ in _L_STD],
    "UPN": [f"UPN {h}" for h in _UPN_STD],
}

# --- parça toplama (dikdörtgen + köşe dolgusu "kavis": kare − çeyrek daire) --------------------------------------------
# Koordinatlar: X yatay, Z düşey (mm). Iy = ∫(Z − Zc)² dA (yatay y ekseni etrafında; güçlü eksen), Iz = ∫(X − Xc)² dA.
_KC = (10.0 - 3.0 * math.pi) / (12.0 - 3.0 * math.pi)     # kavis ağırlık merkezinin köşeden uzaklığı / r


def _dik(xa, xb, za, zb, s=1.0):
    x0, x1, z0, z1 = min(xa, xb), max(xa, xb), min(za, zb), max(za, zb)
    w, h = x1 - x0, z1 - z0
    return {"t": "dik", "s": s, "A": w * h, "cx": (x0 + x1) / 2, "cz": (z0 + z1) / 2, "Iy0": w * h ** 3 / 12.0,
            "Iz0": h * w ** 3 / 12.0, "Iyz0": 0.0, "x": (x0, x1), "z": (z0, z1)}


def _kavis(px, pz, sx, sz, r, s=1.0):
    """Köşe (px, pz)'den (sx, sz) yönüne uzanan kare − çeyrek daire parçası (köşe dolgusu ya da yuvarlatma kaybı).
    a = (1 − π/4)r², c = r(10 − 3π)/(12 − 3π), I_kenar = r⁴(1 − 5π/16), I_xy,köşe = ±r⁴(19/24 − π/4)."""
    if r <= 0:
        return None
    a = (1.0 - math.pi / 4.0) * r * r
    c = _KC * r
    I0 = r ** 4 * (1.0 - 5.0 * math.pi / 16.0) - a * c * c
    Ixy = sx * sz * (r ** 4 * (19.0 / 24.0 - math.pi / 4.0) - a * c * c)
    return {"t": "kavis", "s": s, "A": a, "cx": px + sx * c, "cz": pz + sz * c, "Iy0": I0, "Iz0": I0, "Iyz0": Ixy,
            "x": (min(px, px + sx * r), max(px, px + sx * r)), "z": (min(pz, pz + sz * r), max(pz, pz + sz * r))}


def _ucgen(p1, p2, p3, s=1.0):
    """Üçgen parça (köşe koordinatlarıyla kapalı form): ∫z² dA = A/6 Σ(z_i² + z_i z_j), ∫xz dA = A/12 (2Σx_i z_i + Σ x_i z_j)."""
    (x1, z1), (x2, z2), (x3, z3) = p1, p2, p3
    A = abs((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1)) / 2.0
    cx, cz = (x1 + x2 + x3) / 3.0, (z1 + z2 + z3) / 3.0
    zz = A / 6.0 * (z1 * z1 + z2 * z2 + z3 * z3 + z1 * z2 + z2 * z3 + z1 * z3)
    xx = A / 6.0 * (x1 * x1 + x2 * x2 + x3 * x3 + x1 * x2 + x2 * x3 + x1 * x3)
    xz = A / 12.0 * (2 * (x1 * z1 + x2 * z2 + x3 * z3) + x1 * z2 + x2 * z1 + x1 * z3 + x3 * z1 + x2 * z3 + x3 * z2)
    return {"t": "ucgen", "s": s, "A": A, "cx": cx, "cz": cz, "Iy0": zz - A * cz * cz, "Iz0": xx - A * cx * cx,
            "Iyz0": xz - A * cx * cz, "x": (min(x1, x2, x3), max(x1, x2, x3)), "z": (min(z1, z2, z3), max(z1, z2, z3))}


def _toplam(P):
    P = [p for p in P if p is not None and p["A"] > 0]
    A = sum(p["s"] * p["A"] for p in P)
    cx = sum(p["s"] * p["A"] * p["cx"] for p in P) / A
    cz = sum(p["s"] * p["A"] * p["cz"] for p in P) / A
    Iy = sum(p["s"] * (p["Iy0"] + p["A"] * (p["cz"] - cz) ** 2) for p in P)
    Iz = sum(p["s"] * (p["Iz0"] + p["A"] * (p["cx"] - cx) ** 2) for p in P)
    Iyz = sum(p["s"] * (p["Iyz0"] + p["A"] * (p["cx"] - cx) * (p["cz"] - cz)) for p in P)
    return P, A, cx, cz, Iy, Iz, Iyz


def _plastik(P, A, eksen):
    """W_pl: alanı ikiye bölen eksen (bisection) ve iki yarının statik momentleri toplamı. Dikdörtgenler kesin bölünür;
    küçük kavis parçaları ağırlık merkezinde toplanmış alan sayılır (yaklaşım, etkisi binde birler mertebesinde)."""
    k, c = ("z", "cz") if eksen == "y" else ("x", "cx")

    def alt(u):
        top = 0.0
        for p in P:
            lo, hi = p[k]
            top += p["s"] * p["A"] * (min(max((u - lo) / (hi - lo), 0.0), 1.0) if hi > lo else float(u >= lo))
        return top

    lo = min(p[k][0] for p in P)
    hi = max(p[k][1] for p in P)
    for _ in range(80):
        orta = 0.5 * (lo + hi)
        if alt(orta) < A / 2.0:
            lo = orta
        else:
            hi = orta
    u = 0.5 * (lo + hi)
    W = 0.0
    for p in P:
        a, b = p[k]
        if p["t"] == "dik" and a < u < b:
            W += p["s"] * p["A"] / (b - a) * ((u - a) ** 2 + (b - u) ** 2) / 2.0
        else:
            W += p["s"] * p["A"] * abs(p[c] - u)
    return W, u


def _korniyer_parcalar(b, t, r1, r2, x0=0.0, yon=1.0):
    """Eşit kollu korniyer: sırtı X = x0 (düşey kol dış yüzü), alt yüzü Z = 0; yatay kol ``yon`` (±1) yönüne uzanır."""
    def X(x):
        return x0 + yon * x
    return [_dik(X(0), X(t), 0, b), _dik(X(t), X(b), 0, t),
            _kavis(X(t), t, yon, 1, r1, +1),            # kök dolgusu
            _kavis(X(t), b, -yon, -1, r2, -1),           # düşey kol ucu yuvarlatması
            _kavis(X(b), t, -yon, -1, r2, -1)]           # yatay kol ucu yuvarlatması


def _sayi_kes(v, ad):
    return _sayi(v, ad, pozitif=True, sifir_olur=False)


def _kesit_hesap(tip, b):
    """tip + boyutlar (mm) → mm birimli özellik sözlüğü. Ayrıntı: ``kesit_ozellik``."""
    E_ = {}
    if tip == "kutu":
        H, B, t = (_sayi_kes(b.get(k), f"kutu {k} (mm)") for k in ("H", "B", "t"))
        imalat = str(b.get("imalat", "sicak")).lower()
        if imalat not in ("sicak", "soguk"):
            raise MatrisHatasi("kutu 'imalat' 'sicak' (EN 10210) ya da 'soguk' (EN 10219) olmalı.")
        td = t if imalat == "sicak" else 0.93 * t
        if imalat == "sicak":
            ro0, ri0 = 1.5 * td, 1.0 * td
        else:
            ro0, ri0 = ((2.0, 1.0) if t <= 6 else ((2.5, 1.5) if t <= 10 else (3.0, 2.0)))
            ro0, ri0 = ro0 * td, ri0 * td
        ro = float(b.get("r_o", ro0))
        ri = float(b.get("r_i", ri0))
        if 2 * td >= min(H, B):
            raise MatrisHatasi(f"Kutu et kalınlığı çok büyük: 2t = {2 * td:g} mm ≥ en küçük dış boyut.")
        P = [_dik(0, B, 0, H), _dik(td, B - td, td, H - td, -1)]
        for px, pz, sx, sz in ((0, 0, 1, 1), (B, 0, -1, 1), (0, H, 1, -1), (B, H, -1, -1)):
            P.append(_kavis(px, pz, sx, sz, ro, -1))
        for px, pz, sx, sz in ((td, td, 1, 1), (B - td, td, -1, 1), (td, H - td, 1, -1), (B - td, H - td, -1, -1)):
            P.append(_kavis(px, pz, sx, sz, ri, +1))
        P, A, cx, cz, Iy, Iz, Iyz = _toplam(P)
        Rc = (ro + ri) / 2.0
        p_ = 2.0 * ((B - td) + (H - td)) - 2.0 * Rc * (4.0 - math.pi)
        Ah = (B - td) * (H - td) - Rc ** 2 * (4.0 - math.pi)
        It = td ** 3 * p_ / 3.0 + 4.0 * Ah ** 2 * td / p_
        Iw = 0.0
        ad = f"KUTU {_sad(H)}x{_sad(B)}x{_sad(t)}"
        E_.update({"H": H, "B": B, "t": t, "t_tasarim": td, "r_o": ro, "r_i": ri, "imalat": imalat,
                   "Wely": Iy / (H / 2), "Welz": Iz / (B / 2)})
        varsayim = (f"Köşe yarıçaplı kapalı form (r_o = {_f(ro, 2)} mm, r_i = {_f(ri, 2)} mm); It: EN 10210-2 Ek "
                    "formülü I_t = t³p/3 + 4A_h²t/p" + ("; tasarım et kalınlığı 0,93t (ÇYTHYE 5.4.2)" if imalat == "soguk" else ""))
    elif tip == "boru":
        D, t = _sayi_kes(b.get("D"), "boru D (mm)"), _sayi_kes(b.get("t"), "boru t (mm)")
        imalat = str(b.get("imalat", "sicak")).lower()
        td = t if imalat == "sicak" else 0.93 * t
        if 2 * td >= D:
            raise MatrisHatasi("Boru et kalınlığı dış çapın yarısından küçük olmalı.")
        d = D - 2 * td
        A = math.pi / 4 * (D ** 2 - d ** 2)
        Iy = Iz = math.pi / 64 * (D ** 4 - d ** 4)
        Iyz = 0.0
        cx = cz = D / 2
        It, Iw = 2 * Iy, 0.0
        P = None
        ad = f"BORU {_sad(D)}x{_sad(t)}"
        E_.update({"D": D, "t": t, "t_tasarim": td, "imalat": imalat, "Wely": Iy / (D / 2), "Welz": Iy / (D / 2),
                   "Wply": (D ** 3 - d ** 3) / 6.0, "Wplz": (D ** 3 - d ** 3) / 6.0})
        varsayim = "Kesin kapalı form (A = π(D² − d²)/4, I = π(D⁴ − d⁴)/64, J = 2I, W_pl = (D³ − d³)/6)" + (
            "; tasarım et kalınlığı 0,93t (ÇYTHYE 5.4.2)" if imalat == "soguk" else "")
    elif tip in ("L", "2L"):
        bb, t = _sayi_kes(b.get("b"), "korniyer kol boyu b (mm)"), _sayi_kes(b.get("t"), "korniyer kalınlığı t (mm)")
        if t >= bb / 2:
            raise MatrisHatasi("Korniyer kalınlığı kol boyunun yarısından küçük olmalı.")
        r1 = float(b.get("r1", _L_R1.get((round(bb), round(t)), 0.0)))
        r2 = float(b.get("r2", r1 / 2.0))
        if tip == "L":
            P = _korniyer_parcalar(bb, t, r1, r2)
        else:
            s = float(b.get("s", _2L_ARA))
            if s < 0:
                raise MatrisHatasi("Çift korniyer aralığı s negatif olamaz.")
            P = _korniyer_parcalar(bb, t, r1, r2, s / 2, 1.0) + _korniyer_parcalar(bb, t, r1, r2, -s / 2, -1.0)
        P, A, cx, cz, Iy, Iz, Iyz = _toplam(P)
        It = 2 * (bb - t / 2) * t ** 3 / 3.0 * (1 if tip == "L" else 2)
        Iw = 0.0
        if tip == "L":
            e = cx
            Iu = (Iy + Iz) / 2 + math.hypot((Iy - Iz) / 2, Iyz)
            Iv = (Iy + Iz) / 2 - math.hypot((Iy - Iz) / 2, Iyz)
            uo = math.sqrt(2.0) * (e - t / 2)                   # kayma merkezi: kol orta çizgilerinin kesişimi
            io2 = uo ** 2 + (Iu + Iv) / A
            ad = f"L {_sad(bb)}x{_sad(bb)}x{_sad(t)}"
            E_.update({"b": bb, "t": t, "r1": r1, "r2": r2, "e": e, "Iu": Iu, "Iv": Iv, "iu": math.sqrt(Iu / A),
                       "iv": math.sqrt(Iv / A), "uo": uo, "io": math.sqrt(io2), "H_ftb": 1 - uo ** 2 / io2,
                       "Wely": Iy / (bb - e), "Welz": Iz / (bb - e)})
            varsayim = (f"Parça toplama: iki dikdörtgen kol + kök dolgusu r1 = {_f(r1, 1)} mm, uç yuvarlatması r2 = "
                        f"{_f(r2, 1)} mm (kare − çeyrek daire, kapalı form); J = Σ b t³/3 (orta çizgi), C_w ≈ 0")
        else:
            L1 = _kesit_hesap("L", {"b": bb, "t": t, "r1": r1, "r2": r2})
            zo = cz - t / 2                                      # kayma merkezi: yatay kolların orta çizgisinde
            io2 = zo ** 2 + (Iy + Iz) / A
            ad = f"2L {_sad(bb)}x{_sad(bb)}x{_sad(t)} s={_sad(s)}"
            E_.update({"b": bb, "t": t, "s": s, "r1": r1, "r2": r2, "e": L1["e"], "i_i": L1["iv"], "zo": zo,
                       "io": math.sqrt(io2), "H_ftb": 1 - zo ** 2 / io2, "Wely": Iy / max(cz, bb - cz),
                       "Welz": Iz / (bb + s / 2)})
            varsayim = (f"İki korniyer sırt sırta, düşey kollar arası s = {_f(s, 1)} mm; z (düşey) simetri eksenidir. "
                        "Korniyer özellikleri parça toplamayla; J = 2·Σ b t³/3, C_w ≈ 0 (Denk. 8.14)")
    elif tip == "U":
        h, bb, tw, tf = (_sayi_kes(b.get(k), f"U {k} (mm)") for k in ("h", "b", "tw", "tf"))
        r = float(b.get("r", tf))
        r2 = float(b.get("r2", r / 2.0 if "egim" in b else 0.0))
        egim = float(b.get("egim", 0.0))
        yar = (bb - tw) / 2.0
        t_uc, t_kok = tf - egim * yar, tf + egim * yar          # başlık kalınlığı: uçta / gövdede (tf başlık ortasında)
        if 2 * t_kok >= h or tw >= bb or t_uc <= 0:
            raise MatrisHatasi("U boyutları tutarsız (2tf < h, tw < b olmalı).")
        P = [_dik(0, tw, 0, h), _dik(tw, bb, 0, t_uc), _dik(tw, bb, h - t_uc, h),
             _ucgen((tw, t_uc), (tw, t_kok), (bb, t_uc)), _ucgen((tw, h - t_uc), (tw, h - t_kok), (bb, h - t_uc)),
             _kavis(tw, t_kok, 1, 1, r, +1), _kavis(tw, h - t_kok, 1, -1, r, +1),
             _kavis(bb, t_uc, -1, -1, r2, -1), _kavis(bb, h - t_uc, -1, 1, r2, -1)]
        P, A, cx, cz, Iy, Iz, Iyz = _toplam(P)
        bp, hp = bb - tw / 2, h - tf                         # orta çizgi ölçüleri
        es = 3 * bp ** 2 * tf / (6 * bp * tf + hp * tw)      # kayma merkezi – gövde orta çizgisi
        xo = es + (cx - tw / 2)
        Iw = tf * bp ** 3 * hp ** 2 / 12.0 * (3 * bp * tf + 2 * hp * tw) / (6 * bp * tf + hp * tw)
        It = (2 * bp * tf ** 3 + hp * tw ** 3) / 3.0
        io2 = xo ** 2 + (Iy + Iz) / A
        ad = str(b.get("ad", f"U {_sad(h)}x{_sad(bb)}x{_sad(tw)}x{_sad(tf)}"))
        E_.update({"h": h, "b": bb, "tw": tw, "tf": tf, "r": r, "r2": r2, "egim": egim, "e_ag": cx, "xo": xo, "io": math.sqrt(io2),
                   "H_ftb": 1 - xo ** 2 / io2, "Wely": Iy / (h / 2), "Welz": Iz / (bb - cx)})
        varsayim = (f"Parça toplama: gövde + başlıklar (iç yüz eğimi %{_f(100 * egim, 1)}: uçta {_f(t_uc, 2)}, gövdede "
                    f"{_f(t_kok, 2)} mm — dikdörtgen + üçgen), kök dolgusu r = {_f(r, 1)}, uç yuvarlatması r2 = {_f(r2, 1)} "
                    "mm; kayma merkezi, C_w ve J ince cidar orta çizgi formülleriyle (ortalama tf) — katalogdan C_w "
                    "%10–20, It %5–10 sapabilir")
    else:
        raise MatrisHatasi(f"Kesit tipi {tip!r} tanımsız: 'kutu', 'boru', 'L', '2L', 'U' (ya da IPE/HEA/HEB adı).")
    if P is not None:
        if "Wply" not in E_:
            E_["Wply"], E_["pna_y"] = _plastik(P, A, "y")
            E_["Wplz"], E_["pna_z"] = _plastik(P, A, "z")
    k = {"tip": tip, "ad": ad, "A": A, "Iy": Iy, "Iz": Iz, "iy": math.sqrt(Iy / A), "iz": math.sqrt(Iz / A),
         "Iyz": Iyz, "It": It, "Iw": Iw, "Xc": cx, "Zc": cz, "varsayim": varsayim, "parcalar": P}
    k.update(E_)
    k["i_min"] = min(k["iy"], k["iz"], k.get("iv", math.inf))
    k["g"] = A * 1e-6 * CELIK_KUTLE
    return k


_TIP_ES = {"KUTU": "kutu", "RHS": "kutu", "SHS": "kutu", "BORU": "boru", "CHS": "boru", "L": "L", "KORNIYER": "L",
           "2L": "2L", "CIFT_KORNIYER": "2L", "U": "U", "UPN": "U"}


def _ad_coz(ad):
    """'KUTU 200x100x6' / 'SHS 100x5' / 'BORU 168.3x6.3' / 'L 100x10' / '2L 100x10 s=12' / 'UPN 200' → (tip, boyutlar)."""
    import re
    s = " ".join(str(ad).strip().upper().replace("×", "X").replace("*", "X").replace(",", ".").split())
    m = re.match(r"^(2L|KUTU|RHS|SHS|BORU|CHS|L|UPN)\s*([0-9.]+(?:\s*X\s*[0-9.]+)*)\s*(?:\(?\s*S\s*=?\s*([0-9.]+)\s*\)?)?$", s)
    if not m:
        return None
    on, govde, ara = m.group(1), m.group(2), m.group(3)
    try:
        sayi = [float(x) for x in re.split(r"\s*X\s*", govde)]
    except ValueError:
        return None
    tip = _TIP_ES[on]
    if tip == "kutu":
        if len(sayi) == 2:
            return tip, {"H": sayi[0], "B": sayi[0], "t": sayi[1]}
        if len(sayi) == 3:
            return tip, {"H": sayi[0], "B": sayi[1], "t": sayi[2]}
    elif tip == "boru" and len(sayi) == 2:
        return tip, {"D": sayi[0], "t": sayi[1]}
    elif tip in ("L", "2L") and len(sayi) in (2, 3):
        if len(sayi) == 3 and sayi[0] != sayi[1]:
            raise MatrisHatasi(f"{ad!r}: yalnız eşit kollu korniyer desteklenir (L 100x100x10).")
        bt = {"b": sayi[0], "t": sayi[-1]}
        if tip == "2L":
            bt["s"] = float(ara) if ara is not None else _2L_ARA
        return tip, bt
    elif tip == "U" and len(sayi) == 1:
        h = int(round(sayi[0]))
        if h not in _UPN_STD:
            raise MatrisHatasi(f"UPN {h} tabloda yok; seçenekler: {', '.join(str(x) for x in _UPN_STD)}.")
        bb, tw, tf = _UPN_STD[h]
        return tip, {"h": h, "b": bb, "tw": tw, "tf": tf, "r": tf, "r2": tf / 2, "egim": 0.08, "ad": f"UPN {h}"}
    raise MatrisHatasi(f"Kesit adı {ad!r} çözümlenemedi. Örnekler: 'KUTU 200x100x6', 'KUTU 100x5', 'BORU 168.3x6.3', "
                       "'L 100x10', '2L 100x10 s=10', 'UPN 200'.")


def _katalog(k):
    """mm birimli özellik → katalog birimleri (cm², cm⁴, cm³, cm, ×10³ cm⁶; boyutlar mm)."""
    out = {"tip": k["tip"], "ad": k["ad"], "A": k["A"] / 100, "g": k["g"], "Iy": k["Iy"] / 1e4, "Iz": k["Iz"] / 1e4,
           "iy": k["iy"] / 10, "iz": k["iz"] / 10, "Wely": k["Wely"] / 1e3, "Welz": k["Welz"] / 1e3,
           "Wply": k["Wply"] / 1e3, "Wplz": k["Wplz"] / 1e3, "It": k["It"] / 1e4, "Iw": k["Iw"] / 1e9,
           "i_min": k["i_min"] / 10, "varsayim": k.get("varsayim", "")}
    for a in ("Iu", "Iv"):
        if a in k:
            out[a] = k[a] / 1e4
    for a in ("iu", "iv", "e", "i_i", "uo", "zo", "xo", "io", "e_ag"):
        if a in k:
            out[a] = k[a] / 10
    for a in ("H", "B", "t", "t_tasarim", "r_o", "r_i", "D", "b", "s", "r1", "r2", "h", "tw", "tf", "r", "H_ftb",
              "imalat", "egim"):
        if a in k:
            out[a] = k[a]
    tip = k["tip"]
    out["kaynak"] = _STD_KAYNAK.get({"kutu": "KUTU", "boru": "BORU", "L": "L", "2L": "2L", "U": "UPN"}[tip])
    return out


def kesit_ozellik(tip, boyutlar=None) -> dict:
    """Basit çelik kesitlerin özellikleri (kapalı form, parça toplama).

    ``tip``: "kutu" (RHS/SHS), "boru" (CHS), "L" (eşit kollu korniyer), "2L" (sırt sırta çift korniyer), "U" (UPN) — ya da
    doğrudan ad: "KUTU 200x100x6" (H×B×t), "KUTU 100x5" (kare), "BORU 168.3x6.3", "L 100x10", "2L 100x10 s=12",
    "UPN 200". ``boyutlar`` (mm): kutu {H, B, t, [imalat "sicak"|"soguk", r_o, r_i]}, boru {D, t, [imalat]},
    L {b, t, [r1, r2]}, 2L {b, t, s, [r1, r2]}, U {h, b, tw, tf, [r]}.

    Eksenler: y yatay (Iy, güçlü eksen; kutuda derinlik H), z düşey. Korniyerde ayrıca asal eksenler u (büyük) ve
    v (küçük): Iu, Iv, iu, **iv**; e ağırlık merkezinin sırttan uzaklığı. Çift korniyerde z simetri eksenidir (aralık s
    dahil), ``i_i`` tek korniyerin en küçük atalet yarıçapı (md. 8.4), ``zo`` kayma merkezinin ağırlık merkezine
    uzaklığı. U'da ``e_ag`` ağırlık merkezinin gövde sırtından, ``xo`` kayma merkezinin ağırlık merkezinden uzaklığı.

    Köşe yarıçapları: kutu EN 10210-2 hesap değerleriyle (sıcak r_o = 1,5t, r_i = t; soğuk EN 10219-2 tablosu ve
    ÇYTHYE 5.4.2 tasarım et kalınlığı 0,93t) dahil edilir; r_o = r_i = 0 verilirse keskin köşe (araştırma formülleri).
    Korniyerde kök (r1) ve uç (r2) yuvarlatmaları kare − çeyrek daire parçalarıyla eklenir (r1 = 0 → keskin köşe);
    yuvarlatmaların W_pl'ye katkısı ağırlık merkezinde toplu alan sayılır. U profil paralel başlıkla idealleştirilir
    (UPN konikliği ihmal: A ve I'da %1–3, C_w'de %10–20 sapma).

    Dönüş (katalog birimleri, ``yapi_veri.PROFILLER`` ile aynı): tip, ad, A cm², g kg/m, Iy, Iz cm⁴, iy, iz cm,
    Wely, Welz, Wply, Wplz cm³, It cm⁴, Iw ×10³ cm⁶, i_min cm (+ tipe özgü alanlar), varsayim, kaynak."""
    if boyutlar is None:
        c = _ad_coz(tip)
        if c is None:
            raise MatrisHatasi(f"Kesit adı {tip!r} çözümlenemedi; ya ad ('KUTU 100x5') ya da tip + boyutlar verin.")
        t_, boyutlar = c
    else:
        t_ = _TIP_ES.get(str(tip).strip().upper().replace(" ", "_").replace("İ", "I"), None)
        if t_ is None:
            raise MatrisHatasi(f"Kesit tipi {tip!r} tanımsız: 'kutu', 'boru', 'L', '2L', 'U'.")
        if not isinstance(boyutlar, dict):
            raise MatrisHatasi("boyutlar sözlük olmalı (mm): kutu {H, B, t}, boru {D, t}, L {b, t}, 2L {b, t, s}, "
                               "U {h, b, tw, tf}.")
    return _json(_katalog(_kesit_hesap(t_, boyutlar)))


def _cubuk_kesit(profil):
    """Profil (ad ya da sözlük) → mm birimli kesit sözlüğü; I/H profillerde tip 'I'."""
    if isinstance(profil, dict) and "tip" in profil and profil["tip"] in ("kutu", "boru", "L", "2L", "U"):
        boy = {k: profil[k] for k in ("H", "B", "t", "D", "b", "s", "r1", "r2", "h", "tw", "tf", "r", "r_o", "r_i",
                                      "imalat", "egim") if k in profil}      # kesit_ozellik sonucu ya da boyutlar (mm)
        k = _kesit_hesap(profil["tip"], boy)
        if "ad" in profil:
            k["ad"] = str(profil["ad"])
        return k
    if not isinstance(profil, dict):
        c = _ad_coz(profil)
        if c is not None:
            return _kesit_hesap(*c)
    p = _profil(profil)
    k = dict(p)
    k.update({"tip": "I", "i_min": min(p["iy"], p["iz"]), "g": p["A"] * 1e-6 * CELIK_KUTLE})
    if not isinstance(profil, dict) and yv is not None and p["ad"] in yv.PROFILLER:
        k["g"] = float(yv.PROFILLER[p["ad"]]["g"])
    return k


def _basit_kesit_sinifi(k, Fy, E, anl=None):
    """kesit_sinifi'nin basit kesit yolu (mm birimli kesit sözlüğü k): Tablo 5.1A / 5.1B parça oranları (_basit_sinif)."""
    if isinstance(Fy, (str, dict)):
        t = k.get("t") or max(k.get("tf", 0.0), k.get("tw", 0.0)) or None
        Fy = celik_malzeme(Fy, t if not isinstance(Fy, dict) else None)["Fy"]
    else:
        Fy = _sayi(Fy, "Fy (MPa)", pozitif=True, sifir_olur=False)
    E = _sayi(E, "E (MPa)", pozitif=True, sifir_olur=False)
    sn = _basit_sinif(k, Fy, E)
    sonuc = _json({"tur": "kesit_sinifi", "profil": k["ad"], "Fy": Fy, "E": E, "egilme": sn["egilme"], "basinc": sn["basinc"],
                   "parcalar": sn["parcalar"], "kaynak": sn["kaynak"]})
    if anl is not None:
        _basla(anl, f"Enkesit sınıfı: {k['ad']} (ÇYTHYE 5.4.1)",
               "Kesitin ince parçaları akmadan önce yerel olarak buruşabilir; genişlik/kalınlık oranları Tablo 5.1A (basınç) ve "
               "5.1B (eğilme) sınırlarıyla karşılaştırılır.")
        anl.metin(se._tablo(["Parça", "Oran", "λr (basınç)", "Basınç", "λp (eğilme)", "λr (eğilme)", "Eğilme"],
                            [[x["ad"], _f(x["oran"], 2), _f(x["lambda_r_basinc"], 2), x["basinc"],
                              _f(x["lambda_p"], 2) if x.get("lambda_p") is not None else "–",
                              _f(x["lambda_r"], 2) if x.get("lambda_r") is not None else "–", x.get("egilme") or "–"]
                             for x in sonuc["parcalar"]]))
        anl.metin(f"**{k['ad']}: basınçta {sonuc['basinc']}" + (f", eğilmede {sonuc['egilme']}" if sonuc["egilme"] else "")
                  + f"** ({sonuc['kaynak']}).")
    return sonuc


def _basit_sinif(k, Fy, E):
    """Tablo 5.1A (basınç) ve 5.1B (eğilme) sınıfı — basit kesitler."""
    q = math.sqrt(E / Fy)
    tip = k["tip"]
    P = []

    def parca(ad, oran, lr, durum, lp=None, lre=None, durum_e=None):
        x = {"ad": ad, "oran": oran, "lambda_r_basinc": lr, "durum_basinc": durum,
             "basinc": "narin olmayan" if oran <= lr else "narin"}
        if lp is not None:
            x.update({"lambda_p": lp, "lambda_r": lre, "durum_egilme": durum_e,
                      "egilme": "kompakt" if oran <= lp else ("kompakt olmayan" if oran <= lre else "narin")})
        P.append(x)

    if tip == "kutu":
        t = k["t_tasarim"]
        parca("başlık b/t = (B − 3t)/t", (k["B"] - 3 * t) / t, 1.40 * q, "Durum 6", 1.12 * q, 1.40 * q, "Durum 17")
        parca("gövde h/t = (H − 3t)/t", (k["H"] - 3 * t) / t, 1.40 * q, "Durum 6", 2.42 * q, 5.70 * q, "Durum 19")
        kaynak = K_CYT["sinif_kutu"]
    elif tip == "boru":
        parca("D/t", k["D"] / k["t_tasarim"], 0.11 * E / Fy, "Durum 9", 0.07 * E / Fy, 0.31 * E / Fy, "Durum 20")
        kaynak = K_CYT["sinif_boru"]
    elif tip == "L":
        parca("kol b/t", k["b"] / k["t"], 0.45 * q, "Durum 3", 0.54 * q, 0.91 * q, "Durum 12")
        kaynak = K_CYT["sinif_L"]
    elif tip == "2L":
        if k["s"] > 0:
            parca("kollar b/t (boşluklu bağlı)", k["b"] / k["t"], 0.45 * q, "Durum 3")
            kaynak = K_CYT["sinif_2L_ara"]
        else:
            parca("dış kollar b/t", k["b"] / k["t"], 0.56 * q, "Durum 1")
            parca("bitişik kollar d/(2t)", k["b"] / (2 * k["t"]), 0.75 * q, "Durum 4")
            kaynak = K_CYT["sinif_2L_bitisik"]
    elif tip == "U":
        parca("başlık b/tf", k["b"] / k["tf"], 0.56 * q, "Durum 1", 0.38 * q, 1.00 * q, "Durum 10")
        parca("gövde h/tw = (h − 2tf − 2r)/tw", (k["h"] - 2 * k["tf"] - 2 * k["r"]) / k["tw"], 1.49 * q, "Durum 5",
              3.76 * q, 5.70 * q, "Durum 15")
        kaynak = K_CYT["sinif_U"]
    else:  # pragma: no cover
        raise MatrisHatasi(f"tip {tip!r}")
    sira = ["kompakt", "kompakt olmayan", "narin"]
    eg = [x["egilme"] for x in P if "egilme" in x]
    return {"parcalar": P, "basinc": "narin" if any(x["basinc"] == "narin" for x in P) else "narin olmayan",
            "egilme": sira[max(sira.index(e) for e in eg)] if eg else None, "kaynak": kaynak}


def _fe_ftb(Fe1, Fet, H):
    """Denk. 8.6: eğilmeli-burulmalı burkulma (simetri ekseni etrafında eğilme + burulma)."""
    s = Fe1 + Fet
    return s / (2 * H) * (1 - math.sqrt(max(1 - 4 * Fe1 * Fet * H / s ** 2, 0.0)))


def _basinc_basit(k, Fy, E, G, Ly, Lz, Lt, L, korniyer, a_bag, bag_turu):
    """Basit kesitlerde Fe adayları → (modlar [{ad, Fe, KLr, kaynak}], narinlik oranı KL/i (geometrik, 8.1.1), ek)."""
    tip = k["tip"]
    pi2E = math.pi ** 2 * E
    mod = []
    ek = {}

    def egilmeli(ad, Lc, i):
        lam = Lc / i
        mod.append({"ad": ad, "KLr": lam, "Fe": pi2E / lam ** 2, "kaynak": "ÇYTHYE 2018 md. 8.2.1, Denk. 8.4"})
        return lam

    if tip in ("kutu", "boru"):
        ly = egilmeli("eğilmeli burkulma, y ekseni", Ly, k["iy"])
        lz = egilmeli("eğilmeli burkulma, z ekseni", Lz, k["iz"])
        narin = max(ly, lz)
    elif tip == "L":
        lv = Lz / k["iv"]
        narin = max(lv, Ly / k["iu"])
        if korniyer in ("duzlem", "uzay"):
            La = L / k["iy"]                                     # i_a: bağlı kola paralel geometrik eksen
            if korniyer == "duzlem":
                lam = 72 + 0.75 * La if La <= 80 else min(32 + 1.25 * La, 200.0)
                dn = "8.15" if La <= 80 else "8.16"
            else:
                lam = 60 + 0.8 * La if La <= 75 else min(45 + La, 200.0)
                dn = "8.17" if La <= 75 else "8.18"
            mod.append({"ad": f"etkin narinlik ({'düzlem' if korniyer == 'duzlem' else 'uzay'} kafes, Denk. {dn})",
                        "KLr": lam, "Fe": pi2E / lam ** 2, "kaynak": K_CYT["tek_korniyer"]})
            ek.update({"L_ia": La, "etkin_narinlik": lam})
        else:
            egilmeli("eğilmeli burkulma, v (zayıf asal) ekseni", Lz, k["iv"])
            lu = egilmeli("eğilmeli burkulma, u (güçlü asal) ekseni", Ly, k["iu"])
            sinir = 0.71 * math.sqrt(E / Fy)
            ek["bt_sinir_ftb"] = sinir
            if k["b"] / k["t"] > sinir:
                Fet = G * k["It"] / (k["A"] * k["io"] ** 2)
                Fe = _fe_ftb(pi2E / lu ** 2, Fet, k["H_ftb"])
                mod.append({"ad": "eğilmeli-burulmalı burkulma (u simetri ekseni)", "KLr": math.pi * math.sqrt(E / Fe),
                            "Fe": Fe, "kaynak": K_CYT["ftb"]})
                ek.update({"Fe_t_MPa": Fet})
    elif tip == "2L":
        ly = egilmeli("eğilmeli burkulma, y ekseni (simetri eksenine dik)", Ly, k["iy"])
        lz0 = Lz / k["iz"]
        lzm = lz0
        if a_bag is not None:
            a = a_bag * 1000.0
            ai = a / k["i_i"]
            if bag_turu == "bulonlu":
                lzm, dn = math.sqrt(lz0 ** 2 + ai ** 2), "8.19"
            elif ai <= 40:
                lzm, dn = lz0, "8.20"
            else:
                lzm, dn = math.sqrt(lz0 ** 2 + (0.50 * ai) ** 2), "8.21"
            ek.update({"a_mm": a, "a_ii": ai, "KLr_z0": lz0, "KLr_zm": lzm, "denklem_yapma": dn})
        Fez = pi2E / lzm ** 2
        Fet = G * k["It"] / (k["A"] * k["io"] ** 2)
        Fe = _fe_ftb(Fez, Fet, k["H_ftb"])
        mod.append({"ad": "eğilmeli burkulma, z (simetri) ekseni" + (" — yapma etkin narinlik" if a_bag else ""),
                    "KLr": lzm, "Fe": Fez, "kaynak": "ÇYTHYE 2018 md. 8.2.1, Denk. 8.4" + ("; " + K_CYT["yapma"] if a_bag else "")})
        mod.append({"ad": "eğilmeli-burulmalı burkulma (z simetri ekseni + burulma)", "KLr": math.pi * math.sqrt(E / Fe),
                    "Fe": Fe, "kaynak": K_CYT["ftb"]})
        ek.update({"Fe_t_MPa": Fet})
        narin = max(ly, lzm)
    elif tip == "U":
        lz = egilmeli("eğilmeli burkulma, z ekseni (zayıf, simetri eksenine dik)", Lz, k["iz"])
        ly = Ly / k["iy"]
        Fey = pi2E / ly ** 2
        Fet = (pi2E * k["Iw"] / Lt ** 2 + G * k["It"]) / (k["A"] * k["io"] ** 2)
        Fe = _fe_ftb(Fey, Fet, k["H_ftb"])
        mod.append({"ad": "eğilmeli burkulma, y (simetri) ekseni", "KLr": ly, "Fe": Fey,
                    "kaynak": "ÇYTHYE 2018 md. 8.2.1, Denk. 8.4"})
        mod.append({"ad": "eğilmeli-burulmalı burkulma (y simetri ekseni + burulma)", "KLr": math.pi * math.sqrt(E / Fe),
                    "Fe": Fe, "kaynak": K_CYT["ftb"] + " (U: F_ey yerine F_ex)"})
        ek.update({"Fe_t_MPa": Fet})
        narin = max(lz, ly)
    else:  # pragma: no cover
        raise MatrisHatasi(tip)
    return mod, narin, ek


def _narinlik_sinir(narinlik):
    v = {"basinc": 200.0, "cekme": 300.0}
    if narinlik is not None:
        if not isinstance(narinlik, dict):
            raise MatrisHatasi('narinlik sözlük olmalı: {"basinc": 200, "cekme": 300}.')
        for a, x in narinlik.items():
            if a not in v:
                raise MatrisHatasi(f"narinlik anahtarı {a!r} tanımsız ('basinc', 'cekme').")
            v[a] = _sayi(x, f"narinlik sınırı {a}", pozitif=True, sifir_olur=False)
    kay = {"basinc": K_CYT["narinlik_basinc"] if v["basinc"] == 200.0 else
           f"Kullanıcı sınırı KL/i ≤ {_f(v['basinc'], 1)} (ÇYTHYE 8.1.1: 200; TBDY Bölüm 9 çapraz koşulları ayrıca)",
           "cekme": K_CYT["narinlik_cekme"] if v["cekme"] == 300.0 else
           f"Kullanıcı sınırı L/i ≤ {_f(v['cekme'], 1)} (ÇYTHYE 7.1.1: 300)"}
    return v, kay


def _K2(K):
    if isinstance(K, (list, tuple)):
        if len(K) != 2:
            raise MatrisHatasi("K bir sayı ya da (K_y, K_z) ikilisi olmalı.")
        return tuple(_sayi(x, "K", pozitif=True, sifir_olur=False) for x in K)
    x = _sayi(K, "K", pozitif=True, sifir_olur=False)
    return x, x


def celik_cubuk_kontrol(profil, malzeme="S275", L=3.0, K=(1.0, 1.0), kuvvetler=None, yalniz_cekme=False,
                        narinlik=None, An=None, U=1.0, yontem="YDKT", korniyer="genel", a_bag=None, bag_turu="kaynakli",
                        tbdy_capraz=None, anl=None, ham=False) -> dict:
    """Çelik çekme/basınç çubuğu (çapraz, kafes çubuğu) tahkiki — ÇYTHYE 2018 Bölüm 7 ve 8.

    ``profil``: I/H adı ("HEA 160"), basit kesit adı ("KUTU 100x5", "BORU 114.3x4", "L 80x8", "2L 70x7 s=10", "UPN 160")
    ya da ``kesit_ozellik`` sözlüğü. ``L`` (m) düğümler arası boy; ``K`` = (K_y, K_z): y (yatay/güçlü) ve z (düşey/zayıf)
    eksen burkulma katsayıları — korniyerde (K_u, K_v); burulma boyu L_cz = max(K)·L. ``kuvvetler``: [{"ad", "N"}]
    (kN, basınç +, çekme −; Mx/My verilirse yok sayılır ve uyarılır — eğilme için ``celik_eleman_kontrol``).

    * Çekme: akma T_n = F_y A_g (φ_t = 0,90), kırılma T_n = F_u A_e, A_e = U·A_n (φ_t = 0,75) — Denk. 7.1–7.3.
      ``An`` cm² (varsayılan A_g), ``U`` (Tablo 7.1; korniyer tek kolundan bağlıysa < 1).
    * Basınç: I/H için ``celik_basinc`` (eğilmeli + burulmalı). Kutu/boru: eğilmeli (8.2.1). Korniyer ``korniyer``:
      "genel" → v ekseni eğilmeli + b/t > 0,71√(E/Fy) ise eğilmeli-burulmalı (8.3, 8.2.2); "duzlem" / "uzay" → kafes
      örgü elemanı etkin narinliği (Denk. 8.15–8.18, L/i_a ile). Çift korniyer: y eğilmeli; z simetri ekseni eğilmeli +
      burulmalı (Denk. 8.6, 8.14), ``a_bag`` (m, ara bağlantı aralığı) verilirse yapma etkin narinlik (8.19–8.21;
      ``bag_turu`` "kaynakli" | "bulonlu"). U: z eğilmeli; y simetri ekseni eğilmeli-burulmalı (C_w ile).
      F_cr: F_y/F_e ≤ 2,25 → 0,658^(F_y/F_e) F_y, değilse 0,877 F_e; P_n = F_cr A_g (φ_c = 0,90).
    * ``yalniz_cekme=True``: basınç kontrolü yapılmaz ("basınçta devre dışı"; kombinasyon çözümünde çubuk çıkarılır).
    * Narinlik koşulları ``narinlik`` = {"basinc": 200 (KL/i, md. 8.1.1), "cekme": 300 (L/i, md. 7.1.1)} — koşul satırı;
      basınç sınırı yalnız basınç alan (ya da kuvveti verilmemiş, yalnız çekme olmayan) çubukta uygulanır.
    * Kesit sınıfı Tablo 5.1A/5.1B; basınçta narin kesitte uyarı (md. 8.5 etkin alan uygulanmadı → güvensiz olabilir).
    * ``tbdy_capraz`` = {"suneklik": "SDY" | "SDS", "duzen": "X" | "tek" | "V" | "ters_V" | "K"}: TBDY 2018 merkezi
      çaprazlı sistem koşulları (md. 9.6/9.7; KL/i ≤ 200, SDS V/ters V'de ≤ 4,0√(E/Fy), K düzeni yasak, yalnız çekme
      çaprazı SDY'de yasak / SDS'de KL/i ≤ 300) ve Tablo 9.3 genişlik/kalınlık sınırları koşul satırı olarak eklenir.

    Dönüş: profil, tip, malzeme, yontem, L_m, K, ozellik (katalog birimleri), sinif, cekme {Ag_mm2, An_mm2, Ae_mm2,
    Tc_akma_kN, Tc_kirilma_kN, Tc_kN, belirleyici}, basinc {modlar, Fe_MPa, Fcr_MPa, bolge, Pn_kN, Pc_kN, belirleyen} |
    None, narinlik {basinc: {oran, sinir}, cekme: {...}}, kombinasyonlar [{ad, N, tur, kapasite_kN, dc, not}], dc, durum,
    kontroller, uyarilar."""
    k = _cubuk_kesit(profil)
    tmax = {"kutu": k.get("t"), "boru": k.get("t"), "L": k.get("t"), "2L": k.get("t"), "U": k.get("tf"),
            "I": max(k.get("tf", 0), k.get("tw", 0))}[k["tip"]]
    m = celik_malzeme(malzeme, tmax) if not isinstance(malzeme, dict) else celik_malzeme(malzeme)
    Fy, Fu, E, G = m["Fy"], m["Fu"], m["E"], m["G"]
    L_m = _sayi(L, "L (m)", pozitif=True, sifir_olur=False)
    Ky, Kz = _K2(K)
    if korniyer not in ("genel", "duzlem", "uzay"):
        raise MatrisHatasi("korniyer 'genel', 'duzlem' (düzlem kafes) ya da 'uzay' (uzay kafes) olmalı.")
    if bag_turu not in ("kaynakli", "bulonlu"):
        raise MatrisHatasi("bag_turu 'kaynakli' ya da 'bulonlu' (basit sıkma) olmalı.")
    a_bag = None if a_bag is None else _sayi(a_bag, "a_bag (m)", pozitif=True, sifir_olur=False)
    U = _sayi(U, "U", pozitif=True, sifir_olur=False)
    if U > 1:
        raise MatrisHatasi("U (gerilme yığılması katsayısı, Tablo 7.1) 1'den büyük olamaz.")
    sin, sin_kay = _narinlik_sinir(narinlik)
    kat_c, y = _katsayi(yontem, 0.90, 1.67)
    kat_t, _ = _katsayi(yontem, 0.90, 1.67)
    kat_k, _ = _katsayi(yontem, 0.75, 2.00)
    Lmm = L_m * 1000.0
    uyarilar = []
    kuv = _kuvvet_listesi(kuvvetler)
    if any(abs(c["Mx"]) > 1e-9 or abs(c["My"]) > 1e-9 for c in kuv):
        uyarilar.append("Kuvvetlerde Mx/My var: çubuk tahkiki yalnız eksenel kuvveti kullanır (momentler yok sayıldı). "
                        "Eğilmeli eleman için celik_eleman_kontrol (I/H) kullanın.")
    # --- kesit sınıfı
    if k["tip"] == "I":
        sn0 = kesit_sinifi(_geri(k), Fy, E)
        sinif = {"parcalar": [dict(sn0["baslik"], ad="başlık b/2tf", durum_basinc="Durum 1"),
                              dict(sn0["govde"], ad="gövde h/tw", durum_basinc="Durum 5")],
                 "basinc": sn0["basinc"], "egilme": sn0["egilme"], "kaynak": sn0["kaynak"]}
    else:
        sinif = _basit_sinif(k, Fy, E)
    # --- çekme
    Ag = k["A"]
    An_mm = Ag if An is None else _sayi(An, "An (cm²)", pozitif=True, sifir_olur=False) * 100.0
    if An_mm > Ag * (1 + 1e-9):
        raise MatrisHatasi("Net alan An brüt alandan büyük olamaz.")
    Ae = U * An_mm
    Tcy, Tcu = kat_t * Fy * Ag, kat_k * Fu * Ae
    cekme = {"Ag_mm2": Ag, "An_mm2": An_mm, "U": U, "Ae_mm2": Ae, "Tn_akma_kN": Fy * Ag / 1e3,
             "Tn_kirilma_kN": Fu * Ae / 1e3, "Tc_akma_kN": Tcy / 1e3, "Tc_kirilma_kN": Tcu / 1e3,
             "Tc_kN": min(Tcy, Tcu) / 1e3, "belirleyici": "akma" if Tcy <= Tcu else "kırılma",
             "kaynak": f"{K_CYT['cekme_akma']}; {K_CYT['cekme_kirilma']}"}
    # --- basınç
    Ly, Lz = Ky * Lmm, Kz * Lmm
    Lt = max(Ky, Kz) * Lmm
    if k["tip"] == "I":
        b0 = celik_basinc(_geri(k), Fy, Ly / 1e3, Lz / 1e3, None, yontem, E, G)
        modlar = [{"ad": "eğilmeli burkulma, y ekseni", "KLr": b0["KLr_x"], "Fe": b0["Fe_x_MPa"],
                   "kaynak": "ÇYTHYE 2018 md. 8.2.1, Denk. 8.4"},
                  {"ad": "eğilmeli burkulma, z ekseni", "KLr": b0["KLr_y"], "Fe": b0["Fe_y_MPa"],
                   "kaynak": "ÇYTHYE 2018 md. 8.2.1, Denk. 8.4"},
                  {"ad": "burulmalı burkulma", "KLr": math.pi * math.sqrt(E / b0["Fe_z_MPa"]), "Fe": b0["Fe_z_MPa"],
                   "kaynak": K_CYT["burulmali"]}]
        narin_b, ek = b0["KLr"], {}
        if korniyer != "genel" or a_bag is not None:
            uyarilar.append("korniyer / a_bag seçenekleri yalnız korniyer kesitlerinde kullanılır; yok sayıldı.")
    else:
        modlar, narin_b, ek = _basinc_basit(k, Fy, E, G, Ly, Lz, Lt, Lmm, korniyer, a_bag, bag_turu)
        if k["tip"] == "L" and korniyer == "genel":
            uyarilar.append("Tek korniyer çoğunlukla bir kolundan dışmerkez bağlanır: ÇYTHYE 8.3 koşulları sağlanıyorsa "
                            "korniyer='duzlem' / 'uzay' (etkin narinlik, Denk. 8.15–8.18); sağlanmıyorsa Bölüm 11 (eğilme + "
                            "eksenel) gerekir. Burada merkezi yükleme varsayıldı.")
            if U == 1.0:
                uyarilar.append("Korniyer tek kolundan bağlıysa çekmede gerilme yığılması katsayısı U < 1'dir (Tablo 7.1).")
        if k["tip"] == "2L" and a_bag is None:
            uyarilar.append("Çift korniyer: ara bağlantı aralığı a_bag verilmedi; yapma etkin narinlik (md. 8.4) "
                            "uygulanmadı ((KL/i)_m = (KL/i)_0 — a/i_i ≤ 40 varsayımı). Uç noktalar arasında en az iki ara "
                            "bağlantı gerekir.")
    en = min(modlar, key=lambda x: x["Fe"])
    Fe = en["Fe"]
    Fcr, bolge = _fcr_basinc(Fy, Fe, E, math.pi * math.sqrt(E / Fe))
    Pn = Fcr * Ag
    basinc = None if yalniz_cekme else {
        "modlar": modlar, "Fe_MPa": Fe, "Fcr_MPa": Fcr, "bolge": bolge, "belirleyen": en["ad"],
        "Fy_Fe": Fy / Fe, "Pn_kN": Pn / 1e3, "Pc_kN": kat_c * Pn / 1e3, "Ly_mm": Ly, "Lz_mm": Lz, "Lt_mm": Lt,
        "kaynak": f"{K_CYT['basinc']}; {en['kaynak']}", **ek}
    if not yalniz_cekme and sinif["basinc"] == "narin":
        uyarilar.append("Kesit basınçta narin (Tablo 5.1A): ÇYTHYE 8.5 etkin alan yöntemi gerekir; burada brüt alanla "
                        "hesaplandı (güvensiz tarafta olabilir) — daha kalın cidarlı kesit seçin.")
    # --- narinlik
    oran_c = Lmm / k["i_min"]
    nar = {"basinc": None if yalniz_cekme else {"oran": narin_b, "sinir": sin["basinc"], "kaynak": sin_kay["basinc"]},
           "cekme": {"oran": oran_c, "sinir": sin["cekme"], "kaynak": sin_kay["cekme"], "i_min_mm": k["i_min"]}}
    # --- kombinasyonlar
    kombs = []
    for c in kuv:
        N = c["N"]
        if N > 0:
            if yalniz_cekme:
                kombs.append({"ad": c["ad"], "N": N, "tur": "basınç", "kapasite_kN": 0.0, "dc": 0.0,
                              "not": "basınçta devre dışı (yalnız çekme çubuğu)"})
                continue
            cap = kat_c * Pn / 1e3
            kombs.append({"ad": c["ad"], "N": N, "tur": "basınç", "kapasite_kN": cap, "dc": _dc(N, cap),
                          "belirleyen": en["ad"], "not": ""})
        else:
            cap = cekme["Tc_kN"]
            kombs.append({"ad": c["ad"], "N": N, "tur": "çekme", "kapasite_kN": cap, "dc": _dc(-N, cap),
                          "belirleyen": cekme["belirleyici"], "not": ""})
    kontroller = []
    if kombs:
        eb = max(kombs, key=lambda c: c["dc"])
        if eb["tur"] == "basınç" and not yalniz_cekme:
            kontroller.append(_kontrol(f"{eb['ad']}: Eksenel basınç Pr ≤ Pc ({en['ad']})", eb["N"], eb["kapasite_kN"],
                                       basinc["kaynak"], "kN"))
        elif eb["tur"] == "çekme":
            kontroller.append(_kontrol(f"{eb['ad']}: Eksenel çekme Tr ≤ Tc ({cekme['belirleyici']})", -eb["N"],
                                       eb["kapasite_kN"], cekme["kaynak"], "kN"))
        else:
            kontroller.append(_kontrol(f"{eb['ad']}: Eksenel basınç — devre dışı (yalnız çekme)", 0.0, 1.0,
                                       "Yalnız çekme çubuğu: basınçta çalışmaz", "kN"))
    var_bas = (not kuv and not yalniz_cekme) or any(c["N"] > 1e-9 for c in kuv)
    var_cek = not kuv or yalniz_cekme or any(c["N"] < -1e-9 for c in kuv)
    if var_bas and not yalniz_cekme:
        kontroller.append(_kontrol(f"Narinlik KL/i ≤ {_f(sin['basinc'], 0)} (basınç)", narin_b, sin["basinc"],
                                   sin_kay["basinc"]))
    if var_cek:
        kontroller.append(_kontrol(f"Narinlik L/i ≤ {_f(sin['cekme'], 0)} (çekme)", oran_c, sin["cekme"],
                                   sin_kay["cekme"]))
    if tbdy_capraz is not None:
        kontroller += _tbdy_capraz_kosullari(tbdy_capraz, k, sinif, Fy, E, narin_b, Ky, Kz, Lmm, yalniz_cekme, uyarilar)
    if yalniz_cekme:
        uyarilar.append("Yalnız çekme çubuğu: basınç kontrolü yapılmadı (basınçta devre dışı). Çözümde basınca düşen "
                        "çubuk çıkarılmalıdır (doğrusal olmayan çözüm, süperpozisyon geçersiz).")
    dc = max([x["dc"] for x in kontroller] + [0.0])
    sonuc = {
        "tur": "celik_cubuk_kontrol", "profil": k["ad"], "tip": k["tip"], "malzeme": m, "yontem": y, "L_m": L_m,
        "K": [Ky, Kz], "korniyer": korniyer if k["tip"] == "L" else None, "yalniz_cekme": bool(yalniz_cekme),
        "ozellik": _katalog(k) if k["tip"] != "I" else _geri(k), "agirlik_kg_m": k["g"], "sinif": sinif,
        "cekme": cekme, "basinc": basinc, "narinlik": nar, "kombinasyonlar": kombs, "dc": dc,
        "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller, "uyarilar": uyarilar,
    }
    if ham and anl is None:          # iç kullanım: _json dönüşümü yok, aynı sayılar
        return sonuc
    sonuc = _json(sonuc)
    if anl is not None:
        _anlat_cubuk(anl, sonuc, k, Fy, Fu, E)
    return sonuc


def _tbdy_capraz_kosullari(tc, k, sinif, Fy, E, narin_b, Ky, Kz, Lmm, yalniz_cekme, uyarilar):
    """TBDY 2018 md. 9.6/9.7 merkezi çapraz koşulları ve Tablo 9.3 genişlik/kalınlık sınırları (koşul satırları)."""
    if not isinstance(tc, dict):
        raise MatrisHatasi('tbdy_capraz sözlük olmalı: {"suneklik": "SDY"|"SDS", "duzen": "X"|"tek"|"V"|"ters_V"|"K"}.')
    sd = str(tc.get("suneklik", "SDY")).upper()
    dz = str(tc.get("duzen", "X"))
    if sd not in ("SDY", "SDS"):
        raise MatrisHatasi("tbdy_capraz suneklik 'SDY' (md. 9.6) ya da 'SDS' (md. 9.7) olmalı.")
    if dz not in ("X", "tek", "V", "ters_V", "K"):
        raise MatrisHatasi("tbdy_capraz duzen 'X', 'tek', 'V', 'ters_V' ya da 'K' olmalı.")
    q = math.sqrt(E / Fy)
    md = "9.6" if sd == "SDY" else "9.7"
    out = []
    if dz == "K":
        out.append(_kontrol(f"TBDY {sd}: K düzeni yasak (md. {md}.4.2)", 1.0, 0.0, K_CYT["tbdy_capraz"], dc=DC_UST))
    if yalniz_cekme:
        if sd == "SDY":
            out.append(_kontrol("TBDY SDY: yalnız çekme çaprazı yasak (md. 9.6.4.3)", 1.0, 0.0, K_CYT["tbdy_capraz"],
                                dc=DC_UST))
        else:
            KLr = max(Ky, Kz) * Lmm / k["i_min"]
            out.append(_kontrol("TBDY SDS: yalnız çekme çaprazı KL/i ≤ 300 (md. 9.7.4.3)", KLr, 300.0,
                                K_CYT["tbdy_capraz"]))
    else:
        out.append(_kontrol(f"TBDY {sd}: çapraz KL/i ≤ 200 (md. {md}.3.1)", narin_b, 200.0, K_CYT["tbdy_capraz"]))
        if sd == "SDS" and dz in ("V", "ters_V"):
            out.append(_kontrol("TBDY SDS V/ters V: KL/i ≤ 4,0√(E/Fy) (md. 9.7.3.1)", narin_b, 4.0 * q,
                                K_CYT["tbdy_capraz"]))
    # Tablo 9.3: λhd (SDY) / λmd (SDS)
    tip = k["tip"]
    i_ = 0 if sd == "SDY" else 1
    satir = []
    if tip == "kutu":
        t = k["t_tasarim"]
        lam = (0.55, 0.64)[i_] * q
        satir = [("kutu b/t", max(k["B"], k["H"]) / t - 3.0, lam)]
    elif tip == "boru":
        satir = [("boru D/t", k["D"] / k["t_tasarim"], (0.038, 0.044)[i_] * E / Fy)]
    elif tip in ("L", "2L"):
        satir = [("korniyer kolu b/t", k["b"] / k["t"], (0.30, 0.38)[i_] * q)]
    elif tip == "U":
        satir = [("U başlığı b/tf", k["b"] / k["tf"], (0.30, 0.38)[i_] * q),
                 ("U gövdesi h/tw", (k["h"] - 2 * k["tf"] - 2 * k["r"]) / k["tw"], 1.49 * q)]
    else:
        satir = [("I başlığı b/2tf", k["b"] / (2 * k["tf"]), (0.30, 0.38)[i_] * q),
                 ("I gövdesi h/tw", (k["h"] - 2 * k["tf"] - 2 * k["r"]) / k["tw"], 1.49 * q)]
    for ad, oran, lam in satir:
        out.append(_kontrol(f"TBDY Tablo 9.3 ({'λhd' if i_ == 0 else 'λmd'}): {ad}", oran, lam, K_CYT["tbdy_t93"]))
    uyarilar.append(f"TBDY {sd} merkezi çapraz: birleşim ve kolon/kiriş kuvvetleri kapasite tasarımıyla (md. {md}.2, "
                    "{md}.5–{md}.6: T = R_y F_y A_g, P1 = 1,14 F_cre A_g) ayrıca hesaplanmalıdır (bu tahkikte yok)."
                    .replace("{md}", md))
    return out


def _svg_basit(k, baslik):
    S = _Svg()
    if k["tip"] == "boru":
        s = 160.0 / k["D"]
        R = k["D"] / 2 * s
        S.parca.append(f'<circle cx="{se._n(R)}" cy="{se._n(R)}" r="{se._n(R - k["t_tasarim"] * s / 2)}" '
                       f'{S._renk("a", False)} stroke-width="{se._n(max(k["t_tasarim"] * s, 1.5))}"/>')
        S.kapsa(0, 0, 2 * R, 2 * R)
        S.yazi(R, -6, f"D = {_f(k['D'], 1)} mm, t = {_f(k['t'], 1)}", boyut=10)
        return S.svg(baslik)
    P = [p for p in k["parcalar"] if p["t"] == "dik"]
    x0 = min(p["x"][0] for p in P)
    x1 = max(p["x"][1] for p in P)
    z0 = min(p["z"][0] for p in P)
    z1 = max(p["z"][1] for p in P)
    s = 180.0 / max(x1 - x0, z1 - z0)

    def T(x, z):
        return (x - x0) * s, (z1 - z) * s

    for p in P:
        xa, za = T(p["x"][0], p["z"][1])
        w, h = (p["x"][1] - p["x"][0]) * s, (p["z"][1] - p["z"][0]) * s
        if p["s"] > 0:
            S.dikdortgen(xa, za, w, h, "a", kalin=1.0)
        else:
            S.parca.append(f'<rect x="{se._n(xa)}" y="{se._n(za)}" width="{se._n(w)}" height="{se._n(h)}" '
                           f'fill="var(--sema-zemin, #fff)" stroke="none"/>')
    cx, cz = T(k["Xc"], k["Zc"])
    S.daire(cx, cz, 3, "c")
    S.cizgi((-6, cz), ((x1 - x0) * s + 6, cz), "sil", kalin=0.8, kesik="5 3")
    S.yazi((x1 - x0) * s + 8, cz + 4, "y", anchor="start", boyut=10, aile="sil")
    S.cizgi((cx, -6), (cx, (z1 - z0) * s + 6), "sil", kalin=0.8, kesik="5 3")
    S.yazi(cx, (z1 - z0) * s + 18, "z", boyut=10, aile="sil")
    S.yazi((x1 - x0) * s / 2, -8, k["ad"], boyut=10, kalin=True)
    return S.svg(baslik)


def _anlat_cubuk(anl, s, k, Fy, Fu, E):
    _basla(anl, f"Çelik çubuk tahkiki: {s['profil']} {s['malzeme']['sinif']} (ÇYTHYE Bölüm 7–8)",
           "Kafes ve çapraz çubukları (uçları mafsallı kabul edilen) yalnız eksenel kuvvet taşır. Çekmede brüt kesitin "
           "akması ya da net kesitin kopması, basınçta ise burkulma belirler. Her burkulma biçimi için elastik burkulma "
           "gerilmesi F_e bulunur; en küçüğü kritik gerilmeyi verir. Narinlik sınırları ayrıca koşul olarak denetlenir.")
    o = s["ozellik"]
    anl.metin(f"**Malzeme** {s['malzeme']['sinif']}: Fy = {_f(Fy, 0)} MPa, Fu = {_f(Fu, 0)} MPa ({s['malzeme']['kaynak']}). "
              f"L = {_f(s['L_m'], 3)} m, K_y = {_f(s['K'][0], 2)}, K_z = {_f(s['K'][1], 2)}, yöntem {s['yontem']}.")
    satir = [["A (cm²)", _f(o["A"], 2)], ["i_y (cm)", _f(o["iy"], 2)], ["i_z (cm)", _f(o["iz"], 2)],
             ["I_t (cm⁴)", _g(o["It"])]]
    for a, et in (("iv", "i_v (cm, zayıf asal)"), ("iu", "i_u (cm)"), ("e", "e (cm)"), ("i_i", "i_i (cm, tek parça)"),
                  ("io", "i_o (cm)"), ("H_ftb", "H")):
        if a in o:
            satir.append([et, _g(o[a])])
    anl.metin("**Kesit özellikleri:**\n\n" + se._tablo(["Özellik", "Değer"], satir))
    if o.get("varsayim"):
        anl.metin("Varsayım: " + o["varsayim"] + ".")
    if k["tip"] != "I":
        _sema(anl, f"{s['profil']} enkesiti", [(s["profil"], _svg_basit(k, s["profil"]))])
    sn = s["sinif"]
    anl.metin("**Enkesit sınıfı** (" + sn["kaynak"] + "):\n\n" + se._tablo(
        ["Parça", "Oran", "λr (basınç)", "Basınç", "λp / λr (eğilme)", "Eğilme"],
        [[x["ad"], _f(x["oran"], 2), f"{_f(x['lambda_r_basinc'], 2)} ({x.get('durum_basinc', '')})", x["basinc"],
          (f"{_f(x['lambda_p'], 2)} / {_f(x['lambda_r'], 2)}" if "lambda_p" in x else "–"), x.get("egilme", "–")]
         for x in sn["parcalar"]]))
    c = s["cekme"]
    ta = r"\phi_t" if s["yontem"] == "YDKT" else r"1/\Omega_t"
    anl.mat(rf"T_{{c,akma}} = {ta}F_yA_g = {_L(c['Tc_akma_kN'] / c['Tn_akma_kN'], 3)}\cdot{_L(Fy, 0)}\cdot"
            rf"{_L(c['Ag_mm2'], 0)} = {_L(c['Tc_akma_kN'], 1)}\ \text{{kN}}\quad(\text{{Denk. 7.2}})")
    anl.mat(rf"T_{{c,kırılma}} = {ta}F_uUA_n = {_L(c['Tc_kirilma_kN'] / max(c['Tn_kirilma_kN'], 1e-12), 3)}\cdot"
            rf"{_L(Fu, 0)}\cdot{_L(c['U'], 2)}\cdot{_L(c['An_mm2'], 0)} = {_L(c['Tc_kirilma_kN'], 1)}\ \text{{kN}}\quad"
            rf"(\text{{Denk. 7.1, 7.3}})")
    b = s["basinc"]
    if b is None:
        anl.uyari("Yalnız çekme çubuğu: basınç kontrolü yapılmaz (basınçta devre dışı).")
    else:
        anl.metin("**Burkulma biçimleri** (F_e, MPa):\n\n" + se._tablo(
            ["Biçim", "KL/i (eşdeğer)", "F_e (MPa)", "Kaynak"],
            [[x["ad"], _f(x["KLr"], 1), _f(x["Fe"], 1), x["kaynak"]] for x in b["modlar"]]))
        if "Fe_t_MPa" in b:
            anl.mat(rf"F_{{ez}} = \frac{{\pi^2EC_w/L_{{cz}}^2 + GJ}}{{A_g i_o^2}} = {_L(b['Fe_t_MPa'], 1)}\ \text{{MPa}},\quad"
                    rf" F_e = \frac{{F_{{e1}} + F_{{ez}}}}{{2H}}\left[1 - \sqrt{{1 - \frac{{4F_{{e1}}F_{{ez}}H}}"
                    rf"{{(F_{{e1}} + F_{{ez}})^2}}}}\right]\quad(\text{{Denk. 8.6}})")
        tt = r"\phi_c" if s["yontem"] == "YDKT" else r"1/\Omega_c"
        anl.mat(rf"\frac{{F_y}}{{F_e}} = {_L(b['Fy_Fe'], 3)}\ \Rightarrow\ F_{{cr}} = "
                + (rf"0{{,}}658^{{F_y/F_e}}F_y" if "8.2" in b["bolge"] else r"0{,}877F_e")
                + rf" = {_L(b['Fcr_MPa'], 2)}\ \text{{MPa}},\quad P_c = {tt}F_{{cr}}A_g = {_L(b['Pc_kN'], 1)}\ \text{{kN}}")
    if s["kombinasyonlar"]:
        anl.metin("**Kombinasyonlar:**\n\n" + se._tablo(
            ["Ad", "N (kN)", "Tür", "Kapasite (kN)", "D/C", "Not"],
            [[x["ad"], _f(x["N"], 1), x["tur"], _f(x["kapasite_kN"], 1), _f(x["dc"], 3), x.get("not", "")]
             for x in s["kombinasyonlar"]]))
    _durum_ozet(anl, s)


# ============================================================================
# D) Kesit önerisi (çelik: aile içinde ağırlık sırası; betonarme: b × h taraması)
# ============================================================================
_I_AILELER = ("IPE", "HEA", "HEB")
_EKSENEL_AILELER = ("KUTU", "BORU", "L", "2L", "UPN")
_AILE_ES = {"IPE": "IPE", "HEA": "HEA", "HEB": "HEB", "KUTU": "KUTU", "SHS": "KUTU", "RHS": "KUTU", "BORU": "BORU",
            "CHS": "BORU", "L": "L", "KORNIYER": "L", "2L": "2L", "UPN": "UPN", "U": "UPN"}


def _aile_coz(aile):
    """'IPE' / 'IPE 300' / 'kutu' / 'KUTU 100x5' / '2L 70x7' → (aile, başlangıç profil adı ya da None)."""
    s = " ".join(str(aile).strip().upper().replace("İ", "I").split())
    if s in _AILE_ES:
        return _AILE_ES[s], None
    for on in _I_AILELER:
        if s.startswith(on):
            return on, _profil(s)["ad"]
    c = _ad_coz(s)
    if c is not None:
        tip = c[0]
        return {"kutu": "KUTU", "boru": "BORU", "L": "L", "2L": "2L", "U": "UPN"}[tip], _kesit_hesap(*c)["ad"]
    raise MatrisHatasi(f"Aile {aile!r} tanımsız: IPE, HEA, HEB, KUTU, BORU, L, 2L, UPN (ya da bu ailelerden bir profil adı).")


def _aile_listesi(aile):
    """Ailenin profilleri, ağırlığa (kg/m) göre artan: [(ad, g)]."""
    if aile in _I_AILELER:
        tablo = _kutuphane("PROFILLER")
        liste = [(ad, float(p["g"])) for ad, p in tablo.items() if ad.split()[0] == aile]
    else:
        liste = [(ad, _kesit_hesap(*_ad_coz(ad))["g"]) for ad in STANDART_KESITLER[aile]]
    return sorted(liste, key=lambda x: (x[1], x[0]))


def _oner_parametre(parametreler):
    p = dict(parametreler or {})
    izin = {"L", "Lb", "K", "Cb", "yontem", "An_oran", "U", "yalniz_cekme", "narinlik", "korniyer", "a_bag", "bag_turu",
            "kontrol", "kren", "tbdy_capraz"}
    fazla = set(p) - izin
    if fazla:
        raise MatrisHatasi(f"Kontrol parametresi tanımsız: {', '.join(sorted(fazla))}. Geçerli: {', '.join(sorted(izin))} "
                           "(net alan profilden bağımsız olsun diye 'An_oran' = An/Ag verilir).")
    p.setdefault("L", 3.0)
    p.setdefault("yontem", "YDKT")
    p.setdefault("U", 1.0)
    p.setdefault("An_oran", 1.0)
    an = _sayi(p["An_oran"], "An_oran", pozitif=True, sifir_olur=False)
    if an > 1:
        raise MatrisHatasi("An_oran = An/Ag 1'den büyük olamaz.")
    return p


def _profil_kontrol(ad, aile, malzeme, p, kuvvetler, kontrol_turu):
    """Bir profilin tahkiki → (sonuç, dc, belirleyen)."""
    k = _cubuk_kesit(ad)
    An = None if p["An_oran"] == 1.0 else p["An_oran"] * k["A"] / 100.0
    if kontrol_turu == "eleman":
        r = celik_eleman_kontrol(ad, malzeme, p["L"], p.get("Lb"), p.get("K", 1.0), kuvvetler, p["yontem"],
                                 p.get("Cb", 1.0), An, p["U"], kren=p.get("kren", False), ham=True)
    else:
        r = celik_cubuk_kontrol(ad, malzeme, p["L"], p.get("K", (1.0, 1.0)), kuvvetler, p.get("yalniz_cekme", False),
                                p.get("narinlik"), An, p["U"], p["yontem"], p.get("korniyer", "genel"), p.get("a_bag"),
                                p.get("bag_turu", "kaynakli"), p.get("tbdy_capraz"), ham=True)
    bel = max(r["kontroller"], key=lambda x: x["dc"])["ad"] if r["kontroller"] else "—"
    return r, r["dc"], bel


def _aile_tara(aile, malzeme, p, kuvvetler, kontrol_turu, hepsi=False):
    denenen, bulunan = [], None
    for ad, g in _aile_listesi(aile):
        r, dc, bel = _profil_kontrol(ad, aile, malzeme, p, kuvvetler, kontrol_turu)
        denenen.append({"ad": ad, "agirlik_kg_m": g, "dc": dc, "belirleyen": bel, "durum": r["durum"],
                        "yeterli": bool(dc <= 1.0 + 1e-9)})
        if bulunan is None and dc <= 1.0 + 1e-9:
            bulunan = denenen[-1]
            if not hepsi:
                break
    return denenen, bulunan


def celik_kesit_oner(aile, malzeme="S275", parametreler=None, kuvvetler=None, baslangic=None, aile_degistir=True,
                     anl=None) -> dict:
    """Çelik kesit önerisi: ``aile`` içinden ağırlığa (kg/m) göre artan sırada ilk D/C ≤ 1 profil.

    ``aile``: "IPE" | "HEA" | "HEB" | "KUTU" | "BORU" | "L" | "2L" | "UPN" ya da bir profil adı ("IPE 300": aile IPE,
    mevcut profil IPE 300). Standart boy listeleri: ``yapi_veri.PROFILLER`` (I/H) ve ``STANDART_KESITLER`` (EN 10210/10219
    kutu-boru, EN 10056-1 korniyer, EN 10279 UPN; seçki). ``parametreler``: kontrol işlevine giden sözlük — L, Lb, K, Cb,
    yontem, U, An_oran (An/Ag), yalniz_cekme, narinlik, korniyer, a_bag, bag_turu, kren, tbdy_capraz ve
    ``kontrol`` ("eleman": ``celik_eleman_kontrol``; "cubuk": ``celik_cubuk_kontrol``). Varsayılan: I/H ailesinde
    kuvvetlerde moment ya da kesme varsa "eleman", değilse "cubuk"; diğer ailelerde "cubuk" (yalnız eksenel).
    ``kuvvetler``: [{"ad", "N", "Mx", "My", "V"}] (aynı iç kuvvetler bütün profillere uygulanır — rijitlik değişince
    kuvvetler değişir; yeniden çözüm gerekir). ``baslangic``: mevcut profil (D/C'si raporlanır; tarama her zaman ailenin
    en hafifinden başlar, bu yüzden öneriden hafif bütün profiller denenmiş ve yetersiz bulunmuştur).
    ``aile_degistir``: aynı gruptaki diğer ailelerin (I/H: IPE/HEA/HEB; eksenel: KUTU/BORU/L/2L/UPN) en hafif yeterli
    profilleri de bulunur.

    Dönüş: aile, oneri (ad | None), dc, agirlik_kg_m, belirleyen, denenenler [{ad, agirlik_kg_m, dc, belirleyen, yeterli}],
    gerekce [metin], mevcut {ad, dc, belirleyen} | None, degisim ("büyüt" | "küçült" | "aynı" | None),
    alternatifler [{aile, oneri, dc, agirlik_kg_m}], aile_degistir {aile, oneri, agirlik_kg_m, neden} | None,
    kontrol, durum ("bulundu" | "ailede yeterli profil yok"), uyarilar."""
    aile_, bas_ad = _aile_coz(aile)
    if baslangic is not None:
        a2, bas_ad = _aile_coz(baslangic)
        if bas_ad is None:
            raise MatrisHatasi("baslangic bir profil adı olmalı (\"IPE 300\").")
        if a2 != aile_:
            raise MatrisHatasi(f"baslangic {bas_ad} {aile_} ailesinden değil.")
    p = _oner_parametre(parametreler)
    kuv = _kuvvet_listesi(kuvvetler)
    if not kuv:
        raise MatrisHatasi("Kesit önerisi için kuvvetler verilmeli: [{\"ad\", \"N\", \"Mx\", \"My\", \"V\"}].")
    egilme_var = any(abs(c["Mx"]) > 1e-9 or abs(c["My"]) > 1e-9 or abs(c["V"]) > 1e-9 for c in kuv)

    def kontrol_turu(a):
        k_ = p.get("kontrol")
        if k_ is not None:
            if k_ not in ("eleman", "cubuk"):
                raise MatrisHatasi("kontrol 'eleman' ya da 'cubuk' olmalı.")
            if k_ == "eleman" and a not in _I_AILELER:
                raise MatrisHatasi(f"{a} ailesinde eğilmeli eleman tahkiki yok (yalnız I/H); kontrol='cubuk' kullanın.")
            return k_
        return "eleman" if (a in _I_AILELER and egilme_var) else "cubuk"

    uyarilar = []
    if egilme_var and aile_ not in _I_AILELER:
        uyarilar.append(f"{aile_} ailesinde yalnız eksenel kuvvet denetlenir; Mx/My/V yok sayıldı.")
    kt = kontrol_turu(aile_)
    denenen, bulunan = _aile_tara(aile_, malzeme, p, kuv, kt)
    mevcut = None
    degisim = None
    if bas_ad is not None:
        r, dc, bel = _profil_kontrol(bas_ad, aile_, malzeme, p, kuv, kt)
        mevcut = {"ad": bas_ad, "dc": dc, "belirleyen": bel, "agirlik_kg_m": dict(_aile_listesi(aile_))[bas_ad]}
        if bulunan is not None:
            gb, gm = bulunan["agirlik_kg_m"], mevcut["agirlik_kg_m"]
            degisim = "aynı" if bulunan["ad"] == bas_ad else ("büyüt" if gb > gm else "küçült")
    gerekce = []
    if bulunan is not None:
        onceki = denenen[-2] if len(denenen) > 1 else None
        gerekce.append(f"{aile_} ailesinde {len(denenen)} profil ağırlığa göre artan sırada denendi ({kt} tahkiki); "
                       f"{bulunan['ad']} ({_f(bulunan['agirlik_kg_m'], 1)} kg/m) D/C ≤ 1 sağlayan ilk profil: "
                       f"D/C = {_f(bulunan['dc'], 3)}, belirleyen: {bulunan['belirleyen']}.")
        if onceki is not None:
            gerekce.append(f"Bir hafifi {onceki['ad']} ({_f(onceki['agirlik_kg_m'], 1)} kg/m) yetersiz: D/C = "
                           f"{_f(onceki['dc'], 3)} > 1 ({onceki['belirleyen']}).")
        else:
            gerekce.append("Ailenin en hafif profili yeterli.")
    else:
        gerekce.append(f"{aile_} ailesinin en ağır profili de yetersiz: {denenen[-1]['ad']} D/C = {_f(denenen[-1]['dc'], 3)} "
                       f"({denenen[-1]['belirleyen']}).")
    if mevcut is not None:
        gerekce.append(f"Mevcut {mevcut['ad']}: D/C = {_f(mevcut['dc'], 3)} ({mevcut['belirleyen']})"
                       + (f" → {degisim}." if degisim else "."))
    alternatifler = []
    ad_ = None
    if aile_degistir:
        grup = _I_AILELER if aile_ in _I_AILELER else _EKSENEL_AILELER
        for a in grup:
            if a == aile_:
                continue
            try:
                kta = kontrol_turu(a)
            except MatrisHatasi:
                continue
            d2, b2 = _aile_tara(a, malzeme, p, kuv, kta)
            alternatifler.append({"aile": a, "oneri": b2["ad"] if b2 else None, "dc": b2["dc"] if b2 else d2[-1]["dc"],
                                  "agirlik_kg_m": b2["agirlik_kg_m"] if b2 else None, "deneme_sayisi": len(d2),
                                  "belirleyen": (b2 or d2[-1])["belirleyen"]})
        yeterli = [a for a in alternatifler if a["oneri"]]
        if yeterli:
            en = min(yeterli, key=lambda a: a["agirlik_kg_m"])
            if bulunan is None:
                ad_ = {"aile": en["aile"], "oneri": en["oneri"], "agirlik_kg_m": en["agirlik_kg_m"],
                       "neden": f"{aile_} ailesinde yeterli profil yok; en hafif yeterli seçenek {en['oneri']}."}
            elif en["agirlik_kg_m"] < bulunan["agirlik_kg_m"] - 1e-9:
                ad_ = {"aile": en["aile"], "oneri": en["oneri"], "agirlik_kg_m": en["agirlik_kg_m"],
                       "neden": f"{en['oneri']} ({_f(en['agirlik_kg_m'], 1)} kg/m), {bulunan['ad']} "
                                f"({_f(bulunan['agirlik_kg_m'], 1)} kg/m) profilinden hafif."}
        if ad_ is not None:
            gerekce.append("Aile değiştir: " + ad_["neden"])
    sonuc = _json({
        "tur": "celik_kesit_oner", "aile": aile_, "malzeme": malzeme if isinstance(malzeme, str) else celik_malzeme(malzeme),
        "kontrol": kt, "parametreler": {a: v for a, v in p.items()}, "kuvvetler": kuv,
        "oneri": bulunan["ad"] if bulunan else None, "dc": bulunan["dc"] if bulunan else denenen[-1]["dc"],
        "agirlik_kg_m": bulunan["agirlik_kg_m"] if bulunan else None,
        "belirleyen": (bulunan or denenen[-1])["belirleyen"], "denenenler": denenen, "gerekce": gerekce,
        "mevcut": mevcut, "degisim": degisim, "alternatifler": alternatifler, "aile_degistir": ad_,
        "durum": "bulundu" if bulunan else "ailede yeterli profil yok", "uyarilar": uyarilar,
        "kaynak": "Profil listeleri: " + ("yapi_veri.PROFILLER (ArcelorMittal)" if aile_ in _I_AILELER
                                          else _STD_KAYNAK[aile_]),
    })
    if anl is not None:
        _anlat_celik_oner(anl, sonuc)
    return sonuc


def _anlat_celik_oner(anl, s):
    _basla(anl, f"Çelik kesit önerisi: {s['aile']} ailesi",
           "Aynı iç kuvvetlerle ailenin profillerini hafiften ağıra doğru tek tek tahkik ediyoruz; D/C ≤ 1 sağlayan ilk "
           "profil en hafif yeterli kesittir. Sıralama ağırlığa göre olduğundan öneriden hafif bütün profiller denenmiş ve "
           "yetersiz bulunmuştur. Not: kesit değişince çerçevenin rijitliği, dolayısıyla iç kuvvetler de değişir — "
           "öneriden sonra model yeniden çözülmelidir.")
    anl.metin(f"Tahkik: **{s['kontrol']}** ({'celik_eleman_kontrol' if s['kontrol'] == 'eleman' else 'celik_cubuk_kontrol'}); "
              f"kuvvetler: " + "; ".join(f"{c['ad']}: N = {_f(c['N'], 1)}, Mx = {_f(c['Mx'], 1)}, My = {_f(c['My'], 1)}, "
                                         f"V = {_f(c['V'], 1)}" for c in s["kuvvetler"]) + ".")
    anl.metin("**Deneme tablosu:**\n\n" + se._tablo(
        ["Profil", "Ağırlık (kg/m)", "D/C", "", "Belirleyen"],
        [[d["ad"], _f(d["agirlik_kg_m"], 1), _f(d["dc"], 3), "✓" if d["yeterli"] else "✗", d["belirleyen"]]
         for d in s["denenenler"]]))
    if s["alternatifler"]:
        anl.metin("**Diğer aileler** (en hafif yeterli):\n\n" + se._tablo(
            ["Aile", "Öneri", "Ağırlık (kg/m)", "D/C", "Belirleyen"],
            [[a["aile"], a["oneri"] or "yok", "–" if a["agirlik_kg_m"] is None else _f(a["agirlik_kg_m"], 1),
              _f(a["dc"], 3), a["belirleyen"]] for a in s["alternatifler"]]))
    for g in s["gerekce"]:
        anl.kural(g)
    for u in s["uyarilar"]:
        anl.uyari(u)
    anl.sonuc(r"\text{Öneri: " + (s["oneri"] or "yok") + "}",
              f"D/C = {_f(s['dc'], 3)}" + (f", {_f(s['agirlik_kg_m'], 1)} kg/m" if s["agirlik_kg_m"] else ""))


# --- betonarme --------------------------------------------------------------------------------------------------------
def _bkuvvet(kuvvetler):
    """Betonarme kuvvet listesi (deprem işaretiyle): [{ad, N, Mx, My, V, deprem}]."""
    liste = _kuvvet_listesi(kuvvetler)
    ham = [kuvvetler] if isinstance(kuvvetler, dict) else list(kuvvetler or [])
    for c, h in zip(liste, ham):
        c["deprem"] = None if h.get("deprem") is None else bool(h.get("deprem"))
    return liste


def _malz_cift(malzeme):
    if malzeme is None:
        return "C30", "B420C"
    if isinstance(malzeme, dict) and ("beton" in malzeme or "donati" in malzeme):
        return malzeme.get("beton", "C30"), malzeme.get("donati", "B420C")
    if isinstance(malzeme, (list, tuple)) and len(malzeme) == 2:
        return malzeme[0], malzeme[1]
    raise MatrisHatasi('malzeme {"beton": "C30", "donati": "B420C"} ya da ("C30", "B420C") olmalı.')


def _kolon_rho_tara(c, b, h, pas, beton, donati, yerlesim, n_cubuk, tbdy, deprem, rho_max=0.04, adim=0.0025, n=40, ham=False):
    """ρ = 0,01 … rho_max taranır; N–M D/C ≤ 1 sağlayan ilk ρ → (ρ, sonuç). Sağlanmazsa (None, ρmax sonucu).
    Tarama kolon_kontrol(ham=True) ile; ``ham=False`` ise bulunan ρ'nun sonucu tam (egri_x / egri_y ile) yeniden üretilir."""
    Ac = b * h * 1e4    # cm²
    rho = 0.01
    son = None
    bulunan = None

    def kk(r_, ham_):
        return kolon_kontrol([x["N"] for x in c], [x["Mx"] for x in c], [x["My"] for x in c], b, h, r_ * Ac, pas, beton,
                             donati, yerlesim, n_cubuk, [x["ad"] for x in c], tbdy, n, deprem=deprem, ham=ham_)

    while rho <= rho_max + 1e-12:
        r = kk(rho, True)
        son = (rho, r)
        if r["dc"] <= 1.0 + 1e-9:
            bulunan = rho
            break
        rho = round(rho + adim, 6)
    if son is None:
        return None, None
    return bulunan, (son[1] if ham else kk(son[0], False))


def betonarme_eleman_kontrol(b, h, paspayi=0.04, beton="C30", donati="B420C", kuvvetler=None, tur="kiris",
                             As_toplam=None, As_alt=None, As_ust=None, yerlesim=None, n_cubuk=None, tbdy=False,
                             etriye_cap=None, anl=None, ham=False) -> dict:
    """Betonarme kiriş / kolon / eğik eleman (mertek) birleştirici tahkiki (TS 500 + isteğe bağlı TBDY).

    b, h (m; Mx eğilmesinde derinlik h), paspayi (m, donatı ağırlık merkezi), ``kuvvetler`` [{"ad", "N" (kN, basınç +),
    "Mx" (kN·m; kirişte + alt lif çekme/açıklık, − üst lif çekme/mesnet), "My", "V" (kN), "deprem"}].

    ``tur``:
    * "kiris": eğilme ``kiris_egilme`` (açıklık M+ alt, mesnet M− üst donatı; ``As_alt``/``As_ust`` cm² verilirse tahkik)
      ve kesme ``kiris_kesme`` (N ile, md. 8.1.3); |N_d| ≤ 0,1 f_ck A_c koşulu denetlenir (TS 500 Denk. 7.2, TBDY
      7.4.1.2) — aşılırsa eleman kolon gibi tasarlanmalıdır.
    * "egik": her kombinasyonda |N_d| ≤ 0,1 f_ck A_c ise eksenel kuvvet eğilmede ihmal edilir (kiriş yolu), değilse
      kolon gibi N–M (``kolon_kontrol``, varsayılan iki yüze donatı) — çekmede aynı eşik öğretici yaklaşımdır.
    * "kolon": bütün kombinasyonlar N–M (varsayılan dört yüze donatı) + kesme (``kiris_kesme``, N ile).
    N–M yolunda ``As_toplam`` (cm²) verilmezse kiriş donatısı (As_alt + As_ust) ya da ρ = 0,01 … 0,04 taranarak en az
    yeterli donatı bulunur. Kiriş yolunda My yok sayılır (uyarı).

    Dönüş: tur, b_mm, h_mm, esik_kN (0,1 f_ck A_c), kombinasyonlar [{ad, N, Mx, My, V, yol, dc}], egilme_alt,
    egilme_ust, kolon (kolon_kontrol | None), kesme (en elverişsiz kiris_kesme), As_toplam_cm2, As_kaynak, dc, durum,
    kontroller, uyarilar.

    ``ham=True`` (iç kullanım; ``anl`` yokken): kolon sonucunda egri_x / egri_y yok ve _json dönüşümü yapılmaz (aynı sayılar)."""
    ic = bool(ham) and anl is None
    if tur not in ("kiris", "kolon", "egik"):
        raise MatrisHatasi("tur 'kiris', 'kolon' ya da 'egik' olmalı.")
    bmm = _boyut(b, "b")
    hmm = _boyut(h, "h")
    bm, dm = _malzemeler(beton, donati)
    kuv = _bkuvvet(kuvvetler)
    if not kuv:
        raise MatrisHatasi("kuvvetler verilmeli: [{\"ad\", \"N\", \"Mx\", \"My\", \"V\"}].")
    Ac = bmm * hmm
    esik = 0.1 * bm["fck"] * Ac / 1e3
    uyarilar = []
    for c in kuv:
        c["yol"] = ("N–M" if tur == "kolon" else ("eğilme" if tur == "kiris" or abs(c["N"]) <= esik + 1e-9 else "N–M"))
    kiris_k = [c for c in kuv if c["yol"] == "eğilme"]
    nm_k = [c for c in kuv if c["yol"] == "N–M"]
    kontroller = []
    eg_alt = eg_ust = None
    if kiris_k:
        Mp = max([c["Mx"] for c in kiris_k if c["Mx"] > 0] + [0.0])
        Mn = max([-c["Mx"] for c in kiris_k if c["Mx"] < 0] + [0.0])
        if Mp > 0:
            eg_alt = kiris_egilme(Mp, b, h, paspayi, bm, dm, As_mevcut=As_alt, tbdy=tbdy)
            kontroller += [dict(x, ad=f"Açıklık (alt donatı): {x['ad']}") for x in eg_alt["kontroller"]]
        if Mn > 0:
            eg_ust = kiris_egilme(Mn, b, h, paspayi, bm, dm, As_mevcut=As_ust, tbdy=tbdy)
            kontroller += [dict(x, ad=f"Mesnet (üst donatı): {x['ad']}") for x in eg_ust["kontroller"]]
        for c in kiris_k:
            r_ = eg_alt if c["Mx"] > 0 else eg_ust
            c["dc"] = _dc(abs(c["Mx"]), r_["Mr_kNm"]) if r_ is not None else 0.0
        if any(abs(c["My"]) > 1e-9 for c in kiris_k):
            uyarilar.append("Kiriş yolunda zayıf eksen momenti My yok sayıldı (kiriş tek eksenli eğilme); iki eksenli "
                            "eğilme için tur='kolon' kullanın.")
        Nmax = max(abs(c["N"]) for c in kiris_k)
        kontroller.append(_kontrol("Eğilme elemanı koşulu |N_d| ≤ 0,1 f_ck A_c", Nmax, esik,
                                   "TS 500 md. 7.3, Denk. 7.2; TBDY 2018 md. 7.4.1.2", "kN"))
        if Nmax > esik + 1e-9:
            uyarilar.append(f"|N_d| = {_f(Nmax, 1)} kN > 0,1 f_ck A_c = {_f(esik, 1)} kN: eleman eğilme elemanı sayılamaz, "
                            "kolon gibi (N–M) tasarlanmalıdır (tur='egik' ya da 'kolon').")
    kolon = None
    As_t = None
    As_kay = None
    if nm_k:
        yer = yerlesim or ("dort_yuz" if tur == "kolon" else "iki_yuz")
        dep = [True if c["deprem"] is None else c["deprem"] for c in nm_k]
        if As_toplam is not None:
            As_t, As_kay = _sayi(As_toplam, "As_toplam (cm²)", pozitif=True, sifir_olur=False), "verilen"
        elif As_alt is not None or As_ust is not None:
            As_t = float(As_alt or 0) + float(As_ust or 0)
            As_kay = "As_alt + As_ust"
        if As_t is not None:
            kolon = kolon_kontrol([c["N"] for c in nm_k], [c["Mx"] for c in nm_k], [c["My"] for c in nm_k], b, h, As_t,
                                  paspayi, bm, dm, yer, n_cubuk, [c["ad"] for c in nm_k], tbdy, deprem=dep, ham=ic)
        else:
            rho, kolon = _kolon_rho_tara(nm_k, b, h, paspayi, bm, dm, yer, n_cubuk, tbdy, dep, ham=ic)
            As_t = kolon["As_cm2"]
            As_kay = f"ρ taraması (ρ = {_f(rho, 4)})" if rho is not None else "ρ = 0,04 da yetmiyor"
        for c, pn in zip(nm_k, kolon["noktalar"]):
            c["dc"] = pn["dc"]
        kontroller += [dict(x, ad=f"N–M: {x['ad']}") for x in kolon["kontroller"]]
        uyarilar += kolon["uyarilar"]
        if tur == "egik":
            uyarilar.append(f"{len(nm_k)} kombinasyonda |N_d| > 0,1 f_ck A_c = {_f(esik, 1)} kN: eğik eleman kolon gibi "
                            "N–M ile tahkik edildi (TS 500 Denk. 7.2).")
    # kesme
    kesme = None
    for c in kuv:
        if abs(c["V"]) <= 1e-9:
            continue
        r = kiris_kesme(abs(c["V"]), b, h, paspayi, bm, dm, Nd=c["N"], etriye_cap=etriye_cap)
        c["dc_kesme"] = max(x["dc"] for x in r["kontroller"][:2])      # dayanım satırları (V ≤ 0,22fcd bd; V ≤ Vr)
        if kesme is None or r["dc"] > kesme["dc"]:
            kesme = dict(r, kombinasyon=c["ad"])
    if kesme is not None:
        kontroller += [dict(x, ad=f"Kesme ({kesme['kombinasyon']}): {x['ad']}") for x in kesme["kontroller"]]
    for c in kuv:
        c["dc"] = max(c.get("dc", 0.0), c.get("dc_kesme", 0.0))
    dc = max([x["dc"] for x in kontroller] + [0.0])
    alt_durum = [r["durum"] for r in (eg_alt, eg_ust, kolon, kesme) if r is not None]
    if "kesit büyüt" in alt_durum or any(not x["saglandi"] and "Eğilme elemanı" in x["ad"] for x in kontroller):
        durum = "kesit büyüt"
    elif dc > 1.0 + 1e-9:
        durum = "donatı artır"
    else:
        durum = "yeterli"
    sonuc = {"tur": "betonarme_eleman_kontrol", "eleman": tur, "beton": bm["sinif"], "donati": dm["sinif"],
             "b_mm": bmm, "h_mm": hmm, "esik_kN": esik, "kombinasyonlar": kuv, "egilme_alt": eg_alt,
             "egilme_ust": eg_ust, "kolon": kolon, "kesme": kesme, "As_toplam_cm2": As_t, "As_kaynak": As_kay,
             "dc": dc, "durum": durum, "kontroller": kontroller, "uyarilar": list(dict.fromkeys(uyarilar))}
    if ic:
        return sonuc
    sonuc = _json(sonuc)
    if anl is not None:
        _basla(anl, f"Betonarme eleman tahkiki ({ {'kiris': 'kiriş', 'kolon': 'kolon', 'egik': 'eğik eleman'}[tur] })",
               "Eksenel kuvveti küçük olan eleman eğilme elemanı (kiriş) gibi, büyük olan kolon gibi (N–M etkileşimi) "
               "tahkik edilir. Sınır TS 500 Denk. 7.2: N_d ≤ 0,1 f_ck A_c. Eğik kirişte (mertek) eğimden doğan eksenel "
               "kuvvet çoğu zaman bu sınırın altındadır; değilse eleman kolon gibi boyutlandırılır.")
        anl.mat(rf"0{{,}}1 f_{{ck}} A_c = 0{{,}}1\cdot{_L(bm['fck'], 0)}\cdot{_L(Ac, 0)} = {_L(esik * 1e3, 0)}\ \text{{N}} = "
                rf"{_L(esik, 1)}\ \text{{kN}}")
        anl.metin("**Kombinasyonlar ve hesap yolu:**\n\n" + se._tablo(
            ["Ad", "N (kN)", "Mx", "My", "V", "Yol", "D/C"],
            [[c["ad"], _f(c["N"], 1), _f(c["Mx"], 1), _f(c["My"], 1), _f(c["V"], 1), c["yol"], _f(c["dc"], 3)]
             for c in sonuc["kombinasyonlar"]]))
        if eg_alt is not None:
            kiris_egilme(eg_alt["Md_kNm"], b, h, paspayi, bm, dm, As_mevcut=As_alt, tbdy=tbdy, anl=anl)
        if eg_ust is not None:
            kiris_egilme(eg_ust["Md_kNm"], b, h, paspayi, bm, dm, As_mevcut=As_ust, tbdy=tbdy, anl=anl)
        if kolon is not None:
            _anlat_kolon_kontrol(anl, kolon, bm, dm)
        if kesme is not None:
            c = next(x for x in kuv if x["ad"] == kesme["kombinasyon"])
            kiris_kesme(abs(c["V"]), b, h, paspayi, bm, dm, Nd=c["N"], etriye_cap=etriye_cap, anl=anl)
        anl.baslik("Eleman özeti", 3)
        _durum_ozet(anl, sonuc)
    return sonuc


def _grid(lo, hi, adim):
    n = int(math.floor((hi - lo) / adim + 1e-9))
    return [round(lo + i * adim, 6) for i in range(n + 1)]


def betonarme_kesit_oner(tur, kuvvetler, malzeme=None, mevcut_b=None, mevcut_h=None, kisitlar=None, anl=None, Ndm=None,
                         Ndm_kaynak=None) -> dict:
    """Betonarme kesit önerisi (5 cm adımlı tarama; en küçük alan).

    ``tur`` "kolon" | "kiris"; ``kuvvetler`` [{"ad", "N" (kN, basınç +), "Mx", "My" (kN·m), "V" (kN), "deprem"}];
    ``malzeme`` {"beton", "donati"} (varsayılan C30 / B420C); ``mevcut_b``, ``mevcut_h`` (m) mevcut kesit (D/C'si
    raporlanır; kirişte b'nin varsayılanı). ``kisitlar``: {"adim" (m, 0,05), "tbdy" (True), "paspayi" (kolon 0,05,
    kiriş 0,04 m), "b_sabit" (bool; mevcut_b ya da "b" ile), "b" (m), "b_min", "b_max", "h_min", "h_max" (m),
    "en_boy_max" (kolon h/b ≤ 3, öğretici kısıt), "doseme_kalinligi" (m; TBDY kiriş h ≥ 3 t_f), "yerlesim", "rho_max"
    (kolon 0,04)}.

    * Kolon: A_c,gerekli = max(N_dm/(0,40 f_ck) [TBDY 7.3.1.2, yalnız deprem birleşimleri; işaret yoksa hepsi],
      N_d/(0,9 f_cd) [TS 500 7.4.1, Denk. 7.7]); en küçük boyut ≥ 300 mm (TBDY 7.3.1.1; tbdy=False: 250 mm, TS 500).
      b × h adayları alan sırasıyla (eşitlikte kareye yakın) denenir; ρ = 0,04'te N–M (``kolon_kontrol``) sağlanan ilk
      aday önerilir, gerekli ρ (0,01 … 0,04, 0,0025 adım) ayrıca bulunur.
    * Kiriş: M_d = max |Mx| için tek donatılı ρ ≤ ρ_max = min(0,85ρ_b; 0,02) (TS 500 Denk. 7.4–7.5) ve
      V_d ≤ 0,22 f_cd b_w d (Denk. 8.7) sağlayan en küçük h; h ≥ 300 mm (TS 500 7.3), TBDY: b_w ≥ 250 mm, h ≥ 3t_f,
      h ≤ 3,5 b_w (7.4.1.1). h ≤ 3,5 b sağlanamazsa (b sabit değilse) b 5 cm büyütülür.

    ``Ndm`` (kN, kolon): TBDY 7.3.1.2 boyutlandırmasının N_dm'i dışarıdan (ör. ön elemeden önceki bütün deprem birleşimlerinin
    en büyüğü ya da deprem birleşimi yokken G + Q); kuvvetlerdeki deprem birleşimlerinin en büyüğüyle büyüğü alınır, N_d de en az
    bu değerdir. ``Ndm_kaynak`` "deprem" | "G+Q" | "bütün": gerekçedeki N_dm açıklaması.

    Dönüş: tur, oneri {b, h (m), b_mm, h_mm, ...}, A_c_gerekli_cm2, gerekce [metin], denenenler [...], mevcut, durum,
    uyarilar."""
    if tur not in ("kolon", "kiris"):
        raise MatrisHatasi("tur 'kolon' ya da 'kiris' olmalı.")
    kis = dict(kisitlar or {})
    izin = {"adim", "tbdy", "paspayi", "b_sabit", "b", "b_min", "b_max", "h_min", "h_max", "en_boy_max",
            "doseme_kalinligi", "yerlesim", "rho_max", "deneme_siniri"}
    fazla = set(kis) - izin
    if fazla:
        raise MatrisHatasi(f"kisitlar anahtarı tanımsız: {', '.join(sorted(fazla))}. Geçerli: {', '.join(sorted(izin))}.")
    beton, donati = _malz_cift(malzeme)
    bm, dm = _malzemeler(beton, donati)
    kuv = _bkuvvet(kuvvetler)
    if not kuv:
        raise MatrisHatasi("kuvvetler verilmeli.")
    adim = _sayi(kis.get("adim", 0.05), "adim (m)", pozitif=True, sifir_olur=False)
    tbdy = bool(kis.get("tbdy", True))
    uyarilar = []
    fck, fcd = bm["fck"], bm["fcd"]
    if tur == "kolon":
        sonuc = _kolon_oner(kuv, bm, dm, kis, adim, tbdy, mevcut_b, mevcut_h, uyarilar,
                            Ndm=None if Ndm is None else _sayi(Ndm, "Ndm (kN)"), Ndm_kaynak=Ndm_kaynak)
    else:
        sonuc = _kiris_oner(kuv, bm, dm, kis, adim, tbdy, mevcut_b, mevcut_h, uyarilar)
    sonuc.update({"tur": "betonarme_kesit_oner", "eleman": tur, "beton": bm["sinif"], "donati": dm["sinif"],
                  "fck": fck, "fcd": fcd, "tbdy": tbdy, "uyarilar": uyarilar})
    sonuc = _json(sonuc)
    if anl is not None:
        _anlat_ba_oner(anl, sonuc)
    return sonuc


_NDM_ACIKLAMA = {"G+Q": "(deprem birleşimi yok: N_dm ≈ G + Q, tasarım kaydının 'Ndm ≤ 0,40 fck Ac' satırıyla aynı)",
                 "bütün": "(deprem birleşimi yok: bütün birleşimlerin en büyük eksenel basıncı)"}


def _kolon_oner(kuv, bm, dm, kis, adim, tbdy, mevcut_b, mevcut_h, uyarilar, Ndm=None, Ndm_kaynak=None):
    fck, fcd = bm["fck"], bm["fcd"]
    pas = _sayi(kis.get("paspayi", 0.05), "paspayi (m)", pozitif=True, sifir_olur=False)
    rho_max = _sayi(kis.get("rho_max", 0.04), "rho_max", pozitif=True, sifir_olur=False)
    yer = kis.get("yerlesim", "dort_yuz")
    Nd = max([c["N"] for c in kuv] + [0.0] + ([Ndm] if (tbdy and Ndm is not None) else []))
    isaretli = any(c["deprem"] is not None for c in kuv)
    dep = [True if c["deprem"] is None else c["deprem"] for c in kuv]
    if tbdy and not isaretli and Ndm is None:
        uyarilar.append("Kuvvetlerde 'deprem' işareti yok: TBDY 7.3.1.2 N_dm ≤ 0,40 f_ck A_c bütün kombinasyonlara "
                        "uygulandı (güvenli taraf).")
    Ndm_k = max([c["N"] for c, d in zip(kuv, dep) if d] + [0.0]) if tbdy else 0.0
    Ndm = max(Ndm_k, Ndm) if (tbdy and Ndm is not None) else Ndm_k
    Ac_tbdy = Ndm * 1e3 / (0.40 * fck) if tbdy else 0.0      # mm²
    Ac_ts = Nd * 1e3 / (0.9 * fcd)
    Ac_ger = max(Ac_tbdy, Ac_ts)
    bmin_y = 300.0 if tbdy else 250.0
    bmin = max(bmin_y, 1000.0 * float(kis.get("b_min", 0.0)))
    bmax = 1000.0 * float(kis.get("b_max", 1.5))
    hmax = 1000.0 * float(kis.get("h_max", kis.get("b_max", 1.5)))
    oran = float(kis.get("en_boy_max", 3.0))
    a_mm = adim * 1000.0
    gerekce = []
    if tbdy:
        gerekce.append(f"TBDY 2018 md. 7.3.1.2: A_c ≥ N_dm/(0,40 f_ck) = {_f(Ndm, 1)}·10³/(0,40·{_f(fck, 0)}) = "
                       f"{_f(Ac_tbdy / 100, 1)} cm² "
                       + _NDM_ACIKLAMA.get(Ndm_kaynak, "(N_dm = deprem birleşimlerindeki en büyük eksenel basınç)") + ".")
    gerekce.append(f"TS 500 md. 7.4.1 (Denk. 7.7): A_c ≥ N_d/(0,9 f_cd) = {_f(Nd, 1)}·10³/(0,9·{_f(fcd, 2)}) = "
                   f"{_f(Ac_ts / 100, 1)} cm².")
    gerekce.append(f"Gerekli brüt alan A_c = {_f(Ac_ger / 100, 1)} cm²; en küçük boyut ≥ {_f(bmin_y, 0)} mm "
                   f"({'TBDY 2018 md. 7.3.1.1' if tbdy else 'TS 500 md. 7.4.1'}).")
    b_sabit = bool(kis.get("b_sabit", False))
    if b_sabit:
        bb = kis.get("b", mevcut_b)
        if bb is None:
            raise MatrisHatasi("b_sabit için kisitlar['b'] ya da mevcut_b verilmeli.")
        bs = [_boyut(bb, "b")]
    else:
        bs = _grid(math.ceil(bmin / a_mm - 1e-9) * a_mm, bmax, a_mm)
    hmin_k = 1000.0 * float(kis.get("h_min", 0.0))
    adaylar = []
    for bx in bs:
        for hy in _grid(math.ceil(max(bmin, hmin_k) / a_mm - 1e-9) * a_mm, hmax, a_mm):
            if bx * hy < Ac_ger - 1e-6 or max(bx, hy) / min(bx, hy) > oran + 1e-9:
                continue
            adaylar.append((bx * hy, abs(bx - hy), -hy, bx, hy))
    adaylar.sort()
    sinir = int(kis.get("deneme_siniri", 80))
    denenen = []
    bulunan = None
    for _, _, _, bx, hy in adaylar[:sinir]:
        r = kolon_kontrol([c["N"] for c in kuv], [c["Mx"] for c in kuv], [c["My"] for c in kuv], bx / 1000, hy / 1000,
                          rho_max * (1 - 1e-9) * bx * hy / 100, pas, bm, dm, yer, None, [c["ad"] for c in kuv], tbdy, 40, deprem=dep,
                          ham=True)
        bel = max((x for x in r["kontroller"] if "ρ" not in x["ad"]), key=lambda x: x["dc"])["ad"]
        denenen.append({"b_mm": bx, "h_mm": hy, "A_c_cm2": bx * hy / 100, "dc_rho_max": r["dc"], "belirleyen": bel,
                        "yeterli": bool(r["dc"] <= 1 + 1e-9)})
        if r["dc"] <= 1 + 1e-9:
            bulunan = (bx, hy)
            break
    oneri = None
    if bulunan:
        bx, hy = bulunan
        rho, r = _kolon_rho_tara(kuv, bx / 1000, hy / 1000, pas, bm, dm, yer, None, tbdy, dep, rho_max, ham=True)
        if rho is None:      # sayısal sınır: ρ_max'ta (tolerans içinde) sağlandı
            rho = rho_max
        dc_nm = max(p["dc"] for p in r["noktalar"])
        oneri = {"b": bx / 1000, "h": hy / 1000, "b_mm": bx, "h_mm": hy, "A_c_cm2": bx * hy / 100, "rho": rho,
                 "As_cm2": rho * bx * hy / 100, "dc": r["dc"], "dc_NM": dc_nm, "yerlesim": yer}
        gerekce.append(f"Alan sırasıyla {len(denenen)} aday denendi (ρ = {_f(rho_max, 3)} ile N–M); {_f(bx, 0)} × "
                       f"{_f(hy, 0)} mm (A_c = {_f(bx * hy / 100, 0)} cm²) N–M'yi sağlayan en küçük kesit; gerekli ρ = "
                       f"{_f(rho, 4)} (A_s = {_f(oneri['As_cm2'], 1)} cm²), N–M D/C = {_f(dc_nm, 3)}.")
        if len(denenen) > 1:
            d0 = denenen[-2]
            gerekce.append(f"Bir küçük aday {_f(d0['b_mm'], 0)} × {_f(d0['h_mm'], 0)} mm: ρ = {_f(rho_max, 3)} ile bile "
                           f"D/C = {_f(d0['dc_rho_max'], 3)} > 1 ({d0['belirleyen']}).")
    else:
        gerekce.append(f"{len(denenen)} aday denendi; sınırlar içinde N–M'yi sağlayan kesit bulunamadı (b_max/h_max "
                       "büyütün ya da beton sınıfını yükseltin).")
    mevcut = None
    if mevcut_b is not None and mevcut_h is not None:
        rho_m, rm = _kolon_rho_tara(kuv, mevcut_b, mevcut_h, pas, bm, dm, yer, None, tbdy, dep, rho_max, ham=True)
        mevcut = {"b_mm": _boyut(mevcut_b, "mevcut_b"), "h_mm": _boyut(mevcut_h, "mevcut_h"), "rho_gerekli": rho_m,
                  "dc": rm["dc"], "yeterli": rho_m is not None}
        gerekce.append(f"Mevcut {_f(mevcut['b_mm'], 0)} × {_f(mevcut['h_mm'], 0)} mm: "
                       + (f"ρ = {_f(rho_m, 4)} ile yeterli." if rho_m is not None else
                          f"ρ = {_f(rho_max, 3)} ile bile D/C = {_f(rm['dc'], 3)} > 1."))
    return {"oneri": oneri, "A_c_gerekli_cm2": Ac_ger / 100, "A_c_TBDY_cm2": Ac_tbdy / 100, "A_c_TS500_cm2": Ac_ts / 100,
            "N_d_kN": Nd, "N_dm_kN": Ndm, "b_min_mm": bmin_y, "gerekce": gerekce, "denenenler": denenen,
            "mevcut": mevcut, "durum": "bulundu" if oneri else "bulunamadı",
            "kaynak": f"{K_TS500['N040']}; {K_TS500['N09']}; {K_TS500['kolon_boyut_tbdy']}; {K_TS500['rho_kolon']}"}


def _kiris_oner(kuv, bm, dm, kis, adim, tbdy, mevcut_b, mevcut_h, uyarilar):
    fcd = bm["fcd"]
    pas = _sayi(kis.get("paspayi", 0.04), "paspayi (m)", pozitif=True, sifir_olur=False) * 1000.0
    a_mm = adim * 1000.0
    Md = max([abs(c["Mx"]) for c in kuv] + [0.0])
    Vd = max([abs(c["V"]) for c in kuv] + [0.0])
    bb = kis.get("b", mevcut_b)
    b_sabit = bool(kis.get("b_sabit", False))
    bmin = 250.0 if tbdy else 200.0
    if bb is None:
        b0 = max(bmin, 1000.0 * float(kis.get("b_min", 0.0)))
    else:
        b0 = _boyut(bb, "b")
    bmax = 1000.0 * float(kis.get("b_max", 1.0))
    tf = float(kis.get("doseme_kalinligi", 0.0)) * 1000.0
    hmin = max(300.0, 3.0 * tf if tbdy else 0.0, 1000.0 * float(kis.get("h_min", 0.0)))
    hmax = 1000.0 * float(kis.get("h_max", 1.5))
    rho_b = _rho_b(bm, dm)
    rho_max = min(0.85 * rho_b, 0.02)
    denenen = []
    bulunan = None
    bx = b0
    while bulunan is None and bx <= bmax + 1e-9:
        h0 = math.ceil(hmin / a_mm - 1e-9) * a_mm
        for hy in _grid(h0, hmax, a_mm):
            d = hy - pas
            R = 0.85 * fcd * bx
            disk = d * d - 2.0 * Md * 1e6 / R
            if disk < 0:
                rho = math.inf
            else:
                a = d - math.sqrt(disk)
                rho = R * a / dm["fyd"] / (bx * d)
            Vmax = 0.22 * fcd * bx * d / 1e3
            k_ = [("ρ_gerekli ≤ ρ_max (tek donatılı)", _dc(rho if math.isfinite(rho) else DC_UST, rho_max)),
                  ("V_d ≤ 0,22 f_cd b_w d", _dc(Vd, Vmax))]
            if tbdy:
                k_.append(("TBDY h ≤ 3,5 b_w", _dc(hy, 3.5 * bx)))
            dc = max(x[1] for x in k_)
            bel = max(k_, key=lambda x: x[1])[0]
            denenen.append({"b_mm": bx, "h_mm": hy, "d_mm": d, "rho_gerekli": rho if math.isfinite(rho) else None,
                            "rho_max": rho_max, "V_max_kN": Vmax, "dc": dc, "belirleyen": bel,
                            "yeterli": bool(dc <= 1 + 1e-9)})
            if dc <= 1 + 1e-9:
                bulunan = (bx, hy)
                break
            if tbdy and hy > 3.5 * bx + 1e-9:
                break                    # h büyüdükçe h ≤ 3,5b daha da bozulur → b büyütülmeli
        if bulunan is None:
            if b_sabit:
                break
            bx += a_mm
    gerekce = [f"M_d = max|Mx| = {_f(Md, 1)} kN·m, V_d = max|V| = {_f(Vd, 1)} kN; ρ_b = {_f(rho_b, 5)}, "
               f"ρ_max = min(0,85ρ_b; 0,02) = {_f(rho_max, 5)} (TS 500 md. 7.3, Denk. 7.4–7.5).",
               f"h ≥ {_f(hmin, 0)} mm (TS 500 md. 7.3: 300 mm" + (f"; TBDY 7.4.1.1: 3t_f = {_f(3 * tf, 0)} mm" if tbdy and tf
                                                                     else "") + f"), b_w ≥ {_f(bmin, 0)} mm"
               + (" (TBDY 7.4.1.1), h ≤ 3,5 b_w." if tbdy else " (TS 500 md. 7.3).")]
    oneri = None
    if bulunan:
        bx, hy = bulunan
        son = denenen[-1]
        eg = kiris_egilme(Md, bx / 1000, hy / 1000, pas / 1000, bm, dm, tbdy=tbdy) if Md > 0 else None
        ks = kiris_kesme(Vd, bx / 1000, hy / 1000, pas / 1000, bm, dm) if Vd > 0 else None
        oneri = {"b": bx / 1000, "h": hy / 1000, "b_mm": bx, "h_mm": hy, "d_mm": son["d_mm"],
                 "rho_gerekli": son["rho_gerekli"], "As_gerekli_cm2": eg["As_gerekli_cm2"] if eg else None,
                 "donati_oneri": eg["oneri"]["metin"] if eg and eg["oneri"] else None,
                 "etriye_oneri": ks["oneri"]["metin"] if ks else None}
        gerekce.append(f"{_f(bx, 0)} × {_f(hy, 0)} mm (d = {_f(son['d_mm'], 0)} mm): tek donatılı ρ = "
                       f"{_g(son['rho_gerekli'] or 0)} ≤ ρ_max = {_g(rho_max)}; V_d = {_f(Vd, 1)} ≤ 0,22 f_cd b_w d = "
                       f"{_f(son['V_max_kN'], 1)} kN" + (f"; h/b_w = {_f(hy / bx, 2)} ≤ 3,5" if tbdy else "") + ".")
        onceki = [x for x in denenen[:-1] if x["b_mm"] == bx]
        if onceki:
            o = onceki[-1]
            gerekce.append(f"Bir küçük h = {_f(o['h_mm'], 0)} mm yetersiz: D/C = {_f(o['dc'], 3)} ({o['belirleyen']}).")
        if eg:
            gerekce.append(f"Donatı: A_s = {_f(eg['As_gerekli_cm2'], 2)} cm²"
                           + (f" → {eg['oneri']['metin']}" if eg["oneri"] else "") + (f"; etriye {ks['oneri']['metin']}"
                                                                                       if ks else "") + ".")
        Ac = bx * hy
        Nmax = max(abs(c["N"]) for c in kuv)
        if Nmax > 0.1 * bm["fck"] * Ac / 1e3:
            uyarilar.append(f"|N_d| = {_f(Nmax, 1)} kN > 0,1 f_ck A_c = {_f(0.1 * bm['fck'] * Ac / 1e3, 1)} kN: eleman "
                            "eğilme elemanı değil — kolon gibi (N–M) boyutlandırın (TS 500 Denk. 7.2).")
    else:
        gerekce.append("Sınırlar içinde koşulları sağlayan kiriş kesiti bulunamadı (b/h sınırlarını büyütün ya da "
                       "çift donatılı tasarlayın).")
    if any(abs(c["My"]) > 1e-9 for c in kuv):
        uyarilar.append("Kiriş önerisinde My yok sayıldı (tek eksenli eğilme).")
    mevcut = None
    if mevcut_b is not None and mevcut_h is not None:
        mb, mh = _boyut(mevcut_b, "mevcut_b"), _boyut(mevcut_h, "mevcut_h")
        eg = kiris_egilme(max(Md, 1e-6), mevcut_b, mevcut_h, pas / 1000, bm, dm, tbdy=tbdy)
        Vm = 0.22 * fcd * mb * (mh - pas) / 1e3
        mevcut = {"b_mm": mb, "h_mm": mh, "tek_donatili": eg["tek_donatili"], "rho_gerekli": eg["rho_gerekli"],
                  "V_max_kN": Vm, "yeterli": bool(eg["tek_donatili"] and Vd <= Vm + 1e-9 and
                                                  (eg["rho_gerekli"] or 1) <= rho_max + 1e-12)}
    return {"oneri": oneri, "A_c_gerekli_cm2": None, "M_d_kNm": Md, "V_d_kN": Vd, "rho_b": rho_b, "rho_max": rho_max,
            "h_min_mm": hmin, "b_min_mm": bmin, "gerekce": gerekce, "denenenler": denenen, "mevcut": mevcut,
            "durum": "bulundu" if oneri else "bulunamadı",
            "kaynak": f"{K_TS500['rho_085']}; {K_TS500['rho_002']}; {K_TS500['Vmax']}; {K_TS500['kiris_boyut']}; "
                      f"{K_TS500['kiris_boyut_tbdy']}"}


def _anlat_ba_oner(anl, s):
    kolon = s["eleman"] == "kolon"
    _basla(anl, f"Betonarme kesit önerisi ({'kolon' if kolon else 'kiriş'})",
           ("Önce yönetmeliğin eksenel kuvvet sınırlarından gereken en küçük brüt alanı buluyoruz; sonra 5 cm adımlı "
            "b × h adaylarını alan sırasıyla en büyük donatı oranıyla (ρ = 0,04) N–M etkileşimine sokuyoruz. Sağlayan ilk "
            "aday en küçük kesittir; gereken donatı oranı ayrıca taranır." if kolon else
            "Kiriş yüksekliğini 5 cm adımlarla artırıp üç koşula bakıyoruz: moment tek donatıyla ρ ≤ ρ_max içinde "
            "taşınabilmeli (sünek davranış), kesme beton basınç dikmelerini ezmemeli (V ≤ 0,22 f_cd b_w d) ve boyut "
            "koşulları sağlanmalı. Hepsini sağlayan ilk h önerilir."))
    if kolon:
        anl.mat(rf"A_{{c}} \ge \max\left(\frac{{N_{{dm}}}}{{0{{,}}40f_{{ck}}}};\ \frac{{N_d}}{{0{{,}}9f_{{cd}}}}\right) = "
                rf"\max({_L(s['A_c_TBDY_cm2'], 1)};\ {_L(s['A_c_TS500_cm2'], 1)}) = {_L(s['A_c_gerekli_cm2'], 1)}\ "
                rf"\text{{cm}}^2")
        anl.metin("**Deneme tablosu** (ρ = ρ_max ile):\n\n" + se._tablo(
            ["b (mm)", "h (mm)", "A_c (cm²)", "D/C", "", "Belirleyen"],
            [[_f(d["b_mm"], 0), _f(d["h_mm"], 0), _f(d["A_c_cm2"], 0), _f(d["dc_rho_max"], 3),
              "✓" if d["yeterli"] else "✗", d["belirleyen"]] for d in s["denenenler"]]))
    else:
        anl.mat(r"a = d - \sqrt{d^2 - \frac{2M_d}{0{,}85f_{cd}b}},\quad \rho = \frac{0{,}85f_{cd}\,b\,a}{f_{yd}\,b\,d} \le "
                r"\rho_{max},\qquad V_d \le 0{,}22f_{cd}b_wd")
        anl.metin("**Deneme tablosu:**\n\n" + se._tablo(
            ["b (mm)", "h (mm)", "d (mm)", "ρ gerekli", "ρ_max", "V_max (kN)", "D/C", "", "Belirleyen"],
            [[_f(d["b_mm"], 0), _f(d["h_mm"], 0), _f(d["d_mm"], 0),
              "∞" if d["rho_gerekli"] is None else _g(d["rho_gerekli"]), _g(d["rho_max"]), _f(d["V_max_kN"], 1),
              _f(d["dc"], 3), "✓" if d["yeterli"] else "✗", d["belirleyen"]] for d in s["denenenler"]]))
    for g in s["gerekce"]:
        anl.kural(g)
    for u in s["uyarilar"]:
        anl.uyari(u)
    o = s["oneri"]
    anl.sonuc(r"\text{Öneri: }" + (rf"b \times h = {_L(o['b_mm'], 0)} \times {_L(o['h_mm'], 0)}\ \text{{mm}}" if o
                                   else r"\text{bulunamadı}"), s["durum"])


# ============================================================================
# Anlatımlı sarmalayıcılar (mo.Sonuc döndürür; .veri = sonuç sözlüğü)
# ============================================================================
def kiris_egilme_anlatimli(*args, goster=None, **kw):
    return _anlatimli(kiris_egilme, "kiris_egilme", goster, args, kw)


def kiris_kesme_anlatimli(*args, goster=None, **kw):
    return _anlatimli(kiris_kesme, "kiris_kesme", goster, args, kw)


def kolon_etkilesim_anlatimli(*args, goster=None, **kw):
    return _anlatimli(kolon_etkilesim, "kolon_etkilesim", goster, args, kw)


def kolon_kontrol_anlatimli(*args, goster=None, **kw):
    return _anlatimli(kolon_kontrol, "kolon_kontrol", goster, args, kw)


def kesit_sinifi_anlatimli(*args, goster=None, **kw):
    return _anlatimli(kesit_sinifi, "kesit_sinifi", goster, args, kw)


def celik_egilme_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_egilme, "celik_egilme", goster, args, kw)


def celik_basinc_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_basinc, "celik_basinc", goster, args, kw)


def celik_kesme_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_kesme, "celik_kesme", goster, args, kw)


def celik_cekme_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_cekme, "celik_cekme", goster, args, kw)


def celik_eleman_kontrol_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_eleman_kontrol, "celik_eleman_kontrol", goster, args, kw)


def celik_cubuk_kontrol_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_cubuk_kontrol, "celik_cubuk_kontrol", goster, args, kw)


def celik_kesit_oner_anlatimli(*args, goster=None, **kw):
    return _anlatimli(celik_kesit_oner, "celik_kesit_oner", goster, args, kw)


def betonarme_eleman_kontrol_anlatimli(*args, goster=None, **kw):
    return _anlatimli(betonarme_eleman_kontrol, "betonarme_eleman_kontrol", goster, args, kw)


def betonarme_kesit_oner_anlatimli(*args, goster=None, **kw):
    return _anlatimli(betonarme_kesit_oner, "betonarme_kesit_oner", goster, args, kw)
