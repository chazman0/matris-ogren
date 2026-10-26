# -*- coding: utf-8 -*-
"""Yapı modülü kütüphaneleri (salt veri): malzeme, kesit, TS 498:2021 yükleri, duvar/kaplama takımları, hareketli
yük azaltması ve yük birleşimleri (TS 500, ÇYTHYE, TBDY 2018).

Bu dosyada hesap yoktur; ``yapi.py`` bu tabloları okur. Her kayıt ``kaynak`` (yönetmelik maddesi) ve ``dogrulandi``
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
            _komb("G+0.7E", {"G": 1.0, "EH": 0.7}, "deprem", "ÇYTHYE 5.3.2 (5b) → TBDY Denk. (9.1b)"),
            _komb("G+0.75Q+0.75(Qr|S|R)+0.75W", {"G": 1.0, "Q": 0.75, "S": 0.75, "W": 0.75}, "dayanim", "ÇYTHYE 5.3.2 (6a)"),
            _komb("G+0.75Q+0.75S+0.75(0.7E)", {"G": 1.0, "Q": 0.75, "S": 0.75, "EH": 0.525}, "deprem",
                  "ÇYTHYE 5.3.2 (6b) → TBDY Denk. (9.1a)"),
            _komb("0.6G+W", {"G": 0.6, "W": 1.0}, "dayanim", "ÇYTHYE 5.3.2 (7)"),
            _komb("0.6G+0.7E", {"G": 0.6, "EH": 0.7}, "deprem", "ÇYTHYE 5.3.2 (8) → TBDY Denk. (9.1c): 0,6G + 0,75H ± 0,7Ed"),
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
# Doğrulama listesi
# ============================================================================
def dogrulanmamis_kayitlar():
    """``dogrulandi: False`` olan kayıtların "TABLO.anahtar" listesi (köprü yanıtındaki uyarılar için)."""
    liste = []
    tablolar = (("BETONLAR", BETONLAR), ("DONATILAR", DONATILAR), ("CELIKLER", CELIKLER), ("PROFILLER", PROFILLER),
                ("TS498_HAREKETLI", TS498_HAREKETLI), ("TS498_BIRIM_AGIRLIK", TS498_BIRIM_AGIRLIK),
                ("KAPLAMALAR", KAPLAMALAR), ("DUVARLAR", DUVARLAR))
    for ad, tablo in tablolar:
        for anahtar, kayit in tablo.items():
            if not kayit.get("dogrulandi", False):
                liste.append(f"{ad}.{anahtar}")
    for ad, tablo in (("TS498_AZALTMA", TS498_AZALTMA), ("TBDY_KUTLE_KATILIM", TBDY_KUTLE_KATILIM)):
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
