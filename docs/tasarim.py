# -*- coding: utf-8 -*-
"""Kesit tasarımı ve tahkikleri (Dilim 3): TS 500:2000 betonarme kiriş/kolon, ÇYTHYE 2018 çelik eleman.

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
  (Denk. 7.3–7.5), md. 7.4.1 (Denk. 7.7–7.9), md. 8.1.3–8.1.6 (Denk. 8.1, 8.4–8.7).
* TBDY 2018: md. 7.3.1.1, 7.3.1.2, 7.3.2, 7.4.1.1, 7.4.2.4, 7.4.4.
* ÇYTHYE 2018 Esaslar (RG 15.02.2018/30333 Mük.): Tablo 2.1A, 5.4.1 Tablo 5.1A/5.1B, Bölüm 7, 8, 9 (9.2, 9.3.2,
  9.6), 10.2.1, 11.1.1.
"""
from __future__ import annotations

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
    "narinlik_basinc": "ÇYTHYE 2018 md. 8.1.1 (L_c/i ≤ 200)",
    "kesme": "ÇYTHYE 2018 md. 10.2.1, Denk. 10.1–10.3",
    "cekme_akma": "ÇYTHYE 2018 md. 7.2.1, Denk. 7.2 (φt = 0,90; Ωt = 1,67)",
    "cekme_kirilma": "ÇYTHYE 2018 md. 7.2.2, Denk. 7.3; A_e = U A_n Denk. 7.1 (φt = 0,75; Ωt = 2,00)",
    "narinlik_cekme": "ÇYTHYE 2018 md. 7.1.1 (L/i ≤ 300)",
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
                    n_cubuk=None, anl=None) -> dict:
    """TS 500 dikdörtgen kolon N–M etkileşim eğrisi (şekil değiştirme uygunluğu, md. 7.1 varsayımları).

    b (x yönü), h (y yönü), paspayi (m; boyuna çubuk merkezinin dış yüze uzaklığı), As_toplam (cm², simetrik).
    ``eksen="x"``: x ekseni etrafında eğilme (derinlik h); ``"y"``: y ekseni etrafında (derinlik b).
    ``yerlesim``: "dort_yuz" (varsayılan 8 çubuk) ya da "iki_yuz" (varsayılan 4 çubuk; eğilme yüzlerinde).
    c taranır (saf çekmeden saf basınca); blok a = k₁c ≤ derinlik; σs = Es εs ≤ fyd; bloktaki çubuğun yerini aldığı
    beton düşülür. N (kN, basınç +), M (kN·m, kesit ağırlık merkezine göre).

    Dönüş: noktalar [{c_mm, N_kN, M_kNm}] (N artan), N0_kN, Nt_kN, dengeli {c_mm, N_kN, M_kNm, eps_s, eps_yd},
    N_max_TS500_kN (0,9 fcd Ac), N_max_TBDY_kN (0,40 fck Ac), rho, cubuklar, katmanlar."""
    bmm, hmm, pas, As, bm, dm, cubuklar = _kolon_hazirla(b, h, As_toplam, paspayi, beton, donati, yerlesim, n_cubuk)
    if eksen not in ("x", "y"):
        raise MatrisHatasi(f"eksen {eksen!r} tanımsız; 'x' ya da 'y' olmalı.")
    gen, yuk = (bmm, hmm) if eksen == "x" else (hmm, bmm)
    katmanlar = _katmanlar(cubuklar, eksen, bmm, hmm)
    noktalar, N0, Nt, dengeli = _egri(gen, yuk, katmanlar, bm, dm, n)
    Ac = bmm * hmm
    sonuc = _json({
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
    if anl is not None:
        _anlat_kolon_egri(anl, sonuc, bm, dm, gen, yuk, katmanlar)
    return sonuc


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
                  n_cubuk=None, adlar=None, tbdy=True, n=60, anl=None) -> dict:
    """TS 500 kolon tahkiki: her kombinasyon (Nd kN basınç +, Mdx, Mdy kN·m) için radyal D/C.

    Nd, Mdx, Mdy sayı ya da eşit uzunlukta listeler. Her doğrultuda en küçük dışmerkezlik
    e_min = 15 mm + 0,03h (TS 500 md. 6.3.10) uygulanır (tek eksenli kontrollerde, doğrultu başına ayrı ayrı).
    İki eksenli eğilmede (iki moment de sıfırdan farklı): Nd ≥ 0,1 fck Ac ise Bresler ters yük formülü
    1/Nr = 1/Nrx + 1/Nry − 1/N0; değilse doğrusal moment toplamı Mx/Mrx + My/Mry ≤ 1 (öğretici yaklaşımlar; TS 500
    iki eksenli etkileşim formülü vermez).

    Dönüş: noktalar [{ad, Nd_kN, Mdx_kNm, Mdy_kNm, Mx_tasarim_kNm, My_tasarim_kNm, dc_x, dc_y, dc_iki_eksen,
    iki_eksen_yontemi, N_rx_kN, N_ry_kN, N_r_kN, dc, kontroller}], egri_x, egri_y (etkileşim sonuçları), rho,
    dc, durum, kontroller (en elverişsiz nokta + genel), uyarilar."""
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
    ex = kolon_etkilesim(b, h, As_toplam, paspayi, beton, donati, "x", n, yerlesim, n_cubuk)
    ey = kolon_etkilesim(b, h, As_toplam, paspayi, beton, donati, "y", n, yerlesim, n_cubuk)
    bm, dm = _malzemeler(beton, donati)
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
    for ad, N, Mx, My in zip(adlar, Ns, Mxs, Mys):
        Mx_t = max(abs(Mx), N * emin_x / 1e3) if N > 0 else abs(Mx)
        My_t = max(abs(My), N * emin_y / 1e3) if N > 0 else abs(My)
        dcx, Nrx_e, Mrx_e = _isin_kesisim(egx, N, Mx_t)
        dcy, Nry_e, Mry_e = _isin_kesisim(egy, N, My_t)
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
                d1, Nrx, _ = _isin_kesisim(egx, N, abs(Mx))
                d2, Nry, _ = _isin_kesisim(egy, N, abs(My))
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
            if tbdy:
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
    if tbdy:
        uyarilar.append("TBDY 7.3.1.2'deki Ndm, G + Q + E birleşimi altındaki en büyük eksenel basınçtır; burada her "
                        "kombinasyona uygulandı (güvenli tarafta). Deprem içermeyen birleşimler için tbdy=False.")
    sonuc = _json({"tur": "kolon_kontrol", "beton": bm["sinif"], "donati": dm["sinif"], "b_mm": bmm, "h_mm": hmm,
                   "As_cm2": ex["As_cm2"], "rho": rho, "N0_kN": N0, "noktalar": noktalar, "egri_x": ex, "egri_y": ey,
                   "dc": dc, "durum": durum, "kontroller": kontroller, "uyarilar": uyarilar})
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
            rf"N_d \le 0{{,}}9 f_{{cd}} A_c = {_L(s['egri_x']['N_max_TS500_kN'], 1)}\ \text{{kN}},\qquad "
            rf"N_{{dm}} \le 0{{,}}40 f_{{ck}} A_c = {_L(s['egri_x']['N_max_TBDY_kN'], 1)}\ \text{{kN}}")
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

    Dönüş: baslik {oran, lambda_p, lambda_r, egilme, basinc_lambda_r, basinc}, govde {...}, egilme, basinc."""
    p = _profil(profil)
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
    Pr, Mrx, Mry = (abs(_sayi(v, ad)) for v, ad in ((Pr, "Pr"), (Mrx, "Mrx"), (Mry, "Mry")))
    Pc, Mcx, Mcy = (_sayi(v, ad, pozitif=True, sifir_olur=False) for v, ad in ((Pc, "Pc"), (Mcx, "Mcx"), (Mcy, "Mcy")))
    oP, ox, oy = Pr / Pc, Mrx / Mcx, Mry / Mcy
    if oP >= 0.2:
        dc, dal = oP + 8.0 / 9.0 * (ox + oy), "11.1a"
    else:
        dc, dal = oP / 2.0 + ox + oy, "11.1b"
    return _json({"oran_P": oP, "oran_Mx": ox, "oran_My": oy, "dal": dal, "dc": min(dc, DC_UST),
                  "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kaynak": K_CYT["etkilesim"]})


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
                         An=None, U=1.0, anl=None) -> dict:
    """Toplu çelik eleman tahkiki (ÇYTHYE): basınç/çekme, iki eksenli eğilme, güçlü eksen kesmesi, etkileşim.

    L (m) eleman boyu, Lb (m; varsayılan L), K sayı ya da (Kx, Ky), kuvvetler: sözlük ya da liste
    [{"ad", "N" (kN, basınç +, çekme −), "Mx" (güçlü eksen, kN·m), "My" (zayıf eksen), "V" (güçlü eksen kesmesi, kN)}].

    Dönüş: malzeme, sinif, basinc, cekme, egilme, kesme (alt sonuçlar), kombinasyonlar [{ad, ..., dc_etkilesim, dal,
    dc_kesme, dc}], dc, durum, kontroller (en elverişsiz kombinasyon), uyarilar."""
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
    for k in _kuvvet_listesi(kuvvetler):
        N = k["N"]
        if N >= 0:
            Pc, tur = bas["Pc_kN"], "basınç"
        else:
            Pc, tur = cek["Tc_kN"], "çekme"
        et = celik_etkilesim(abs(N), k["Mx"], k["My"], Pc, eg["Mc_kNm"], eg["Mcy_kNm"])
        dck = _dc(abs(k["V"]), ks["Vc_kN"])
        kont = [
            _kontrol(f"Eksenel ({tur}) Pr ≤ Pc", abs(N), Pc, K_CYT["basinc"] if N >= 0 else K_CYT["cekme_akma"], "kN"),
            _kontrol("Güçlü eksen eğilmesi Mrx ≤ Mcx", abs(k["Mx"]), eg["Mc_kNm"], K_CYT["YBB"], "kN·m"),
            _kontrol("Zayıf eksen eğilmesi Mry ≤ Mcy", abs(k["My"]), eg["Mcy_kNm"], K_CYT["zayif"], "kN·m"),
            _kontrol(f"Bileşik etki (Denk. {et['dal']})", et["dc"], 1.0, K_CYT["etkilesim"], dc=et["dc"]),
            _kontrol("Kesme Vr ≤ Vc", abs(k["V"]), ks["Vc_kN"], K_CYT["kesme"], "kN"),
        ]
        kombs.append(dict(k, tur=tur, Pc_kN=Pc, etkilesim=et, dc_etkilesim=et["dc"], dal=et["dal"], dc_kesme=dck,
                          dc=max(x["dc"] for x in kont), kontroller=kont))
    genel = [bas["kontroller"][-1]] + [x for x in cek["kontroller"] if "Narinlik" in x["ad"]]
    if kombs:
        en = max(kombs, key=lambda c: c["dc"])
        kontroller = [dict(x, ad=f"{en['ad']}: {x['ad']}") for x in en["kontroller"]] + genel
    else:
        kontroller = genel
    dc = max(x["dc"] for x in kontroller)
    uyarilar = list(dict.fromkeys(bas["uyarilar"] + eg["uyarilar"]))
    uyarilar.append("Pr ve Mr ikinci mertebe etkilerini içermelidir (ÇYTHYE Bölüm 6, B1/B2); bu tahkik verilen iç "
                    "kuvvetleri doğrudan kullanır.")
    sonuc = _json({"tur": "celik_eleman_kontrol", "profil": p["ad"], "malzeme": m, "yontem": bas["yontem"],
                   "L_m": L_m, "Lb_m": Lb_m, "Kx": Kx, "Ky": Ky, "Cb": Cb, "sinif": eg["sinif"],
                   "basinc": bas, "cekme": cek, "egilme": eg, "kesme": ks, "kombinasyonlar": kombs,
                   "dc": dc, "durum": "yeterli" if dc <= 1 + 1e-9 else "kesit büyüt", "kontroller": kontroller,
                   "uyarilar": uyarilar})
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
