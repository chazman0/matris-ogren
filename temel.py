# -*- coding: utf-8 -*-
"""Temel modelleme ve tasarım yardımcıları (Matris Öğren, bina modülü; tasarım belgesi §13).

Tekil temel (kolon başına B × L, mesnet modeli ankastre / mafsal / elastik) ``yapi.py`` içindedir ve değişmez. Bu modül
iki sürekli temel tipini ``cerceve3b`` ağına ekler ve tasarlar:

* **Mütemadi (sürekli) temel** — seçilen aks çizgileri boyunca temel seviyesinde (kot_0) ters T kesitli temel kirişleri
  (tabla + gövde; dikdörtgen özel hal), ``ag`` aralığında bölünmüş; kolon tabanları kiriş düğümlerine bağlanır (sabit mesnet
  yok). Zemin: ayrık Winkler yayları ``k_z = k0·B·l_etki`` (xy'de kesişim tabla alanı bir kez sayılır).
* **Radye** — plak alanı = aks dış zarfı + taşma; iki doğrultulu ızgara (grillage): her çubuk genişliği şerit genişliği
  (kenarda yarım), ``I = b·h³/12``, ``J ≈ b·h³/6``; düğüm yayları ``k_z = k0·A_etki``; isteğe bağlı aks kirişleri.

Yatay kararlılık: temel düğümlerinde bina X ve Y ötelemeleri tutulu (varsayılan, ``yatay: "tutulu"``) ya da yatay yaylar
(``yatay: "yay"``, ``kh_oran``·k_z; oran geoteknik rapordan). Dönmeler serbesttir (yay ve kiriş/şerit rijitliği taşır).

Değerler ve madde numaraları araştırma dosyasından (``arastirma_kar_ruzgar_temel.json``: TBDY 2018 Bölüm 16, TS 500
md. 8.1.3, 8.3.1, 10.1–10.4) ve TS 500 metninden alınmıştır; bkz. ``KAYNAK``.

Kullanım (``yapi.bina_coz`` çağırır)::

    temel.oku(B, t)                     # bina.temeller → doğrulanmış yapılandırma (öğretici hatalar)
    info = temel.ag_kur(B, dugum, ...)  # ağ: düğümler, elemanlar, yaylar, yatay mesnetler, öz ağırlık (G)
    T = temel.sonuclar(B, ag, paket, kombinasyonlar)   # veri.temel (taban basıncı, oturma, zemin ve kesit tahkikleri)
    temel.anlatim(anl, no, B, ag, T)    # "Temel ve zemin" anlatım adımı

Saf yardımcılar (testlenir): ``ters_t_kesit``, ``zimbalama``, ``plak_egilme``, ``kiris_winkler_modeli``.
"""
from __future__ import annotations

import importlib
import math
from types import SimpleNamespace

import matris_ogren as mo

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

MatrisHatasi = mo.MatrisHatasi
__version__ = "0.1.0"

# ============================================================================
# Yönetmelik değerleri (araştırma: arastirma_kar_ruzgar_temel.json; TS 500 metni)
# ============================================================================
GAMMA_RV = 1.4            # TBDY 2018 Tablo 16.2 (md. 16.8.2): temel taşıma gücü dayanım katsayısı γ_Rv; q_t = q_k/γ_Rv (Denk. 16.7)
ORTU = 0.05               # TS 500 md. 10.1: temellerde beton örtüsü ≥ 50 mm
PAS_EK = 0.02             # donatı ağırlık merkezi için örtüye eklenen pay (çubuk yarıçapı + iki doğrultu ortalaması)
PAS = ORTU + PAS_EK       # donatı ağırlık merkezi – dış yüz (m); d = h − 0,07 (iki doğrultu ortalaması, TS 500 md. 10.0)
RHO_MIN = 0.002           # TS 500 md. 10.3.3 (temelde her doğrultuda ≥ 0,002) ve md. 10.4.3 → md. 11.2.2 (plak, S420/B500: 0,002)
ARALIK_EN_FAZLA = 0.20    # TS 500 md. 11.2.2: plak asal donatı aralığı ≤ 1,5h ve ≤ 200 mm (md. 10.3.3 temel: ≤ 250 mm)
H_RADYE_MIN = 0.30        # TS 500 md. 10.4.2: kirişsiz plak (radye) kalınlığı ≥ 300 mm
H_PLAK_MIN = 0.20         # TS 500 md. 10.4.2: kirişli sürekli temelde plak (tabla) kalınlığı ≥ 200 mm
KIRIS_ORAN = 10.0         # TS 500 md. 10.4.2: kirişli sürekli temelde kiriş yüksekliği (plak dahil) ≥ serbest açıklık/10
GS_KLASIK = 3.0           # araştırma (TBDY 16 notu): q_em = q_k/GS, klasik GS ≈ 3 (statik) — q_k verilmezse VARSAYIM
CUBUKLAR = (12, 14, 16, 18, 20, 22, 24, 26)    # mm (tasarim.CUBUK_CAPLARI ile aynı)
EN_KUCUK_AG = 0.10        # m; daha sık ağ tarayıcıda çözülemez

KAYNAK = {
    "emniyet": "TS 500 md. 10.1 (zemin kontrolünde yük katsayıları 1,0; σ ≤ q_em, geoteknik rapor)",
    "tbdy": "TBDY 2018 md. 16.8.3, Denk. 16.6–16.7: q_o ≤ q_t = q_k/γ_Rv, γ_Rv = 1,4 (Tablo 16.2); q_o katsayılı yüklerle (16.8.2)",
    "winkler": "TS 500 md. 10.4.2: zemin yeterli sayıda birbirinden bağımsız yayla temsil edilebilir; p = k_s·w (yatak katsayısı)",
    "surekli_h": "TS 500 md. 10.4.2: kirişli sürekli temelde kiriş yüksekliği (plak dahil) ≥ serbest açıklık/10",
    "plak_h": "TS 500 md. 10.4.2: kirişli sürekli temelde plak kalınlığı ≥ 200 mm",
    "radye_h": "TS 500 md. 10.4.2: kirişsiz plak (radye) kalınlığı ≥ 300 mm",
    "vcr": "TS 500 md. 8.1.3, Denk. 8.1: V_cr = 0,65 f_ctd b d (N = 0)",
    "vcr_kiris": "TS 500 md. 10.4.2: kolon yüzünde V_d ≤ V_cr olabildiğince sağlanmalı",
    "zimbalama": "TS 500 md. 8.3.1, Denk. 8.20–8.21, 8.24: V_pd ≤ V_pr = γ f_ctd u_p d; u_p kolon yüzünden d/2; V_pd = N_d − F_a "
                 "(F_a: çevre içindeki zemin gerilmeleri); radyede donatı katkısı yok (md. 10.4.2)",
    "rho_min": "TS 500 md. 10.3.3 ve md. 10.4.3 → 11.2.2: ρ ≥ 0,002 (her doğrultu, b·d)",
    "aralik": "TS 500 md. 11.2.2: plak asal donatı aralığı ≤ 200 mm (temelde md. 10.3.3 ≤ 250 mm)",
    "basinc_donatisi": "TS 500 md. 10.4.3: eğilmede basınç bölgesinde çekme donatısının ≥ 1/3'ü kadar basınç donatısı",
    "ortu": "TS 500 md. 10.1: temellerde beton örtüsü ≥ 50 mm",
    "kiris": "TS 500 md. 7 (eğilme, tasarim.kiris_egilme) ve md. 8.1 (kesme, tasarim.kiris_kesme)",
}

_TIP_TAKMA = {"tekil": "tekil", "surekli": "surekli", "sürekli": "surekli", "mutemadi": "surekli", "mütemadi": "surekli",
              "radye": "radye"}
_TUR_AD = {"temel-kirisi": "temel kirişi", "radye-serit": "radye şeridi"}


# ============================================================================
# Küçük yardımcılar
# ============================================================================
def _sayi(v, ad, pozitif=False, sifir_olur=True):
    if isinstance(v, bool) or v is None or (isinstance(v, str) and not v.strip()):
        raise MatrisHatasi(f"{ad} verilmedi (sayı bekleniyor).")
    try:
        x = float(v.replace(",", ".")) if isinstance(v, str) else float(v)
    except (TypeError, ValueError, AttributeError):
        raise MatrisHatasi(f"{ad} sayı olmalı (girilen: {v!r}).") from None
    if x != x or x in (float("inf"), float("-inf")):
        raise MatrisHatasi(f"{ad} sonlu bir sayı olmalı (girilen: {v!r}).")
    if pozitif and (x < 0 or (x == 0 and not sifir_olur)):
        raise MatrisHatasi(f"{ad} pozitif olmalı (girilen: {v!r}).")
    return x


def _f(x, b=2):
    s = f"{float(x):.{b}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _r(x, n=6):
    x = float(x)
    if x == 0.0 or x != x:
        return 0.0
    return float(f"{x:.{n}g}")


def _tasarim():
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def _se():
    return importlib.import_module("sonlu_eleman")


# ============================================================================
# Kesit: ters T (tabla altta + gövde) — dikdörtgen özel hal
# ============================================================================
def _beta(a, c):
    """Dikdörtgen burulma katsayısı β (J ≈ β·a·c³, a ≥ c): β = 1/3 − 0,21(c/a)(1 − c⁴/(12a⁴)) (yapi.py ile aynı)."""
    a, c = max(a, c), min(a, c)
    if c <= 0:
        return 0.0
    return 1.0 / 3.0 - 0.21 * (c / a) * (1.0 - c ** 4 / (12.0 * a ** 4))


def ters_t_kesit(B, h_tabla, b_govde, h_govde):
    """Ters T kesit (tabla B × h_tabla altta, gövde b_govde × (h_govde − h_tabla) üstte; h_govde TOPLAM yükseklik):
    A, y_c (alttan ağırlık merkezi), I_guclu (yatay eksen; düşey düzlemde eğilme, motor Iz), I_zayif (düşey eksen, motor Iy),
    J ≈ Σ β·a·c³ (iki dikdörtgen, açık kesit yaklaşımı). b_govde = B ya da h_tabla = 0 → dikdörtgen B × h_govde (ya da
    b_govde × h_govde)."""
    B, t, b, H = float(B), float(h_tabla), float(b_govde), float(h_govde)
    if B <= 0 or b <= 0 or H <= 0:
        raise MatrisHatasi("Ters T kesit: B, b_govde ve h_govde pozitif olmalı.")
    if t < 0 or t > H + 1e-12:
        raise MatrisHatasi(f"Ters T kesit: h_tabla = {t} m, 0 ile h_govde = {H} m arasında olmalı (h_govde tabla dahil toplam yükseklik).")
    if b > B + 1e-12:
        raise MatrisHatasi(f"Ters T kesit: gövde genişliği b_govde = {b} m tabla genişliği B = {B} m'den büyük olamaz.")
    dikdortgen = t <= 1e-12 or abs(b - B) <= 1e-12 or abs(t - H) <= 1e-12
    if dikdortgen:
        gen = B if (abs(b - B) <= 1e-12 or abs(t - H) <= 1e-12) else b
        A = gen * H
        return {"A": A, "y_c": H / 2.0, "I_guclu": gen * H ** 3 / 12.0, "I_zayif": H * gen ** 3 / 12.0,
                "J": _beta(gen, H) * max(gen, H) * min(gen, H) ** 3, "dikdortgen": True, "B": gen, "h_tabla": 0.0,
                "b_govde": gen, "h_govde": H}
    hw = H - t
    A1, A2 = B * t, b * hw
    A = A1 + A2
    y1, y2 = t / 2.0, t + hw / 2.0
    yc = (A1 * y1 + A2 * y2) / A
    I = B * t ** 3 / 12.0 + A1 * (yc - y1) ** 2 + b * hw ** 3 / 12.0 + A2 * (y2 - yc) ** 2
    Iz = t * B ** 3 / 12.0 + hw * b ** 3 / 12.0
    J = _beta(B, t) * max(B, t) * min(B, t) ** 3 + _beta(b, hw) * max(b, hw) * min(b, hw) ** 3
    return {"A": A, "y_c": yc, "I_guclu": I, "I_zayif": Iz, "J": J, "dikdortgen": False, "B": B, "h_tabla": t,
            "b_govde": b, "h_govde": H}


# ============================================================================
# Okuma ve doğrulama
# ============================================================================
def tip_oku(v):
    """temeller.tip → 'tekil' | 'surekli' | 'radye' (mütemadi/sürekli eş anlamlı)."""
    s = str(v or "tekil").strip().lower()
    if s not in _TIP_TAKMA:
        raise MatrisHatasi(f"temeller.tip {v!r} tanımsız; 'tekil' (kolon başına B × L), 'surekli' (mütemadi: aks boyunca temel "
                           "kirişi) ya da 'radye' (bütün planı kaplayan plak) olmalı.")
    return _TIP_TAKMA[s]


def _malzeme_sec(B, t):
    """Temel betonu ve donatısı: temeller.malzeme / temeller.donati (B.malzemeler anahtarı) ya da ilk beton/donatı kaydı;
    çelik binada beton yoksa kütüphaneden C30/37 (varsayım)."""
    import yapi_veri as yv
    mad = t.get("malzeme")
    beton = None
    if mad not in (None, ""):
        mad = str(mad).strip()
        if mad not in B.malzemeler or B.malzemeler[mad]["tur"] != "beton":
            betonlar = [a for a, m in B.malzemeler.items() if m["tur"] == "beton"]
            raise MatrisHatasi(f"temeller.malzeme {mad!r} 'malzemeler' sözlüğünde beton değil. Tanımlı betonlar: {', '.join(betonlar) or '(yok)'}.")
        beton = B.malzemeler[mad]
    else:
        for c in sorted(B.kolonlar, key=lambda c: c["kat"]):
            m = B.malzemeler[c["malzeme"]]
            if m["tur"] == "beton":
                beton = m
                break
        if beton is None:
            beton = next((m for m in B.malzemeler.values() if m["tur"] == "beton"), None)
    varsayim = []
    if beton is None:
        kart = yv.BETONLAR["C30/37"]
        E = kart["Ec"] * 1000.0
        beton = {"ad": "C30/37", "kutuphane": "C30/37", "tur": "beton", "E": E, "G": kart["G_oran"] * E, "gamma": kart["gamma"],
                 "fck": kart["fck"], "nu": kart["nu"]}
        varsayim.append("Binada beton malzeme yok; temel betonu kütüphaneden C30/37 alındı (temeller.malzeme ile değiştirin).")
    don = t.get("donati")
    if don not in (None, ""):
        don = str(don).strip()
        if don in B.malzemeler and B.malzemeler[don]["tur"] == "donati":
            donati = B.malzemeler[don]["kutuphane"]
        elif don in yv.DONATILAR:
            donati = don
        else:
            raise MatrisHatasi(f"temeller.donati {don!r} tanımsız; 'malzemeler' içindeki bir donatı adı ya da {', '.join(yv.DONATILAR)}.")
    else:
        donati = next((m["kutuphane"] for m in B.malzemeler.values() if m["tur"] == "donati"), "B420C")
    return beton, donati, varsayim


def oku(B, t):
    """bina.temeller (sözlük) → B.temeller'e eklenecek doğrulanmış alanlar (tip 'surekli' / 'radye'). B.kolonlar, B.ax/ay,
    B.malzemeler okunmuş olmalı. Dönüş sözlüğü: {"surekli" | "radye": {...}, "zemin_ek": {...}, "beton", "donati", "varsayim"}."""
    tip = tip_oku(t.get("tip"))
    zem = t.get("zemin") if isinstance(t.get("zemin"), dict) else {}
    out = {"tip": tip}
    gamma = zem.get("gamma")
    out["zemin_ek"] = {"gamma": _sayi(gamma, "temeller.zemin.gamma (zemin birim hacim ağırlığı, kN/m³)", pozitif=True, sifir_olur=False)
                       if gamma not in (None, "") else None}
    qk = zem.get("q_k")
    out["zemin_ek"]["q_k"] = (_sayi(qk, "temeller.zemin.q_k (karakteristik taşıma gücü, kN/m²)", pozitif=True, sifir_olur=False)
                              if qk not in (None, "") else None)
    if tip == "tekil":
        return out
    beton, donati, varsayim = _malzeme_sec(B, t)
    out.update({"beton": beton, "donati": donati, "varsayim": varsayim})

    def yatay_oku(d, on):
        yatay = str(d.get("yatay") or "tutulu").strip().lower()
        if yatay not in ("tutulu", "yay"):
            raise MatrisHatasi(f"{on}.yatay {yatay!r}; 'tutulu' (temel düğümlerinde X ve Y ötelemeleri tutulu, varsayılan) ya da 'yay' "
                               "(yatay yaylar k_h = kh_oran·k_z) olmalı.")
        kh = None
        if yatay == "yay":
            if d.get("kh_oran") in (None, ""):
                raise MatrisHatasi(f"{on}.yatay = 'yay' için kh_oran (yatay/düşey yatak katsayısı oranı k_h/k_z) verilmeli; bu oran "
                                   "yönetmelikte yoktur, geoteknik rapordan alınır. Bilinmiyorsa yatay: 'tutulu' kullanın.")
            kh = _sayi(d.get("kh_oran"), f"{on}.kh_oran", pozitif=True, sifir_olur=False)
        return yatay, kh

    def ag_oku(d, on, vars_):
        ag = _sayi(d.get("ag", vars_), f"{on}.ag (eleman bölme aralığı, m)")
        if ag <= 0:
            raise MatrisHatasi(f"{on}.ag = {ag} m; ağ aralığı pozitif olmalı (0,25–1,0 m önerilir; karakteristik boy 1/β'nın "
                               "üçte birinden küçük seçilir).")
        if ag < EN_KUCUK_AG:
            raise MatrisHatasi(f"{on}.ag = {ag} m çok küçük; en az {EN_KUCUK_AG} m (serbestlik sayısı tarayıcı sınırını aşar).")
        return ag

    if tip == "surekli":
        s = t.get("surekli") if isinstance(t.get("surekli"), dict) else {}
        on = "temeller.surekli"
        yon = str(s.get("yon") or "xy").strip().lower()
        if yon not in ("x", "y", "xy"):
            raise MatrisHatasi(f"{on}.yon {yon!r}; 'x' (sayılı akslar boyunca, X doğrultusunda kirişler), 'y' (harfli akslar boyunca) "
                               "ya da 'xy' (iki doğrultu, ızgara) olmalı.")
        Bt = _sayi(s.get("B", 1.2), f"{on}.B (tabla genişliği, m)")
        if Bt <= 0:
            raise MatrisHatasi(f"{on}.B = {Bt} m; tabla (taban) genişliği pozitif olmalı.")
        ht = _sayi(s.get("h_tabla", 0.40), f"{on}.h_tabla (tabla kalınlığı, m)")
        bg = _sayi(s.get("b_govde", 0.50), f"{on}.b_govde (gövde genişliği, m)")
        hg = _sayi(s.get("h_govde", 1.00), f"{on}.h_govde (toplam kiriş yüksekliği, tabla dahil, m)")
        if ht < 0:
            raise MatrisHatasi(f"{on}.h_tabla = {ht} m negatif olamaz (dikdörtgen kesit için h_tabla = 0, b_govde = B).")
        if bg <= 0 or hg <= 0:
            raise MatrisHatasi(f"{on}: b_govde ve h_govde pozitif olmalı (girilen b_govde = {bg}, h_govde = {hg}).")
        if ht > hg + 1e-12:
            raise MatrisHatasi(f"{on}: h_tabla = {ht} m > h_govde = {hg} m. h_govde TOPLAM kiriş yüksekliğidir (tabla dahil); tabla "
                               "bundan kalın olamaz.")
        if bg > Bt + 1e-12:
            raise MatrisHatasi(f"{on}: b_govde = {bg} m > B = {Bt} m; gövde tabladan geniş olamaz. Dikdörtgen kesit için b_govde = B "
                               "ve h_tabla = 0 yazın.")
        if Bt > 6.0 or hg > 4.0:
            raise MatrisHatasi(f"{on}: B = {Bt} m, h_govde = {hg} m çok büyük; boyutlar metre girilir (120 cm → 1.2). Çok geniş "
                               "tabla gerekiyorsa radye düşünün.")
        tasma = _sayi(s.get("tasma", 0.5), f"{on}.tasma (uç kolondan taşma, m)")
        if tasma < 0:
            raise MatrisHatasi(f"{on}.tasma = {tasma} m; taşma (konsol) negatif olamaz (0 = kiriş uç kolonda biter).")
        ag = ag_oku(s, on, 0.5)
        akslar = s.get("akslar", "tum")
        if akslar in (None, "", "tum", "tüm", "hepsi"):
            secili = None
        else:
            if not isinstance(akslar, (list, tuple)) or not akslar:
                raise MatrisHatasi(f"{on}.akslar \"tum\" ya da aks adları listesi olmalı, örn. [\"1\", \"3\"].")
            secili = [str(a).strip() for a in akslar]
            for a in secili:
                yx = a in B.ay and yon in ("x", "xy")      # sayılı aks → X doğrultusunda kiriş
                yy = a in B.ax and yon in ("y", "xy")      # harfli aks → Y doğrultusunda kiriş
                if not (yx or yy):
                    beklenen = {"x": f"Y aksları (X doğrultusunda kiriş): {', '.join(B.ay)}",
                                "y": f"X aksları (Y doğrultusunda kiriş): {', '.join(B.ax)}",
                                "xy": f"Y aksları {', '.join(B.ay)} ya da X aksları {', '.join(B.ax)}"}[yon]
                    raise MatrisHatasi(f"{on}.akslar: {a!r} bu yön ({yon}) için bilinmeyen aks. Seçenekler — {beklenen}.")
        yatay, kh = yatay_oku(s, on)
        kesit = ters_t_kesit(Bt, ht, bg, hg)
        if kesit["dikdortgen"] and not (ht <= 1e-12 and abs(bg - Bt) <= 1e-12):
            varsayim.append(f"Temel kirişi kesiti dikdörtgen ({_f(kesit['B'])} × {_f(hg)} m) olarak alındı (h_tabla = {_f(ht)}, "
                            f"b_govde = {_f(bg)}, B = {_f(Bt)}).")
        out["surekli"] = {"yon": yon, "akslar": "tum" if secili is None else secili, "B": Bt, "h_tabla": ht, "b_govde": bg,
                          "h_govde": hg, "tasma": tasma, "ag": ag, "yatay": yatay, "kh_oran": kh, "kesit": kesit}
    else:
        r = t.get("radye") if isinstance(t.get("radye"), dict) else {}
        on = "temeller.radye"
        h = _sayi(r.get("h", 0.80), f"{on}.h (plak kalınlığı, m)")
        if h <= 0:
            raise MatrisHatasi(f"{on}.h = {h} m; plak kalınlığı pozitif olmalı (TS 500 md. 10.4.2: kirişsiz radye ≥ 0,30 m).")
        if h > 4.0:
            raise MatrisHatasi(f"{on}.h = {h} m çok büyük; kalınlık metre girilir (80 cm → 0.8).")
        tasma = _sayi(r.get("tasma", 1.0), f"{on}.tasma (aks dışına taşma, m)")
        if tasma < 0:
            raise MatrisHatasi(f"{on}.tasma = {tasma} m; radye taşması negatif olamaz (0 = plak dış akslarda biter).")
        ag = ag_oku(r, on, 0.5)
        kiris = r.get("kiris")
        kir = None
        if kiris not in (None, False, "", {}):
            if not isinstance(kiris, dict):
                raise MatrisHatasi(f"{on}.kiris null ya da {{\"b\": 0.5, \"h\": 1.2}} olmalı (kirişli radye: aks çizgilerinde temel kirişleri).")
            kb = _sayi(kiris.get("b", 0.5), f"{on}.kiris.b (m)")
            kh_ = _sayi(kiris.get("h", 1.2), f"{on}.kiris.h (plak dahil toplam yükseklik, m)")
            if kb <= 0 or kh_ <= 0:
                raise MatrisHatasi(f"{on}.kiris: b ve h pozitif olmalı.")
            if kh_ <= h + 1e-9:
                raise MatrisHatasi(f"{on}.kiris.h = {kh_} m plak kalınlığından (h = {h} m) büyük olmalı; kiriş yüksekliği plak dahil "
                                   "toplam yüksekliktir.")
            kir = {"b": kb, "h": kh_}
        yatay, khr = yatay_oku(r, on)
        out["radye"] = {"h": h, "tasma": tasma, "ag": ag, "kiris": kir, "yatay": yatay, "kh_oran": khr}
    return out


# ============================================================================
# Ağ kurma
# ============================================================================
def _bolumle(noktalar, ag):
    """Sıralı kırılma noktaları → her aralığı ag'yi aşmayan eşit parçalara bölünmüş nokta listesi."""
    out = [noktalar[0]]
    for a, b in zip(noktalar, noktalar[1:]):
        n = max(1, math.ceil((b - a) / ag - 1e-9))
        for k in range(1, n + 1):
            out.append(a + (b - a) * k / n)
    return out


def _kirilma(degerler):
    out = []
    for v in sorted(degerler):
        if not out or v - out[-1] > 1e-6:
            out.append(v)
    return out


def _kesisim(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def _yarim_boylar(pts):
    """Her nokta için (sol, sağ) etki yarı boyu (uçta 0)."""
    n = len(pts)
    return [((pts[i] - pts[i - 1]) / 2.0 if i > 0 else 0.0, (pts[i + 1] - pts[i]) / 2.0 if i < n - 1 else 0.0) for i in range(n)]


class _AgKurucu:
    """Temel düğümü/elemanı kaydı: aks kesişimindeki noktalar bina düğüm numarasını (1000·0 + 20·ix + iy + 1) alır, öteki
    noktalar 50001'den sıralı numaralanır."""

    def __init__(self, B, dugum, dugumler, elemanlar, model_el, eno, kot0, info):
        self.B, self.dugum, self.dugumler, self.elemanlar, self.model_el = B, dugum, dugumler, elemanlar, model_el
        self.eno, self.kot0, self.info = eno, kot0, info
        self.xidx = {round(x, 6): i for i, x in enumerate(B.xk)}
        self.yidx = {round(y, 6): i for i, y in enumerate(B.yk)}
        self.nokta = {}
        self.sonraki = 50001

    def dugum_al(self, X, Y):
        key = (round(X, 6), round(Y, 6))
        if key in self.nokta:
            return self.nokta[key]
        ix, iy = self.xidx.get(key[0]), self.yidx.get(key[1])
        kolon = None
        if ix is not None and iy is not None:
            no = self.dugum(ix, iy, 0)
            dg = next(d for d in self.dugumler if d["no"] == no)
            dg["temel"] = True
            kolon = self.B.kolon_key.get((ix, iy, 1))
            adres = dg["adres"]
        else:
            no = self.sonraki
            self.sonraki += 1
            adres = f"T({_f(X)}; {_f(Y)})"
            self.dugumler.append({"no": no, "X": float(X), "Y": float(Y), "Z": self.kot0, "adres": adres, "kat": 0, "aks": None,
                                  "key": None, "efendi": False, "temel": True})
        rec = {"no": no, "X": float(X), "Y": float(Y), "A": 0.0, "A_govde": 0.0, "k": 0.0, "kolon": kolon["no"] if kolon else None,
               "aks": [self.B.xad[ix], self.B.yad[iy]] if (ix is not None and iy is not None) else None, "adres": adres,
               "ix": ix, "iy": iy, "dW": 0.0}
        self.nokta[key] = rec
        self.info.dugumler.append(rec)
        return rec

    def eleman(self, a, b, tur, yon, hat, parca, bgen, h, kesit, E, G, q_oz, kaynak_no):
        self.eno += 1
        L = math.hypot(b["X"] - a["X"], b["Y"] - a["Y"])
        adres = (f"{'TK' if tur == 'temel-kirisi' else 'RŞ'}-{hat} p{parca}")
        self.elemanlar.append({"no": self.eno, "dugumler": [a["no"], b["no"]], "tur": tur, "kaynak_no": kaynak_no, "parca": parca,
                               "kat": 0, "L": L, "kesit": "TK" if tur == "temel-kirisi" else "RS",
                               "kaynak": {"tur": "temel", "hat": hat, "yon": yon, "parca": parca}, "key": None,
                               "adres": adres, "rijitlik_carpani": 1.0})
        # yatay eleman: y′ yukarı (Kassimali), Iz_m = düşey düzlemde eğilme (güçlü), Iy_m = düşey eksen etrafında
        self.model_el.append({"no": self.eno, "dugumler": [a["no"], b["no"]], "E": E, "G": G, "A": kesit["A"], "Iy": kesit["I_zayif"],
                              "Iz": kesit["I_guclu"], "J": kesit["J"], "kaynak": {"tur": "temel", "hat": hat, "parca": parca}})
        rec = {"no": self.eno, "tur": tur, "yon": yon, "hat": hat, "parca": parca, "dugumler": [a["no"], b["no"]], "L": L,
               "b": bgen, "h": h, "A": kesit["A"], "I": kesit["I_guclu"], "J": kesit["J"], "q_oz": q_oz, "kesit": kesit}
        self.info.elemanlar.append(rec)
        return rec


def ag_kur(B, dugum, dugumler, elemanlar, model_el, eno):
    """Mütemadi ya da radye temel ağını bina ağına ekler. ``dugum(ix, iy, kat)`` yapi.py'nin düğüm kayıt işlevi (aks
    kesişiminde bina numarası); ``dugumler``, ``elemanlar`` (ag, bina koordinatı), ``model_el`` (motor) listelerine ekler.
    Dönüş (yeni eno, info). info: tip, dugumler [{no, X, Y, A (etki alanı), k, kolon, aks}], elemanlar, hatlar / plak,
    model_mesnet, model_yay, yuk_G {"yayili", "yukler"} (motor), W (öz ağırlık, kN), k0."""
    tem = B.temeller
    tip = tem["tip"]
    beton = tem["beton"]
    E, G, gam = beton["E"], beton["G"], beton["gamma"]
    k0 = tem["zemin"]["k0"]
    kot0 = B.kat[0]["kot"]
    info = SimpleNamespace(tip=tip, dugumler=[], elemanlar=[], hatlar=[], plak=None, model_mesnet=[], model_yay=[],
                           yuk_G={"yayili": [], "yukler": []}, W=0.0, k0=k0, E=E, G=G, gamma=gam, varsayim=list(tem.get("varsayim", [])),
                           notlar=[])
    K = _AgKurucu(B, dugum, dugumler, elemanlar, model_el, eno, kot0, info)
    taban = [c for c in B.kolonlar if c["kat"] == 1]
    if tip == "surekli":
        cfg = tem["surekli"]
        ks = cfg["kesit"]
        Bt, ag, tasma = ks["B"], cfg["ag"], cfg["tasma"]
        hatlar = []
        if cfg["yon"] in ("x", "xy"):
            for iy, ad in enumerate(B.yad):
                if cfg["akslar"] == "tum" or ad in cfg["akslar"]:
                    hatlar.append(("x", iy, ad))
        if cfg["yon"] in ("y", "xy"):
            for ix, ad in enumerate(B.xad):
                if cfg["akslar"] == "tum" or ad in cfg["akslar"]:
                    hatlar.append(("y", ix, ad))
        tasinan = set()
        hat_kayit = []
        for no_h, (yon, sabit, ad) in enumerate(hatlar, start=1):
            if yon == "x":
                kol = [c for c in taban if c["iy"] == sabit]
                konum = sorted(B.xk[c["ix"]] for c in kol)
                eksen = B.xk
            else:
                kol = [c for c in taban if c["ix"] == sabit]
                konum = sorted(B.yk[c["iy"]] for c in kol)
                eksen = B.yk
            if not kol:
                if cfg["akslar"] == "tum":
                    continue          # "tum": kolonsuz aks çizgisi atlanır
                raise MatrisHatasi(f"temeller.surekli.akslar: {ad!r} aksında zemin kat (kat 1) kolonu yok; temel kirişi yük almaz ve "
                                   "uçları belirsiz kalır. Bu aksı listeden çıkarın.")
            bas, son = konum[0] - tasma, konum[-1] + tasma
            if son - bas < 1e-6:
                raise MatrisHatasi(f"temeller.surekli: {ad!r} aksında tek kolon var ve tasma = 0; temel kirişinin boyu sıfır. "
                                   "tasma > 0 verin ya da tekil temel kullanın.")
            kir = _kirilma([bas, son] + [v for v in eksen if bas - 1e-9 <= v <= son + 1e-9])
            pts = _bolumle(kir, ag)
            sabit_k = B.yk[sabit] if yon == "x" else B.xk[sabit]
            noktalar = [K.dugum_al(p, sabit_k) if yon == "x" else K.dugum_al(sabit_k, p) for p in pts]
            for c in kol:
                tasinan.add(c["no"])
            hat_kayit.append({"ad": ad, "yon": yon, "sabit": sabit_k, "bas": bas, "son": son, "pts": pts, "noktalar": noktalar,
                              "no": no_h, "kolonlar": [c["no"] for c in kol]})
        if not hat_kayit:
            raise MatrisHatasi("temeller.surekli: seçilen akslarda kat 1 kolonu yok; temel kirişi kurulamadı.")
        eksik = [c["adres"] for c in taban if c["no"] not in tasinan]
        if eksik:
            raise MatrisHatasi(f"Mütemadi temel: {', '.join(eksik[:8])}{'…' if len(eksik) > 8 else ''} kolon(lar)ının altında temel "
                               f"kirişi yok (yon = {cfg['yon']}, akslar = {cfg['akslar']}). Her zemin kat kolonu bir temel kirişine "
                               "oturmalı: aksı listeye ekleyin ya da yon = 'xy' seçin.")
        # paralel kirişlerin tablaları üst üste binmesin (birleşik tabla = radye)
        for yon in ("x", "y"):
            sab = sorted(h["sabit"] for h in hat_kayit if h["yon"] == yon)
            for a, b in zip(sab, sab[1:]):
                if b - a < Bt - 1e-9:
                    raise MatrisHatasi(f"Mütemadi temel: paralel iki temel kirişinin aks aralığı {b - a:.2f} m < B = {Bt} m; tablalar üst "
                                       "üste biniyor. B'yi küçültün ya da radye seçin.")
        q_oz = gam * ks["A"]
        for h in hat_kayit:
            parca = 0
            yaril = _yarim_boylar(h["pts"])
            for (sol, sag), rec in zip(yaril, h["noktalar"]):
                rec["A"] += Bt * (sol + sag)
                rec["A_govde"] += ks["b_govde"] * (sol + sag)
                rec.setdefault("hatlar", []).append(h["ad"])
            h["elemanlar"] = []
            for a, b in zip(h["noktalar"], h["noktalar"][1:]):
                parca += 1
                e = K.eleman(a, b, "temel-kirisi", h["yon"], h["ad"], parca, ks["b_govde"], ks["h_govde"], ks, E, G, q_oz, h["no"])
                h["elemanlar"].append(e["no"])
                info.yuk_G["yayili"].append({"eleman": e["no"], "q": -q_oz})
            L = h["son"] - h["bas"]
            info.W += q_oz * L
        # kesişim düzeltmesi: x ve y şeritlerinin ortak tabla alanı (ve hacmi) iki kez sayılmasın — her iki şeridin düğümlerinden
        # yarı yarıya düşülür (toplam düşülen = ortak alan; yay toplamı = birleşik taban alanı × k0)
        bg, ht, hg = ks["b_govde"], ks["h_tabla"], ks["h_govde"]
        ortak_alan = ortak_hacim = 0.0
        hx = [h for h in hat_kayit if h["yon"] == "x"]
        hy = [h for h in hat_kayit if h["yon"] == "y"]
        for a in hx:
            for b in hy:
                # tabla katmanı (B genişlik) ve gövde katmanı (b_govde genişlik)
                for gen, kalin in ((Bt, ht if not ks["dikdortgen"] else hg), (bg, (hg - ht) if not ks["dikdortgen"] else 0.0)):
                    ox0, ox1 = max(a["bas"], b["sabit"] - gen / 2), min(a["son"], b["sabit"] + gen / 2)
                    oy0, oy1 = max(b["bas"], a["sabit"] - gen / 2), min(b["son"], a["sabit"] + gen / 2)
                    if ox1 - ox0 <= 1e-12 or oy1 - oy0 <= 1e-12:
                        continue
                    alan = (ox1 - ox0) * (oy1 - oy0)
                    tabla = gen == Bt
                    if tabla:
                        ortak_alan += alan
                    ortak_hacim += alan * kalin
                    for hh, eks0, eks1, dik0, dik1 in ((a, ox0, ox1, oy0, oy1), (b, oy0, oy1, ox0, ox1)):
                        # şerit düğümünün etki dikdörtgeni ile ortak bölgenin kesişimi
                        for (sol, sag), p, rec in zip(_yarim_boylar(hh["pts"]), hh["pts"], hh["noktalar"]):
                            boy = _kesisim(p - sol, p + sag, eks0, eks1)
                            if boy <= 0:
                                continue
                            pay = boy * (dik1 - dik0) / 2.0
                            if tabla:
                                rec["A"] -= pay
                            else:
                                rec["A_govde"] -= pay
                            rec["dW"] += gam * pay * kalin
        if ortak_hacim > 0:
            info.W -= gam * ortak_hacim
            info.notlar.append(f"xy kesişimlerinde ortak tabla alanı {_f(ortak_alan, 3)} m² ve ortak hacim {_f(ortak_hacim, 3)} m³ "
                               "bir kez sayıldı (yay ve öz ağırlık düzeltmesi düğümlere yarı yarıya).")
        info.hatlar = [{"ad": h["ad"], "yon": h["yon"], "no": h["no"], "sabit": h["sabit"], "bas": h["bas"], "son": h["son"],
                        "elemanlar": h["elemanlar"], "dugumler": [r["no"] for r in h["noktalar"]], "kolonlar": h["kolonlar"],
                        "L": h["son"] - h["bas"]} for h in hat_kayit]
        info.ortak_alan = ortak_alan
        info.taban_alani = sum(h["son"] - h["bas"] for h in hat_kayit) * Bt - ortak_alan
        yatay, kh = cfg["yatay"], cfg["kh_oran"]
    else:
        cfg = tem["radye"]
        h, tasma, ag = cfg["h"], cfg["tasma"], cfg["ag"]
        X0, X1 = B.xk[0] - tasma, B.xk[-1] + tasma
        Y0, Y1 = B.yk[0] - tasma, B.yk[-1] + tasma
        if X1 - X0 < 1e-6 or Y1 - Y0 < 1e-6:
            raise MatrisHatasi("Radye: plak alanı sıfır (tek aks ve tasma = 0); tasma > 0 verin.")
        xs = _bolumle(_kirilma([X0, X1] + list(B.xk)), ag)
        ys = _bolumle(_kirilma([Y0, Y1] + list(B.yk)), ag)
        info.izgara = {"x": xs, "y": ys}
        wx = [s + g for s, g in _yarim_boylar(xs)]
        wy = [s + g for s, g in _yarim_boylar(ys)]
        nd = [[K.dugum_al(x, y) for y in ys] for x in xs]
        for i in range(len(xs)):
            for j in range(len(ys)):
                nd[i][j]["A"] = wx[i] * wy[j]
                nd[i][j]["w_x"], nd[i][j]["w_y"] = wx[i], wy[j]
                nd[i][j]["dW"] += gam * h * wx[i] * wy[j]
        kir = cfg["kiris"]
        xaks = {round(x, 6) for x in B.xk}
        yaks = {round(y, 6) for y in B.yk}
        kesit_cache = {}

        def serit_kesit(bgen, kirisli):
            anahtar = (round(bgen, 9), kirisli)
            if anahtar not in kesit_cache:
                if kirisli:
                    if bgen >= kir["b"]:
                        kk = ters_t_kesit(bgen, h, kir["b"], kir["h"])
                    else:
                        kk = ters_t_kesit(kir["b"], 0.0, kir["b"], kir["h"])
                else:
                    kk = {"A": bgen * h, "I_guclu": bgen * h ** 3 / 12.0, "I_zayif": h * bgen ** 3 / 12.0, "J": bgen * h ** 3 / 6.0,
                          "dikdortgen": True, "B": bgen, "h_tabla": h, "b_govde": bgen, "h_govde": h}
                kesit_cache[anahtar] = kk
            return kesit_cache[anahtar]

        hatlar = []
        no_h = 0
        for j, y in enumerate(ys):
            kirisli = kir is not None and round(y, 6) in yaks
            no_h += 1
            ad = f"y={_f(y)}"
            if kirisli:
                ad = B.yad[B.yk.index(next(v for v in B.yk if abs(v - y) < 1e-6))]
            ks = serit_kesit(wy[j], kirisli)
            tur = "temel-kirisi" if kirisli else "radye-serit"
            q_ek = gam * kir["b"] * (kir["h"] - h) if kirisli else 0.0
            el = []
            for i in range(len(xs) - 1):
                e = K.eleman(nd[i][j], nd[i + 1][j], tur, "x", ad, i + 1, wy[j], kir["h"] if kirisli else h, ks, E, G, q_ek, no_h)
                el.append(e["no"])
                if q_ek:
                    info.yuk_G["yayili"].append({"eleman": e["no"], "q": -q_ek})
            hatlar.append({"ad": ad, "yon": "x", "no": no_h, "sabit": y, "bas": X0, "son": X1, "elemanlar": el, "kirisli": kirisli,
                           "b": wy[j], "dugumler": [nd[i][j]["no"] for i in range(len(xs))], "L": X1 - X0})
            if q_ek:
                info.W += q_ek * (X1 - X0)
        for i, x in enumerate(xs):
            kirisli = kir is not None and round(x, 6) in xaks
            no_h += 1
            ad = f"x={_f(x)}"
            if kirisli:
                ad = B.xad[B.xk.index(next(v for v in B.xk if abs(v - x) < 1e-6))]
            ks = serit_kesit(wx[i], kirisli)
            tur = "temel-kirisi" if kirisli else "radye-serit"
            q_ek = gam * kir["b"] * (kir["h"] - h) if kirisli else 0.0
            el = []
            for j in range(len(ys) - 1):
                e = K.eleman(nd[i][j], nd[i][j + 1], tur, "y", ad, j + 1, wx[i], kir["h"] if kirisli else h, ks, E, G, q_ek, no_h)
                el.append(e["no"])
                if q_ek:
                    info.yuk_G["yayili"].append({"eleman": e["no"], "q": -q_ek})
            hatlar.append({"ad": ad, "yon": "y", "no": no_h, "sabit": x, "bas": Y0, "son": Y1, "elemanlar": el, "kirisli": kirisli,
                           "b": wx[i], "dugumler": [nd[i][j]["no"] for j in range(len(ys))], "L": Y1 - Y0})
            if q_ek:
                info.W += q_ek * (Y1 - Y0)
        if kir is not None:
            # kiriş kesişimlerinde gövde hacmi iki kez sayılmasın
            for x in B.xk:
                for y in B.yk:
                    rec = K.nokta.get((round(x, 6), round(y, 6)))
                    if rec is not None:
                        dv = kir["b"] ** 2 * (kir["h"] - h)
                        rec["dW"] -= gam * dv
                        info.W -= gam * dv
        info.W += gam * h * (X1 - X0) * (Y1 - Y0)
        info.hatlar = hatlar
        info.plak = {"X0": X0, "X1": X1, "Y0": Y0, "Y1": Y1, "h": h, "alan": (X1 - X0) * (Y1 - Y0), "nx": len(xs), "ny": len(ys)}
        info.taban_alani = info.plak["alan"]
        info.notlar.append("Izgara (grillage) eşdeğerliği: şerit eğilme rijitliği I = b·h³/12; burulma sabiti J ≈ b·h³/6 (plak burulma "
                           "rijitliğinin şerit genişliği başına eşdeğeri; G = E/(2(1+ν))); kenar şeritleri yarım genişliktedir.")
        yatay, kh = cfg["yatay"], cfg["kh_oran"]
    # düğüm yayları ve yatay mesnetler; öz ağırlık düzeltmeleri / radye öz ağırlığı düğüm yükü (G)
    for rec in info.dugumler:
        rec["k"] = k0 * rec["A"]
        if rec["A"] <= 0:
            raise MatrisHatasi(f"Temel düğümü {rec['adres']}: etki alanı sıfır; ağ aralığını ya da taşmayı değiştirin.")
        yay = {"dugum": rec["no"], "ky": rec["k"]}
        if yatay == "tutulu":
            info.model_mesnet.append({"dugum": rec["no"], "ux": True, "uz": True})
        else:
            yay["kx"] = kh * rec["k"]
            yay["kz"] = kh * rec["k"]
        info.model_yay.append(yay)
        if abs(rec["dW"]) > 1e-12:
            # motor: düşey = y_m; aşağı negatif (öz ağırlık), kesişim düzeltmesi yukarı (+)
            Fy = -rec["dW"] if tip == "radye" else rec["dW"]
            info.yuk_G["yukler"].append({"dugum": rec["no"], "Fx": 0.0, "Fy": Fy, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": 0.0})
    info.yatay, info.kh_oran = yatay, kh
    info.dno = {r["no"]: r for r in info.dugumler}
    info.eno = {e["no"]: e for e in info.elemanlar}
    info.ince = {e["no"] for e in info.elemanlar if e["tur"] == "radye-serit"}
    return K.eno, info


def yuk_kaydet(Y, info):
    """Temel öz ağırlığını yük özetlerine ekler: kat 0 (temel seviyesi) G, toplam G, korunum (temel_oz)."""
    W = info.W
    Y.kat0["G"] += W
    for k in Y.katlar:
        if k["kat"] == 0:
            k["G"] += W
            k["w"] += W
    Y.toplam["G"] += W
    for d in ("G", "Q", "S"):
        Y.korunum_parcalari[d]["temel_oz"] = W if d == "G" else 0.0
    Y.korunum_parcalari["G"]["toplam"] += W


def sayilar_sd_denetimi(B, n_ust, info_sayisi, en_fazla):
    """SD sınırı aşılırsa ağ aralığını büyütmeyi öneren öğretici hata."""
    n = 6 * (n_ust + info_sayisi)
    if n <= en_fazla:
        return
    tem = B.temeller
    tip = tem["tip"]
    ag = tem[tip]["ag"]
    oneri = None
    for aday in [round(ag + 0.25 * k, 2) for k in range(1, 40)]:
        if tip == "radye":
            t = tem["radye"]["tasma"]
            nx = len(_bolumle(_kirilma([B.xk[0] - t, B.xk[-1] + t] + list(B.xk)), aday))
            ny = len(_bolumle(_kirilma([B.yk[0] - t, B.yk[-1] + t] + list(B.yk)), aday))
            yeni = nx * ny
            ortak = len(B.xk) * len(B.yk)
            if 6 * (n_ust - ortak + yeni) <= en_fazla:
                oneri = aday
                break
        else:
            oran = ag / aday
            if 6 * (n_ust + int(info_sayisi * oran) + 1) <= en_fazla:
                oneri = aday
                break
    raise MatrisHatasi(f"{'Radye' if tip == 'radye' else 'Mütemadi temel'} ağı ile bina {n_ust + info_sayisi} düğüm × 6 = {n} serbestlik "
                       f"derecesi; tarayıcıda en fazla {en_fazla}. Ağ aralığını büyütün: temeller.{tip}.ag = {ag} m yerine "
                       + (f"≈ {oneri} m" if oneri else "daha büyük bir değer") + " (karakteristik boy 1/β'nın üçte birinden küçük kaldıkça "
                       "sonuç pek değişmez) ya da aks/kat sayısını azaltın.")


# ============================================================================
# Saf tasarım yardımcıları
# ============================================================================
def _malzemeler(beton, donati):
    ts = _tasarim()
    if ts is None:
        raise MatrisHatasi("tasarim.py bulunamadı; temel kesit hesabı yapılamaz.")
    sinif = beton.get("kutuphane", beton) if isinstance(beton, dict) else beton
    return ts, ts.beton_malzeme(sinif), ts.donati_malzeme(donati)


def plak_egilme(Md, h, beton="C30", donati="B420C", pas=PAS, b=1.0, rho_min=RHO_MIN, s_max=ARALIK_EN_FAZLA):
    """Plak (radye şeridi, tabla konsolu) metre başına eğilme donatısı, TS 500 dikdörtgen basınç bloğu: Md (kN·m/m), h (m).
    a = d − √(d² − 2M/(0,85 f_cd b)), A_s = 0,85 f_cd b a / f_yd; A_s ≥ ρ_min·b·d (TS 500 md. 10.3.3 / 11.2.2, 0,002);
    ρ ≤ min(0,85ρ_b; 0,02). Çubuk önerisi Φ/s (s ≤ 200 mm, ≥ 100 mm). Dönüş: d_mm, As_gerekli_cm2 (m başına), As_min_cm2,
    oneri, As_saglanan_cm2, Mr_kNm, dc, durum."""
    ts, bm, dm = _malzemeler(beton, donati)
    fcd, fyd = bm["fcd"], dm["fyd"]
    d = (h - pas) * 1000.0
    bmm = b * 1000.0
    if d <= 0:
        return {"d_mm": d, "As_gerekli_cm2": None, "As_min_cm2": None, "oneri": None, "As_saglanan_cm2": 0.0, "Mr_kNm": 0.0,
                "dc": 99.0, "durum": "kesit büyüt", "rho": None, "rho_max": None, "Md_kNm": abs(Md)}
    M = abs(float(Md)) * 1e6
    R = 0.85 * fcd * bmm
    rho_b = 0.85 * bm["k1"] * bm["fcd"] / fyd * (0.003 * dm["Es"]) / (0.003 * dm["Es"] + fyd)
    rho_max = min(0.85 * rho_b, 0.02)
    disk = d * d - 2.0 * M / R
    As_min = rho_min * bmm * d
    if disk < 0:
        As = math.inf
    else:
        a = d - math.sqrt(disk)
        As = R * a / fyd
    As_ger = max(As, As_min)
    rho = As_ger / (bmm * d)
    if not math.isfinite(As_ger) or rho > rho_max + 1e-12:
        dc = (rho / rho_max) if math.isfinite(rho) else 99.0
        return {"d_mm": d, "As_gerekli_cm2": None if not math.isfinite(As_ger) else As_ger / 100.0, "As_min_cm2": As_min / 100.0,
                "oneri": None, "As_saglanan_cm2": 0.0, "Mr_kNm": 0.0, "dc": min(max(dc, 1.01), 99.0), "durum": "kesit büyüt",
                "rho": rho if math.isfinite(rho) else None, "rho_max": rho_max, "Md_kNm": abs(Md)}
    oneri = None
    for cap in CUBUKLAR:
        A1 = math.pi * cap * cap / 4.0
        s = min(A1 * bmm / As_ger, s_max * 1000.0)
        s = math.floor(s / 10.0 + 1e-9) * 10.0
        if s >= 100.0:
            oneri = {"cap": cap, "s_mm": s, "metin": f"Φ{cap}/{_f(s / 10.0, 1)}", "As_mm2": A1 * bmm / s}
            break
    if oneri is None:
        cap = CUBUKLAR[-1]
        A1 = math.pi * cap * cap / 4.0
        oneri = {"cap": cap, "s_mm": 100.0, "metin": f"Φ{cap}/10", "As_mm2": A1 * bmm / 100.0}
    As_s = oneri["As_mm2"]
    a_s = As_s * fyd / R
    Mr = As_s * fyd * (d - a_s / 2.0)
    dc = M / Mr if Mr > 0 else 99.0
    return {"d_mm": d, "As_gerekli_cm2": As_ger / 100.0, "As_hesap_cm2": As / 100.0, "As_min_cm2": As_min / 100.0, "oneri": oneri,
            "As_saglanan_cm2": As_s / 100.0, "Mr_kNm": Mr / 1e6, "dc": dc, "durum": "yeterli" if dc <= 1.0 + 1e-9 else "donatı artır",
            "rho": rho, "rho_max": rho_max, "Md_kNm": abs(Md)}


def _cevre(bx, by, d, kenar):
    """Zımbalama çevresi seçenekleri (TS 500 md. 8.3.1, Şekil 8.2 ve 8.5): her yanda kapalı (kolon yüzünden d/2) ya da plak
    serbest kenarına uzanan açık çevre. kenar: {"-X", "+X", "-Y", "+Y"} → kolon yüzünden serbest kenara uzaklık (m) ya da None
    (uzak). Dönüş: [(u_p, A_bolge, {yan: "kapali"|"acik"})] — açık yan yalnız kenar uzaklığı bilinen yanlarda; kapalı yan, kenar
    uzaklığı ≥ d/2 ise."""
    yanlar = ("-X", "+X", "-Y", "+Y")
    secenek = []
    for maske in range(16):
        ext, durum, gecerli = {}, {}, True
        for k, yan in enumerate(yanlar):
            a = kenar.get(yan) if kenar else None
            acik = bool(maske >> k & 1)
            if acik:
                if a is None:
                    gecerli = False
                    break
                ext[yan], durum[yan] = max(a, 0.0), "acik"
            else:
                if a is not None and a < d / 2.0 - 1e-12:
                    gecerli = False
                    break
                ext[yan], durum[yan] = d / 2.0, "kapali"
        if not gecerli:
            continue
        Lx = bx + ext["-X"] + ext["+X"]
        Ly = by + ext["-Y"] + ext["+Y"]
        u = 0.0
        u += Ly if durum["-X"] == "kapali" else 0.0
        u += Ly if durum["+X"] == "kapali" else 0.0
        u += Lx if durum["-Y"] == "kapali" else 0.0
        u += Lx if durum["+Y"] == "kapali" else 0.0
        if u <= 0:
            continue
        secenek.append((u, Lx * Ly, durum))
    return secenek


def zimbalama(Nd, bx, by, d, beton="C30", p_d=0.0, kenar=None, ex=0.0, ey=0.0):
    """TS 500 md. 8.3.1 zımbalama: V_pd ≤ V_pr = γ·f_ctd·u_p·d (Denk. 8.20–8.21).

    Nd (kN, kolon tasarım eksenel kuvveti, basınç +), bx, by (m, kolon boyutları), d (m, iki doğrultu ortalaması faydalı
    yükseklik), p_d (kN/m², aynı kombinasyonda kolon altındaki zemin basıncı), kenar ({"-X": a, ...}: kolon yüzünden plak
    serbest kenarına uzaklık, m; None = iç kolon), ex, ey (m, dışmerkezlik e = 0,4·M/N, Şekil 8.3).
    u_p: kolon yüzünden d/2 uzaklıkta çevre; kenar/köşe kolonda serbest kenara uzanan açık çevre ile kapalı çevreden küçüğü
    (Şekil 8.5). γ = 1 (eksenel) ya da Denk. 8.24: γ = 1/(1 + 1,5(e_x + e_y)/√(b_x b_y)). V_pd = N_d − F_a, F_a = p_d·A
    (zımbalama çevresi içindeki zemin tepkisi; temellerde, Şekil 8.2)."""
    _, bm, _ = _malzemeler(beton, "B420C")
    fctd = bm["fctd"]                                  # MPa
    secenek = _cevre(float(bx), float(by), float(d), kenar or {})
    if not secenek:
        raise MatrisHatasi("Zımbalama çevresi kurulamadı (kolon plak kenarının dışında).")
    u_p, A, durum = min(secenek, key=lambda s: s[0])
    ic = all(v == "kapali" for v in durum.values())
    konum = "iç" if ic else ("köşe" if sum(1 for v in durum.values() if v == "acik") >= 2 else "kenar")
    if ex > 0 or ey > 0:
        gamma = 1.0 / (1.0 + 1.5 * (ex + ey) / math.sqrt(bx * by))
        g_kaynak = "Denk. 8.24" + ("" if ic else " (kenar/köşe kolonda yaklaşık; kesin hesap Denk. 8.22, W_m)")
    else:
        gamma, g_kaynak = 1.0, "eksenel yükleme γ = 1,0"
    Vpr = gamma * fctd * 1000.0 * u_p * d             # kN (f_ctd MPa → kN/m²)
    Fa = float(p_d) * A
    Vpd = float(Nd) - Fa
    dc = max(Vpd, 0.0) / Vpr if Vpr > 0 else 99.0
    return {"N_d": float(Nd), "b_x": float(bx), "b_y": float(by), "d": float(d), "u_p": u_p, "A_bolge": A, "p_d": float(p_d),
            "F_a": Fa, "V_pd": Vpd, "e_x": float(ex), "e_y": float(ey), "gamma": gamma, "gamma_kaynak": g_kaynak, "f_ctd": fctd,
            "V_pr": Vpr, "dc": min(dc, 99.0), "konum": konum, "cevre": durum, "kaynak": KAYNAK["zimbalama"]}


def kiris_winkler_modeli(L, ag, b, k0, E, I, P, x_P=None, G=None, A=None, J=None):
    """Öğretim/test modeli: Winkler zemininde uzun kiriş (cerceve3b, X ekseni boyunca), ayrık düşey yaylar k_z = k0·b·l_etki
    (mütemadi temelle AYNI ağ ve yay kuralı), x_P'de (varsayılan orta) aşağı P. Yatay ötelemeler ve burulma tutulu."""
    pts = _bolumle(_kirilma([0.0, L] + ([x_P] if x_P is not None else [L / 2.0])), ag)
    xP = L / 2.0 if x_P is None else x_P
    dug, mes, yay = [], [], []
    for i, ((sol, sag), x) in enumerate(zip(_yarim_boylar(pts), pts), start=1):
        dug.append({"no": i, "x": x, "y": 0.0, "z": 0.0})
        mes.append({"dugum": i, "ux": True, "uz": True, "rx": True})
        yay.append({"dugum": i, "ky": k0 * b * (sol + sag)})
    G = G if G is not None else E / 2.4
    A = A if A is not None else b * 1.0
    J = J if J is not None else I
    el = [{"no": i, "dugumler": [i, i + 1], "E": E, "G": G, "A": A, "Iy": I, "Iz": I, "J": J} for i in range(1, len(pts))]
    iP = min(range(len(pts)), key=lambda i: abs(pts[i] - xP)) + 1
    return {"tip": "cerceve3b", "hesap": "sayisal", "dugumler": dug, "elemanlar": el, "mesnetler": mes, "yaylar": yay,
            "yukler": [{"dugum": iP, "Fy": -float(P)}]}, iP, pts


# ============================================================================
# Sonuçlar ve tasarım (veri.temel)
# ============================================================================
_DIY = ("N", "V", "M", "Vz", "My", "T")


class _Kmb:
    """Paket üzerinde temel düğümleri ve elemanları için kombinasyon sonuçları (numpy)."""

    def __init__(self, paket, info):
        self.p = paket
        self.info = info
        self.didx = {no: i for i, no in enumerate(paket.dugum_no)}
        self.eidx = {no: j for j, no in enumerate(paket.el_no)}
        self.nd = [self.didx[r["no"]] for r in info.dugumler]

    def uz(self, kat):
        """Σ γ·u_Z (temel düğümleri, bina Z; m)."""
        out = np.zeros(len(self.nd))
        for d, g in kat.items():
            if d in self.p.durum:
                out += float(g) * self.p.durum[d]["dug"][self.nd, 2]
        return out

    def blok(self, kat, eno):
        j = self.eidx[eno]
        o, n = self.p.ofs[j], self.p.ns[j]
        out = np.zeros(6 * n)
        for d, g in kat.items():
            if d in self.p.durum:
                out += float(g) * self.p.durum[d]["diy"][o:o + 6 * n]
        return out.reshape(6, n)

    def uc(self, kat, eno):
        j = self.eidx[eno]
        out = np.zeros(12)
        for d, g in kat.items():
            if d in self.p.durum:
                out += float(g) * self.p.durum[d]["uc"][j]
        return out


def basinc_meta(info):
    """kombinasyon_kisa için küçük meta: düğümler (no, X, Y) ve k0."""
    return {"k0": info.k0, "dugumler": [(r["no"], r["X"], r["Y"]) for r in info.dugumler]}


def basinc(meta, kisa):
    """Tek kombinasyon/durum KISA'sından (bina koordinatı) temel düğümü oturması ve taban basıncı p = k0·w (tembel yol)."""
    uZ = {d["no"]: d["uZ"] for d in kisa["dugumler"]}
    k0 = meta["k0"]
    dug = []
    for no, X, Y in meta["dugumler"]:
        w = -uZ.get(no, 0.0)
        dug.append({"no": no, "X": _r(X), "Y": _r(Y), "w_mm": _r(w * 1000.0, 5), "p_kNm2": _r(k0 * w, 5)})
    ps = [d["p_kNm2"] for d in dug] or [0.0]
    return {"dugumler": dug, "p_maks": max(ps), "p_min": min(ps), "oturma_maks_mm": max((d["w_mm"] for d in dug), default=0.0)}


def _komb_satirlari(kombinasyonlar, paket):
    """(dayanım + deprem, servis) kombinasyon listeleri: [(ad, katsayılar (çözüm), tur)]."""
    tas, ser = [], []
    for k in kombinasyonlar:
        if not k.get("uygulandi"):
            continue
        if k["tur"] in ("dayanim", "deprem"):
            tas.append((k["ad"], k.get("cozum", k["katsayilar"]), k["tur"]))
        elif k["tur"] == "servis":
            ser.append((k["ad"], dict(k["katsayilar"]), "servis"))
    if not any(ad == "G+Q" for ad, _, _ in ser):
        ser.insert(0, ("G+Q", {"G": 1.0, "Q": 1.0}, "servis"))
    ser = [s for s in ser if all(d in paket.durum for d in s[1])]
    return tas, ser


def _kolon_yuzu_serbest(B, hat, kol_no_listesi):
    """Hat boyunca komşu kolonlar arasındaki en büyük serbest açıklık (kolon yüzleri arası, m)."""
    kol = sorted((B.kolon_no[n] for n in kol_no_listesi), key=lambda c: (B.xk[c["ix"]] if hat["yon"] == "x" else B.yk[c["iy"]]))
    en = 0.0
    for a, b in zip(kol, kol[1:]):
        if hat["yon"] == "x":
            L = B.xk[b["ix"]] - B.xk[a["ix"]] - a["bX"] / 2.0 - b["bX"] / 2.0
        else:
            L = B.yk[b["iy"]] - B.yk[a["iy"]] - a["bY"] / 2.0 - b["bY"] / 2.0
        en = max(en, L)
    return en


def _kontrol(ad, talep, kapasite, kaynak, birim="", kombinasyon=None, kosul=False, bilgi=False):
    dc = 99.0 if kapasite <= 0 else min(max(talep / kapasite, 0.0), 99.0)
    return {"ad": ad, "talep": _r(talep, 5), "kapasite": _r(kapasite, 5), "dc": _r(dc, 5), "birim": birim, "kaynak": kaynak,
            "saglandi": dc <= 1.0 + 1e-9, "kombinasyon": kombinasyon, **({"kosul": True} if kosul else {}), **({"bilgi": True} if bilgi else {})}


def sonuclar(B, ag, paket, kombinasyonlar):
    """veri.temel (§13): taban basıncı (servis), oturma, TS 500 emniyet ve TBDY 16.8 taşıma gücü kontrolleri, temel kirişi /
    tabla / radye şeridi donatısı, zımbalama, en küçük kalınlıklar. İkinci değer anlatım için iç ayrıntılar."""
    info = ag["temel"]
    tem = B.temeller
    tip = tem["tip"]
    k0 = info.k0
    q_em = tem["zemin"]["q_em"]
    q_k = tem["zemin"].get("q_k")
    km = _Kmb(paket, info)
    tas, ser = _komb_satirlari(kombinasyonlar, paket)
    uyarilar, notlar = [], list(info.notlar)
    # --- servis: oturma ve taban basıncı ---
    servis = []
    for ad, kat, _ in ser:
        w = -km.uz(kat)
        p = k0 * w
        servis.append({"ad": ad, "p_maks": float(p.max()), "p_min": float(p.min()), "w_maks_mm": float(w.max() * 1000.0),
                       "w_min_mm": float(w.min() * 1000.0), "DC": float(p.max()) / q_em, "_w": w, "_p": p})
    gq = servis[0]
    bel = max(servis, key=lambda s: s["p_maks"])
    w, p = gq["_w"], gq["_p"]
    dugumler = [{"no": r["no"], "X": _r(r["X"]), "Y": _r(r["Y"]), "w_mm": _r(w[i] * 1000.0, 5), "p_kNm2": _r(p[i], 5),
                 "A": _r(r["A"], 5), **({"kolon": r["kolon"]} if r["kolon"] else {})} for i, r in enumerate(info.dugumler)]
    if any(s["p_min"] < -1e-9 for s in servis):
        uyarilar.append(f"Servis yükünde taban basıncı negatif (p_min = {_f(min(s['p_min'] for s in servis))} kN/m²): zemin çekme "
                        "alamaz; o bölgede temel zeminden ayrılır (ayrılma). Doğrusal Winkler modeli çekme yayı varsayar; yineleme "
                        "(çekme yaylarını çıkarıp yeniden çözme) yapılmadı — sonuç o bölgede güvensiz olabilir.")
    # farklı oturma: komşu kolonlar (aks çizgisi boyunca) arasındaki |Δw| / L
    kol_w = {}
    for i, r in enumerate(info.dugumler):
        if r["kolon"] is not None:
            kol_w[(r["ix"], r["iy"])] = (w[i], r)
    farkli, farkli_yer = 0.0, None
    for (ix, iy), (wi, ri) in kol_w.items():
        for (jx, jy) in ((ix + 1, iy), (ix, iy + 1)):
            if (jx, jy) not in kol_w:
                continue
            wj, rj = kol_w[(jx, jy)]
            L = math.hypot(rj["X"] - ri["X"], rj["Y"] - ri["Y"])
            oran = abs(wi - wj) / L if L > 0 else 0.0
            if oran > farkli:
                farkli, farkli_yer = oran, f"{ri['adres']}–{rj['adres']}"
    # --- TBDY 16.8: katsayılı yüklerle q_o ≤ q_t ---
    q_k_kaynak = "kullanıcı (geoteknik rapor)"
    if q_k is None:
        q_k = GS_KLASIK * q_em
        q_k_kaynak = f"VARSAYIM: q_k = GS·q_em = {_f(GS_KLASIK)}·{_f(q_em)} (klasik GS ≈ 3; geoteknik rapordan q_k girin)"
        notlar.append("TBDY 16.8 kontrolü için q_k verilmedi; q_k = 3·q_em varsayıldı (temeller.zemin.q_k ile girin).")
    q_t = q_k / GAMMA_RV
    P = None
    q_o, q_o_k, p_min_d = 0.0, None, 0.0
    if tas:
        P = np.array([-k0 * km.uz(kat) for _, kat, _ in tas])          # (nk × nn) kN/m²
        i, j = np.unravel_index(int(np.argmax(P)), P.shape)
        q_o, q_o_k = float(P[i, j]), tas[i][0]
        p_min_d = float(P.min())
        if p_min_d < -1e-9:
            uyarilar.append(f"Katsayılı kombinasyonda taban basıncı negatif (en küçük p = {_f(p_min_d)} kN/m², "
                            f"{tas[int(np.unravel_index(int(np.argmin(P)), P.shape)[0])][0]}): zemin çekme alamaz; ayrılma bölgesi oluşur "
                            "(yineleme yapılmadı).")
    zemin_kontrolleri = [
        _kontrol(f"TS 500 emniyet (servis {bel['ad']}): p_maks ≤ q_em", bel["p_maks"], q_em, KAYNAK["emniyet"], "kN/m²", bel["ad"]),
        _kontrol("TBDY 16.8: q_o (katsayılı) ≤ q_t = q_k/γ_Rv", q_o, q_t, KAYNAK["tbdy"] + "; q_k: " + q_k_kaynak, "kN/m²", q_o_k),
    ]
    # --- elemanlar (servis G+Q diyagramları; radye şeridinde yalnız uç kuvvetleri + enb) ---
    kat_gq = {"G": 1.0, "Q": 1.0}
    elemanlar = []
    for e in info.elemanlar:
        blok = km.blok(kat_gq, e["no"])
        uc = km.uc(kat_gq, e["no"])
        j = km.eidx[e["no"]]
        kayit = {"no": e["no"], "tur": e["tur"], "yon": e["yon"], "kaynak": {"tur": "temel", "hat": e["hat"], "parca": e["parca"]},
                 "dugumler": e["dugumler"], "L": _r(e["L"]), "b": _r(e["b"]), "h": _r(e["h"]),
                 "uc_kuvvetleri": [_r(x, 5) for x in uc],
                 "enb": {a: _r(float(blok[k][np.argmax(np.abs(blok[k]))]), 5) for k, a in enumerate(_DIY)}}
        if e["tur"] != "radye-serit":
            kayit["x"] = [_r(x) for x in paket.el_x[j]]
            for k, a in enumerate(_DIY):
                kayit[a] = [_r(x) for x in blok[k]]
        elemanlar.append(kayit)
    # --- tasarım ---
    ts = _tasarim()
    tasarim, kontroller = [], []
    zimb = []
    ic = {"servis": servis, "q_t": q_t, "q_k": q_k, "q_o": q_o, "q_o_k": q_o_k, "P": P, "tas": tas, "km": km}
    beton, donati = tem["beton"], tem["donati"]
    beton_ad = beton.get("kutuphane") or beton.get("ad")
    if ts is None:
        uyarilar.append("tasarim.py yok: temel kesit hesapları (donatı, zımbalama) yapılmadı.")
    elif not tas:
        uyarilar.append("Dayanım kombinasyonu yok: temel kesit hesapları yapılmadı.")
    else:
        Ga = np.zeros((len(tas), len(paket.durum)))
        adlar_d = list(paket.durum)
        for i, (_, kat, _) in enumerate(tas):
            for d, g in kat.items():
                if d in paket.durum:
                    Ga[i, adlar_d.index(d)] = g

        def kmb_blok(eno):
            j = km.eidx[eno]
            o, n = paket.ofs[j], paket.ns[j]
            D = np.array([paket.durum[d]["diy"][o:o + 6 * n] for d in adlar_d])
            return (Ga @ D).reshape(len(tas), 6, n)

        bloklar = {e["no"]: kmb_blok(e["no"]) for e in info.elemanlar}
        p_d_maks = float(P.max()) if P is not None else 0.0
        # ---- temel kirişleri (mütemadi; kirişli radyede aks kirişleri) ----
        for h in info.hatlar:
            el = [info.eno[n] for n in h["elemanlar"]]
            if not el or el[0]["tur"] != "temel-kirisi":
                continue
            ks = el[0]["kesit"]
            if tip == "surekli":
                bw, H = ks["b_govde"], ks["h_govde"]
            else:
                bw, H = tem["radye"]["kiris"]["b"], tem["radye"]["kiris"]["h"]
            Mp, Mn, Vm = [0.0, None, None], [0.0, None, None], [0.0, None, None]
            for e in el:
                bl = bloklar[e["no"]]
                M, V = bl[:, 2, :], bl[:, 1, :]
                i, s = np.unravel_index(int(np.argmax(M)), M.shape)
                if M[i, s] > Mp[0]:
                    Mp = [float(M[i, s]), tas[i][0], e["no"]]
                i, s = np.unravel_index(int(np.argmin(M)), M.shape)
                if -M[i, s] > Mn[0]:
                    Mn = [float(-M[i, s]), tas[i][0], e["no"]]
                i, s = np.unravel_index(int(np.argmax(np.abs(V))), V.shape)
                if abs(V[i, s]) > Vm[0]:
                    Vm = [float(abs(V[i, s])), tas[i][0], e["no"]]
            ea = ts.kiris_egilme(Mp[0], bw, H, PAS, beton_ad, donati, tbdy=False)
            eu = ts.kiris_egilme(Mn[0], bw, H, PAS, beton_ad, donati, tbdy=False)
            kk = ts.kiris_kesme(Vm[0], bw, H, PAS, beton_ad, donati)
            As_alt = ea["As_saglanan_cm2"]
            As_ust = eu["As_saglanan_cm2"]
            kont = [
                _kontrol("Eğilme (kolon altı, alt donatı) Md ≤ Mr", Mp[0], ea["Mr_kNm"], KAYNAK["kiris"], "kN·m", Mp[1]),
                _kontrol("Eğilme (açıklık, üst donatı) Md ≤ Mr", Mn[0], eu["Mr_kNm"], KAYNAK["kiris"], "kN·m", Mn[1]),
                _kontrol("Kesme Vd ≤ Vr (Vc + Vw)", Vm[0], kk["V_r_kN"], KAYNAK["kiris"], "kN", Vm[1]),
                _kontrol("Kesme üst sınırı Vd ≤ 0,22 fcd bw d", Vm[0], kk["V_max_kN"], KAYNAK["kiris"], "kN", Vm[1]),
                _kontrol("Vd ≤ Vcr (olabildiğince)", Vm[0], kk["V_cr_kN"], KAYNAK["vcr_kiris"], "kN", Vm[1], bilgi=True),
            ]
            ln = _kolon_yuzu_serbest(B, h, h.get("kolonlar") or [info.dno[n]["kolon"] for n in h["dugumler"] if info.dno[n]["kolon"]])
            if ln > 0:
                kont.append(_kontrol(f"Kiriş yüksekliği h ≥ l_n/10 (l_n = {_f(ln)} m)", ln / KIRIS_ORAN, H, KAYNAK["surekli_h"], "m", kosul=True))
            # basınç bölgesi donatısı ≥ çekme/3 (md. 10.4.3): öneri metnine yansır
            ust_min, alt_min = As_alt / 3.0, As_ust / 3.0
            etkin = [k for k in kont if not k.get("bilgi")]
            dc = max(k["dc"] for k in etkin)
            durum = "yeterli"
            if ea["durum"] == "kesit büyüt" or eu["durum"] == "kesit büyüt" or kk["durum"] == "kesit büyüt" or any(
                    k.get("kosul") and not k["saglandi"] for k in kont):
                durum = "kesit büyüt"
            elif dc > 1.0 + 1e-9:
                durum = "donatı artır"
            oneri = []
            if durum == "kesit büyüt":
                oneri.append("h_govde (kiriş yüksekliği) artırın" if tip == "surekli" else "kiriş h artırın")
            tasarim.append({
                "tur": "temel-kirisi", "hat": h["ad"], "yon": h["yon"], "elemanlar": h["elemanlar"], "b": bw, "h": H,
                "Md_alt": _r(Mp[0], 5), "Md_ust": _r(Mn[0], 5), "Vd": _r(Vm[0], 5),
                "As_alt_cm2": _r(max(As_alt, alt_min), 4), "As_ust_cm2": _r(max(As_ust, ust_min), 4),
                "oneri_alt": (ea["oneri"] or {}).get("metin"), "oneri_ust": (eu["oneri"] or {}).get("metin"),
                "etriye": (kk["oneri"] or {}).get("metin"), "V_cr": _r(kk["V_cr_kN"], 5),
                "dc": _r(dc, 5), "durum": durum, "oneri": "; ".join(oneri) or None, "kontroller": kont,
                "kaynak": KAYNAK["kiris"] + "; " + KAYNAK["basinc_donatisi"]})
        # ---- tabla konsolu (mütemadi ters T) ----
        if tip == "surekli" and not tem["surekli"]["kesit"]["dikdortgen"]:
            ks = tem["surekli"]["kesit"]
            c = (ks["B"] - ks["b_govde"]) / 2.0
            Mm = p_d_maks * c * c / 2.0
            Vm_ = p_d_maks * c
            pe = plak_egilme(Mm, ks["h_tabla"], beton_ad, donati)
            _, bm, _ = _malzemeler(beton_ad, donati)
            d = ks["h_tabla"] - PAS
            Vcr = 0.65 * bm["fctd"] * 1000.0 * 1.0 * d if d > 0 else 0.0
            kont = [_kontrol("Tabla eğilmesi (m başına) Md ≤ Mr", Mm, pe["Mr_kNm"], KAYNAK["rho_min"], "kN·m/m", q_o_k),
                    _kontrol("Tabla kesmesi (m başına, etriyesiz) Vd ≤ Vcr", Vm_, Vcr, KAYNAK["vcr"], "kN/m", q_o_k),
                    _kontrol("Tabla kalınlığı ≥ 200 mm", H_PLAK_MIN, ks["h_tabla"], KAYNAK["plak_h"], "m", kosul=True)]
            dc = max(k["dc"] for k in kont)
            durum = "yeterli" if dc <= 1.0 + 1e-9 else ("donatı artır" if (pe["durum"] == "donatı artır" and kont[1]["saglandi"]
                                                                             and kont[2]["saglandi"]) else "kesit büyüt")
            tasarim.append({"tur": "tabla", "konsol_boyu": _r(c, 5), "p_d": _r(p_d_maks, 5), "M_m": _r(Mm, 5), "V_m": _r(Vm_, 5),
                            "h": ks["h_tabla"], "d_mm": _r(pe["d_mm"], 5), "As_cm2_m": _r(pe["As_gerekli_cm2"] or 0.0, 4),
                            "oneri_donati": (pe["oneri"] or {}).get("metin"), "V_cr": _r(Vcr, 5), "dc": _r(dc, 5), "durum": durum,
                            "oneri": None if durum == "yeterli" else "h_tabla artırın", "kontroller": kont, "kombinasyon": q_o_k,
                            "kaynak": "TS 500 md. 10.3.2 (konsol, kritik kesit gövde yüzü); " + KAYNAK["rho_min"] + "; " + KAYNAK["vcr"]})
        # ---- radye şeritleri (m başına, iki doğrultu, alt/üst) ----
        if tip == "radye":
            hR = tem["radye"]["h"]
            for yon in ("x", "y"):
                Mp, Mn = [0.0, None, None], [0.0, None, None]
                for e in info.elemanlar:
                    if e["yon"] != yon or e["tur"] != "radye-serit":
                        continue
                    M = bloklar[e["no"]][:, 2, :] / e["b"]
                    i, s = np.unravel_index(int(np.argmax(M)), M.shape)
                    if M[i, s] > Mp[0]:
                        Mp = [float(M[i, s]), tas[i][0], e["no"]]
                    i, s = np.unravel_index(int(np.argmin(M)), M.shape)
                    if -M[i, s] > Mn[0]:
                        Mn = [float(-M[i, s]), tas[i][0], e["no"]]
                alt = plak_egilme(Mp[0], hR, beton_ad, donati)
                ust = plak_egilme(Mn[0], hR, beton_ad, donati)
                kont = [_kontrol(f"{yon.upper()} şeridi alt donatı (m başına) Md ≤ Mr", Mp[0], alt["Mr_kNm"], KAYNAK["rho_min"], "kN·m/m", Mp[1]),
                        _kontrol(f"{yon.upper()} şeridi üst donatı (m başına) Md ≤ Mr", Mn[0], ust["Mr_kNm"], KAYNAK["rho_min"], "kN·m/m", Mn[1])]
                dc = max(k["dc"] for k in kont)
                durum = "kesit büyüt" if "kesit büyüt" in (alt["durum"], ust["durum"]) else ("yeterli" if dc <= 1.0 + 1e-9 else "donatı artır")
                tasarim.append({"tur": "radye-serit", "yon": yon, "h": hR, "M_alt_m": _r(Mp[0], 5), "M_ust_m": _r(Mn[0], 5),
                                "As_alt_cm2_m": _r(alt["As_gerekli_cm2"] or 0.0, 4), "As_ust_cm2_m": _r(ust["As_gerekli_cm2"] or 0.0, 4),
                                "As_min_cm2_m": _r(alt["As_min_cm2"] or 0.0, 4),
                                "oneri_alt": (alt["oneri"] or {}).get("metin"), "oneri_ust": (ust["oneri"] or {}).get("metin"),
                                "eleman_alt": Mp[2], "eleman_ust": Mn[2], "dc": _r(dc, 5), "durum": durum,
                                "oneri": None if durum != "kesit büyüt" else "radye h artırın", "kontroller": kont,
                                "kaynak": KAYNAK["rho_min"] + "; " + KAYNAK["aralik"]})
            # ---- zımbalama (kirişsiz radye; TS 500 md. 10.4.2 → 8.3.1) ----
            if tem["radye"]["kiris"] is None:
                d = hR - PAS
                pl = info.plak
                for r in info.dugumler:
                    if r["kolon"] is None:
                        continue
                    c = B.kolon_no[r["kolon"]]
                    j_n = info.dugumler.index(r)
                    kenar = {"-X": (r["X"] - c["bX"] / 2.0) - pl["X0"], "+X": pl["X1"] - (r["X"] + c["bX"] / 2.0),
                             "-Y": (r["Y"] - c["bY"] / 2.0) - pl["Y0"], "+Y": pl["Y1"] - (r["Y"] + c["bY"] / 2.0)}
                    # yalnız kenara yakın yanlar için açık çevre seçeneği (5d'den uzaksa iç kolon gibi)
                    kenar = {k: (v if v < 5.0 * d else None) for k, v in kenar.items()}
                    en = None
                    for i, (ad, kat, _) in enumerate(tas):
                        u = km.uc(kat, c["eleman"])
                        N = float(u[0])
                        if N <= 0:
                            continue
                        ex = 0.4 * abs(float(u[5])) / N
                        ey = 0.4 * abs(float(u[4])) / N
                        z = zimbalama(N, c["bX"], c["bY"], d, beton_ad, p_d=max(float(P[i, j_n]), 0.0), kenar=kenar, ex=ex, ey=ey)
                        if en is None or z["dc"] > en["dc"]:
                            en = dict(z, kombinasyon=ad)
                    if en is None:
                        continue
                    en.update({"kolon_no": c["no"], "aks": c["aks"], "adres": c["adres"], "dugum": r["no"]})
                    zimb.append(en)
                for z in zimb:
                    durum = "yeterli" if z["dc"] <= 1.0 + 1e-9 else "kesit büyüt"
                    tasarim.append({"tur": "zimbalama", "kolon_no": z["kolon_no"], "aks": z["aks"], "adres": z["adres"],
                                    "konum": z["konum"], "N_d": _r(z["N_d"], 5), "p_d": _r(z["p_d"], 5), "F_a": _r(z["F_a"], 5),
                                    "V_pd": _r(z["V_pd"], 5), "u_p": _r(z["u_p"], 5), "A_bolge": _r(z["A_bolge"], 5), "d": _r(z["d"], 5),
                                    "gamma": _r(z["gamma"], 5), "f_ctd": _r(z["f_ctd"], 5), "V_pr": _r(z["V_pr"], 5), "dc": _r(z["dc"], 5),
                                    "kombinasyon": z["kombinasyon"], "durum": durum,
                                    "oneri": None if durum == "yeterli" else "radye h artırın (zımbalama donatısı radyede sayılmaz)",
                                    "kaynak": z["kaynak"]})
            # en küçük kalınlık
            if tem["radye"]["kiris"] is None:
                kontroller.append(_kontrol("Radye kalınlığı h ≥ 300 mm", H_RADYE_MIN, hR, KAYNAK["radye_h"], "m", kosul=True))
            else:
                kontroller.append(_kontrol("Kirişli radye plak kalınlığı h ≥ 200 mm", H_PLAK_MIN, hR, KAYNAK["plak_h"], "m", kosul=True))
    # --- özet ---
    tasarim_dc = max((t["dc"] for t in tasarim), default=0.0)
    kosul_dc = max((k["dc"] for k in kontroller if not k["saglandi"]), default=0.0)
    zemin_dc = max(k["dc"] for k in zemin_kontrolleri)
    en_dc = max(tasarim_dc, kosul_dc, zemin_dc)
    oneriler = []
    if zemin_kontrolleri[0]["dc"] > 1.0 or zemin_kontrolleri[1]["dc"] > 1.0:
        oneriler.append("Taban basıncı sınırı aşılıyor: " + ("tabla genişliği B'yi artırın" if tip == "surekli"
                                                              else "radye taşmasını artırın") + " (taban alanı büyür).")
    for t in tasarim:
        if t.get("oneri") and t["dc"] > 1.0 + 1e-9:
            yer = t.get("hat") or t.get("adres") or t.get("yon") or ""
            oneriler.append(f"{t['tur']} {yer}: {t['oneri']}")
    for k in kontroller:
        if not k["saglandi"]:
            oneriler.append(f"{k['ad']}: sağlanmıyor ({k['kaynak']}).")
    dc_dagilim = {"<0.7": 0, "0.7-0.9": 0, "0.9-1.0": 0, ">1.0": 0}
    for t in tasarim:
        x = t["dc"]
        dc_dagilim["<0.7" if x < 0.7 else "0.7-0.9" if x < 0.9 else "0.9-1.0" if x <= 1.0 + 1e-9 else ">1.0"] += 1
    model = {"k0": k0, "yatay": info.yatay, "kh_oran": info.kh_oran, "dugum_sayisi": len(info.dugumler),
             "eleman_sayisi": len(info.elemanlar), "taban_alani": _r(info.taban_alani, 6), "yay_toplami": _r(sum(r["k"] for r in info.dugumler), 6),
             "W_temel": _r(info.W, 6), "beton": tem["beton"].get("kutuphane") or tem["beton"].get("ad"), "donati": tem["donati"]}
    if tip == "surekli":
        cfg = tem["surekli"]
        ks = cfg["kesit"]
        model.update({"yon": cfg["yon"], "akslar": cfg["akslar"], "ag": cfg["ag"], "tasma": cfg["tasma"],
                      "kesit": {"B": ks["B"], "h_tabla": ks["h_tabla"], "b_govde": ks["b_govde"], "h_govde": ks["h_govde"], "A": _r(ks["A"]),
                                "y_c": _r(ks["y_c"]), "I": _r(ks["I_guclu"]), "Iz": _r(ks["I_zayif"]), "J": _r(ks["J"]),
                                "dikdortgen": ks["dikdortgen"]},
                      "ortak_alan": _r(info.ortak_alan, 6)})
        EI = info.E * ks["I_guclu"]
        model["beta"] = _r((k0 * ks["B"] / (4.0 * EI)) ** 0.25, 5)
        model["ag_beta"] = _r(cfg["ag"] * model["beta"], 4)
    else:
        cfg = tem["radye"]
        model.update({"h": cfg["h"], "tasma": cfg["tasma"], "ag": cfg["ag"], "kiris": cfg["kiris"], "plak": {a: _r(v) for a, v in info.plak.items()},
                      "izgara": {"x": [_r(v) for v in info.izgara["x"]], "y": [_r(v) for v in info.izgara["y"]]}})
        EI = info.E * cfg["h"] ** 3 / 12.0
        model["beta"] = _r((k0 / (4.0 * EI)) ** 0.25, 5)
        model["ag_beta"] = _r(cfg["ag"] * model["beta"], 4)
    if model["ag_beta"] > 0.5:
        notlar.append(f"Ağ aralığı karakteristik boya göre kaba (a·β = {_f(model['ag_beta'], 3)} > 0,5): ayrık yaylar tutarlı Winkler "
                      "matrisinden belirgin sapabilir; ag'yi küçültün.")
    veri = {
        "tip": tip, "q_em": q_em, "q_k": _r(q_k, 6), "q_t": _r(q_t, 6), "gamma_Rv": GAMMA_RV, "q_k_kaynak": q_k_kaynak,
        "p_maks": _r(gq["p_maks"], 6), "p_min": _r(gq["p_min"], 6),
        "DC_zemin": _r(bel["DC"], 5), "belirleyen_servis": bel["ad"],
        "oturma_maks_mm": _r(gq["w_maks_mm"], 5), "oturma_min_mm": _r(gq["w_min_mm"], 5),
        "farkli_oturma": _r(farkli, 5), "farkli_oturma_metin": f"1/{_f(1.0 / farkli, 0)}" if farkli > 1e-12 else "–",
        "farkli_oturma_yer": farkli_yer,
        "servis": [{a: (_r(v, 6) if isinstance(v, float) else v) for a, v in s.items() if not a.startswith("_")} for s in servis],
        "q_o": _r(q_o, 6), "q_o_kombinasyon": q_o_k, "p_min_katsayili": _r(p_min_d, 6),
        "zemin_kontrolleri": zemin_kontrolleri, "kontroller": kontroller,
        "dugumler": dugumler, "elemanlar": elemanlar,
        "hatlar": [{a: (_r(v) if isinstance(v, float) else v) for a, v in hh.items()} for hh in info.hatlar],
        "model": model, "tasarim": tasarim, "en_buyuk_dc": _r(en_dc, 5), "dc_dagilimi": dc_dagilim,
        "uyarilar": uyarilar, "oneriler": oneriler, "notlar": notlar, "varsayimlar": list(info.varsayim),
        "kaynaklar": dict(KAYNAK),
    }
    ic.update({"zimbalama": zimb, "kritik_zimbalama": max(zimb, key=lambda z: z["dc"]) if zimb else None})
    return veri, ic


def tekil_ozet(akis_temeller, q_em):
    """Tekil temelde veri.temel kısa özeti (ayrıntı veri.akis.temeller'de; davranış değişmez)."""
    sig = [t["sigma_max"] for t in akis_temeller] or [0.0]
    smin = [t["sigma_min"] for t in akis_temeller] or [0.0]
    dc = [t["DC"] for t in akis_temeller] or [0.0]
    return {"tip": "tekil", "q_em": q_em, "p_maks": _r(max(sig), 6), "p_min": _r(min(smin), 6), "DC_zemin": _r(max(dc), 5),
            "elemanlar": [], "dugumler": [], "tasarim": [], "uyarilar": [], "not": "Tekil temel tabloları veri.akis.temeller'dedir."}


# ============================================================================
# Anlatım: "Temel ve zemin" adımı
# ============================================================================
def _sema_basinc(B, info, veri):
    """Plan: temel düğümlerinin etki alanları renk tonlu kareler (servis G+Q taban basıncı), kolonlar, akslar."""
    se = _se()
    AILE = se._AILE
    xs = [r["X"] for r in info.dugumler] + [B.xk[0], B.xk[-1]]
    ys = [r["Y"] for r in info.dugumler] + [B.yk[0], B.yk[-1]]
    M = SimpleNamespace(dugumler=[SimpleNamespace(px=min(xs) - 0.5, py=min(ys) - 0.5), SimpleNamespace(px=max(xs) + 0.5, py=max(ys) + 0.5)],
                        uc=False, elemanlar=[])
    c = se._Cizim(M, genislik=440.0)
    q_em = veri["q_em"]
    p_ust = max(max(abs(d["p_kNm2"]) for d in veri["dugumler"]), 1e-9)
    Bt = B.temeller["surekli"]["kesit"]["B"] if info.tip == "surekli" else None
    for r, d in zip(info.dugumler, veri["dugumler"]):
        if info.tip == "radye":
            wx, wy = r["w_x"], r["w_y"]
        else:
            # şerit boyunca etki boyu × B (kesişimde kare)
            l = r["A"] / Bt if Bt else 0.5
            hat = r.get("hatlar") or []
            yonler = {h["yon"] for h in info.hatlar if h["ad"] in hat and r["no"] in h["dugumler"]}
            if yonler == {"x"}:
                wx, wy = l, Bt
            elif yonler == {"y"}:
                wx, wy = Bt, l
            else:
                wx = wy = max(Bt, math.sqrt(max(r["A"], 1e-9)))
        x0, y0 = c.P(r["X"] - wx / 2.0, r["Y"] + wy / 2.0)
        x1, y1 = c.P(r["X"] + wx / 2.0, r["Y"] - wy / 2.0)
        p = d["p_kNm2"]
        if p < 0:
            aile, op = "a", 0.6
        elif p > q_em:
            aile, op = "sil", 0.85
        else:
            aile, op = "b", 0.12 + 0.75 * min(p / max(q_em, p_ust), 1.0)
        c.orta.append(f'<rect class="g0" x="{se._n(x0)}" y="{se._n(y0)}" width="{se._n(x1 - x0)}" height="{se._n(y1 - y0)}" '
                      f'style="fill:{AILE[aile][1]};fill-opacity:{op:.2f}" stroke="none"/>')
        c.kapsa(x0, y0, x1, y1)
    for i, x in enumerate(B.xk):
        a, b = c.P(x, min(ys) - 0.3), c.P(x, max(ys) + 0.3)
        c.cizgi(a, b, "n", kalin=0.8, kesik="4 3", sinif="g3")
        c.yazi(a[0], a[1] + 12, B.xad[i], boyut=11, opak=0.8)
    for j, y in enumerate(B.yk):
        a, b = c.P(min(xs) - 0.3, y), c.P(max(xs) + 0.3, y)
        c.cizgi(a, b, "n", kalin=0.8, kesik="4 3", sinif="g3")
        c.yazi(a[0] - 12, a[1], B.yad[j], boyut=11, opak=0.8)
    for col in B.kolonlar:
        if col["kat"] != 1:
            continue
        x0, y0 = c.P(B.xk[col["ix"]] - col["bX"] / 2.0, B.yk[col["iy"]] + col["bY"] / 2.0)
        x1, y1 = c.P(B.xk[col["ix"]] + col["bX"] / 2.0, B.yk[col["iy"]] - col["bY"] / 2.0)
        c.dikdortgen(x0, y0, x1 - x0, y1 - y0, aile="a", sinif="g1", katman="on", kalin=1.4)
    i_max = max(range(len(veri["dugumler"])), key=lambda i: veri["dugumler"][i]["p_kNm2"])
    r = info.dugumler[i_max]
    X, Y = c.P(r["X"], r["Y"])
    c.daire((X, Y), 6.0, aile="sil", sinif="g2")
    c.yazi(X + 9, Y - 10, f"p_maks = {_f(veri['dugumler'][i_max]['p_kNm2'], 1)}", boyut=10, hiza="start")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 18.0, f"Servis G+Q taban basıncı p = k0·w (kN/m²): açık → koyu amber = 0 → q_em "
           f"({_f(q_em)}); kırmızı > q_em; mavi < 0 (çekme/ayrılma)", boyut=10, opak=0.8)
    return {"baslik": "Taban basıncı planı (servis G+Q)", "svg": c.svg("Taban basıncı")}


def anlatim(anl, no, B, ag, veri, ic, toplam_servis=None):
    """'Temel ve zemin' anlatım adımı (mütemadi / radye)."""
    se = _se()
    info = ag["temel"]
    tem = B.temeller
    tip = tem["tip"]
    ad_tip = "mütemadi (sürekli) temel" if tip == "surekli" else ("kirişli radye" if tem["radye"]["kiris"] else "radye (kirişsiz plak)")
    se._basla(anl, no, "Temel ve zemin: Winkler yayları, taban basıncı, zımbalama, donatı",
              "Kolonlardan inen yük temelden zemine yayılır. Temel ne kadar rijitse basınç o kadar düzgün dağılır; zemin "
              "yumuşaksa (k0 küçük) temel eğilir ve kolon altlarında basınç yoğunlaşır. Bu etkileşimi temel elemanlarını "
              "zemin yaylarına oturtarak bina ile birlikte çözdük; şimdi taban basıncını, oturmayı ve temel kesitlerini denetliyoruz.")
    # tip seçimi
    m = veri["model"]
    plan = (B.xk[-1] - B.xk[0]) * (B.yk[-1] - B.yk[0])
    N_top = toplam_servis or 0.0
    A_ger = N_top / tem["zemin"]["q_em"] if tem["zemin"]["q_em"] else 0.0
    oran = A_ger / plan if plan > 0 else 0.0
    anl.metin(f"**Seçilen tip:** {ad_tip}. Servis yükü ΣN ≈ {_f(N_top)} kN, q_em = {_f(tem['zemin']['q_em'])} kN/m² → gereken taban "
              f"alanı ΣN/q_em ≈ {_f(A_ger)} m²; aks planı {_f(plan)} m² (oran ≈ {_f(oran, 2)}). Oran küçükken tekil temeller "
              "birbirinden uzak kalır; büyüdükçe temeller birleşir: önce aks boyunca şeritler (mütemadi), alanın büyük bölümü "
              "gerekiyorsa bütün planı kaplayan radye. Farklı oturmanın sınırlanması ve yumuşak zemin de sürekli temeli öne çıkarır "
              "(uygulamadaki yaygın ölçüt; yönetmelik eşiği değildir).")
    anl.metin(f"**Model** ({KAYNAK['winkler']}): zemin, temel düğümlerine bağlı birbirinden bağımsız düşey yaylardır "
              f"(ayrık Winkler). k0 = {_f(m['k0'], 0)} kN/m³; her düğümün yayı k_z = k0·A_etki.")
    if tip == "surekli":
        ks = m["kesit"]
        anl.metin(f"Temel kirişleri {m['yon']} doğrultusunda, akslar: {m['akslar']}; ters T kesit B = {_f(ks['B'])} m, h_tabla = "
                  f"{_f(ks['h_tabla'])} m, b_gövde = {_f(ks['b_govde'])} m, h = {_f(ks['h_govde'])} m (tabla dahil); uç taşma "
                  f"{_f(m['tasma'])} m; ağ aralığı a = {_f(m['ag'])} m. Kesit özellikleri (tabla + gövde, ağırlık merkezi alttan y_c):")
        anl.mat(r"A = B\,t + b_w(h - t),\quad y_c = \frac{B t\,\tfrac t2 + b_w(h-t)\left(t + \tfrac{h-t}{2}\right)}{A},\quad "
                r"I = \frac{B t^3}{12} + B t\left(y_c - \tfrac t2\right)^2 + \frac{b_w (h-t)^3}{12} + b_w (h-t)\left(t + \tfrac{h-t}2 - y_c\right)^2")
        anl.mat(rf"A = {_f(ks['A'], 4)}\ \text{{m}}^2,\quad y_c = {_f(ks['y_c'], 3)}\ \text{{m}},\quad I = {_f(ks['I'], 5)}\ \text{{m}}^4,"
                rf"\quad J \approx \sum \beta a c^3 = {_f(ks['J'], 5)}\ \text{{m}}^4")
        anl.mat(r"k_{z,i} = k_0\,B\,l_{etki,i},\qquad l_{etki,i} = \tfrac12 (a_{i-1} + a_i)")
        if m.get("ortak_alan", 0) > 0:
            anl.metin(f"xy ızgarasında iki şeridin kesiştiği {_f(m['ortak_alan'], 3)} m² ortak tabla alanı yay hesabında bir kez sayıldı "
                      "(her iki şeridin düğümlerinden yarı yarıya düşüldü); temel öz ağırlığında da ortak hacim bir kez sayıldı.")
    else:
        anl.metin(f"Plak alanı = aks dış zarfı + {_f(m['tasma'])} m taşma = {_f(m['plak']['X1'] - m['plak']['X0'])} × "
                  f"{_f(m['plak']['Y1'] - m['plak']['Y0'])} m; h = {_f(m['h'])} m. Plak iki doğrultulu ızgara (grillage) ile "
                  f"temsil edildi: {m['plak']['nx']} × {m['plak']['ny']} düğüm, ağ aralığı ≤ {_f(m['ag'])} m (aks çizgileri ızgara "
                  "çizgisi; kolonlar düğümde). Her çubuk, komşu ızgara çizgilerinin ortasına kadar uzanan şeridi temsil eder (kenar "
                  "şeritleri yarım genişlik):")
        anl.mat(r"I_{şerit} = \frac{b\,h^3}{12},\qquad J \approx \frac{b\,h^3}{6},\qquad k_{z,i} = k_0\,A_{etki,i} = k_0\,b_{x,i}\,b_{y,i}")
        anl.metin("J ≈ b·h³/6, plağın burulma rijitliğinin şerit genişliği başına eşdeğeridir (G = E/(2(1+ν)) ile); ızgara "
                  "yöntemi plağın eğilme ve burulmasını çubuklara paylaştıran bir yaklaşımdır." + (
                      f" Kirişli radye: aks çizgilerindeki çubuklar ters T (plak + kiriş gövdesi b = {_f(m['kiris']['b'])}, "
                      f"h = {_f(m['kiris']['h'])} m)." if m.get("kiris") else ""))
    anl.metin(f"Toplam yay rijitliği Σk = {_f(m['yay_toplami'], 0)} kN/m = k0 × taban alanı ({_f(m['taban_alani'], 3)} m²). "
              f"Yatay kararlılık: {'temel düğümlerinde X ve Y ötelemeleri tutulu (dönmeler serbest)' if m['yatay'] == 'tutulu' else 'yatay yaylar k_h = ' + _f(m['kh_oran'], 3) + '·k_z'}. "
              f"Temel öz ağırlığı {_f(m['W_temel'])} kN G durumuna eklendi.")
    anl.metin(f"**Ayrık yay ↔ tutarlı Winkler matrisi:** tutarlı yaklaşımda zemin rijitliği k0·B·∫NᵀN dx ile eleman eğilme "
              f"serbestliklerine tam matris olarak eklenir; ayrık yay aynı toplamı düğümlere toplar (lumped). Karakteristik boy "
              f"1/β, β = ⁴√(k0·B/(4EI)) = {_f(m['beta'], 4)} 1/m; a·β = {_f(m['ag_beta'], 3)}. a·β küçükse (≈ 0,3'ün altı) iki yaklaşım "
              "pratikte aynı sonucu verir (Hetényi sonsuz kiriş çözümüyle sınandı).")
    anl.mat(r"p_i = \frac{F_{yay,i}}{A_{etki,i}} = k_0\,w_i \quad(\text{basınç} +,\ w\ \text{oturma, aşağı} +)")
    # taban basıncı tablosu
    sat = [[s["ad"], _f(s["p_maks"]), _f(s["p_min"]), _f(s["w_maks_mm"], 2), _f(s["DC"], 3)] for s in veri["servis"]]
    anl.metin("**Taban basıncı ve oturma (servis, yük katsayıları 1,0; TS 500 md. 10.1):**\n\n"
              + se._tablo(["Kombinasyon", "p_maks (kN/m²)", "p_min (kN/m²)", "w_maks (mm)", "p_maks/q_em"], sat))
    dg = veri["dugumler"]
    i_max = max(range(len(dg)), key=lambda i: dg[i]["p_kNm2"])
    i_min = min(range(len(dg)), key=lambda i: dg[i]["p_kNm2"])
    anl.metin(f"Kritik bölge: en büyük basınç {info.dugumler[i_max]['adres']} ({_f(dg[i_max]['p_kNm2'])} kN/m², w = {_f(dg[i_max]['w_mm'], 2)} mm), "
              f"en küçük {info.dugumler[i_min]['adres']} ({_f(dg[i_min]['p_kNm2'])} kN/m²). Farklı oturma (komşu kolonlar): "
              f"{veri['farkli_oturma_metin']}" + (f" ({veri['farkli_oturma_yer']})." if veri.get("farkli_oturma_yer") else "."))
    kont = veri["zemin_kontrolleri"]
    anl.metin("**Zemin kontrolleri** (iki ayrı yaklaşım):\n\n" + se._tablo(
        ["Kontrol", "Talep (kN/m²)", "Kapasite (kN/m²)", "D/C", "Kaynak"],
        [[k["ad"], _f(k["talep"]), _f(k["kapasite"]), _f(k["dc"], 3), k["kaynak"]] for k in kont]))
    anl.mat(rf"q_t = \frac{{q_k}}{{\gamma_{{Rv}}}} = \frac{{{_f(veri['q_k'])}}}{{{_f(GAMMA_RV, 1)}}} = {_f(veri['q_t'])}\ \text{{kN/m}}^2"
            rf"\quad(\text{{TBDY Denk. 16.7}})")
    for u in veri["uyarilar"]:
        anl.uyari(u)
    anl.sema("Taban basıncı", [_sema_basinc(B, info, veri)])
    # zımbalama
    z = ic.get("kritik_zimbalama")
    if z is not None:
        anl.metin(f"**Zımbalama** ({KAYNAK['zimbalama']}). En kritik kolon {z['adres']} ({z['konum']} kolon), kombinasyon `{z['kombinasyon']}`:")
        anl.mat(rf"d = h - {_f(PAS, 2)} = {_f(z['d'], 3)}\ \text{{m}},\quad u_p = {_f(z['u_p'], 3)}\ \text{{m}}\ (\text{{kolon yüzünden }} d/2),"
                rf"\quad A_{{zımb}} = {_f(z['A_bolge'], 3)}\ \text{{m}}^2")
        anl.mat(rf"V_{{pd}} = N_d - F_a = N_d - p_d A_{{zımb}} = {_f(z['N_d'])} - {_f(z['p_d'])}\cdot{_f(z['A_bolge'], 3)} = {_f(z['V_pd'])}\ \text{{kN}}")
        anl.mat(rf"\gamma = {_f(z['gamma'], 3)}\ ({z['gamma_kaynak']}),\quad V_{{pr}} = \gamma f_{{ctd}} u_p d = {_f(z['gamma'], 3)}\cdot"
                rf"{_f(z['f_ctd'] * 1000.0, 0)}\cdot{_f(z['u_p'], 3)}\cdot{_f(z['d'], 3)} = {_f(z['V_pr'])}\ \text{{kN}}")
        anl.metin(f"D/C = V_pd/V_pr = **{_f(z['dc'], 3)}**. Radyede zımbalama donatısı hesaba katılmaz (TS 500 md. 10.4.2); yetmezse "
                  "plak kalınlaştırılır ya da kolon altında başlık yapılır.")
        sat = [[t["adres"], t["konum"], _f(t["N_d"]), _f(t["V_pd"]), _f(t["u_p"], 2), _f(t["V_pr"]), _f(t["dc"], 3)]
               for t in sorted((t for t in veri["tasarim"] if t["tur"] == "zimbalama"), key=lambda t: -t["dc"])[:8]]
        anl.metin("**Zımbalama tablosu** (en kritik 8 kolon):\n\n" + se._tablo(["Kolon", "Konum", "N_d", "V_pd", "u_p (m)", "V_pr", "D/C"], sat))
    # donatı özeti
    sat = []
    for t in veri["tasarim"]:
        if t["tur"] == "temel-kirisi":
            sat.append([f"Temel kirişi {t['hat']} ({t['yon']})", f"{_f(t['b'])} × {_f(t['h'])}", f"alt {t['oneri_alt'] or '–'}, üst {t['oneri_ust'] or '–'}",
                        t["etriye"] or "–", _f(t["dc"], 3), t["durum"]])
        elif t["tur"] == "tabla":
            sat.append(["Tabla konsolu (m başına)", f"c = {_f(t['konsol_boyu'])}, h = {_f(t['h'])}", t["oneri_donati"] or "–", "etriyesiz",
                        _f(t["dc"], 3), t["durum"]])
        elif t["tur"] == "radye-serit":
            sat.append([f"Radye {t['yon'].upper()} doğrultusu (m başına)", f"h = {_f(t['h'])}", f"alt {t['oneri_alt'] or '–'}, üst {t['oneri_ust'] or '–'}",
                        "–", _f(t["dc"], 3), t["durum"]])
    if sat:
        anl.metin("**Donatı özeti** (dayanım ve deprem kombinasyonlarının zarfı; TS 500 md. 10.1: katsayılı yükler, örtü ≥ 50 mm; "
                  "eğilmede basınç bölgesine çekme donatısının ≥ 1/3'ü, md. 10.4.3):\n\n"
                  + se._tablo(["Eleman", "Boyut (m)", "Boyuna donatı", "Etriye", "D/C", "Durum"], sat))
    for k in veri["kontroller"]:
        if not k["saglandi"]:
            anl.uyari(f"{k['ad']}: {_f(k['kapasite'])} < {_f(k['talep'])} ({k['kaynak']}).")
    for o in veri["oneriler"][:6]:
        anl.uyari(o)
    if veri["varsayimlar"] or veri["notlar"]:
        anl.metin("**Varsayımlar ve notlar:**\n\n" + "\n".join(f"- {v}" for v in veri["varsayimlar"] + veri["notlar"]))
