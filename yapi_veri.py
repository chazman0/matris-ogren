# -*- coding: utf-8 -*-
"""Yapı modülü kütüphaneleri (salt veri): malzeme, kesit, TS 498:2021 yükleri, duvar/kaplama takımları, hareketli
yük azaltması ve yük birleşimleri (TS 500, ÇYTHYE, TBDY 2018).

Bu dosyada hesap yoktur (yalnız tablo okuma yardımcıları: ``zemin_katsayisi``, ``kar_Sk``, ``kar_mu1``, ``ruzgar_q``,
``kar_bolgesi``); ``yapi.py`` bu tabloları okur. Dilim 2 tabloları: TBDY 2018 (F_S/F_1, I, DTS, BYS, Tablo 4.1 R/D,
C_t, n, Tablo 4.2/4.4, drift ve θ_II kuralları) ve TS 498:2021 kar (Çizelge 3, Ek 1) / rüzgâr (Çizelge 4, 5). Her kayıt ``kaynak`` (yönetmelik maddesi) ve ``dogrulandi``
(değer yürürlükteki belgeden okunup çapraz kontrol edildi mi?) taşır. ``dogrulandi: False`` olan kayıtlar
``dogrulanmamis_kayitlar()`` ile listelenir; köprü yanıtında ``uyarilar``a girer ve arayüzde "doğrulanacak" rozeti alır.

Birimler: MPa (malzeme kartları), kN/m³ (birim ağırlık), kN/m² (alan yükü), mm / cm² / cm⁴ / cm³ (profil tabloları,
Avrupa kataloğu birimleri; ``yapi.py`` m'ye çevirir). Profil tablosunda ``Iy`` **güçlü** eksendir (Avrupa kuralı).

Kaynak kısaltmaları (``KAYNAKLAR``): TS 498:2021, TS 500:2000 (+T1/T2/T3), ÇYTHYE 2018 (RG 15.02.2018/30333 Mük.),
TBDY 2018 (RG 18.03.2018/30364 Mük.), TS ISO 9194 (TS 498:2021 md. 5 atfı), ArcelorMittal profil kataloğu.
"""
from __future__ import annotations

import copy

__version__ = "0.1.0"

KAYNAKLAR = {
    "TS498": "TS 498:2021 Yapı elemanlarının boyutlandırılmasında alınacak yüklerin hesap değerleri (TSE, 30.09.2021; "
             "TS 498:1997 yerine)",
    "TS500": "TS 500:2000 Betonarme yapıların tasarım ve yapım kuralları (+T1:2001, T2:2002, T3:2014; RG 12.07.2000/24107)",
    "CYTHYE": "Çelik Yapıların Tasarım, Hesap ve Yapımına Dair Esaslar (RG 15.02.2018/30333 Mük.; ana yönetmelik "
              "RG 04.02.2016/29614)",
    "TBDY": "Türkiye Bina Deprem Yönetmeliği 2018 (RG 18.03.2018/30364 Mük.; yürürlük 01.01.2019)",
    "TS708": "TS 708:2016 Beton donatı çelikleri",
    "TSISO9194": "TS ISO 9194 Ek A/B birim hacim ağırlıkları (TS 498:2021 md. 5.1–5.7 atfı; Topçu ESOGÜ notu ve İMO "
                 "çizelgesi üzerinden)",
    "ARCELOR": "ArcelorMittal 'Sections and Merchant Bars' kataloğu (IPE Euronorm 19-57, HEA/HEB Euronorm 53-62; "
               "EN 10365:2017 ile aynı boyutlar; çapraz kontrol: Perfis 4 hane, Stahlwerk Thüringen, eurocodeapplied)",
    "TUREV": "Yönetmelik değeri değildir; statikten/katman hesabından türetilmiştir",
}


def _k(deger, kaynak, dogrulandi=True, **ek):
    """Tek sayısal yönetmelik değeri: {"deger", "kaynak", "dogrulandi", ...}."""
    d = {"deger": deger, "kaynak": kaynak, "dogrulandi": bool(dogrulandi)}
    d.update(ek)
    return d


# ============================================================================
# Beton (TS 500:2000 Çizelge 3.2; fctk = 0,35√fck (Denk. 3.1), Ec = 3250√fck + 14000 (Denk. 3.2); çizelge değerleri
# yuvarlatılmıştır ve uygulamada çizelge değerleri kullanılır)
# ============================================================================
_BETON_KAYNAK = "TS 500:2000 Çizelge 3.2 (md. 3.3.2–3.3.3)"
BETONLAR = {}
for _ad, _fck, _fctk, _Ec, _k1 in (
    ("C16/20", 16, 1.4, 27000, 0.85), ("C18/22", 18, 1.5, 27500, 0.85), ("C20/25", 20, 1.6, 28000, 0.85),
    ("C25/30", 25, 1.8, 30000, 0.85), ("C30/37", 30, 1.9, 32000, 0.82), ("C35/45", 35, 2.1, 33000, 0.79),
    ("C40/50", 40, 2.2, 34000, 0.76), ("C45/55", 45, 2.3, 36000, 0.73), ("C50/60", 50, 2.5, 37000, 0.70),
):
    BETONLAR[_ad] = {
        "tur": "beton", "fck": _fck, "fctk": _fctk, "Ec": _Ec, "k1": _k1,
        "fcd": round(_fck / 1.5, 2), "fctd": round(_fctk / 1.5, 3),
        "gamma": 25.0, "nu": 0.2, "G_oran": 0.40,
        "kaynak": _BETON_KAYNAK + "; γ: TS ISO 9194 Ek A betonarme 25 kN/m³; ν = 0,20 ve Gc = 0,40Ec: TS 500 md. 3.3.3",
        "dogrulandi": True,
        "not": "fcd = fck/1,5 (γmc yerinde döküm, md. 6.2.5); TBDY 7.2.5: deprem elemanlarında en az C25",
    }

# ============================================================================
# Donatı (TS 500 Çizelge 3.1 / TS 708:2016; TBDY 7.2.5.3b: B420C ve B500C)
# ============================================================================
DONATILAR = {
    "B420C": {"tur": "donati", "fyk": 420, "fsu": 500, "Es": 200000, "fyd": 365.22, "eps_sy": 0.001826,
              "kaynak": "TS 708:2016 B420C (fyk = 420 MPa); TS 500 Çizelge 3.1 S420 (fsu 500); Es = 2×10⁵ MPa TS 500 md. 7.1; "
                        "fyd = fyk/1,15 (md. 6.2.5)", "dogrulandi": True},
    "B500C": {"tur": "donati", "fyk": 500, "fsu": 550, "Es": 200000, "fyd": 434.78, "eps_sy": 0.002174,
              "kaynak": "TS 500 Çizelge 3.1 S500a (fyk 500, fsu 550); TBDY 7.2.5.3b B500C; Es = 2×10⁵ MPa",
              "dogrulandi": True},
}

# ============================================================================
# Yapı çeliği (ÇYTHYE 2018 Tablo 2.1A, EN 10025-2; E = 200 000, G = 77 200 MPa: Esaslar simgeler listesi / md. 8.2.2)
# ============================================================================
_CELIK_KAYNAK = "ÇYTHYE 2018 Esaslar md. 2.1.1 Tablo 2.1A (EN 10025-2); E, G: simgeler listesi ve md. 8.2.2"
CELIKLER = {}
for _ad, _fy, _fu, _fy2, _fu2 in (("S235", 235, 360, 215, 360), ("S275", 275, 430, 255, 410), ("S355", 355, 510, 335, 470)):
    CELIKLER[_ad] = {
        "tur": "celik", "Fy": _fy, "Fu": _fu, "Fy_40_80": _fy2, "Fu_40_80": _fu2, "E": 200000, "G": 77200,
        "gamma": 78.5, "nu": 0.3,
        "kaynak": _CELIK_KAYNAK + " (Fy, Fu: t ≤ 40 mm; Fy_40_80/Fu_40_80: 40 < t ≤ 80 mm); γ = 78,5 kN/m³: "
                  "TS ISO 9194 / İMO çizelgesi (7850 kg/m³)",
        "dogrulandi": True,
    }

# ============================================================================
# Sıcak haddelenmiş profiller (ArcelorMittal kataloğu; araştırma dosyası arastirma_profiller.json)
# Alanlar: h, b, tw, tf, r [mm]; A [cm²]; g [kg/m]; Iy, Iz, It [cm⁴]; Wely, Wply, Welz, Wplz [cm³]; iy, iz [cm];
# Iw [×10³ cm⁶]; Avz [cm²] (EN 1993-1-1 6.2.6). Iy güçlü eksen (y-y), Iz zayıf eksen (z-z).
# ============================================================================
_PROFIL_ALANLAR = ("h", "b", "tw", "tf", "r", "A", "g", "Iy", "Wely", "Wply", "iy", "Iz", "Welz", "Wplz", "iz", "It", "Iw", "Avz")
_PROFIL_KAYNAK = "ArcelorMittal Sections and Merchant Bars (Perfis 4 hane ile birebir; It/Iw kataloglar arası %1–2 fark)"


def _P(*v):
    d = dict(zip(_PROFIL_ALANLAR, v))
    d["kaynak"] = _PROFIL_KAYNAK
    d["dogrulandi"] = True
    return d


PROFILLER = {
    "IPE 80": _P(80.0, 46.0, 3.8, 5.2, 5.0, 7.64, 6.0, 80.1, 20.0, 23.22, 3.24, 8.49, 3.69, 5.82, 1.05, 0.698, 0.12, 3.57),
    "IPE 100": _P(100.0, 55.0, 4.1, 5.7, 7.0, 10.32, 8.1, 171.0, 34.2, 39.41, 4.07, 15.92, 5.79, 9.15, 1.24, 1.2, 0.35, 5.08),
    "IPE 120": _P(120.0, 64.0, 4.4, 6.3, 7.0, 13.21, 10.4, 317.8, 53.0, 60.73, 4.9, 27.67, 8.65, 13.58, 1.45, 1.74, 0.89, 6.31),
    "IPE 140": _P(140.0, 73.0, 4.7, 6.9, 7.0, 16.43, 12.9, 541.2, 77.3, 88.34, 5.74, 44.92, 12.31, 19.25, 1.65, 2.45, 1.98, 7.64),
    "IPE 160": _P(160.0, 82.0, 5.0, 7.4, 9.0, 20.09, 15.8, 869.3, 108.7, 123.9, 6.58, 68.31, 16.66, 26.1, 1.84, 3.6, 3.96, 9.66),
    "IPE 180": _P(180.0, 91.0, 5.3, 8.0, 9.0, 23.95, 18.8, 1317.0, 146.3, 166.4, 7.42, 100.9, 22.16, 34.6, 2.05, 4.79, 7.43, 11.25),
    "IPE 200": _P(200.0, 100.0, 5.6, 8.5, 12.0, 28.48, 22.4, 1943.0, 194.3, 220.6, 8.26, 142.4, 28.47, 44.61, 2.24, 6.98, 12.99, 14.0),
    "IPE 220": _P(220.0, 110.0, 5.9, 9.2, 12.0, 33.37, 26.2, 2772.0, 252.0, 285.4, 9.11, 204.9, 37.25, 58.11, 2.48, 9.07, 22.67, 15.88),
    "IPE 240": _P(240.0, 120.0, 6.2, 9.8, 15.0, 39.12, 30.7, 3892.0, 324.3, 366.6, 9.97, 283.6, 47.27, 73.92, 2.69, 12.88, 37.39, 19.14),
    "IPE 270": _P(270.0, 135.0, 6.6, 10.2, 15.0, 45.95, 36.1, 5790.0, 428.9, 484.0, 11.23, 419.9, 62.2, 96.95, 3.02, 15.94, 70.58, 22.14),
    "IPE 300": _P(300.0, 150.0, 7.1, 10.7, 15.0, 53.81, 42.2, 8356.0, 557.1, 628.4, 12.46, 603.8, 80.5, 125.2, 3.35, 20.12, 125.9, 25.68),
    "IPE 330": _P(330.0, 160.0, 7.5, 11.5, 18.0, 62.61, 49.1, 11770.0, 713.1, 804.3, 13.71, 788.1, 98.52, 153.7, 3.55, 28.15, 199.1, 30.81),
    "IPE 360": _P(360.0, 170.0, 8.0, 12.7, 18.0, 72.73, 57.1, 16270.0, 903.6, 1019.0, 14.95, 1043.0, 122.8, 191.1, 3.79, 37.32, 313.6, 35.14),
    "IPE 400": _P(400.0, 180.0, 8.6, 13.5, 21.0, 84.46, 66.3, 23130.0, 1156.0, 1307.0, 16.55, 1318.0, 146.4, 229.0, 3.95, 51.08, 490.0, 42.69),
    "IPE 450": _P(450.0, 190.0, 9.4, 14.6, 21.0, 98.82, 77.6, 33740.0, 1500.0, 1702.0, 18.48, 1676.0, 176.4, 276.4, 4.12, 66.87, 791.0, 50.85),
    "IPE 500": _P(500.0, 200.0, 10.2, 16.0, 21.0, 115.5, 90.7, 48200.0, 1928.0, 2194.0, 20.43, 2142.0, 214.2, 335.9, 4.31, 89.29, 1249.0, 59.87),
    "IPE 550": _P(550.0, 210.0, 11.1, 17.2, 24.0, 134.4, 106.0, 67120.0, 2441.0, 2787.0, 22.35, 2668.0, 254.1, 400.5, 4.45, 123.2, 1884.0, 72.34),
    "IPE 600": _P(600.0, 220.0, 12.0, 19.0, 24.0, 156.0, 122.0, 92080.0, 3069.0, 3512.0, 24.3, 3387.0, 307.9, 485.6, 4.66, 165.4, 2846.0, 83.78),
    "HEA 100": _P(96.0, 100.0, 5.0, 8.0, 12.0, 21.24, 16.7, 349.2, 72.76, 83.01, 4.06, 133.8, 26.76, 41.14, 2.51, 5.24, 2.58, 7.56),
    "HEA 120": _P(114.0, 120.0, 5.0, 8.0, 12.0, 25.34, 19.9, 606.2, 106.3, 119.5, 4.89, 230.9, 38.48, 58.85, 3.02, 5.99, 6.47, 8.46),
    "HEA 140": _P(133.0, 140.0, 5.5, 8.5, 12.0, 31.42, 24.7, 1033.0, 155.4, 173.5, 5.73, 389.3, 55.62, 84.85, 3.52, 8.13, 15.06, 10.12),
    "HEA 160": _P(152.0, 160.0, 6.0, 9.0, 15.0, 38.77, 30.4, 1673.0, 220.1, 245.1, 6.57, 615.6, 76.95, 117.6, 3.98, 12.19, 31.41, 13.21),
    "HEA 180": _P(171.0, 180.0, 6.0, 9.5, 15.0, 45.25, 35.5, 2510.0, 293.6, 324.9, 7.45, 924.6, 102.7, 156.5, 4.52, 14.8, 60.21, 14.47),
    "HEA 200": _P(190.0, 200.0, 6.5, 10.0, 18.0, 53.83, 42.3, 3692.0, 388.6, 429.5, 8.28, 1336.0, 133.6, 203.8, 4.98, 20.98, 108.0, 18.08),
    "HEA 220": _P(210.0, 220.0, 7.0, 11.0, 18.0, 64.34, 50.5, 5410.0, 515.2, 568.5, 9.17, 1955.0, 177.7, 270.6, 5.51, 28.46, 193.3, 20.67),
    "HEA 240": _P(230.0, 240.0, 7.5, 12.0, 21.0, 76.84, 60.3, 7763.0, 675.1, 744.6, 10.05, 2769.0, 230.7, 351.7, 6.0, 41.55, 328.5, 25.18),
    "HEA 260": _P(250.0, 260.0, 7.5, 12.5, 24.0, 86.82, 68.2, 10450.0, 836.4, 919.8, 10.97, 3668.0, 282.1, 430.2, 6.5, 52.37, 516.4, 28.76),
    "HEA 280": _P(270.0, 280.0, 8.0, 13.0, 24.0, 97.26, 76.4, 13670.0, 1013.0, 1112.0, 11.86, 4763.0, 340.2, 518.1, 7.0, 62.1, 785.4, 31.74),
    "HEA 300": _P(290.0, 300.0, 8.5, 14.0, 27.0, 112.5, 88.0, 18260.0, 1260.0, 1383.0, 12.74, 6310.0, 420.6, 641.2, 7.49, 85.17, 1200.0, 37.28),
    "HEA 320": _P(310.0, 300.0, 9.0, 15.5, 27.0, 124.4, 97.6, 22930.0, 1479.0, 1628.0, 13.58, 6985.0, 465.7, 709.7, 7.49, 108.0, 1512.0, 41.13),
    "HEA 340": _P(330.0, 300.0, 9.5, 16.5, 27.0, 133.5, 105.0, 27690.0, 1678.0, 1850.0, 14.4, 7436.0, 495.7, 755.9, 7.46, 127.2, 1824.0, 44.95),
    "HEA 360": _P(350.0, 300.0, 10.0, 17.5, 27.0, 142.8, 112.0, 33090.0, 1891.0, 2088.0, 15.22, 7887.0, 525.8, 802.3, 7.43, 148.8, 2177.0, 48.96),
    "HEA 400": _P(390.0, 300.0, 11.0, 19.0, 27.0, 159.0, 125.0, 45070.0, 2311.0, 2562.0, 16.84, 8564.0, 570.9, 872.9, 7.34, 189.0, 2942.0, 57.33),
    "HEA 450": _P(440.0, 300.0, 11.5, 21.0, 27.0, 178.0, 140.0, 63720.0, 2896.0, 3216.0, 18.92, 9465.0, 631.0, 965.5, 7.29, 243.8, 4148.0, 65.78),
    "HEA 500": _P(490.0, 300.0, 12.0, 23.0, 27.0, 197.5, 155.0, 86970.0, 3550.0, 3949.0, 20.98, 10370.0, 691.1, 1059.0, 7.24, 309.3, 5643.0, 74.72),
    "HEA 550": _P(540.0, 300.0, 12.5, 24.0, 27.0, 211.8, 166.0, 111900.0, 4146.0, 4622.0, 22.99, 10820.0, 721.3, 1107.0, 7.15, 351.5, 7189.0, 83.72),
    "HEA 600": _P(590.0, 300.0, 13.0, 25.0, 27.0, 226.5, 178.0, 141200.0, 4787.0, 5350.0, 24.97, 11270.0, 751.4, 1156.0, 7.05, 397.8, 8978.0, 93.21),
    "HEB 100": _P(100.0, 100.0, 6.0, 10.0, 12.0, 26.04, 20.4, 449.5, 89.91, 104.2, 4.16, 167.3, 33.45, 51.42, 2.53, 9.25, 3.38, 9.04),
    "HEB 120": _P(120.0, 120.0, 6.5, 11.0, 12.0, 34.01, 26.7, 864.4, 144.1, 165.2, 5.04, 317.5, 52.92, 80.97, 3.06, 13.84, 9.41, 10.96),
    "HEB 140": _P(140.0, 140.0, 7.0, 12.0, 12.0, 42.96, 33.7, 1509.0, 215.6, 245.4, 5.93, 549.7, 78.52, 119.8, 3.58, 20.06, 22.48, 13.08),
    "HEB 160": _P(160.0, 160.0, 8.0, 13.0, 15.0, 54.25, 42.6, 2492.0, 311.5, 354.0, 6.78, 889.2, 111.2, 170.0, 4.05, 31.24, 47.94, 17.59),
    "HEB 180": _P(180.0, 180.0, 8.5, 14.0, 15.0, 65.25, 51.2, 3831.0, 425.7, 481.4, 7.66, 1363.0, 151.4, 231.0, 4.57, 42.16, 93.75, 20.24),
    "HEB 200": _P(200.0, 200.0, 9.0, 15.0, 18.0, 78.08, 61.3, 5696.0, 569.6, 642.5, 8.54, 2003.0, 200.3, 305.8, 5.07, 59.28, 171.1, 24.83),
    "HEB 220": _P(220.0, 220.0, 9.5, 16.0, 18.0, 91.04, 71.5, 8091.0, 735.5, 827.0, 9.43, 2843.0, 258.5, 393.9, 5.59, 76.57, 295.4, 27.92),
    "HEB 240": _P(240.0, 240.0, 10.0, 17.0, 21.0, 106.0, 83.2, 11260.0, 938.3, 1053.0, 10.31, 3923.0, 326.9, 498.4, 6.08, 102.7, 486.9, 33.23),
    "HEB 260": _P(260.0, 260.0, 10.0, 17.5, 24.0, 118.4, 93.0, 14920.0, 1148.0, 1283.0, 11.22, 5135.0, 395.0, 602.2, 6.58, 123.8, 753.7, 37.59),
    "HEB 280": _P(280.0, 280.0, 10.5, 18.0, 24.0, 131.4, 103.0, 19270.0, 1376.0, 1534.0, 12.11, 6595.0, 471.0, 717.6, 7.09, 143.7, 1130.0, 41.09),
    "HEB 300": _P(300.0, 300.0, 11.0, 19.0, 27.0, 149.1, 117.0, 25170.0, 1678.0, 1869.0, 12.99, 8563.0, 570.9, 870.1, 7.58, 185.0, 1688.0, 47.43),
    "HEB 320": _P(320.0, 300.0, 11.5, 20.5, 27.0, 161.3, 127.0, 30820.0, 1926.0, 2149.0, 13.82, 9239.0, 615.9, 939.1, 7.57, 225.1, 2069.0, 51.77),
    "HEB 340": _P(340.0, 300.0, 12.0, 21.5, 27.0, 170.9, 134.0, 36660.0, 2156.0, 2408.0, 14.65, 9690.0, 646.0, 985.7, 7.53, 257.2, 2454.0, 56.09),
    "HEB 360": _P(360.0, 300.0, 12.5, 22.5, 27.0, 180.6, 142.0, 43190.0, 2400.0, 2683.0, 15.46, 10140.0, 676.1, 1032.0, 7.49, 292.5, 2883.0, 60.6),
    "HEB 400": _P(400.0, 300.0, 13.5, 24.0, 27.0, 197.8, 155.0, 57680.0, 2884.0, 3232.0, 17.08, 10820.0, 721.3, 1104.0, 7.4, 355.7, 3817.0, 69.98),
    "HEB 450": _P(450.0, 300.0, 14.0, 26.0, 27.0, 218.0, 171.0, 79890.0, 3551.0, 3982.0, 19.14, 11720.0, 781.4, 1198.0, 7.33, 440.5, 5258.0, 79.66),
    "HEB 500": _P(500.0, 300.0, 14.5, 28.0, 27.0, 238.6, 187.0, 107200.0, 4287.0, 4815.0, 21.19, 12620.0, 841.6, 1292.0, 7.27, 538.4, 7018.0, 89.82),
    "HEB 550": _P(550.0, 300.0, 15.0, 29.0, 27.0, 254.1, 199.0, 136700.0, 4971.0, 5591.0, 23.2, 13080.0, 871.8, 1341.0, 7.17, 600.3, 8856.0, 100.1),
    "HEB 600": _P(600.0, 300.0, 15.5, 30.0, 27.0, 270.0, 212.0, 171000.0, 5701.0, 6425.0, 25.17, 13530.0, 902.0, 1391.0, 7.08, 667.2, 10970.0, 110.8),
}
PROFIL_BIRIMLER = {"h": "mm", "b": "mm", "tw": "mm", "tf": "mm", "r": "mm", "A": "cm²", "g": "kg/m", "Iy": "cm⁴",
                   "Wely": "cm³", "Wply": "cm³", "iy": "cm", "Iz": "cm⁴", "Welz": "cm³", "Wplz": "cm³", "iz": "cm",
                   "It": "cm⁴", "Iw": "×10³ cm⁶", "Avz": "cm²"}

# ============================================================================
# TS 498:2021 Madde 15.1 Çizelge 6 — düşey hareketli yükler (kN/m²)
# ============================================================================
_C6 = "TS 498:2021 md. 15.1 Çizelge 6"
TS498_HAREKETLI = {
    "konut": _k(2.0, _C6 + " satır 2 (konut oda ve koridorları)", ad="Konut (oda ve koridorlar)", azaltma_grubu="a"),
    "ofis": _k(2.0, _C6 + " satır 2 (bürolar)", ad="Büro / ofis", azaltma_grubu="a"),
    "teras": _k(2.0, _C6 + " satır 2 (teras)", ad="Teras", azaltma_grubu="a"),
    "hastane-oda": _k(2.0, _C6 + " satır 2 (hastane odaları)", ad="Hastane odası", azaltma_grubu="a"),
    "dukkan-konut": _k(2.0, _C6 + " satır 2 (konutlardaki ≤ 50 m² dükkânlar)", ad="Konut içi dükkân (≤ 50 m²)", azaltma_grubu="b"),
    "cati-gezilen": _k(2.0, _C6 + " satır 2 (zaman zaman kullanılan yatay / ≤ 1/20 eğimli çatılar)",
                       ad="Çatı (zaman zaman kullanılan, düz)", azaltma_grubu="a"),
    "cati-arasi": _k(1.5, _C6 + " satır 1 (çatı arası odalar)", ad="Çatı arası oda", azaltma_grubu="a"),
    "derslik": _k(3.5, _C6 + " satır 3 (sınıflar)", ad="Derslik / sınıf", azaltma_grubu="a"),
    "yatakhane": _k(3.5, _C6 + " satır 3 (yatakhaneler)", ad="Yatakhane", azaltma_grubu="a"),
    "hastane-mutfak": _k(3.5, _C6 + " satır 3 (hastane mutfakları, muayene ve poliklinik odaları)",
                         ad="Hastane mutfağı / poliklinik", azaltma_grubu="a"),
    "merdiven-konut": _k(3.5, _C6 + " satır 3 (konut merdivenleri, sahanlık dahil)", ad="Konut merdiveni", azaltma_grubu="a"),
    "cati-bahcesi": _k(3.5, _C6 + " satır 3 (çiçeklik / çatı bahçesi)", ad="Çatı bahçesi", azaltma_grubu="a"),
    "koridor-genel": _k(5.0, _C6 + " satır 4 (büro, hastane, okul, tiyatro, kütüphane, depo vb. koridorları)",
                        ad="Genel yapı koridoru", azaltma_grubu="a"),
    "merdiven-umumi": _k(5.0, _C6 + " satır 4 (umuma açık yapılarda merdivenler)", ad="Umuma açık merdiven", azaltma_grubu="a"),
    "balkon": _k(5.0, _C6 + " satır 4 (balkonlar, 10 m²'ye kadar; > 10 m²: 5,0 + 0,35·(A − 10))", ad="Balkon (≤ 10 m²)",
                 azaltma_grubu="a"),
    "magaza": _k(5.0, _C6 + " satır 4 (mağazalar)", ad="Mağaza", azaltma_grubu="b"),
    "toplanti": _k(5.0, _C6 + " satır 4 (toplantı ve bekleme salonları, tiyatro/sinema, camiler)", ad="Toplantı salonu",
                   azaltma_grubu="a"),
    "lokanta": _k(5.0, _C6 + " satır 4 (lokantalar, büyük mutfaklar, kantinler)", ad="Lokanta / kantin", azaltma_grubu="b"),
    "kutuphane": _k(5.0, _C6 + " satır 4 (kütüphaneler, arşivler)", ad="Kütüphane / arşiv", azaltma_grubu="b"),
    "atolye-hafif": _k(5.0, _C6 + " satır 4 (hafif ağırlıklı atölyeler)", ad="Hafif atölye", azaltma_grubu="b"),
    "spor": _k(5.0, _C6 + " satır 4 (spor, dans ve sergi salonları)", ad="Spor / sergi salonu", azaltma_grubu="a"),
    "tribun-sabit": _k(5.0, _C6 + " satır 4 (tribünler, oturma yeri sabit)", ad="Tribün (sabit oturma)", azaltma_grubu="a"),
    "garaj": _k(5.0, _C6 + " satır 6 (garajlar, toplam ağırlığı 2,5 tona kadar araçlar)", ad="Garaj (≤ 2,5 t araç)",
                azaltma_grubu="a"),
    "tribun-ayakta": _k(7.5, _C6 + " satır 5 (tribünler, oturma yeri sabit olmayan)", ad="Tribün (ayakta)", azaltma_grubu="a"),
    "depo": _k(5.0, "TS 498:2021'de genel 'depo' satırı yok (arşiv ve depo koridorları 5,0; depolanan malzeme "
                    "md. 5.1 → TS ISO 9194 ile ayrıca hesaplanır); md. 16: depolarda hareketli yük azaltması yapılmaz",
               dogrulandi=False, ad="Depo (öğretim varsayımı; malzeme yığını ayrıca)", azaltma_grubu="yok"),
}

# ============================================================================
# Birim hacim ağırlıkları (kN/m³) — TS 498:2021 md. 5.1–5.7 → TS ISO 9194 Ek A/B (ikincil aktarım: Topçu, İMO)
# ============================================================================
_BA = "TS ISO 9194 Ek A (TS 498:2021 md. 5 atfı; Topçu ESOGÜ s.143 / İMO çizelgesi)"
TS498_BIRIM_AGIRLIK = {
    "betonarme": _k(25.0, _BA + "; betonarme betonu 2500 kg/m³; TS 500 kalıp basıncı 25 kN/m³", ad="Betonarme"),
    "beton": _k(22.0, _BA + "; demirsiz / tesviye betonu 2200 kg/m³", ad="Beton (donatısız)"),
    "celik": _k(78.5, "İMO çizelgesi: çelik 7850 kg/m³ (TS EN 1991-1-1 Tablo A.4 ile uyumlu)", ad="Çelik"),
    "tugla-dolu": _k(18.0, _BA + "; dolu tuğla duvar (harçlı, sıvasız) 1800 kg/m³", ad="Dolu tuğla duvar"),
    "tugla-bosluklu": _k(14.5, _BA + "; boşluklu (düşey delikli) tuğla duvar 1450 kg/m³", ad="Boşluklu tuğla duvar"),
    "tugla-yatay-delikli": _k(10.0, "İMO çizelgesi: yatay delikli tuğlalarla duvarlar (TS 4563) 1000 kg/m³",
                              ad="Yatay delikli tuğla duvar"),
    "gazbeton-blok": _k(6.0, "İMO çizelgesi: gazbeton duvar blokları (TS 453) 400–800 kg/m³; TS ISO 9194: 600",
                        ad="Gazbeton blok"),
    "gazbeton-duvar": _k(7.0, _BA + "; gazbeton dolgu duvar 700 kg/m³ (harç dahil, sıva hariç)", ad="Gazbeton dolgu duvar"),
    "siva": _k(20.0, _BA + "; kireçli çimento harcı sıva 2000 kg/m³", ad="Sıva (kireç-çimento)"),
    "siva-alci": _k(12.0, "İMO çizelgesi: agregasız alçı sıva 1200 kg/m³", ad="Alçı sıva"),
    "sap": _k(21.0, "İMO çizelgesi: çimento harçlı şap 2000–2100 kg/m³; TS ISO 9194 tesviye betonu 2200", ad="Şap / tesviye"),
    "mermer": _k(27.0, _BA + "; mermer 2700 kg/m³", ad="Mermer"),
    "seramik": _k(20.0, "TS ISO 9194 / İMO çizelgesinde ayrı satır yok; DAÜ INSA471 örneği (seramik+tesviye+sıva 20 kN/m³); "
                        "TS EN 1991-1-1 Ek A ile kontrol edilmeli", dogrulandi=False, ad="Seramik kaplama"),
    "parke": _k(6.0, "İMO çizelgesi: yapı kerestesi (çam vb.) 600 kg/m³", ad="Ahşap parke (çam)"),
    "ahsap-sert": _k(8.0, "İMO çizelgesi: sert ağaçlar (meşe) 800 kg/m³", ad="Sert ahşap (meşe)"),
    "buz": _k(7.0, "TS 498:2021 md. 13", ad="Buz"),
    "kum-cakil": _k(18.0, "İMO çizelgesi: dökme kum/çakıl 1800 kg/m³", ad="Kum / çakıl (dökme)"),
    "toprak-kil": _k(20.0, "İMO çizelgesi: sıkı kil/toprak 2000 kg/m³", ad="Sıkı toprak / kil"),
}

# ============================================================================
# Döşeme kaplama takımları (kN/m²): katman kalınlığı × birim ağırlık (TS 498 tablo vermez; md. 5.6 → TS ISO 9194)
# ============================================================================
_KAP = "TS 498:2021 md. 3.2 ve 5.4–5.6 → TS ISO 9194 katman hesabı (türetilmiş: Σ t_i·γ_i)"


def _kaplama(ad, katmanlar, kaynak_ek=""):
    toplam, dogru = 0.0, True
    liste = []
    for malzeme, t in katmanlar:
        g = TS498_BIRIM_AGIRLIK[malzeme]
        toplam += t * g["deger"]
        dogru = dogru and g["dogrulandi"]
        liste.append({"malzeme": malzeme, "t": t, "gamma": g["deger"], "kN_m2": round(t * g["deger"], 3)})
    return {"ad": ad, "deger": round(toplam, 2), "katmanlar": liste, "kaynak": _KAP + kaynak_ek, "dogrulandi": dogru}


KAPLAMALAR = {
    "sap-seramik-siva": _kaplama("Şap 3 cm + seramik 1 cm + tavan sıvası 2 cm", [("sap", 0.03), ("seramik", 0.01), ("siva", 0.02)]),
    "sap-parke-siva": _kaplama("Şap 3 cm + parke 2 cm + tavan sıvası 2 cm", [("sap", 0.03), ("parke", 0.02), ("siva", 0.02)]),
    "sap-mermer-siva": _kaplama("Şap 5 cm + mermer 2 cm + tavan sıvası 2 cm", [("sap", 0.05), ("mermer", 0.02), ("siva", 0.02)],
                                "; Topçu ESOGÜ konut örneği (tesviye 5 cm, mermer 2 cm, sıva 2 cm)"),
    "sap-siva": _kaplama("Şap 3 cm + tavan sıvası 2 cm (kaplamasız)", [("sap", 0.03), ("siva", 0.02)]),
    "cati-teras": _kaplama("Teras çatı: eğim şapı 5 cm + sıva 2 cm (yalıtım katmanları ihmal)", [("sap", 0.05), ("siva", 0.02)]),
}

# ============================================================================
# Duvar takımları (kN/m² duvar alanı, iki yüz sıva dahil) — TS ISO 9194 değerleriyle katman hesabı
# ============================================================================
_DUV = "TS 498:2021 md. 5 → TS ISO 9194 Ek A; g_d = t_d·γ_d + Σ t_s·γ_s (Topçu ESOGÜ s.144 yöntemi)"


def _duvar(ad, malzeme, t, siva=(0.02, 0.02), kaynak_ek=""):
    g = TS498_BIRIM_AGIRLIK[malzeme]
    s = TS498_BIRIM_AGIRLIK["siva"]
    toplam = t * g["deger"] + sum(siva) * s["deger"]
    return {"ad": ad, "deger": round(toplam, 2), "malzeme": malzeme, "t": t, "siva": list(siva), "gamma": g["deger"],
            "kaynak": _DUV + kaynak_ek, "dogrulandi": g["dogrulandi"] and s["dogrulandi"]}


DUVARLAR = {
    "tugla-delikli-19": _duvar("Yatay delikli tuğla 19 cm + 2×2 cm sıva (2,70 kN/m²)", "tugla-yatay-delikli", 0.19),
    "tugla-delikli-13": _duvar("Yatay delikli tuğla 13,5 cm + 2×2 cm sıva (2,15 kN/m²)", "tugla-yatay-delikli", 0.135),
    "tugla-bosluklu-19": _duvar("Boşluklu tuğla 19 cm + 2×2 cm sıva (3,56 kN/m²)", "tugla-bosluklu", 0.19),
    "tugla-bosluklu-13": _duvar("Boşluklu tuğla 13,5 cm + 2×2 cm sıva (2,76 kN/m²)", "tugla-bosluklu", 0.135),
    "tugla-dolu-19": _duvar("Dolu tuğla 19 cm + 2×2 cm sıva (4,22 kN/m²)", "tugla-dolu", 0.19),
    "gazbeton-20": _duvar("Gazbeton 20 cm + 2×2 cm sıva (2,20 kN/m²)", "gazbeton-duvar", 0.20),
    "gazbeton-25": _duvar("Gazbeton 25 cm + 2 cm dış, 1,5 cm iç sıva (2,45 kN/m²)", "gazbeton-duvar", 0.25, (0.02, 0.015),
                          "; Topçu örneği 2,45 kN/m²"),
    "gazbeton-10": _duvar("Gazbeton 10 cm bölme + 2×1,5 cm sıva (1,30 kN/m²)", "gazbeton-duvar", 0.10, (0.015, 0.015)),
}

# ============================================================================
# TS 498:2021 Madde 16 Çizelge 7 — hareketli yük azaltması β (kat adedine göre; β = alınacak Q / toplam Q)
# ============================================================================
TS498_AZALTMA = {
    "kaynak": "TS 498:2021 md. 16 Çizelge 7 (= TS 498:1997 md. 13 Çizelge 8)",
    "dogrulandi": True,
    "kosullar": [
        "En az üç tam kattan fazla yük taşıyan kolon, perde, temel duvarı vb. elemanlar için uygulanır.",
        "Ağır sanayi atölyeleri, imalathaneler ve depolarda azaltma yapılmaz (β = 1).",
        "En fazla yüke maruz üç kattaki hareketli yük tam alınır; diğer katlar kademeli azaltılır.",
        "Toplam azaltma sınırı: (a) konut, büro, işhanı en fazla %40 (β ≥ 0,60); (b) hafif işyeri, atölye, mağaza en fazla %20 (β ≥ 0,80).",
        "Döşeme ve kiriş hesabında (tek kat) azaltma yoktur.",
        "Çizelge 7'nin '% eksiltme' satırı β satırıyla tutarsızdır (olası dizgi hatası); kodlamada β satırı esastır.",
    ],
    "a": {"ad": "Konut, büro, işhanı", "beta": [1.0, 1.0, 1.0, 0.95, 0.88, 0.80, 0.71, 0.65, 0.60, 0.60, 0.60, 0.60], "beta_min": 0.60},
    "b": {"ad": "Hafif işyeri, atölye, imalathane, mağaza", "beta": [1.0, 1.0, 1.0, 0.98, 0.94, 0.90, 0.86, 0.83, 0.80, 0.80, 0.80, 0.80],
          "beta_min": 0.80},
    "yok": {"ad": "Depo, ağır sanayi (azaltma yok)", "beta": [1.0] * 12, "beta_min": 1.0},
}


def azaltma_beta(grup, kat_adedi):
    """Elemanın taşıdığı tam kat sayısına göre β (Çizelge 7); tablo dışı kat sayısı için alt sınır."""
    satir = TS498_AZALTMA.get(grup) or TS498_AZALTMA["yok"]
    n = max(1, int(kat_adedi))
    if n <= len(satir["beta"]):
        return satir["beta"][n - 1]
    return satir["beta_min"]


# ============================================================================
# Yük birleşimleri — her satır: ad, katsayılar {durum: γ}, tür, kaynak; Dilim 1 yalnız G ve Q durumlarını üretir,
# ötekiler listede kalır ve "uygulanabilir" alanı çözümde eldeki durumlara göre doldurulur.
# ============================================================================
def _komb(ad, katsayilar, tur, kaynak, not_=""):
    return {"ad": ad, "katsayilar": katsayilar, "tur": tur, "kaynak": kaynak, "dogrulandi": True, "not": not_}


_TBDY_411 = "TBDY 2018 md. 4.4.4.1 Denk. (4.11)"
_TBDY_412 = "TBDY 2018 md. 4.4.4.1 Denk. (4.12)"
_TBDY_DRIFT = "TBDY 2018 md. 4.9.1: göreli kat ötelemesi Δ_i azaltılmış deprem yükleri altında (Denk. 4.32); düşey yükler yatay ötelemeyi değiştirmez"
_GKT_E_NOT = "E = Ed(H) + 0,3·Ed(Z) yorumu (TBDY 4.4.4.1 düşey deprem payı GKT'ye de taşındı; 0,6G satırında −0,3)"
# Yer tutucular (yapi.py çoğaltır): W → W+X, W-X, W+Y, W-Y; EH → ±EX± ± 0,3·EY± ve ±0,3·EX± ± EY± (32 yön/dışmerkezlik);
# EZ → EZ durumu ((2/3)·S_DS·G); drift satırı → tek doğrultulu EX+, EX-, EY+, EY-; T ve H durumu üretilmez (uygulanmaz).
KOMBINASYONLAR = {
    "ts500": {
        "ad": "Betonarme: TS 500 md. 6.2.6 + TBDY 2018 md. 4.4.4",
        "kaynak": "TS 500:2000 md. 6.2.6 Denk. (6.3)–(6.10); TBDY 2018 md. 4.4.4.1",
        "dogrulandi": True,
        "liste": [
            _komb("1.4G+1.6Q", {"G": 1.4, "Q": 1.6}, "dayanim", "TS 500 Denk. (6.3)"),
            _komb("G+1.2Q+1.2T", {"G": 1.0, "Q": 1.2, "T": 1.2}, "dayanim", "TS 500 Denk. (6.4)", "T: sıcaklık, büzülme, farklı oturma"),
            _komb("G+1.3Q+1.3W", {"G": 1.0, "Q": 1.3, "W": 1.3}, "dayanim", "TS 500 Denk. (6.5)"),
            _komb("0.9G+1.3W", {"G": 0.9, "W": 1.3}, "dayanim", "TS 500 Denk. (6.6)"),
            _komb("1.4G+1.6Q+1.6H", {"G": 1.4, "Q": 1.6, "H": 1.6}, "dayanim", "TS 500 Denk. (6.9)", "H: yanal toprak itkisi"),
            _komb("0.9G+1.6H", {"G": 0.9, "H": 1.6}, "dayanim", "TS 500 Denk. (6.10)"),
            _komb("G+Q+0.2S+Ed(H)+0.3Ed(Z)", {"G": 1.0, "Q": 1.0, "S": 0.2, "EH": 1.0, "EZ": 0.3}, "deprem", _TBDY_411,
                  "TS 500 (6.7) yerine TBDY; Ed(H) doğrultu birleştirmeli (4.4.2), Ed(Z) düşey deprem (4.4.3)"),
            _komb("0.9G+H+Ed(H)-0.3Ed(Z)", {"G": 0.9, "H": 1.0, "EH": 1.0, "EZ": -0.3}, "deprem", _TBDY_412,
                  "TS 500 (6.8) yerine TBDY"),
            _komb("G+Q", {"G": 1.0, "Q": 1.0}, "servis", "TS 500 md. 6.2.6(f): kullanılabilirlikte tüm yük katsayıları 1,0"),
            _komb("G+Q+Ed(H)", {"G": 1.0, "Q": 1.0, "EH": 1.0}, "drift", _TBDY_DRIFT, "tek doğrultu (EX ya da EY), dışmerkezlik ±"),
        ],
    },
    "cythye_ydkt": {
        "ad": "Çelik YDKT: ÇYTHYE 2018 md. 5.3.1 + TBDY 2018 md. 9.2.5.1",
        "kaynak": "ÇYTHYE 2018 Esaslar md. 5.3.1 (1)–(7); TBDY 2018 md. 4.4.4.2(a) ve 9.2.5.1",
        "dogrulandi": True,
        "liste": [
            _komb("1.4G", {"G": 1.4}, "dayanim", "ÇYTHYE 5.3.1 (1)"),
            _komb("1.2G+1.6(Qr|S|R)", {"G": 1.2, "S": 1.6}, "dayanim", "ÇYTHYE 5.3.1 (2a)", "Qr çatı hareketli, S kar, R yağmur: en büyüğü"),
            _komb("1.2G+1.6Q+0.5(Qr|S|R)", {"G": 1.2, "Q": 1.6, "S": 0.5}, "dayanim", "ÇYTHYE 5.3.1 (2b)"),
            _komb("1.2G+1.6(Qr|S|R)+(Q|0.8W)", {"G": 1.2, "S": 1.6, "Q": 1.0, "W": 0.8}, "dayanim", "ÇYTHYE 5.3.1 (3)",
                  "Q ya da 0,8W: elverişsiz olanı"),
            _komb("1.2G+Q+0.5(Qr|S|R)+1.6W", {"G": 1.2, "Q": 1.0, "S": 0.5, "W": 1.6}, "dayanim", "ÇYTHYE 5.3.1 (4)",
                  "rüzgâr katsayısı 1,6 (1,3 değil)"),
            _komb("1.2G+Q+0.2S+Ed(H)+0.3Ed(Z)", {"G": 1.2, "Q": 1.0, "S": 0.2, "EH": 1.0, "EZ": 0.3}, "deprem",
                  "ÇYTHYE 5.3.1 (5) → TBDY 2018 4.4.4.2(a) / 9.2.5.1: (4.11)'de G yerine 1,2G",
                  "Q ≤ 5 kN/m² ise Q %50 azaltılabilir (garaj ve kalabalık binalar hariç)"),
            _komb("0.9G+1.6W", {"G": 0.9, "W": 1.6}, "dayanim", "ÇYTHYE 5.3.1 (6)"),
            _komb("0.9G+H+Ed(H)-0.3Ed(Z)", {"G": 0.9, "H": 1.0, "EH": 1.0, "EZ": -0.3}, "deprem",
                  "ÇYTHYE 5.3.1 (7) → " + _TBDY_412),
            _komb("G+Q", {"G": 1.0, "Q": 1.0}, "servis", "ÇYTHYE md. 15.1 (1): kullanılabilirlik birleşimi G + Q"),
            _komb("G+Q+Ed(H)", {"G": 1.0, "Q": 1.0, "EH": 1.0}, "drift", _TBDY_DRIFT, "tek doğrultu (EX ya da EY), dışmerkezlik ±"),
        ],
    },
    "cythye_gkt": {
        "ad": "Çelik GKT: ÇYTHYE 2018 md. 5.3.2 + TBDY 2018 md. 9.2.5.2",
        "kaynak": "ÇYTHYE 2018 Esaslar md. 5.3.2 (1)–(8); TBDY 2018 Denk. (9.1a–c)",
        "dogrulandi": True,
        "liste": [
            _komb("G", {"G": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (1)"),
            _komb("G+Q", {"G": 1.0, "Q": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (2)", "GKT'de dayanım birleşimi; servis için de aynı"),
            _komb("G+(Qr|S|R)", {"G": 1.0, "S": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (3)"),
            _komb("G+0.75Q+0.75(Qr|S|R)", {"G": 1.0, "Q": 0.75, "S": 0.75}, "dayanim", "ÇYTHYE 5.3.2 (4)"),
            _komb("G+W", {"G": 1.0, "W": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (5a)"),
            _komb("G+0.7E", {"G": 1.0, "EH": 0.7, "EZ": 0.21}, "deprem", "ÇYTHYE 5.3.2 (5b) → TBDY Denk. (9.1b)", _GKT_E_NOT),
            _komb("G+0.75Q+0.75(Qr|S|R)+0.75W", {"G": 1.0, "Q": 0.75, "S": 0.75, "W": 0.75}, "dayanim", "ÇYTHYE 5.3.2 (6a)"),
            _komb("G+0.75Q+0.75S+0.75(0.7E)", {"G": 1.0, "Q": 0.75, "S": 0.75, "EH": 0.525, "EZ": 0.1575}, "deprem",
                  "ÇYTHYE 5.3.2 (6b) → TBDY Denk. (9.1a)", _GKT_E_NOT),
            _komb("0.6G+W", {"G": 0.6, "W": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (7)"),
            _komb("0.6G+0.7E", {"G": 0.6, "EH": 0.7, "EZ": -0.21}, "deprem", "ÇYTHYE 5.3.2 (8) → TBDY Denk. (9.1c): 0,6G + 0,75H ± 0,7Ed", _GKT_E_NOT),
            _komb("G+Q+Ed(H)", {"G": 1.0, "Q": 1.0, "EH": 1.0}, "drift", _TBDY_DRIFT, "tek doğrultu (EX ya da EY), dışmerkezlik ±"),
        ],
    },
}
YUK_DURUMU_ADLARI = {"G": "sabit yük", "Q": "hareketli yük", "S": "kar", "W": "rüzgâr", "EH": "yatay deprem Ed(H)",
                     "EZ": "düşey deprem Ed(Z)", "T": "sıcaklık / büzülme / oturma", "H": "toprak itkisi"}

# TBDY 2018 Tablo 4.3 hareketli yük kütle katılım katsayısı n (Dilim 2'de kütle hesabı için; burada yalnız bilgi)
TBDY_KUTLE_KATILIM = {
    "kaynak": "TBDY 2018 Tablo 4.3 (md. 4.5.9 / Denk. 4.16)", "dogrulandi": True,
    "n": {"depo": 0.8, "okul-magaza-sinema-lokanta": 0.6, "konut-isyeri-otel-hastane-otopark": 0.3, "endustri-sabit-ekipman": 1.0},
}


# ============================================================================
# TBDY 2018 — deprem (Bölüm 2, 3, 4; araştırma dosyası arastirma_tbdy2018.json; birincil metin satır satır doğrulandı)
# ============================================================================
_TBDY_21 = "TBDY 2018 Tablo 2.1 (md. 2.3.3.1); ara değer doğrusal, uçlarda sabit"
_TBDY_22 = "TBDY 2018 Tablo 2.2 (md. 2.3.3.1); ara değer doğrusal, uçlarda sabit"
TBDY_FS = {
    "kaynak": _TBDY_21, "dogrulandi": True,
    "SS": [0.25, 0.50, 0.75, 1.00, 1.25, 1.50],
    "ZA": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], "ZB": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9], "ZC": [1.3, 1.3, 1.2, 1.2, 1.2, 1.2],
    "ZD": [1.6, 1.4, 1.2, 1.1, 1.0, 1.0], "ZE": [2.4, 1.7, 1.3, 1.1, 0.9, 0.8],
}
TBDY_F1 = {
    "kaynak": _TBDY_22, "dogrulandi": True,
    "S1": [0.10, 0.20, 0.30, 0.40, 0.50, 0.60],
    "ZA": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], "ZB": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], "ZC": [1.5, 1.5, 1.5, 1.5, 1.5, 1.4],
    "ZD": [2.4, 2.2, 2.0, 1.9, 1.8, 1.7], "ZE": [4.2, 3.3, 2.8, 2.4, 2.2, 2.0],
}
ZEMIN_SINIFLARI = {
    "kaynak": "TBDY 2018 Tablo 16.1 (md. 16.4); ZF: sahaya özel analiz (16.5), Tablo 2.1/2.2'de değer yok", "dogrulandi": True,
    "ZA": "Sağlam, sert kayalar (V_S30 > 1500 m/s)", "ZB": "Az ayrışmış, orta sağlam kayalar (760–1500 m/s)",
    "ZC": "Çok sıkı kum, çakıl ve sert kil tabakaları ya da ayrışmış, çok çatlaklı zayıf kayalar (360–760 m/s)",
    "ZD": "Orta sıkı – sıkı kum, çakıl ya da çok katı kil tabakaları (180–360 m/s)",
    "ZE": "Gevşek kum, çakıl ya da yumuşak–katı kil tabakaları (< 180 m/s)",
}


def zemin_katsayisi(tablo, zemin, deger):
    """F_S ya da F_1 (Tablo 2.1 / 2.2): sütunlar arasında doğrusal ara değer, uç sütunların dışında sabit (md. 2.3.3.1)."""
    zemin = str(zemin).strip().upper()
    if zemin not in tablo or zemin in ("SS", "S1"):
        raise KeyError(zemin)
    x = tablo["SS"] if "SS" in tablo else tablo["S1"]
    y = tablo[zemin]
    v = float(deger)
    if v <= x[0]:
        return y[0]
    if v >= x[-1]:
        return y[-1]
    for i in range(len(x) - 1):
        if x[i] <= v <= x[i + 1]:
            t = (v - x[i]) / (x[i + 1] - x[i])
            return y[i] + t * (y[i + 1] - y[i])
    return y[-1]  # pragma: no cover


TBDY_SPEKTRUM = {
    "kaynak": "TBDY 2018 Denk. (2.1)–(2.3) md. 2.3.2.2, 2.3.4.1; T_L = 6 s; Denk. (2.5)–(2.6) düşey spektrum köşeleri",
    "dogrulandi": True, "TL": 6.0, "sonum": 0.05,
    "formul": {"SDS": "S_S·F_S", "SD1": "S_1·F_1", "TA": "0,2·S_D1/S_DS", "TB": "S_D1/S_DS",
               "Sae": "(0,4 + 0,6·T/T_A)·S_DS [T ≤ T_A]; S_DS [T_A ≤ T ≤ T_B]; S_D1/T [T_B ≤ T ≤ T_L]; S_D1·T_L/T² [T ≥ T_L]"},
    "duzeyler": {"DD-1": "2475 yıl (%2/50)", "DD-2": "475 yıl (%10/50; tasarım)", "DD-3": "72 yıl (%50/50; λ için)", "DD-4": "43 yıl"},
}
TBDY_BKS_I = {
    "kaynak": "TBDY 2018 Tablo 3.1 (md. 3.1.1–3.1.2)", "dogrulandi": True,
    1: {"I": 1.5, "tanim": "Deprem sonrası kullanımı gereken ya da yoğun/uzun süreli insan bulunan binalar: hastane, okul, yurt, "
                           "itfaiye, enerji, haberleşme, tehlikeli madde"},
    2: {"I": 1.2, "tanim": "Kısa süreli yoğun insan bulunan binalar: AVM, spor tesisi, sinema, tiyatro, konser salonu, ibadethane"},
    3: {"I": 1.0, "tanim": "Diğer binalar: konut, işyeri, otel, bina türü endüstri yapıları"},
}
TBDY_DTS = {
    "kaynak": "TBDY 2018 Tablo 3.2 (md. 3.2); S_DS DD-2 için", "dogrulandi": True,
    "satirlar": [(0.75, "1"), (0.50, "2"), (0.33, "3"), (0.0, "4")],   # S_DS ≥ eşik → DTS; BKS = 1 ise 'a' eki
}
TBDY_BYS = {
    "kaynak": "TBDY 2018 Tablo 3.3 (md. 3.3.2); H_N bina tabanından ölçülen yükseklik (m)", "dogrulandi": True,
    # (BYS, DTS=1,1a,2,2a üst sınır, DTS=3,3a üst sınır, DTS=4,4a üst sınır); H_N ≤ sınır → o BYS (küçük BYS = yüksek bina)
    "satirlar": [(8, 7.0, 10.5, 10.5), (7, 10.5, 17.5, 17.5), (6, 17.5, 28.0, 28.0), (5, 28.0, 42.0, 42.0), (4, 42.0, 56.0, 56.0),
                 (3, 56.0, 70.0, 91.0), (2, 70.0, 91.0, 105.0), (1, None, None, None)],
}
_T41 = "TBDY 2018 Tablo 4.1 (md. 4.3.2)"


def _ts(kod, tanim, R, D, bys, grup, suneklik):
    return {"kod": kod, "tanim": tanim, "R": R, "D": D, "BYS_min": bys, "grup": grup, "suneklik": suneklik,
            "kaynak": _T41, "dogrulandi": True}


# anahtar → Tablo 4.1 satırı; BYS_min: "BYS ≥ n" kuralındaki n (None: sınırsız, 8: yalnız BYS = 8)
TBDY_TASIYICI = {
    "betonarme-cerceve-yuksek": _ts("A11", "Tamamı moment aktaran süneklik düzeyi yüksek (SDY) betonarme çerçeve", 8, 3, 3, "betonarme", "yuksek"),
    "betonarme-perde-bagkirisli-yuksek": _ts("A12", "Tamamı SDY bağ kirişli (boşluklu) betonarme perde", 7, 2.5, 2, "betonarme", "yuksek"),
    "betonarme-perde-yuksek": _ts("A13", "Tamamı SDY boşluksuz betonarme perde", 6, 2.5, 2, "betonarme", "yuksek"),
    "betonarme-perde-cerceve-bagkirisli-yuksek": _ts("A14", "SDY çerçeve + SDY bağ kirişli perde (perde-çerçeve; 4.3.4.5)", 8, 2.5, 2, "betonarme", "yuksek"),
    "betonarme-perde-cerceve-yuksek": _ts("A15", "SDY çerçeve + SDY boşluksuz perde (perde-çerçeve; 4.3.4.5)", 7, 2.5, 2, "betonarme", "yuksek"),
    "betonarme-tek-katli-mafsalli": _ts("A16", "Tek katlı, çatı bağlantısı mafsallı, H ≤ 12 m SDY betonarme kolonlar", 3, 2, None, "betonarme", "yuksek"),
    "betonarme-karma-perde-bagkirisli": _ts("A21", "SDS çerçeve + SDY bağ kirişli perde (karma; 4.3.1.2)", 6, 2.5, 4, "betonarme", "karma"),
    "betonarme-karma-perde": _ts("A22", "SDS çerçeve + SDY boşluksuz perde (karma; 4.3.1.2)", 5, 2.5, 4, "betonarme", "karma"),
    "betonarme-karma-asmolen-perde-bagkirisli": _ts("A23", "SDS dişli/asmolen döşemeli çerçeve + SDY bağ kirişli perde", 6, 2.5, 6, "betonarme", "karma"),
    "betonarme-karma-asmolen-perde": _ts("A24", "SDS dişli/asmolen döşemeli çerçeve + SDY boşluksuz perde", 5, 2.5, 6, "betonarme", "karma"),
    "betonarme-cerceve-sinirli": _ts("A31", "Tamamı moment aktaran süneklik düzeyi sınırlı (SDS) betonarme çerçeve (yalnız DTS = 3, 4; 4.3.4.3)", 4, 2.5, 7, "betonarme", "sinirli"),
    "betonarme-perde-sinirli": _ts("A32", "Tamamı SDS boşluksuz betonarme perde", 4, 2, 6, "betonarme", "sinirli"),
    "betonarme-perde-cerceve-sinirli": _ts("A33", "SDS çerçeve + SDS boşluksuz perde", 4, 2, 6, "betonarme", "sinirli"),
    "onuretimli-cerceve-yuksek": _ts("B11", "Tamamı SDY önüretimli moment çerçeve (MAB1–MAB2; MAB3–MAB4: R = 5, BYS ≥ 6)", 7, 2.5, 4, "onuretimli", "yuksek"),
    "onuretimli-cerceve-perde-bagkirisli-yuksek": _ts("B12", "SDY önüretimli çerçeve + SDY yerinde dökme bağ kirişli perde (MAB1–MAB2)", 7, 2.5, 2, "onuretimli", "yuksek"),
    "onuretimli-cerceve-perde-yuksek": _ts("B13", "SDY önüretimli çerçeve + SDY yerinde dökme boşluksuz perde (MAB1–MAB2)", 6, 2.5, 2, "onuretimli", "yuksek"),
    "onuretimli-mafsalli-perde-yuksek": _ts("B14", "Mafsallı önüretimli çerçeve + tamamı SDY yerinde dökme perde", 4, 2, 7, "onuretimli", "yuksek"),
    "onuretimli-tek-katli-mafsalli": _ts("B15", "Tek katlı mafsallı çatılı SDY önüretimli kolonlar, H ≤ 12 m", 3, 2, None, "onuretimli", "yuksek"),
    "onuretimli-karma-perde": _ts("B21", "SDS önüretimli çerçeve + SDY yerinde dökme perde (karma; MAB1–MAB2)", 5, 2.5, 5, "onuretimli", "karma"),
    "onuretimli-cerceve-sinirli": _ts("B31", "Tamamı SDS önüretimli moment çerçeve", 3, 2, 8, "onuretimli", "sinirli"),
    "onuretimli-cerceve-perde-sinirli": _ts("B32", "SDS önüretimli çerçeve + SDS yerinde dökme boşluksuz perde", 3, 2, 7, "onuretimli", "sinirli"),
    "onuretimli-panel-cift-cidar": _ts("B33", "Önüretimli düşey çift cidarlı paneller (SDS)", 4, 2, 6, "onuretimli", "sinirli"),
    "onuretimli-panel-tek-cidar": _ts("B34", "Önüretimli düşey tek cidarlı paneller (SDS)", 3, 2, 7, "onuretimli", "sinirli"),
    "celik-mcm-yuksek": _ts("C11", "Tamamı moment aktaran SDY çelik çerçeve", 8, 3, 3, "celik", "yuksek"),
    "celik-dismerkez-capraz-yuksek": _ts("C12", "Tamamı SDY dışmerkez çaprazlı ya da burkulması önlenmiş merkezi çaprazlı çelik çerçeve", 8, 2.5, 2, "celik", "yuksek"),
    "celik-merkezi-capraz-yuksek": _ts("C13", "Tamamı SDY merkezi çaprazlı çelik çerçeve", 5, 2, 4, "celik", "yuksek"),
    "celik-mcm-dismerkez-capraz-yuksek": _ts("C14", "SDY moment çerçeve + SDY dışmerkez/BÖÇ çaprazlı çerçeve ya da SDY bağ kirişli BA perde (4.3.4.5)", 8, 3, 2, "celik", "yuksek"),
    "celik-mcm-merkezi-capraz-yuksek": _ts("C15", "SDY moment çerçeve + SDY merkezi çaprazlı çerçeve ya da SDY boşluksuz BA perde (4.3.4.5)", 6, 2.5, 2, "celik", "yuksek"),
    "celik-tek-katli-mafsalli": _ts("C16", "Tek katlı, çatı bağlantısı mafsallı, H ≤ 12 m SDY çelik kolonlar", 4, 2, None, "celik", "yuksek"),
    "celik-karma-dismerkez-capraz": _ts("C21", "SDS moment çerçeve + SDY dışmerkez/BÖÇ çaprazlı çerçeve ya da SDY bağ kirişli BA perde (karma; 4.3.1.2)", 6, 2.5, 4, "celik", "karma"),
    "celik-karma-merkezi-capraz": _ts("C22", "SDS moment çerçeve + SDY merkezi çaprazlı çerçeve ya da SDY boşluksuz BA perde (karma; 4.3.1.2)", 5, 2, 4, "celik", "karma"),
    "celik-mcm-sinirli": _ts("C31", "Tamamı moment aktaran SDS çelik çerçeve", 4, 2.5, 7, "celik", "sinirli"),
    "celik-merkezi-capraz-sinirli": _ts("C32", "Tamamı SDS merkezi çaprazlı çelik çerçeve", 3, 2, 8, "celik", "sinirli"),
    "celik-mcm-merkezi-capraz-sinirli": _ts("C33", "SDS moment çerçeve + SDS merkezi çaprazlı çerçeve", 4, 2, 7, "celik", "sinirli"),
    "hafif-celik-vidali-panel": _ts("D1", "Hafif çelik: SDY vidalı sac/OSB/kontrplak panel", 4, 2, 8, "hafif-celik", "yuksek"),
    "hafif-celik-alci-panel": _ts("D2", "Hafif çelik: SDS alçı levha / çapraz panel", 3, 2, 8, "hafif-celik", "sinirli"),
    "yigma-donatili": _ts("E11", "Donatılı yığma", 4, 2, 7, "yigma", "sinirli"),
    "yigma-donatili-gazbeton-panel": _ts("E12", "Donatılı gazbeton panel", 4, 2, 7, "yigma", "sinirli"),
    "yigma-kusatilmis": _ts("E21", "Kuşatılmış yığma", 3, 2, 8, "yigma", "sinirli"),
    "yigma-donatisiz": _ts("E22", "Donatısız yığma", 2.5, 1.5, 8, "yigma", "sinirli"),
    "ahsap-civili-panel": _ts("F1", "Ahşap: SDY çivili/vidalı OSB/kontrplak panel", 4, 2, 7, "ahsap", "yuksek"),
    "ahsap-tutkalli-panel": _ts("F2", "Ahşap: SDS tutkallı panel ya da ahşap çapraz", 3, 2, 8, "ahsap", "sinirli"),
}
TBDY_TASIYICI_KURALLAR = {
    "kaynak": _T41 + " dipnotları ve md. 4.3.4", "dogrulandi": True,
    "4.3.2.3": "Dıştan rijit perdelerle çevrili bodrumda (R/I) = 2,5 ve D = 1,5",
    "4.3.4.1": "DTS = 1a, 2a, 3a, 4a binalarda SDS sistem kullanılamaz; BYS ≤ 6 ve DTS = 1a, 2a binalarda karma sistem kullanılamaz",
    "4.3.4.3": "A31, B31, C31 yalnız DTS = 3 ve DTS = 4 binalarda",
    "4.3.5.2": "D sünek etkiler (eğilme, çekme) için kullanılmaz; sünek olmayan etkilerde (kesme, birleşim, döşeme, temel) çarpandır",
}
TBDY_CT = {
    "kaynak": "TBDY 2018 Denk. (4.27) md. 4.7.3.4 (tamamı perdeli binalarda Denk. 4.28: C_t = 0,1/√A_t ≤ 0,07)", "dogrulandi": True,
    "betonarme-cerceve": 0.10, "celik-cerceve": 0.08, "diger": 0.07,
}
TBDY_KUTLE_KATILIM_KULLANIM = {
    "kaynak": "TBDY 2018 Tablo 4.3 (md. 4.5.9.2) ↔ TS 498:2021 Çizelge 6 eşlemesi (araştırma dosyası; 'yorum' satırları yönetmelikte açık değildir)",
    "dogrulandi": True,
    "n": {"konut": 0.3, "ofis": 0.3, "teras": 0.3, "hastane-oda": 0.3, "dukkan-konut": 0.3, "cati-gezilen": 0.3, "cati-arasi": 0.3,
          "derslik": 0.6, "yatakhane": 0.6, "hastane-mutfak": 0.3, "merdiven-konut": 0.3, "cati-bahcesi": 0.3, "koridor-genel": 0.3,
          "merdiven-umumi": 0.3, "balkon": 0.3, "magaza": 0.6, "toplanti": 0.6, "lokanta": 0.6, "kutuphane": 0.6,
          "atolye-hafif": 0.6, "spor": 0.6, "tribun-sabit": 0.6, "garaj": 0.3, "tribun-ayakta": 0.6, "depo": 0.8},
    "yorum": ["hastane-mutfak", "atolye-hafif", "kutuphane", "koridor-genel", "merdiven-umumi"],
    "kar": 0.30, "not": "Çatı katı ağırlığında kar yükünün %30'u alınır (md. 4.5.9.2)",
}
TBDY_UYGULANABILIRLIK = {
    "kaynak": "TBDY 2018 Tablo 4.4 (md. 4.6.2.2); EDYY = eşdeğer deprem yükü yöntemi", "dogrulandi": True,
    # dts12: DTS = 1, 1a, 2, 2a için BYS ≥ n; dts34: DTS = 3, 3a, 4, 4a için BYS ≥ n
    "duzenli": {"kosul": "Her katta η_bi ≤ 2,0 ve B2 (yumuşak kat) düzensizliği yok", "dts12": 4, "dts34": 5},
    "diger": {"kosul": "Diğer tüm binalar", "dts12": 5, "dts34": 6},
}
TBDY_ETKIN_RIJITLIK = {
    "kaynak": "TBDY 2018 Tablo 4.2 (md. 4.5.8); yalnız deprem etkili yük birleşimlerinde (4.5.8.3)", "dogrulandi": True,
    "kolon": {"egilme": 0.70, "kesme": 1.0}, "kiris": {"egilme": 0.35, "kesme": 1.0}, "bag-kirisi": {"egilme": 0.15, "kesme": 1.0},
    "perde": {"egilme": 0.50, "kesme": 0.50},
}
TBDY_DEPREM_KURALLAR = {
    "kaynak": "TBDY 2018 md. 4.4.2–4.4.4, 4.5.10, 4.7, 4.9", "dogrulandi": True,
    "Ra": "R_a(T) = R/I (T > T_B); D + (R/I − D)·T/T_B (T ≤ T_B) — Denk. (4.1a, 4.1b)",
    "SaR": "S_aR(T) = S_ae(T)/R_a(T) — Denk. (4.8)",
    "VtE": "V_tE = m_t·S_aR(T_p)·g ≥ 0,04·m_t·I·S_DS·g — Denk. (4.19)",
    "dFN": "ΔF_NE = 0,0075·N·V_tE — Denk. (4.22)",
    "FiE": "F_iE = (V_tE − ΔF_NE)·m_i·H_i/Σ m_j·H_j — Denk. (4.23)",
    "Tp": "T_p = 2π·√(Σ m_i·d_fi² / Σ F_fi·d_fi) ≤ 1,4·T_pA — Denk. (4.26), md. 4.7.3.2",
    "TpA": "T_pA = C_t·H_N^(3/4) — Denk. (4.27)",
    "dismerkezlik": "e = ±0,05·B_i (deprem doğrultusuna dik kat boyutu); M_ib = F_iE·e — md. 4.5.10.2, Denk. (4.17)",
    "eta_b": "η_bi = (Δ_i)max/(Δ_i)ort, (Δ)ort = ½[(Δ)max + (Δ)min]; η_bi > 1,2 → A1 düzensizliği; D_bi = (η_bi/1,2)² — Tablo 3.6, Denk. (4.29)",
    "EdH": "E_d(H) = ±E_d(X) ± 0,3·E_d(Y); ±0,3·E_d(X) ± E_d(Y) — Denk. (4.9)",
    "EdZ": "E_d(Z) ≈ (2/3)·S_DS·G — Denk. (4.10)",
    "drift": "Δ_i = u_i − u_{i−1}; δ_i = (R/I)·Δ_i; λ·δ_i,max/h_i ≤ 0,008κ (a: bitişik gevrek dolgu) | 0,016κ (b: esnek derz) — Denk. (4.32)–(4.34)",
    "lambda": "λ = S_ae(T_p; DD-3)/S_ae(T_p; DD-2) — md. 4.9.1.4",
    "kappa": {"betonarme": 1.0, "celik": 0.5},
    "theta": "θ_II,i = (Δ_i)ort·Σ_{k≥i} w_k/(V_i·h_i) ≤ 0,12·D/(C_h·R); aşılırsa β_II = 0,88 + (C_h·R/D)·θ_II,max ≥ 1 — Denk. (4.35)–(4.37)",
    "Ch": {"betonarme": 0.5, "celik": 1.0},
    "drift_notu": "Δ_i hesabında 4.7.3.2'deki 1,4·T_pA sınırı ve Denk. (4.19) alt sınırı uygulanmaz (md. 4.9.1.1)",
    "tek_katli_celik": "Tek katlı çelik moment çerçevede drift sınırları en çok %50 artırılabilir (4.9.1.5)",
}

# ============================================================================
# TS 498:2021 — kar (md. 11, Çizelge 3, Ek 1) ve rüzgâr (md. 14, Çizelge 4/5, Şekil 1); TS EN 1991-1-3 μ1
# ============================================================================
TS498_KAR = {
    "kaynak": "TS 498:2021 md. 11 Çizelge 3 (s. 9); 9 kar bölgesi (Ek 1 il/ilçe listesi, Ek 2 harita); kar yağmayan yerde S = 0",
    "dogrulandi": True,
    "rakim": [200, 300, 400, 500, 600, 700, 800, 900, 1000],     # ilk satır 0–200 m; ara rakımda üst satır (güvenli taraf)
    "Sk": {1: [0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.80, 0.80], 2: [0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.90, 0.95, 1.05],
           3: [0.75, 0.75, 0.75, 0.75, 0.80, 0.85, 0.95, 1.05, 1.10], 4: [0.75, 0.75, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10, 1.20],
           5: [0.75, 0.75, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10, 1.30], 6: [0.75, 0.75, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10, 1.35],
           7: [0.75, 0.75, 0.80, 0.85, 0.90, 0.95, 1.10, 1.25, 1.40], 8: [0.80, 0.85, 0.90, 0.95, 1.00, 1.10, 1.20, 1.30, 1.50],
           9: [0.85, 0.90, 0.95, 1.00, 1.10, 1.20, 1.30, 1.40, 1.60]},
    "ustu_1000": {"1500": 1.10, "ustu": 1.15},   # 1000 m değerine: 1000 < h ≤ 1500 m %10, h > 1500 m %15 artış (Çizelge 3 notu)
    "ara_rakim": "Standart ara değer kuralı vermez; bir üst rakım satırı alınır (güvenli taraf; araştırma notu)",
}
EN1991_KAR_SEKIL = {
    "kaynak": "TS EN 1991-1-3 md. 5.2–5.3 Tablo 5.2 (TS 498:2021 md. 11 atfı); s = μ_i·C_e·C_t·S_k, C_e = C_t = 1,0 varsayılan",
    "dogrulandi": False,
    "mu1": {"alpha<=30": 0.8, "30<alpha<60": "0,8·(60 − α)/30", "alpha>=60": 0.0},
    "Ce": {"ruzgara-acik": 0.8, "normal": 1.0, "korunakli": 1.2},
    "not": "Standart metni doğrudan görülmedi; ikincil kaynaklar tutarlı (orta-yüksek güven). Düz çatı: μ1 = 0,8.",
}


def kar_mu1(alpha_derece):
    """TS EN 1991-1-3 Tablo 5.2 μ1 (tek eğimli / düz çatı): α ≤ 30° → 0,8; 30–60° doğrusal; ≥ 60° → 0."""
    a = float(alpha_derece)
    if a <= 30.0:
        return 0.8
    if a >= 60.0:
        return 0.0
    return 0.8 * (60.0 - a) / 30.0


def kar_Sk(bolge, rakim):
    """Karakteristik zemin kar yükü S_k (kN/m²): Çizelge 3 bölge satırı ve rakım sütunu (ara rakımda üst satır);
    1000 m üstünde %10 / %15 artış. Dönüş (S_k, açıklama)."""
    b = int(bolge)
    if b not in TS498_KAR["Sk"]:
        raise KeyError(b)
    satir = TS498_KAR["Sk"][b]
    h = float(rakim)
    if h <= 1000.0:
        for r, v in zip(TS498_KAR["rakim"], satir):
            if h <= r:
                return v, f"bölge {b}, rakım ≤ {r} m sütunu"
    v = satir[-1]
    if h <= 1500.0:
        return v * TS498_KAR["ustu_1000"]["1500"], f"bölge {b}, 1000 m değeri {v} × 1,10 (1000 < h ≤ 1500 m)"
    return v * TS498_KAR["ustu_1000"]["ustu"], f"bölge {b}, 1000 m değeri {v} × 1,15 (h > 1500 m)"


TS498_RUZGAR = {
    "kaynak": "TS 498:2021 md. 14 Çizelge 4 (yüksekliğe bağlı hız ve emme basıncı; q = v²/1600), Şekil 1 ve Çizelge 5 (C = 1,2)",
    "dogrulandi": True,
    "q": [(8.0, 28, 0.5), (20.0, 36, 0.8), (100.0, 42, 1.1), (None, 46, 1.3)],   # (üst sınır m, v m/s, q kN/m²)
    "Cp": {"ruzgara-bakan-duvar": 0.8, "ruzgar-arkasi-duvar": -0.4, "duz-cati": -0.4, "yan-duvar": -0.4},
    "C": 1.2, "C_kule": 1.6,
    "not": "Kapalı binada rüzgâra dik yüzey: basınç +0,8q ve emme −0,4q → taşıyıcı sisteme toplam C = 1,2 (Çizelge 5 1.1.1); "
           "kule tipi (cephe yüksekliği ≥ 5 × genişlik) 1,6. Yüksekte ve sarp yamaçta q ≥ 1,1 kN/m² (md. 14.3). "
           "ÇYTHYE md. 5.3: karakteristik rüzgâr yükü ≥ 0,5 kN/m², v_b ≥ 28 m/s.",
    "kar_ruzgar": "TS 498:2021 md. 12.1: eğimi ≤ 45° çatıda S ve W birlikte: S/2 + W ya da S + W/2 (elverişsiz olanı)",
}


def ruzgar_q(h):
    """Zeminden h (m) yükseklikteki emme basıncı q (kN/m²), Çizelge 4 basamakları (8 / 20 / 100 m)."""
    h = float(h)
    for ust, _v, q in TS498_RUZGAR["q"]:
        if ust is None or h <= ust:
            return q
    return TS498_RUZGAR["q"][-1][2]  # pragma: no cover


# Ek 1 il/ilçe kar bölgeleri (OCR aktarımı, tek tek doğrulanmadı → dogrulandi False; bölge numarasını doğrudan girmek esastır)
TS498_KAR_BOLGE_KAYNAK = {"kaynak": "TS 498:2021 Ek 1 (s. 16–20), OCR aktarımı", "dogrulandi": False}
TS498_KAR_BOLGE_IL = {
    "Adana": {"Aladağ": 5, "Ceyhan": 3, "Çukurova": 3, "Feke": 5, "İmamoğlu": 3, "Karaisalı": 5, "Karataş": 3, "Kozan": 5, "Pozantı": 5, "Saimbeyli": 5, "Sarıçam": 3, "Seyhan": 3, "Tufanbeyli": 5, "Yumurtalık": 3, "Yüreğir": 3},
    "Adıyaman": {"Merkez": 2, "Besni": 2, "Çelikhan": 3, "Gerger": 2, "Gölbaşı": 2, "Kahta": 2, "Samsat": 2, "Sincik": 3, "Tut": 2},
    "Afyonkarahisar": {"Merkez": 6, "Başmakçı": 6, "Bayat": 6, "Bolvadin": 6, "Çay": 6, "Çobanlar": 6, "Dazkırı": 6, "Dinar": 6, "Emirdağ": 6, "Evciler": 6, "Hocalar": 6, "İhsaniye": 6, "İscehisar": 6, "Kızılören": 6, "Sandıklı": 6, "Sinanpaşa": 6, "Sultandağı": 6, "Şuhut": 6},
    "Ağrı": {"Merkez": 7, "Diyadin": 6, "Doğubayazıt": 6, "Eleşkirt": 7, "Hamur": 7, "Patnos": 6, "Taşlıçay": 6, "Tutak": 7},
    "Amasya": {"Merkez": 2, "Göynücek": 2, "Gümüşhacıköy": 2, "Hamamözü": 2, "Merzifon": 2, "Suluova": 2, "Taşova": 2},
    "Ankara": {"Akyurt": 3, "Altındağ": 3, "Ayaş": 3, "Bala": 4, "Beypazarı": 3, "Çamlıdere": 5, "Çankaya": 4, "Çubuk": 4, "Elmadağ": 5, "Etimesgut": 3, "Evren": 4, "Gölbaşı": 4, "Güdül": 4, "Haymana": 3, "Kahramankazan": 3, "Kalecik": 4, "Keçiören": 3, "Kızılcahamam": 5, "Mamak": 4, "Nallıhan": 3, "Polatlı": 3, "Pursaklar": 3, "Sincan": 3, "Şereflikoçhisar": 4, "Yenimahalle": 3},
    "Antalya": {"Akseki": 6, "Aksu": 6, "Alanya": 1, "Demre": 1, "Döşemealtı": 1, "Elmalı": 6, "Finike": 1, "Gazipaşa": 3, "Gündoğmuş": 6, "İbradı": 5, "Kaş": 1, "Kemer": 1, "Kepez": 1, "Konyaaltı": 1, "Korkuteli": 1, "Kumluca": 1, "Manavgat": 3, "Muratpaşa": 1, "Serik": 1},
    "Artvin": {"Merkez": 6, "Ardanuç": 7, "Arhavi": 2, "Borçka": 6, "Hopa": 2, "Kemalpaşa": 2, "Murgul": 6, "Şavşat": 8, "Yusufeli": 6},
    "Aydın": {"Bozdoğan": 1, "Buharkent": 1, "Çine": 1, "Didim": 1, "Efeler": 1, "Germencik": 1, "İncirliova": 1, "Karacasu": 1, "Karpuzlu": 1, "Koçarlı": 1, "Köşk": 1, "Kuşadası": 1, "Kuyucak": 1, "Nazilli": 1, "Söke": 1, "Sultanhisar": 1, "Yenipazar": 1},
    "Balıkesir": {"Altıeylül": 1, "Ayvalık": 1, "Balya": 1, "Bandırma": 1, "Bigadiç": 1, "Burhaniye": 1, "Dursunbey": 2, "Edremit": 1, "Erdek": 1, "Gömeç": 1, "Gönen": 1, "Havran": 1, "İvrindi": 1, "Karesi": 1, "Kepsut": 2, "Manyas": 1, "Marmara": 1, "Savaştepe": 1, "Sındırgı": 2, "Susurluk": 1},
    "Bilecik": {"Merkez": 2, "Bozüyük": 6, "Gölpazarı": 2, "İnhisar": 6, "Osmaneli": 2, "Pazaryeri": 2, "Söğüt": 6, "Yenipazar": 6},
    "Bingöl": {"Merkez": 6, "Adaklı": 6, "Genç": 7, "Karlıova": 7, "Kiğı": 6, "Solhan": 7, "Yayladere": 6, "Yedisu": 7},
    "Bitlis": {"Merkez": 8, "Adilcevaz": 7, "Ahlat": 7, "Güroymak": 8, "Hizan": 8, "Mutki": 8, "Tatvan": 7},
    "Bolu": {"Merkez": 7, "Dörtdivan": 7, "Gerede": 7, "Göynük": 7, "Kıbrıscık": 7, "Mengen": 7, "Mudurnu": 7, "Seben": 7, "Yeniçağa": 7},
    "Burdur": {"Merkez": 6, "Ağlasun": 6, "Altınyayla": 6, "Bucak": 6, "Çavdır": 6, "Çeltikçi": 6, "Gölhisar": 6, "Karamanlı": 6, "Kemer": 6, "Tefenni": 6, "Yeşilova": 6},
    "Bursa": {"Büyükorhan": 6, "Gemlik": 4, "Gürsu": 6, "Harmancık": 7, "İnegöl": 4, "İznik": 5, "Karacabey": 4, "Keles": 4, "Kestel": 4, "Mudanya": 4, "Mustafakemalpaşa": 4, "Nilüfer": 8, "Orhaneli": 8, "Orhangazi": 8, "Osmangazi": 9, "Yenişehir": 4, "Yıldırım": 9},
    "Çanakkale": {"Merkez": 1, "Ayvacık": 1, "Bayramiç": 1, "Biga": 1, "Bozcaada": 1, "Çan": 1, "Eceabat": 1, "Ezine": 1, "Gelibolu": 1, "Gökçeada": 1, "Lapseki": 1, "Yenice": 1},
    "Çankırı": {"Merkez": 4, "Atkaracalar": 4, "Bayramören": 4, "Çerkeş": 4, "Eldivan": 4, "Ilgaz": 5, "Kızılırmak": 4, "Korgun": 4, "Kurşunlu": 5, "Orta": 4, "Şabanözü": 4, "Yapraklı": 5},
    "Çorum": {"Merkez": 4, "Alaca": 5, "Bayat": 4, "Boğazkale": 4, "Dodurga": 4, "İskilip": 4, "Kargı": 4, "Laçin": 4, "Mecitözü": 4, "Oğuzlar": 4, "Ortaköy": 4, "Osmancık": 4, "Sungurlu": 4, "Uğurludağ": 4},
    "Denizli": {"Acıpayam": 6, "Babadağ": 6, "Baklan": 6, "Bekilli": 6, "Beyağaç": 2, "Bozkurt": 6, "Buldan": 6, "Çal": 6, "Çameli": 6, "Çardak": 2, "Çivril": 6, "Güney": 6, "Honaz": 6, "Kale": 2, "Merkezefendi": 6, "Pamukkale": 6, "Sarayköy": 6, "Serinhisar": 6, "Tavas": 6},
    "Diyarbakır": {"Bağlar": 2, "Bismil": 2, "Çermik": 4, "Çınar": 2, "Çüngüş": 5, "Dicle": 4, "Eğil": 5, "Ergani": 5, "Hani": 6, "Hazro": 6, "Kayapınar": 4, "Kocaköy": 6, "Kulp": 6, "Lice": 6, "Silvan": 5, "Sur": 4, "Yenişehir": 4},
    "Edirne": {"Merkez": 2, "Enez": 2, "Havsa": 2, "İpsala": 2, "Keşan": 2, "Lalapaşa": 2, "Meriç": 2, "Süloğlu": 2, "Uzunköprü": 2},
    "Elazığ": {"Merkez": 4, "Ağın": 5, "Alacakaya": 4, "Arıcak": 4, "Baskil": 3, "Karakoçan": 5, "Keban": 5, "Kovancılar": 5, "Maden": 5, "Palu": 4, "Sivrice": 4},
    "Erzincan": {"Merkez": 6, "Çayırlı": 7, "İliç": 5, "Kemah": 6, "Kemaliye": 6, "Otlukbeli": 7, "Refahiye": 5, "Tercan": 7, "Üzümlü": 6},
    "Erzurum": {"Aşkale": 7, "Aziziye": 8, "Çat": 8, "Hınıs": 8, "Horasan": 8, "İspir": 7, "Karaçoban": 8, "Karayazı": 8, "Köprüköy": 8, "Narman": 8, "Oltu": 8, "Olur": 8, "Palandöken": 8, "Pasinler": 8, "Pazaryolu": 7, "Şenkaya": 8, "Tekman": 8, "Tortum": 8, "Uzundere": 8, "Yakutiye": 8},
    "Eskişehir": {"Alpu": 5, "Beylikova": 5, "Çifteler": 6, "Günyüzü": 5, "Han": 6, "İnönü": 6, "Mahmudiye": 5, "Mihalgazi": 5, "Mihalıççık": 5, "Odunpazarı": 5, "Sarıcakaya": 5, "Seyitgazi": 6, "Sivrihisar": 5, "Tepebaşı": 5},
    "Gaziantep": {"Araban": 2, "İslahiye": 2, "Karkamış": 2, "Nizip": 2, "Nurdağı": 2, "Oğuzeli": 2, "Şahinbey": 2, "Şehitkamil": 2, "Yavuzeli": 2},
    "Giresun": {"Merkez": 2, "Alucra": 7, "Bulancak": 2, "Çamoluk": 6, "Çanakçı": 4, "Dereli": 5, "Doğankent": 5, "Espiye": 2, "Eynesil": 3, "Görele": 3, "Güce": 3, "Keşap": 2, "Piraziz": 3, "Şebinkarahisar": 7, "Tirebolu": 2, "Yağlıdere": 2},
    "Gümüşhane": {"Merkez": 6, "Kelkit": 6, "Köse": 6, "Kürtün": 5, "Şiran": 5, "Torul": 5},
    "Hakkari": {"Merkez": 9, "Çukurca": 9, "Derecik": 9, "Şemdinli": 9, "Yüksekova": 9},
    "Hatay": {"Altınözü": 2, "Antakya": 2, "Arsuz": 2, "Belen": 2, "Defne": 2, "Dörtyol": 2, "Erzin": 2, "Hassa": 2, "İskenderun": 2, "Kırıkhan": 2, "Kumlu": 2, "Payas": 2, "Reyhanlı": 2, "Samandağ": 3, "Yayladağı": 3},
    "Isparta": {"Merkez": 6, "Aksu": 6, "Atabey": 6, "Eğirdir": 6, "Gelendost": 6, "Gönen": 6, "Keçiborlu": 6, "Senirkent": 6, "Sütçüler": 6, "Şarkikaraağaç": 6, "Uluborlu": 6, "Yalvaç": 6, "Yenişarbademli": 6},
    "Mersin": {"Akdeniz": 2, "Anamur": 3, "Aydıncık": 3, "Bozyazı": 3, "Çamlıyayla": 6, "Erdemli": 3, "Gülnar": 6, "Mezitli": 2, "Mut": 6, "Silifke": 3, "Tarsus": 2, "Toroslar": 2, "Yenişehir": 2},
    "İstanbul": {"Adalar": 1, "Arnavutköy": 1, "Ataşehir": 1, "Avcılar": 1, "Bağcılar": 1, "Bahçelievler": 1, "Bakırköy": 1, "Başakşehir": 1, "Bayrampaşa": 1, "Beşiktaş": 1, "Beykoz": 1, "Beylikdüzü": 1, "Beyoğlu": 1, "Büyükçekmece": 1, "Çatalca": 1, "Çekmeköy": 1, "Esenler": 1, "Esenyurt": 1, "Eyüpsultan": 1, "Fatih": 1, "Gaziosmanpaşa": 1, "Güngören": 1, "Kadıköy": 1, "Kağıthane": 1, "Kartal": 1, "Küçükçekmece": 1, "Maltepe": 1, "Pendik": 1, "Sancaktepe": 1, "Sarıyer": 1, "Silivri": 1, "Sultanbeyli": 1, "Sultangazi": 1, "Şile": 1, "Şişli": 1, "Tuzla": 1, "Ümraniye": 1, "Üsküdar": 1, "Zeytinburnu": 1},
    "İzmir": {"Aliağa": 1, "Balçova": 1, "Bayındır": 1, "Bayraklı": 1, "Bergama": 1, "Beydağ": 1, "Bornova": 1, "Buca": 1, "Çeşme": 1, "Çiğli": 1, "Dikili": 1, "Foça": 1, "Gaziemir": 1, "Güzelbahçe": 1, "Karabağlar": 1, "Karaburun": 1, "Karşıyaka": 1, "Kemalpaşa": 1, "Kınık": 1, "Kiraz": 1, "Konak": 1, "Menderes": 1, "Menemen": 1, "Narlıdere": 1, "Ödemiş": 1, "Seferihisar": 1, "Selçuk": 1, "Tire": 1, "Torbalı": 1, "Urla": 1},
    "Kars": {"Merkez": 9, "Akyaka": 8, "Arpaçay": 9, "Digor": 8, "Kağızman": 9, "Sarıkamış": 9, "Selim": 9, "Susuz": 9},
    "Kastamonu": {"Merkez": 4, "Abana": 3, "Ağlı": 5, "Araç": 4, "Azdavay": 4, "Bozkurt": 3, "Cide": 3, "Çatalzeytin": 3, "Daday": 5, "Devrekani": 4, "Doğanyurt": 2, "Hanönü": 4, "İhsangazi": 4, "İnebolu": 3, "Küre": 5, "Pınarbaşı": 3, "Seydiler": 5, "Şenpazar": 3, "Taşköprü": 4, "Tosya": 4},
    "Kayseri": {"Akkışla": 7, "Bünyan": 7, "Develi": 7, "Felahiye": 5, "Hacılar": 6, "İncesu": 5, "Kocasinan": 5, "Melikgazi": 5, "Özvatan": 5, "Pınarbaşı": 8, "Sarıoğlan": 6, "Sarız": 8, "Talas": 7, "Tomarza": 8, "Yahyalı": 6, "Yeşilhisar": 5},
    "Kırklareli": {"Merkez": 1, "Babaeski": 1, "Demirköy": 1, "Kofçaz": 1, "Lüleburgaz": 1, "Pehlivanköy": 1, "Pınarhisar": 1, "Vize": 1},
    "Kırşehir": {"Merkez": 4, "Akçakent": 4, "Akpınar": 4, "Boztepe": 4, "Çiçekdağı": 4, "Kaman": 5, "Mucur": 4},
    "Kocaeli": {"Başiskele": 1, "Çayırova": 1, "Darıca": 1, "Derince": 1, "Dilovası": 1, "Gebze": 1, "Gölcük": 1, "İzmit": 1, "Kandıra": 1, "Karamürsel": 1, "Kartepe": 1, "Körfez": 1},
    "Konya": {"Ahırlı": 7, "Akören": 7, "Akşehir": 7, "Altınekin": 3, "Beyşehir": 7, "Bozkır": 7, "Cihanbeyli": 3, "Çeltik": 4, "Çumra": 7, "Derbent": 7, "Derebucak": 7, "Doğanhisar": 7, "Emirgazi": 7, "Ereğli": 7, "Güneysınır": 7, "Hadim": 7, "Halkapınar": 7, "Hüyük": 7, "Ilgın": 7, "Kadınhanı": 7, "Karapınar": 7, "Karatay": 7, "Kulu": 4, "Meram": 7, "Sarayönü": 7, "Selçuklu": 7, "Seydişehir": 7, "Taşkent": 7, "Tuzlukçu": 7, "Yalıhüyük": 7, "Yunak": 4},
    "Kütahya": {"Merkez": 6, "Altıntaş": 6, "Aslanapa": 6, "Çavdarhisar": 6, "Domaniç": 6, "Dumlupınar": 6, "Emet": 6, "Gediz": 6, "Hisarcık": 6, "Pazarlar": 6, "Simav": 6, "Şaphane": 6, "Tavşanlı": 6},
    "Malatya": {"Akçadağ": 4, "Arapgir": 7, "Arguvan": 6, "Battalgazi": 5, "Darende": 6, "Doğanşehir": 4, "Doğanyol": 3, "Hekimhan": 5, "Kale": 4, "Kuluncak": 5, "Pütürge": 3, "Yazıhan": 4, "Yeşilyurt": 3},
    "Manisa": {"Ahmetli": 1, "Akhisar": 1, "Alaşehir": 6, "Demirci": 6, "Gölmarmara": 1, "Gördes": 1, "Kırkağaç": 1, "Köprübaşı": 1, "Kula": 6, "Salihli": 1, "Sarıgöl": 6, "Saruhanlı": 1, "Selendi": 6, "Soma": 1, "Şehzadeler": 1, "Turgutlu": 1, "Yunusemre": 1},
    "Kahramanmaraş": {"Afşin": 7, "Andırın": 4, "Çağlayancerit": 5, "Dulkadiroğlu": 3, "Ekinözü": 7, "Elbistan": 7, "Göksun": 6, "Nurhak": 6, "Onikişubat": 1, "Pazarcık": 2, "Türkoğlu": 1},
    "Mardin": {"Artuklu": 2, "Dargeçit": 2, "Derik": 2, "Kızıltepe": 1, "Mazıdağı": 2, "Midyat": 2, "Nusaybin": 1, "Ömerli": 2, "Savur": 2, "Yeşilli": 2},
    "Muğla": {"Bodrum": 1, "Dalaman": 1, "Datça": 1, "Fethiye": 1, "Kavaklıdere": 1, "Köyceğiz": 1, "Marmaris": 1, "Menteşe": 1, "Milas": 1, "Ortaca": 1, "Seydikemer": 1, "Ula": 1, "Yatağan": 1},
    "Muş": {"Merkez": 8, "Bulanık": 8, "Hasköy": 8, "Korkut": 8, "Malazgirt": 9, "Varto": 8},
    "Nevşehir": {"Merkez": 5, "Acıgöl": 5, "Avanos": 5, "Derinkuyu": 5, "Gülşehir": 5, "Hacıbektaş": 5, "Kozaklı": 5, "Ürgüp": 5},
    "Niğde": {"Merkez": 5, "Altunhisar": 6, "Bor": 6, "Çamardı": 6, "Çiftlik": 6, "Ulukışla": 6},
    "Ordu": {"Akkuş": 3, "Altınordu": 3, "Aybastı": 4, "Çamaş": 1, "Çatalpınar": 2, "Çaybaşı": 2, "Fatsa": 1, "Gölköy": 4, "Gülyalı": 2, "Gürgentepe": 3, "İkizce": 2, "Kabadüz": 3, "Kabataş": 3, "Korgan": 3, "Kumru": 2, "Mesudiye": 4, "Perşembe": 1, "Ulubey": 2, "Ünye": 1},
    "Rize": {"Merkez": 1, "Ardeşen": 3, "Çamlıhemşin": 4, "Çayeli": 1, "Derepazarı": 1, "Fındıklı": 2, "Güneysu": 1, "Hemşin": 1, "İkizdere": 4, "İyidere": 1, "Kalkandere": 1, "Pazar": 1},
    "Sakarya": {"Adapazarı": 1, "Akyazı": 1, "Arifiye": 1, "Erenler": 1, "Ferizli": 1, "Geyve": 1, "Hendek": 1, "Karapürçek": 1, "Karasu": 1, "Kaynarca": 1, "Kocaali": 1, "Pamukova": 1, "Sapanca": 2, "Serdivan": 2, "Söğütlü": 1, "Taraklı": 1},
    "Samsun": {"Alaçam": 2, "Asarcık": 2, "Atakum": 2, "Ayvacık": 2, "Bafra": 2, "Canik": 2, "Çarşamba": 1, "Havza": 2, "İlkadım": 2, "Kavak": 2, "Ladik": 2, "19 Mayıs": 1, "Salıpazarı": 2, "Tekkeköy": 1, "Terme": 1, "Vezirköprü": 2, "Yakakent": 1},
    "Siirt": {"Merkez": 4, "Baykan": 5, "Eruh": 6, "Kurtalan": 4, "Pervari": 7, "Şirvan": 7, "Tillo": 5},
    "Sinop": {"Merkez": 1, "Ayancık": 2, "Boyabat": 3, "Dikmen": 3, "Durağan": 3, "Erfelek": 1, "Gerze": 1, "Saraydüzü": 3, "Türkeli": 2},
    "Sivas": {"Merkez": 7, "Akıncılar": 6, "Altınyayla": 7, "Divriği": 6, "Doğanşar": 6, "Gemerek": 6, "Gölova": 6, "Gürün": 6, "Hafik": 6, "İmranlı": 6, "Kangal": 8, "Koyulhisar": 6, "Suşehri": 6, "Şarkışla": 7, "Ulaş": 7, "Yıldızeli": 6, "Zara": 8},
    "Tekirdağ": {"Çerkezköy": 1, "Çorlu": 1, "Ergene": 1, "Hayrabolu": 2, "Kapaklı": 1, "Malkara": 2, "Marmaraereğlisi": 1, "Muratlı": 1, "Saray": 1, "Süleymanpaşa": 1, "Şarköy": 1},
    "Tokat": {"Merkez": 3, "Almus": 4, "Artova": 3, "Başçiftlik": 4, "Erbaa": 3, "Niksar": 4, "Pazar": 3, "Reşadiye": 5, "Sulusaray": 3, "Turhal": 3, "Yeşilyurt": 3, "Zile": 3},
    "Trabzon": {"Akçaabat": 2, "Araklı": 1, "Arsin": 2, "Beşikdüzü": 1, "Çarşıbaşı": 1, "Çaykara": 1, "Dernekpazarı": 1, "Düzköy": 4, "Hayrat": 4, "Köprübaşı": 4, "Maçka": 4, "Of": 1, "Ortahisar": 1, "Sürmene": 4, "Şalpazarı": 4, "Tonya": 4, "Vakfıkebir": 1, "Yomra": 1},
    "Tunceli": {"Merkez": 6, "Çemişgezek": 5, "Hozat": 5, "Mazgirt": 5, "Nazımiye": 6, "Ovacık": 6, "Pertek": 5, "Pülümür": 7},
    "Şanlıurfa": {"Akçakale": 1, "Birecik": 2, "Bozova": 2, "Ceylanpınar": 1, "Eyyübiye": 1, "Halfeti": 2, "Haliliye": 2, "Harran": 1, "Hilvan": 2, "Karaköprü": 1, "Siverek": 2, "Suruç": 1, "Viranşehir": 1},
    "Uşak": {"Merkez": 6, "Banaz": 6, "Eşme": 6, "Karahallı": 6, "Sivaslı": 6, "Ulubey": 6},
    "Van": {"Bahçesaray": 8, "Başkale": 9, "Çaldıran": 8, "Çatak": 8, "Edremit": 8, "Erciş": 8, "Gevaş": 8, "Gürpınar": 8, "İpekyolu": 8, "Muradiye": 8, "Özalp": 8, "Saray": 9, "Tuşba": 8},
    "Yozgat": {"Merkez": 6, "Akdağmadeni": 5, "Aydıncık": 5, "Boğazlıyan": 5, "Çandır": 5, "Çayıralan": 6, "Çekerek": 4, "Kadışehri": 4, "Saraykent": 5, "Sarıkaya": 5, "Sorgun": 6, "Şefaatli": 5, "Yenifakılı": 5, "Yerköy": 5},
    "Zonguldak": {"Merkez": 1, "Alaplı": 1, "Çaycuma": 2, "Devrek": 2, "Ereğli": 1, "Gökçebey": 2, "Kilimli": 1, "Kozlu": 1},
    "Aksaray": {"Merkez": 6, "Ağaçören": 5, "Eskil": 6, "Gülağaç": 5, "Güzelyurt": 5, "Ortaköy": 5, "Sarıyahşi": 5, "Sultanhanı": 5},
    "Bayburt": {"Merkez": 8, "Aydıntepe": 7, "Demirözü": 7},
    "Karaman": {"Merkez": 7, "Ayrancı": 7, "Başyayla": 7, "Ermenek": 7, "Kazımkarabekir": 7, "Sarıveliler": 7},
    "Kırıkkale": {"Merkez": 4, "Bahşılı": 4, "Balışeyh": 4, "Çelebi": 4, "Delice": 4, "Karakeçili": 4, "Keskin": 4, "Sulakyurt": 4, "Yahşihan": 4},
    "Batman": {"Merkez": 2, "Beşiri": 2, "Gercüş": 2, "Hasankeyf": 2, "Kozluk": 2, "Sason": 2},
    "Şırnak": {"Merkez": 7, "Beytüşşebap": 8, "Cizre": 6, "Güçlükonak": 5, "İdil": 5, "Silopi": 5, "Uludere": 8},
    "Bartın": {"Merkez": 2, "Amasra": 2, "Kurucaşile": 2, "Ulus": 2},
    "Ardahan": {"Merkez": 9, "Çıldır": 8, "Damal": 8, "Göle": 8, "Hanak": 9, "Posof": 8},
    "Iğdır": {"Merkez": 5, "Aralık": 6, "Karakoyunlu": 6, "Tuzluca": 7},
    "Yalova": {"Merkez": 2, "Altınova": 2, "Armutlu": 2, "Çınarcık": 2, "Çiftlikköy": 2, "Termal": 2},
    "Karabük": {"Merkez": 2, "Eflani": 2, "Eskipazar": 2, "Ovacık": 2, "Safranbolu": 2, "Yenice": 2},
    "Kilis": {"Merkez": 1, "Elbeyli": 1, "Musabeyli": 1, "Polateli": 1},
    "Osmaniye": {"Merkez": 3, "Bahçe": 2, "Düziçi": 2, "Hasanbeyli": 4, "Kadirli": 4, "Sumbas": 4, "Toprakkale": 4},
    "Düzce": {"Merkez": 2, "Akçakoca": 2, "Cumayeri": 2, "Çilimli": 2, "Gölyaka": 2, "Gümüşova": 2, "Kaynaşlı": 2, "Yığılca": 2},
}


def kar_bolgesi(il, ilce=None):
    """Ek 1'den bölge: il (ve ilçe) adıyla; ilçe verilmezse 'Merkez' ya da ilin en sık bölgesi. Bulunamazsa None."""
    il_ad = str(il).strip()
    ilceler = TS498_KAR_BOLGE_IL.get(il_ad)
    if ilceler is None:
        kucuk = {k.lower(): k for k in TS498_KAR_BOLGE_IL}
        ilceler = TS498_KAR_BOLGE_IL.get(kucuk.get(il_ad.lower(), ""))
    if not ilceler:
        return None
    if ilce:
        kucuk = {k.lower(): v for k, v in ilceler.items()}
        return kucuk.get(str(ilce).strip().lower())
    if "Merkez" in ilceler:
        return ilceler["Merkez"]
    sayac = {}
    for v in ilceler.values():
        sayac[v] = sayac.get(v, 0) + 1
    return max(sayac, key=lambda b: (sayac[b], b))


# ============================================================================
# Doğrulama listesi
# ============================================================================
def dogrulanmamis_kayitlar():
    """``dogrulandi: False`` olan kayıtların "TABLO.anahtar" listesi (köprü yanıtındaki uyarılar için)."""
    liste = []
    tablolar = (("BETONLAR", BETONLAR), ("DONATILAR", DONATILAR), ("CELIKLER", CELIKLER), ("PROFILLER", PROFILLER),
                ("TS498_HAREKETLI", TS498_HAREKETLI), ("TS498_BIRIM_AGIRLIK", TS498_BIRIM_AGIRLIK),
                ("KAPLAMALAR", KAPLAMALAR), ("DUVARLAR", DUVARLAR), ("TBDY_TASIYICI", TBDY_TASIYICI))
    for ad, tablo in tablolar:
        for anahtar, kayit in tablo.items():
            if not kayit.get("dogrulandi", False):
                liste.append(f"{ad}.{anahtar}")
    for ad, tablo in (("TS498_AZALTMA", TS498_AZALTMA), ("TBDY_KUTLE_KATILIM", TBDY_KUTLE_KATILIM),
                      ("TBDY_FS", TBDY_FS), ("TBDY_F1", TBDY_F1), ("TBDY_BKS_I", TBDY_BKS_I), ("TBDY_DTS", TBDY_DTS),
                      ("TBDY_BYS", TBDY_BYS), ("TBDY_CT", TBDY_CT), ("TBDY_KUTLE_KATILIM_KULLANIM", TBDY_KUTLE_KATILIM_KULLANIM),
                      ("TBDY_UYGULANABILIRLIK", TBDY_UYGULANABILIRLIK), ("TBDY_ETKIN_RIJITLIK", TBDY_ETKIN_RIJITLIK),
                      ("TBDY_DEPREM_KURALLAR", TBDY_DEPREM_KURALLAR), ("TS498_KAR", TS498_KAR), ("EN1991_KAR_SEKIL", EN1991_KAR_SEKIL),
                      ("TS498_RUZGAR", TS498_RUZGAR), ("TS498_KAR_BOLGE_KAYNAK", TS498_KAR_BOLGE_KAYNAK)):
        if not tablo.get("dogrulandi", False):
            liste.append(ad)
    for kume, kayit in KOMBINASYONLAR.items():
        for satir in kayit["liste"]:
            if not satir.get("dogrulandi", False):
                liste.append(f"KOMBINASYONLAR.{kume}.{satir['ad']}")
    return liste


def kopya(tablo):
    """Tablonun bağımsız kopyası (çağıran değiştirebilsin)."""
    return copy.deepcopy(tablo)
