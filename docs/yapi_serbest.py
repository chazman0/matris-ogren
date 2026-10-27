# -*- coding: utf-8 -*-
"""Aks sistemi tabanlı düğüm–çubuk–panel modeli (bina JSON ``surum: 3``) — Matris Öğren bina motorunun genel katmanı.

``yapi.bina_coz`` bina ``surum >= 3`` ise (ya da ``cubuklar`` / ``paneller`` listesi varsa) buraya yönlendirir. Aks–kat
elemanları (kolonlar, kirisler, dosemeler) varsa önce aynı kurallarla genel listeye çevrilir (``docs/model_ops.js``
``genellestir`` ile birebir), böylece aynı bina iki yoldan aynı sonucu verir.

Modelleme ilkesi (tasarım belgesi §19): her düğüm bir **aks kesişimi** (X aksı × Y aksı × Z aksı; ek kartezyen ya da
silindirik aks sistemleri) ya da bir çubuğun **bölme / kesişim** noktasıdır. Aks taşınınca ona bağlı düğümler (bölme
düğümleri dahil) birlikte taşınır: düğüm konumu her çözümde akslardan yeniden hesaplanır.

Düğüm başvurusu (REF)::

    {"aks": ["B", "3"], "z": "Saçak"}                       # GLOBAL akslar
    {"sistem": "KANAT-B", "aks": ["C", "2"], "z": "±0.00"}   # ek aks sistemi (silindirikte aks = [r, teta])
    {"aks": ["B", "3"], "kat": 1}                            # eski aks–kat başvurusu (= kat 1'in Z aksı)
    {"dugum": 100004}                                        # dugumler kaydı (bölme / kesişim / aks)
    {"X": .., "Y": .., "Z": ..}                              # yalnız geriye uyum (serbest koordinat)

``dugumler`` kayıtları: ``{"no", "tur": "bolme", "cubuk_i": REF, "cubuk_j": REF, "oran": t}``,
``{"no", "tur": "kesisim", "a": [REF, REF], "b": [REF, REF]}``, ``{"no", "aks": [...], "z" | "kat": ..}`` ya da
``{"no", "X", "Y", "Z"}`` (geriye uyum). Kayıtlar birbirine başvurabilir (yinelemeli çözüm, döngü denetimi).

Akış: okuma ve doğrulama → paneller → çubuklar yük dağıtımı (iki doğrultulu: açıortay bölgeleri, dikdörtgende TS 500
45° kuralıyla aynı; tek doğrultulu; yok) → öz ağırlık, duvar, kar μ1(α), rüzgâr (panel normaline, TS 498:2021 Şekil 1),
kren (K durumu, konum başına alt durum) → kütle seviyeleri ve TBDY eşdeğer deprem yükü (yapi hattı) → çözüm (yalnız
çekme çubuk varsa kombinasyon başına doğrudan) → kombinasyon, zarf → ÇYTHYE / TS 500 tahkikleri, kesit önerisi.
"""
from __future__ import annotations

import copy
import json
import math


# ============================================================================
# Şablonlar (surum 3). yapi içe aktarılmadan ÖNCE tanımlanır: yapi.py bu sözlüğü modül sonunda BINA_SABLONLARI'na
# ekler (iki yönlü içe aktarma güvenli olsun diye bu bölüm yalnız math kullanır).
# ============================================================================
def _zaks(ad, konum, kat=None):
    r = {"ad": ad, "konum": round(float(konum), 6)}
    if kat is not None:
        r["kat"] = kat
    return r


def _sablon_sanayi(kren=True):
    """4 açıklıklı (4 × 20 m) çelik sanayi yapısı: 7 çerçeve @ 6 m, saçak 8 m, beşik çatılar, vuteli mertek, aşıklar,
    çatı ve cephe X çaprazları, rüzgâr kolonları, isteğe bağlı kren yolu (1. holde)."""
    X = [("A", 0.0), ("B", 10.0), ("C", 20.0), ("D", 30.0), ("E", 40.0), ("F", 50.0), ("G", 60.0), ("H", 70.0), ("I", 80.0)]
    kolon_x = ["A", "C", "E", "G", "I"]
    mahya_x = ["B", "D", "F", "H"]
    Yk = [str(j) for j in range(1, 8)]
    sacak, mahya, kren_z = 8.0, 9.75, 6.0
    L_mertek = math.hypot(10.0, mahya - sacak)
    vute_boy = 2.0
    o_v, o_p = vute_boy / L_mertek, 0.55
    Z = [_zaks("±0.00", 0.0, 0), _zaks("Kren", kren_z), _zaks("Saçak", sacak, 1), _zaks("Mahya", mahya)]
    if not kren:
        Z = [z for z in Z if z["ad"] != "Kren"]

    def A(x, y, z):
        return {"aks": [x, y], "z": z}

    dugumler, cubuklar, paneller = [], [], []
    no_d = [100000]
    bolme = {}

    def bolme_dugum(xa, xr, y, oran, ad):
        no_d[0] += 1
        dugumler.append({"no": no_d[0], "tur": "bolme", "cubuk_i": A(xa, y, "Saçak"), "cubuk_j": A(xr, y, "Mahya"),
                         "oran": round(oran, 6), "ad": ad})
        return no_d[0]

    for y in Yk:
        for h in range(4):
            for taraf, xa in (("sol", kolon_x[h]), ("sag", kolon_x[h + 1])):
                bolme[(y, h, taraf, "V")] = bolme_dugum(xa, mahya_x[h], y, o_v, f"Vute ucu {xa}{y}")
                bolme[(y, h, taraf, "P")] = bolme_dugum(xa, mahya_x[h], y, o_p, f"Aşık {xa}{y}")
    nc = [0]

    def cubuk(i, j, tur, kesit, **oz):
        nc[0] += 1
        c = {"no": nc[0], "i": i, "j": j, "tur": tur, "kesit": kesit}
        c.update(oz)
        cubuklar.append(c)
        return nc[0]

    mafsal = {"i": ["My", "Mz"], "j": ["My", "Mz"]}
    D = lambda n: {"dugum": n}  # noqa: E731
    egim = math.degrees(math.atan2(mahya - sacak, 10.0))
    for y in Yk:
        for x in kolon_x:
            if kren and x in ("A", "C"):
                cubuk(A(x, y, "±0.00"), A(x, y, "Kren"), "kolon", "KOLON", grup="KOLON")
                cubuk(A(x, y, "Kren"), A(x, y, "Saçak"), "kolon", "KOLON", grup="KOLON")
            else:
                cubuk(A(x, y, "±0.00"), A(x, y, "Saçak"), "kolon", "KOLON", grup="KOLON")
        for h in range(4):
            for taraf, xa in (("sol", kolon_x[h]), ("sag", kolon_x[h + 1])):
                v, p = bolme[(y, h, taraf, "V")], bolme[(y, h, taraf, "P")]
                cubuk(A(xa, y, "Saçak"), D(v), "kiris", "VUTE", grup="VUTE")
                cubuk(D(v), D(p), "kiris", "MERTEK", grup="MERTEK")
                cubuk(D(p), A(mahya_x[h], y, "Mahya"), "kiris", "MERTEK", grup="MERTEK")
    # rüzgâr kolonları (kalkan duvarlar, mahya akslarında; üstte mafsallı ve düşeyde kayıcı: çatı yükü almaz, yatay mesnet olur)
    for y in (Yk[0], Yk[-1]):
        for xr in mahya_x:
            cubuk(A(xr, y, "±0.00"), A(xr, y, "Mahya"), "kolon", "RUZGAR-KOLONU", aci=90, serbest={"j": ["N", "My", "Mz"]},
                  grup="RUZGAR-KOLONU", Lb=round((mahya) / 2.0, 3), K=[1.0, 0.5])   # cephe kuşağı orta yükseklikte tutar
    # boyuna elemanlar: saçak / dere kirişleri, mahya ve ara aşıklar
    for k in range(len(Yk) - 1):
        y0, y1 = Yk[k], Yk[k + 1]
        for x in kolon_x:
            cubuk(A(x, y0, "Saçak"), A(x, y1, "Saçak"), "kiris", "SACAK", serbest=mafsal, grup="SACAK-KIRISI")
        for h, xr in enumerate(mahya_x):
            cubuk(A(xr, y0, "Mahya"), A(xr, y1, "Mahya"), "asik", "ASIK", serbest=mafsal, grup="MAHYA-ASIGI")
            for taraf in ("sol", "sag"):
                a = -egim if taraf == "sol" else egim
                cubuk(D(bolme[(y0, h, taraf, "P")]), D(bolme[(y1, h, taraf, "P")]), "asik", "ASIK", serbest=mafsal,
                      aci=round(a, 6), grup="ARA-ASIK")
    # çatı X çaprazları (uç gözler, her çatı yüzünde aşık aralığı başına bir X) ve düşey X çaprazlar (uç gözler, bütün kolon akslarında)
    for k in (0, len(Yk) - 2):
        y0, y1 = Yk[k], Yk[k + 1]
        for h, xr in enumerate(mahya_x):
            for taraf, xa in (("sol", kolon_x[h]), ("sag", kolon_x[h + 1])):
                p0, p1 = D(bolme[(y0, h, taraf, "P")]), D(bolme[(y1, h, taraf, "P")])
                for a0, a1, b0, b1 in ((A(xa, y0, "Saçak"), A(xa, y1, "Saçak"), p0, p1), (p0, p1, A(xr, y0, "Mahya"), A(xr, y1, "Mahya"))):
                    cubuk(a0, b1, "capraz", "CATI-CAPRAZ", serbest=mafsal, grup="CATI-CAPRAZI")
                    cubuk(a1, b0, "capraz", "CATI-CAPRAZ", serbest=mafsal, grup="CATI-CAPRAZI")
        for x in kolon_x:
            cubuk(A(x, y0, "±0.00"), A(x, y1, "Saçak"), "capraz", "CEPHE-CAPRAZ", serbest=mafsal, grup="DUSEY-CAPRAZ")
            cubuk(A(x, y1, "±0.00"), A(x, y0, "Saçak"), "capraz", "CEPHE-CAPRAZ", serbest=mafsal, grup="DUSEY-CAPRAZ")
    # kren yolu (1. hol: A ve C aksları, kren kotunda; basit kirişler)
    kren_kayit = []
    if kren:
        yollar = []
        for x in ("A", "C"):
            yol = []
            for k in range(len(Yk) - 1):
                yol.append(cubuk(A(x, Yk[k], "Kren"), A(x, Yk[k + 1], "Kren"), "kren", "KREN-KIRISI", serbest=mafsal,
                                 grup="KREN-KIRISI"))
            yollar.append(yol)
        for n, yol in enumerate(yollar, start=1):
            kren_kayit.append({"no": n, "yol": yol, "kopru": 1,
                               "tekerlek": {"P_maks": 60.0, "P_min": 20.0, "H_yanal": 6.0, "H_fren": 5.0, "aralik": 3.0, "adet": 2},
                               "dinamik": 1.25, "konum_sayisi": 5,
                               "kaynak": "öğretici örnek: 10 t köprülü kren (üretici verisiyle doğrulanmalı)"})
    # paneller: çatı (aşıklar arası, aşıklara tek doğrultulu), yan cepheler ve kalkan duvarlar (kolonlara tek doğrultulu)
    npn = [0]

    def panel(kose, **oz):
        npn[0] += 1
        p = {"no": npn[0], "kose": kose}
        p.update(oz)
        paneller.append(p)

    cati = {"tur": "cati", "kalinlik": 0.0, "g": 0.25, "q": 0.4, "kar": True, "ruzgar": {"cp": "otomatik"}, "dagitim": "tek-13"}
    cephe = {"tur": "cephe", "kalinlik": 0.0, "g": 0.15, "q": 0.0, "kar": False, "ruzgar": {"cp": "otomatik"}, "dagitim": "tek-24"}
    for k in range(len(Yk) - 1):
        y0, y1 = Yk[k], Yk[k + 1]
        for h, xr in enumerate(mahya_x):
            for taraf, xa in (("sol", kolon_x[h]), ("sag", kolon_x[h + 1])):
                p0, p1 = bolme[(y0, h, taraf, "P")], bolme[(y1, h, taraf, "P")]
                panel([A(xa, y0, "Saçak"), A(xa, y1, "Saçak"), D(p1), D(p0)], **cati)
                panel([D(p0), D(p1), A(xr, y1, "Mahya"), A(xr, y0, "Mahya")], **cati)
        for x in ("A", "I"):
            panel([A(x, y0, "±0.00"), A(x, y1, "±0.00"), A(x, y1, "Saçak"), A(x, y0, "Saçak")], **cephe)
    for y in (Yk[0], Yk[-1]):
        for h, xr in enumerate(mahya_x):
            xa, xb = kolon_x[h], kolon_x[h + 1]
            panel([A(xa, y, "±0.00"), A(xr, y, "±0.00"), A(xr, y, "Mahya"), A(xa, y, "Saçak")], **cephe)
            panel([A(xr, y, "±0.00"), A(xb, y, "±0.00"), A(xb, y, "Saçak"), A(xr, y, "Mahya")], **cephe)
    b = {
        "tur": "bina", "surum": 3, "sablon": "celik-sanayi-4hol",
        "baslik": "Çelik sanayi yapısı: 4 hol (4 × 20 m), 7 çerçeve" + (", kren yolu" if kren else ""),
        "aciklama": "4 açıklıklı (4 × 20 m) beşik çatılı çelik sanayi yapısı; 7 çerçeve @ 6 m, saçak 8 m, mahya 9,75 m (α ≈ 10°). "
                    "Çerçeveler: HEA kolonlar (tabanda ankastre), vuteli IPE mertekler (vute 2 m, +40 cm), dere ve saçak "
                    "kirişleri mafsallı; aşıklar (mahya + ara aşık) mafsallı, ara aşıklar çatı eğimiyle döndürülmüş (aci). "
                    "Boyuna doğrultuda uç gözlerde çatı X çaprazları (aşık aralığı başına) ve bütün kolon akslarında düşey X çaprazlar; kalkan duvarlarda "
                    "mahya akslarında rüzgâr kolonları. Sac çatı paneli (kalınlık 0: taşıyıcı değil) aşıklara, cephe "
                    "panelleri kolonlara tek doğrultuda yük aktarır; çatı seviyesinde esnek diyafram. 1. holde kren yolu "
                    "(A ve C aksları, 6 m kotunda; K yük durumu, 5 konum). Tüm düğümler aks kesişimi ya da mertek bölme "
                    "noktasıdır (aks taşınınca birlikte taşınır).",
        "sistem": "celik", "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "akslar": {"x": [{"ad": a, "konum": k} for a, k in X], "y": [{"ad": a, "konum": 6.0 * i} for i, a in enumerate(Yk)], "z": Z},
        "katlar": [{"no": 0, "ad": "±0.00", "kot": 0.0}, {"no": 1, "ad": "Saçak", "kot": sacak}],
        "malzemeler": {"S275": {"kutuphane": "S275"}, "S355": {"kutuphane": "S355"}},
        "kesitler": {
            "KOLON": {"tip": "profil", "profil": "HEA 320", "malzeme": "S275"},
            "MERTEK": {"tip": "profil", "profil": "IPE 400", "malzeme": "S275"},
            "VUTE": {"tip": "vute", "temel": "MERTEK", "ek_yukseklik": 0.40, "boy": vute_boy},
            "RUZGAR-KOLONU": {"tip": "profil", "profil": "IPE 360", "malzeme": "S275"},
            "SACAK": {"tip": "profil", "profil": "IPE 270", "malzeme": "S275"},
            "ASIK": {"tip": "profil", "profil": "IPE 270", "malzeme": "S275"},
            "CATI-CAPRAZ": {"tip": "profil", "profil": "BORU 168.3x6.3", "malzeme": "S275"},
            "CEPHE-CAPRAZ": {"tip": "profil", "profil": "BORU 168.3x6.3", "malzeme": "S275"},
            "KREN-KIRISI": {"tip": "profil", "profil": "HEA 300", "malzeme": "S275"},
        },
        "dugumler": dugumler, "cubuklar": cubuklar, "paneller": paneller, "mesnetler": [], "kren": kren_kayit,
        "ek_yukler": [],
        "temeller": {"tip": "tekil", "varsayilan": {"B": 1.8, "L": 1.8, "h": 0.7}, "zemin": {"q_em": 200, "k0": 20000},
                     "mesnet": "ankastre", "ozel": []},
        "yuk_durumlari": {"G": {"acik": True}, "Q": {"acik": True}, "S": {"acik": True, "bolge": 2, "rakim": 400},
                          "W": {"acik": True}, "E": {"acik": True}},
        "deprem": {"etkin": True, "SS": 0.5, "S1": 0.15, "SS_DD3": 0.2, "S1_DD3": 0.06, "zemin_sinifi": "ZC", "DD": "DD-2", "BKS": 3,
                   "tasiyici": "celik-mcm-merkezi-capraz-yuksek", "periyot": "otomatik", "diyafram": "esnek", "dismerkezlik": 0.05,
                   "dolgu": "esnek"},
        "kombinasyon_kumesi": "cythye_ydkt",
        "analiz": {"diyagram_nokta": 9, "vute_parca": 1, "diyafram": {"1": "esnek"}},
    }
    return b


def _sablon_cbf():
    """3 katlı çelik merkezi çaprazlı çerçeve: X yönünde ters V (chevron), Y yönünde X çaprazlı gözler; mafsallı kirişler."""
    X = [("A", 0.0), ("B", 6.0), ("C", 12.0), ("D", 18.0)]
    Yk = [("1", 0.0), ("2", 6.0), ("3", 12.0)]
    zad = ["±0.00", "+3.50", "+7.00", "+10.50"]
    Z = [_zaks(a, 3.5 * k, k) for k, a in enumerate(zad)]

    def A(x, y, k):
        return {"aks": [x, y], "z": zad[k]}

    dugumler, cubuklar, paneller = [], [], []
    nd = [100000]
    nc = [0]

    def cubuk(i, j, tur, kesit, **oz):
        nc[0] += 1
        c = {"no": nc[0], "i": i, "j": j, "tur": tur, "kesit": kesit}
        c.update(oz)
        cubuklar.append(c)
        return nc[0]

    mafsal = {"i": ["My", "Mz"], "j": ["My", "Mz"]}
    xs, ys = [a for a, _ in X], [a for a, _ in Yk]
    orta = {}
    for k in range(1, 4):
        for y in ("1", "3"):                      # ters V gözleri: B–C açıklığı, 1 ve 3 akslarında
            nd[0] += 1
            dugumler.append({"no": nd[0], "tur": "bolme", "cubuk_i": A("B", y, k), "cubuk_j": A("C", y, k), "oran": 0.5,
                             "ad": f"Ters V düğümü B–C/{y}, {zad[k]}"})
            orta[(y, k)] = nd[0]
    nd[0] += 1                                    # 1. kat A aksı X çaprazının kesişim düğümü
    kes = nd[0]
    dugumler.append({"no": kes, "tur": "kesisim", "a": [A("A", "1", 0), A("A", "2", 1)], "b": [A("A", "2", 0), A("A", "1", 1)],
                     "ad": "X çapraz kesişimi A/1–2, 1. kat"})
    for k in range(1, 4):
        for x in xs:
            for y in ys:
                cubuk(A(x, y, k - 1), A(x, y, k), "kolon", "KOLON", grup="KOLON", kat=k)
        for y in ys:                              # X yönü kirişleri (ters V gözünde bölme düğümünden geçer)
            for a, b_ in zip(xs, xs[1:]):
                if a == "B" and y in ("1", "3"):
                    m = {"dugum": orta[(y, k)]}
                    cubuk(A(a, y, k), m, "kiris", "KIRIS-CAPRAZLI", serbest={"i": ["My", "Mz"]}, grup="KIRIS", kat=k)
                    cubuk(m, A(b_, y, k), "kiris", "KIRIS-CAPRAZLI", serbest={"j": ["My", "Mz"]}, grup="KIRIS", kat=k)
                else:
                    cubuk(A(a, y, k), A(b_, y, k), "kiris", "KIRIS", serbest=mafsal, grup="KIRIS", kat=k)
        for x in xs:                              # Y yönü kirişleri
            for a, b_ in zip(ys, ys[1:]):
                cubuk(A(x, a, k), A(x, b_, k), "kiris", "KIRIS", serbest=mafsal, grup="KIRIS", kat=k)
        for y in ("1", "3"):                      # ters V çaprazları
            m = {"dugum": orta[(y, k)]}
            cubuk(A("B", y, k - 1), m, "capraz", "CAPRAZ-V", serbest=mafsal, grup="TERS-V", kat=k)
            cubuk(A("C", y, k - 1), m, "capraz", "CAPRAZ-V", serbest=mafsal, grup="TERS-V", kat=k)
        for x in ("A", "D"):                      # X çaprazları (1–2 gözü)
            if x == "A" and k == 1:
                m = {"dugum": kes}
                for p in (A("A", "1", 0), A("A", "2", 1), A("A", "2", 0), A("A", "1", 1)):   # kesişimde sürekli, uçta mafsallı
                    cubuk(p, m, "capraz", "CAPRAZ-X", serbest={"i": ["My", "Mz"]}, grup="X-CAPRAZ", kat=k)
            else:
                cubuk(A(x, "1", k - 1), A(x, "2", k), "capraz", "CAPRAZ-X", serbest=mafsal, grup="X-CAPRAZ", kat=k)
                cubuk(A(x, "2", k - 1), A(x, "1", k), "capraz", "CAPRAZ-X", serbest=mafsal, grup="X-CAPRAZ", kat=k)
        npn = len(paneller)
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                npn += 1
                paneller.append({"no": npn, "kose": [A(xs[i], ys[j], k), A(xs[i + 1], ys[j], k), A(xs[i + 1], ys[j + 1], k),
                                                     A(xs[i], ys[j + 1], k)], "tur": "doseme", "kalinlik": 0.12,
                                 "g": 1.5, "kullanim": "cati-gezilen" if k == 3 else "ofis", "kar": k == 3, "dagitim": "iki", "kat": k})
    return {
        "tur": "bina", "surum": 3, "sablon": "celik-cbf-3kat",
        "baslik": "3 katlı çelik merkezi çaprazlı çerçeve (ters V ve X)",
        "aciklama": "3 × 6 m (X) ve 2 × 6 m (Y) planlı, 3 katlı (3,5 m) çelik bina. Kirişler mafsallı (basit), kolonlar sürekli: yatay "
                    "yükü yalnız merkezi çaprazlar taşır. X yönünde 1 ve 3 akslarının B–C gözlerinde ters V (chevron) çaprazlar "
                    "kiriş ortasındaki bölme düğümüne bağlanır; Y yönünde A ve D akslarının 1–2 gözlerinde X çaprazlar (A aksı 1. katta "
                    "kesişim düğümlü). 12 cm betonarme döşeme (rijit diyafram), ofis yükü. TBDY 2018 SDY merkezi çaprazlı çerçeve "
                    "(C13, R = 5, D = 2): çapraz KL/i ≤ 200, Tablo 9.3 genişlik/kalınlık sınırları denetlenir.",
        "sistem": "celik", "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "akslar": {"x": [{"ad": a, "konum": k} for a, k in X], "y": [{"ad": a, "konum": k} for a, k in Yk], "z": Z},
        "katlar": [{"no": k, "ad": a, "kot": 3.5 * k} for k, a in enumerate(zad)],
        "malzemeler": {"S275": {"kutuphane": "S275"}, "S355": {"kutuphane": "S355"}},
        "kesitler": {
            "KOLON": {"tip": "profil", "profil": "HEB 240", "malzeme": "S355"},
            "KIRIS": {"tip": "profil", "profil": "IPE 330", "malzeme": "S275"},
            "KIRIS-CAPRAZLI": {"tip": "profil", "profil": "IPE 400", "malzeme": "S275"},
            "CAPRAZ-V": {"tip": "profil", "profil": "BORU 168.3x6.3", "malzeme": "S275"},
            "CAPRAZ-X": {"tip": "profil", "profil": "BORU 168.3x6.3", "malzeme": "S275"},
        },
        "dugumler": dugumler, "cubuklar": cubuklar, "paneller": paneller, "mesnetler": [], "ek_yukler": [],
        "temeller": {"tip": "tekil", "varsayilan": {"B": 2.0, "L": 2.0, "h": 0.7}, "zemin": {"q_em": 250, "k0": 25000},
                     "mesnet": "mafsal", "ozel": []},
        "yuk_durumlari": {"G": {"acik": True}, "Q": {"acik": True}, "S": {"acik": True, "bolge": 3, "rakim": 0},
                          "W": {"acik": True}, "E": {"acik": True}},
        "deprem": {"etkin": True, "SS": 1.0, "S1": 0.3, "SS_DD3": 0.4, "S1_DD3": 0.12, "zemin_sinifi": "ZC", "DD": "DD-2",
                   "BKS": 3, "tasiyici": "celik-merkezi-capraz", "periyot": "otomatik", "diyafram": "rijit",
                   "dismerkezlik": 0.05, "dolgu": "bitisik"},
        "kombinasyon_kumesi": "cythye_ydkt",
        "analiz": {"diyagram_nokta": 11},
    }


SERBEST_SABLONLAR = {
    "celik-sanayi-4hol": _sablon_sanayi(kren=True),
    "celik-cbf-3kat": _sablon_cbf(),
}


# ============================================================================
# Motor bağımlılıkları (şablonlardan SONRA: yapi.py modül sonunda bu dosyadan SERBEST_SABLONLAR alır)
# ============================================================================
import importlib  # noqa: E402
import warnings  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import sympy as sp  # noqa: E402

import matris_ogren as mo  # noqa: E402
import sonlu_eleman as se  # noqa: E402
import yapi as Y  # noqa: E402
import yapi_veri as yv  # noqa: E402

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

MatrisHatasi = mo.MatrisHatasi
TOL = 0.001                      # REF / düğüm birleştirme toleransı (m)
EN_FAZLA_SD = 2000               # tarayıcıda yoğun çözüm sınırı (serbest modelde aks–kat sınırından biraz geniş)
ILK_SERBEST = 100001
_IC_DUGUM = 800001               # vute ara düğümleri (yalnız motor)
_EFENDI = 900000                 # rijit diyafram efendi düğümü = 900000 + kat
_TURLER = ("kolon", "kiris", "capraz", "makas-ust", "makas-alt", "makas-dikme", "makas-diyagonal", "asik", "kren", "bag", "diger")
_CUBUK_TURLERI = ("capraz", "makas-ust", "makas-alt", "makas-dikme", "makas-diyagonal")   # eksenel (çubuk) tahkiki
_SERBEST_ADLAR = ("N", "Vy", "Vz", "T", "My", "Mz")
_PANEL_TURLERI = ("doseme", "cati", "cephe")
_DAGITIMLAR = ("iki", "tek-13", "tek-24", "yok")
_SEVIYE_TOL = 0.3                # kütle seviyesi: düğüm Z'si seviyeye ≤ 0,3 m ise o seviye
_r, _r5, _r6, _f = Y._r, Y._r5, Y._r6, Y._f


def _vek(a, b):
    return (b[0] - a[0], b[1] - a[1], b[2] - a[2])


def _ic(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _dis(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _boy(a):
    return math.sqrt(_ic(a, a))


def _birim(a):
    L = _boy(a)
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-15 else (0.0, 0.0, 0.0)


def _olc(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _top(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def serbest_mi(bina):
    """Bina genel (surum 3) yolla mı çözülür: surum ≥ 3 ya da cubuklar/paneller listesi var."""
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError:
            return False
    if not isinstance(bina, dict):
        return False
    try:
        surum = int(bina.get("surum") or 1)
    except (TypeError, ValueError):
        surum = 1
    return surum >= 3 or bool(bina.get("cubuklar")) or bool(bina.get("paneller"))


# ============================================================================
# 1) Akslar, aks sistemleri, seviyeler (kat = Z aksı alt kümesi)
# ============================================================================
def _aks_listesi(liste, ad_yon, sistem, aci=False):
    if liste is None:
        return []
    if not isinstance(liste, list):
        raise MatrisHatasi(f"{sistem}: {ad_yon} aksları bir liste olmalı: [{{\"ad\": \"A\", \"konum\": 0}}, ...].")
    out, gor = [], set()
    for k, a in enumerate(liste, start=1):
        if not isinstance(a, dict):
            raise MatrisHatasi(f"{sistem}: {ad_yon} aksı {k} sözlük olmalı ({{\"ad\": \"A\", \"konum\": 0}}).")
        ad = str(a.get("ad", "")).strip()
        if not ad:
            raise MatrisHatasi(f"{sistem}: {ad_yon} aksı {k}: 'ad' boş.")
        if ad in gor:
            raise MatrisHatasi(f"{sistem}: {ad_yon} aks adı {ad!r} tekrarlı; aks adları sistem içinde benzersiz olmalı.")
        gor.add(ad)
        r = {"ad": ad, "konum": Y._sayi(a.get("konum"), f"{sistem}: {ad_yon} aksı {ad!r}: konum" + (" (derece)" if aci else " (m)"))}
        if a.get("kat") not in (None, ""):
            r["kat"] = Y._tam(a.get("kat"), f"{sistem}: Z aksı {ad!r}: kat")
        for alan in ("tur", "gorunur", "balon"):
            if alan in a:
                r[alan] = a[alan]
        out.append(r)
    out.sort(key=lambda a: a["konum"])
    return out


def _akslari_oku(B, bina):
    ak = bina.get("akslar") if isinstance(bina.get("akslar"), dict) else {}
    xs = _aks_listesi(ak.get("x"), "X", "GLOBAL")
    ys = _aks_listesi(ak.get("y"), "Y", "GLOBAL")
    katlar_ham = bina.get("katlar") if isinstance(bina.get("katlar"), list) else []
    if ak.get("z"):
        zs = _aks_listesi(ak.get("z"), "Z", "GLOBAL")
    else:      # geriye uyum: Z aksları katlardan türetilir
        zs = []
        for k, kt in enumerate(katlar_ham):
            if not isinstance(kt, dict):
                raise MatrisHatasi(f"Kat {k}: sözlük olmalı ({{\"no\": 1, \"kot\": 3.0}}).")
            no = Y._tam(kt.get("no", k), f"Kat {k}: no")
            zs.append({"ad": str(kt.get("ad") or (f"{no}. kat" if no else "Temel")), "konum": Y._sayi(kt.get("kot"), f"Kat {no}: kot"),
                       "kat": no})
        zs.sort(key=lambda a: a["konum"])
        if len({z["ad"] for z in zs}) != len(zs):
            for z in zs:
                z["ad"] = f"k{z['kat']}"
    B.akslar = {"x": xs, "y": ys, "z": zs}
    # seviyeler (katlar): Z akslarının "kat" işaretlileri; yoksa katlar listesi
    seviye = {}
    for z in zs:
        if "kat" in z:
            if z["kat"] in seviye:
                raise MatrisHatasi(f"Kat {z['kat']} iki Z aksına verilmiş ({seviye[z['kat']]['ad']!r}, {z['ad']!r}); her kat tek Z aksıdır.")
            seviye[z["kat"]] = {"no": z["kat"], "ad": z["ad"], "kot": z["konum"], "z": z["ad"]}
    if not seviye and katlar_ham:
        for k, kt in enumerate(katlar_ham):
            no = Y._tam(kt.get("no", k), f"Kat {k}: no")
            seviye[no] = {"no": no, "ad": str(kt.get("ad") or f"{no}. kat"), "kot": Y._sayi(kt.get("kot"), f"Kat {no}: kot"), "z": None}
    B.katlar = [seviye[k] for k in sorted(seviye)]
    if B.katlar and [kt["no"] for kt in B.katlar] != list(range(len(B.katlar))):
        raise MatrisHatasi(f"Kat numaraları 0'dan başlayıp ardışık olmalı (temel = 0): {[kt['no'] for kt in B.katlar]}.")
    for a, b in zip(B.katlar, B.katlar[1:]):
        b["h"] = b["kot"] - a["kot"]
        if b["h"] <= 0.3:
            raise MatrisHatasi(f"Kat {b['no']} ({b['ad']}) kotu {b['kot']} alttaki katın kotundan ({a['kot']}) en az 0,3 m büyük olmalı.")
    if B.katlar:
        B.katlar[0]["h"] = 0.0
    B.sistemler = {"GLOBAL": {"ad": "GLOBAL", "tur": "kartezyen", "orijin": (0.0, 0.0, 0.0), "aci": 0.0,
                              "a1": {a["ad"]: a["konum"] for a in xs}, "a2": {a["ad"]: a["konum"] for a in ys},
                              "z": {a["ad"]: a["konum"] for a in zs}, "s1": [a["ad"] for a in xs], "s2": [a["ad"] for a in ys],
                              "z_global": False}}
    for k, s in enumerate(bina.get("aks_sistemleri") or [], start=1):
        if not isinstance(s, dict):
            raise MatrisHatasi(f"aks_sistemleri[{k}] sözlük olmalı.")
        ad = str(s.get("ad") or "").strip()
        if not ad or ad == "GLOBAL" or ad in B.sistemler:
            raise MatrisHatasi(f"aks_sistemleri[{k}]: ad {ad!r} boş, 'GLOBAL' ya da tekrarlı olamaz.")
        tur = str(s.get("tur") or "kartezyen").strip().lower()
        if tur not in ("kartezyen", "silindirik"):
            raise MatrisHatasi(f"Aks sistemi {ad!r}: tur {tur!r}; 'kartezyen' ya da 'silindirik' olmalı.")
        o = s.get("orijin") or [0, 0, 0]
        if not isinstance(o, (list, tuple)) or len(o) not in (2, 3):
            raise MatrisHatasi(f"Aks sistemi {ad!r}: orijin [X, Y, Z] olmalı.")
        org = tuple(Y._sayi(v, f"Aks sistemi {ad!r}: orijin") for v in (list(o) + [0.0])[:3])
        aci = Y._sayi(s.get("aci", 0.0), f"Aks sistemi {ad!r}: aci (derece)")
        if tur == "kartezyen":
            l1, l2 = _aks_listesi(s.get("x"), "X", ad), _aks_listesi(s.get("y"), "Y", ad)
        else:
            l1, l2 = _aks_listesi(s.get("r"), "r", ad), _aks_listesi(s.get("teta"), "teta", ad, aci=True)
        zl = _aks_listesi(s.get("z"), "Z", ad) if s.get("z") else None
        B.sistemler[ad] = {"ad": ad, "tur": tur, "orijin": org, "aci": aci, "a1": {a["ad"]: a["konum"] for a in l1},
                           "a2": {a["ad"]: a["konum"] for a in l2}, "z": {a["ad"]: a["konum"] for a in zl} if zl else B.sistemler["GLOBAL"]["z"],
                           "s1": [a["ad"] for a in l1], "s2": [a["ad"] for a in l2], "z_global": zl is None,
                           "listeler": {"1": l1, "2": l2, "z": zl}}


def _kat_kotu(B, kat, ad):
    for kt in B.katlar:
        if kt["no"] == kat:
            return kt["kot"]
    raise MatrisHatasi(f"{ad}: kat {kat} tanımsız. Tanımlı katlar: {[kt['no'] for kt in B.katlar]} (Z akslarında 'kat' alanı).")


# ============================================================================
# 2) Düğüm çözümleyici (REF → konum → düğüm no)
# ============================================================================
class _Cozucu:
    """REF'leri düğüm numarasına çevirir. Konumlar akslardan (ve bölme/kesişim kayıtlarından, yinelemeli) hesaplanır;
    1 mm içindeki konumlar tek düğümdür."""

    def __init__(self, B, kayitlar):
        self.B = B
        self.kayit = {}
        for k, d in enumerate(kayitlar or [], start=1):
            if not isinstance(d, dict):
                raise MatrisHatasi(f"dugumler[{k}] sözlük olmalı.")
            no = Y._tam(d.get("no"), f"dugumler[{k}]: no")
            if no in self.kayit:
                raise MatrisHatasi(f"Düğüm numarası {no} dugumler listesinde tekrarlı.")
            self.kayit[no] = d
        self.konum = {}           # kayıt no → (X, Y, Z)
        self.yigin = []
        self.dugum = {}           # model düğümleri: no → {no, X, Y, Z, tur, aks, ...}
        self.izgara = {}
        self.takma = {}           # çakışan kayıt → asıl düğüm
        self._sira = 500000

    # --- aks konumu
    def aks(self, sistem, aks, z, kat, ad):
        S = self.B.sistemler.get(sistem or "GLOBAL")
        if S is None:
            raise MatrisHatasi(f"{ad}: aks sistemi {sistem!r} tanımsız. Tanımlı: {', '.join(self.B.sistemler)}.")
        if not isinstance(aks, (list, tuple)) or len(aks) != 2:
            raise MatrisHatasi(f"{ad}: aks iki öğeli olmalı, örn. [\"B\", \"2\"] (girilen: {aks!r}).")
        a1, a2 = str(aks[0]).strip(), str(aks[1]).strip()
        if a1 not in S["a1"]:
            raise MatrisHatasi(f"{ad}: {S['ad']} sisteminde {a1!r} aksı yok. Tanımlı: {', '.join(S['s1'])}.")
        if a2 not in S["a2"]:
            raise MatrisHatasi(f"{ad}: {S['ad']} sisteminde {a2!r} aksı yok. Tanımlı: {', '.join(S['s2'])}.")
        if kat is not None:
            Zl = _kat_kotu(self.B, Y._tam(kat, f"{ad}: kat"), ad)
            z_ad = next((kt["z"] for kt in self.B.katlar if kt["no"] == int(kat)), None) or f"k{kat}"
            yerel_z = False
        else:
            z_ad = str(z).strip() if z is not None else None
            if z_ad not in S["z"]:
                raise MatrisHatasi(f"{ad}: Z aksı {z!r} tanımsız. Tanımlı Z aksları: {', '.join(S['z']) or '(yok)'}.")
            Zl = S["z"][z_ad]
            yerel_z = not S["z_global"]
        u, v = S["a1"][a1], S["a2"][a2]
        if S["tur"] == "silindirik":
            t = math.radians(v)
            u, v = u * math.cos(t), u * math.sin(t)
        c, s_ = math.cos(math.radians(S["aci"])), math.sin(math.radians(S["aci"]))
        X = S["orijin"][0] + u * c - v * s_
        Yy = S["orijin"][1] + u * s_ + v * c
        Zz = (S["orijin"][2] + Zl) if (yerel_z and S["ad"] != "GLOBAL") else Zl
        meta = {"tur": "aks", "sistem": S["ad"], "aks": [a1, a2], "z": z_ad}
        if S["ad"] == "GLOBAL":
            meta["ix"], meta["iy"] = S["s1"].index(a1), S["s2"].index(a2)
        return (float(X), float(Yy), float(Zz)), meta

    # --- kayıt konumu (yinelemeli)
    def kayit_konum(self, no, ad):
        if no in self.konum:
            return self.konum[no]
        if no in self.yigin:
            zincir = " → ".join(str(n) for n in self.yigin[self.yigin.index(no):] + [no])
            raise MatrisHatasi(f"Düğüm kayıtları döngü oluşturuyor: {zincir}. Bölme/kesişim düğümü kendine (dolaylı) başvuramaz.")
        d = self.kayit[no]
        self.yigin.append(no)
        tur = str(d.get("tur") or "").strip().lower()
        a = f"Düğüm {no}"
        if tur == "bolme":
            Pi = self.ref_konum(d.get("cubuk_i"), f"{a} (bölme) cubuk_i")[0]
            Pj = self.ref_konum(d.get("cubuk_j"), f"{a} (bölme) cubuk_j")[0]
            t = Y._sayi(d.get("oran"), f"{a}: oran (0…1)")
            if not -1e-9 <= t <= 1 + 1e-9:
                raise MatrisHatasi(f"{a}: bölme oranı {t} 0 ile 1 arasında olmalı (çubuğun i ucundan oran).")
            P = _top(Pi, _olc(_vek(Pi, Pj), t))
            meta = {"tur": "bolme", "oran": t}
        elif tur == "kesisim":
            ca, cb = d.get("a"), d.get("b")
            if not (isinstance(ca, (list, tuple)) and len(ca) == 2 and isinstance(cb, (list, tuple)) and len(cb) == 2):
                raise MatrisHatasi(f"{a}: kesişim düğümü \"a\": [REF, REF] ve \"b\": [REF, REF] (iki doğru parçası) ister.")
            P1, P2 = (self.ref_konum(r, f"{a} (kesişim) a")[0] for r in ca)
            Q1, Q2 = (self.ref_konum(r, f"{a} (kesişim) b")[0] for r in cb)
            P = _kesisim(P1, P2, Q1, Q2, a)
            meta = {"tur": "kesisim"}
        elif d.get("aks") is not None:
            P, meta = self.aks(d.get("sistem"), d.get("aks"), d.get("z"), d.get("kat") if d.get("z") is None else None, a)
        elif all(d.get(k) is not None for k in ("X", "Y", "Z")):
            P = tuple(Y._sayi(d.get(k), f"{a}: {k}") for k in ("X", "Y", "Z"))
            meta = {"tur": "koordinat"}
        else:
            raise MatrisHatasi(f"{a}: konum tanımsız. Düğüm ya aks kesişimidir ({{\"aks\": [\"B\", \"2\"], \"z\": \"Saçak\"}}), ya bölme "
                               "({\"tur\": \"bolme\", \"cubuk_i\": REF, \"cubuk_j\": REF, \"oran\": 0.5}) ya da kesişim "
                               "({\"tur\": \"kesisim\", \"a\": [REF, REF], \"b\": [REF, REF]}) düğümüdür.")
        self.yigin.pop()
        self.konum[no] = tuple(float(v) for v in P)
        self.kayit[no]["_meta"] = meta
        return self.konum[no]

    # --- REF → konum (düğüm yaratmadan)
    def ref_konum(self, ref, ad):
        if isinstance(ref, str) and ref.strip().isdigit():
            ref = int(ref.strip())
        if isinstance(ref, bool):
            raise MatrisHatasi(f"{ad}: düğüm başvurusu anlaşılamadı ({ref!r}).")
        if isinstance(ref, (int, float)) and float(ref) == int(ref):
            ref = {"dugum": int(ref)}
        if isinstance(ref, (list, tuple)) and len(ref) == 3:
            return tuple(Y._sayi(v, ad) for v in ref), {"tur": "koordinat"}
        if not isinstance(ref, dict):
            raise MatrisHatasi(f"{ad}: düğüm başvurusu anlaşılamadı ({ref!r}). Örnek: {{\"aks\": [\"B\", \"2\"], \"z\": \"Saçak\"}} "
                               "ya da {\"dugum\": 100004}.")
        if ref.get("dugum") is not None:
            no = Y._tam(ref.get("dugum"), f"{ad}: dugum")
            no = self.takma.get(no, no)
            if no in self.kayit:
                return self.kayit_konum(no, ad), {"tur": "kayit", "no": no}
            if no in self.dugum:
                d = self.dugum[no]
                return (d["X"], d["Y"], d["Z"]), {"tur": "kayit", "no": no}
            kat, kalan = divmod(no, 1000)
            ix, iy = divmod(kalan - 1, 20) if kalan else (-1, -1)
            S = self.B.sistemler["GLOBAL"]
            if 0 <= ix < len(S["s1"]) and 0 <= iy < len(S["s2"]) and kalan and any(kt["no"] == kat for kt in self.B.katlar):
                return self.aks("GLOBAL", [S["s1"][ix], S["s2"][iy]], None, kat, ad)
            raise MatrisHatasi(f"{ad}: düğüm {no} modelde yok (dugumler listesinde tanımlayın ya da aks başvurusu verin).")
        if ref.get("aks") is not None:
            return self.aks(ref.get("sistem"), ref.get("aks"), ref.get("z"), ref.get("kat", 1) if ref.get("z") is None else None, ad)
        if all(ref.get(k) is not None for k in ("X", "Y", "Z")):
            return tuple(Y._sayi(ref.get(k), f"{ad}: {k}") for k in ("X", "Y", "Z")), {"tur": "koordinat"}
        raise MatrisHatasi(f"{ad}: düğüm başvurusu anlaşılamadı ({ref!r}). {{\"aks\": [x, y], \"z\": \"Z aksı\"}}, {{\"aks\": [x, y], "
                           "\"kat\": k}, {\"dugum\": no} ya da (geriye uyum) {\"X\", \"Y\", \"Z\"} olmalı.")

    # --- uzaysal arama
    def _anahtar(self, P):
        h = 2 * TOL
        return (int(math.floor(P[0] / h)), int(math.floor(P[1] / h)), int(math.floor(P[2] / h)))

    def bul(self, P):
        k = self._anahtar(P)
        en, en_d = None, TOL
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for c in (-1, 0, 1):
                    for no in self.izgara.get((k[0] + a, k[1] + b, k[2] + c), ()):
                        d = self.dugum[no]
                        dd = math.sqrt((d["X"] - P[0]) ** 2 + (d["Y"] - P[1]) ** 2 + (d["Z"] - P[2]) ** 2)
                        if dd <= en_d:
                            en, en_d = no, dd
        return en

    def ekle(self, no, P, meta, ad=None):
        d = {"no": no, "X": P[0], "Y": P[1], "Z": P[2], "tur": meta.get("tur", "aks"), "ad": ad}
        for k in ("sistem", "aks", "z", "ix", "iy", "oran"):
            if k in meta:
                d[k] = meta[k]
        self.dugum[no] = d
        self.izgara.setdefault(self._anahtar(P), []).append(no)
        return no

    def kayitlari_kaydet(self):
        for no in sorted(self.kayit):
            P = self.kayit_konum(no, f"Düğüm {no}")
            var = self.bul(P)
            if var is not None:
                self.takma[no] = var
                self.B.uyarilar.append(f"Düğüm {no}, düğüm {var} ile aynı konumda (1 mm içinde): birleştirildi.")
                continue
            self.ekle(no, P, self.kayit[no].get("_meta", {}), self.kayit[no].get("ad"))

    def no(self, ref, ad):
        """REF → düğüm no (yoksa yaratılır)."""
        P, meta = self.ref_konum(ref, ad)
        if meta.get("tur") == "kayit":
            n = self.takma.get(meta["no"], meta["no"])
            if n in self.dugum:
                return n
        var = self.bul(P)
        if var is not None:
            return var
        n = None
        if meta.get("sistem") == "GLOBAL" and meta.get("iy", 99) < 20:
            kat = next((kt["no"] for kt in self.B.katlar if abs(kt["kot"] - P[2]) < 1e-6), None)
            if kat is not None:
                aday = 1000 * kat + 20 * meta["ix"] + meta["iy"] + 1
                if aday not in self.dugum and aday not in self.kayit:
                    n = aday
        if n is None:
            self._sira += 1
            while self._sira in self.dugum or self._sira in self.kayit:
                self._sira += 1
            n = self._sira
        return self.ekle(n, P, meta)


def _kesisim(P1, P2, Q1, Q2, ad):
    """İki doğrunun (P1P2, Q1Q2) en yakın noktalarının ortası; 1 cm'den uzaksa öğretici hata."""
    d1, d2, r = _vek(P1, P2), _vek(Q1, Q2), _vek(Q1, P1)
    a, e, b = _ic(d1, d1), _ic(d2, d2), _ic(d1, d2)
    c, f = _ic(d1, r), _ic(d2, r)
    den = a * e - b * b
    if a < 1e-12 or e < 1e-12 or den <= 1e-12 * a * e:
        raise MatrisHatasi(f"{ad}: kesişim düğümünün iki doğrusu paralel ya da sıfır boylu; kesişim tanımsız.")
    s = (b * f - c * e) / den
    t = (a * f - b * c) / den
    Ps, Qt = _top(P1, _olc(d1, s)), _top(Q1, _olc(d2, t))
    if _boy(_vek(Ps, Qt)) > 0.01:
        raise MatrisHatasi(f"{ad}: iki doğru kesişmiyor (en yakın noktalar {_boy(_vek(Ps, Qt)) * 1000:.0f} mm uzakta); aynı düzlemdeki "
                           "iki çubuğu seçin.")
    return _olc(_top(Ps, Qt), 0.5)


# ============================================================================
# 3) Kesitler: dikdörtgen, I/H profil, basit çelik kesitler (kutu, boru, korniyer, U), vute (değişken kesit)
# ============================================================================
def _tasarim_mod():
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def _kesit_kart(ad, kayit, B):
    if not isinstance(kayit, dict):
        raise MatrisHatasi(f"Kesit {ad!r} bir sözlük olmalı.")
    tip = str(kayit.get("tip", "dikdortgen")).strip().lower()
    if tip == "vute":
        return None                                    # temel kesitten sonra kurulur
    pad = str(kayit.get("profil") or "").strip()
    pad_n = pad.upper().replace("  ", " ")
    if pad_n and " " not in pad_n:
        for on in ("IPE", "HEA", "HEB"):
            if pad_n.startswith(on):
                pad_n = on + " " + pad_n[len(on):]
    if tip == "dikdortgen" or (tip == "profil" and pad_n in yv.PROFILLER):
        k = Y._kesit_ozellikleri(ad, kayit, B.malzemeler)
        k["aile"] = pad_n.split()[0] if k.get("profil") else None
        return k
    # basit çelik kesitler (tasarim.kesit_ozellik): "KUTU 150x8", "BORU 114.3x4", "L 100x10", "2L 70x7 s=10", "UPN 200"
    ts = _tasarim_mod()
    if ts is None:
        raise MatrisHatasi(f"Kesit {ad!r}: {pad or tip!r} kesiti için tasarim.py gerekir (yüklenemedi).")
    mad = str(kayit.get("malzeme", "")).strip()
    if mad not in B.malzemeler:
        raise MatrisHatasi(f"Kesit {ad!r}: malzeme {mad!r} 'malzemeler' sözlüğünde yok. Tanımlı: {', '.join(B.malzemeler)}.")
    m = B.malzemeler[mad]
    try:
        if pad:
            p = ts.kesit_ozellik(pad)
        else:
            p = ts.kesit_ozellik(tip, kayit.get("boyutlar"))
    except MatrisHatasi as h:
        raise MatrisHatasi(f"Kesit {ad!r}: {h} (I/H profiller: IPE, HEA, HEB; basit kesitler: KUTU, BORU, L, 2L, UPN).") from None
    hh = (p.get("H") or p.get("D") or p.get("h") or p.get("b") or 0.0) / 1000.0
    bb = (p.get("B") or p.get("D") or p.get("b") or 0.0) / 1000.0
    aile = {"kutu": "KUTU", "boru": "BORU", "L": "L", "2L": "2L", "U": "UPN"}.get(p["tip"], p["tip"])
    return {"ad": ad, "tip": "basit", "malzeme": mad, "E": m["E"], "G": m["G"], "gamma": m["gamma"], "b": bb, "h": hh,
            "A": p["A"] * 1e-4, "I_guclu": p["Iy"] * 1e-8, "I_zayif": p["Iz"] * 1e-8, "J": max(p["It"], 1e-6) * 1e-8,
            "Wpl": p["Wply"] * 1e-6, "Wel": p["Wely"] * 1e-6, "profil": p["ad"], "g_kg": p["g"], "aile": aile,
            "dogrulandi": True, "kaynak": p.get("kaynak")}


def _vute_kart(ad, kayit, B):
    temel = str(kayit.get("temel") or "").strip()
    if temel not in B.kesitler or B.kesitler[temel] is None or B.kesitler[temel]["tip"] == "vute":
        raise MatrisHatasi(f"Vute kesiti {ad!r}: temel kesit {temel!r} tanımsız (vute = temel kesit + doğrusal artan yükseklik).")
    t = B.kesitler[temel]
    dh = Y._sayi(kayit.get("ek_yukseklik", 0.0), f"Vute {ad!r}: ek_yukseklik (m)", pozitif=True)
    boy = kayit.get("boy")
    k = dict(t)
    k.update({"ad": ad, "tip": "vute", "temel": temel, "ek_yukseklik": dh,
              "boy": None if boy in (None, "") else Y._sayi(boy, f"Vute {ad!r}: boy (m)", pozitif=True, sifir_olur=False),
              "derin_uc": str(kayit.get("derin_uc") or "i").strip().lower()})
    if k["derin_uc"] not in ("i", "j"):
        raise MatrisHatasi(f"Vute {ad!r}: derin_uc 'i' ya da 'j' olmalı.")
    return k


def _derin_kesit(k, h):
    """Temel kesitin h yüksekliğindeki eşdeğeri (vute parçası): profil başlıkları aynı, gövde uzar (kaynaklı I yaklaşımı;
    katalog/formül oranıyla ölçeklenir); dikdörtgen b × h."""
    t = k
    if t["tip"] == "dikdortgen" or t.get("profil") is None or t["profil"] not in yv.PROFILLER:
        b = t["b"]
        h0 = t["h"]
        if t["tip"] == "dikdortgen":
            return {"A": b * h, "I_guclu": b * h ** 3 / 12.0, "I_zayif": h * b ** 3 / 12.0, "J": t["J"] * (h / h0), "h": h}
        r = h / h0
        return {"A": t["A"] * r, "I_guclu": t["I_guclu"] * r ** 2, "I_zayif": t["I_zayif"], "J": t["J"], "h": h}
    p = yv.PROFILLER[t["profil"]]
    bf, tf, tw, h0 = p["b"] / 1000.0, p["tf"] / 1000.0, p["tw"] / 1000.0, p["h"] / 1000.0

    def If(hh):
        return (bf * hh ** 3 - (bf - tw) * (hh - 2 * tf) ** 3) / 12.0
    dh = h - h0
    return {"A": t["A"] + tw * dh, "I_guclu": t["I_guclu"] * If(h) / If(h0), "I_zayif": t["I_zayif"] + dh * tw ** 3 / 12.0,
            "J": t["J"] + dh * tw ** 3 / 3.0, "h": h}


# ============================================================================
# 4) Modeli okuma: aks–kat elemanlarının genel listeye çevrilmesi (model_ops.genellestir ile aynı kural)
# ============================================================================
def _aks_kat_donustur(bina, B):
    """kolonlar/kirisler/dosemeler → cubuklar/paneller; ek yükler (kiris, aks–kat düğüm, doseme) dönüştürülür."""
    kolonlar, kirisler, dosemeler = bina.get("kolonlar") or [], bina.get("kirisler") or [], bina.get("dosemeler") or []
    cubuklar = [dict(c) for c in (bina.get("cubuklar") or [])]
    paneller = [dict(p) for p in (bina.get("paneller") or [])]
    ek = [dict(y) for y in (bina.get("ek_yukler") or []) if isinstance(y, dict)]
    if not (kolonlar or kirisler or dosemeler):
        return cubuklar, paneller, ek
    S = B.sistemler["GLOBAL"]
    sira_x, sira_y = S["s1"], S["s2"]
    ust = max((kt["no"] for kt in B.katlar), default=1)
    no = [max([Y._tam(c.get("no", 0), "çubuk no") for c in cubuklar] + [0])]

    def yeni():
        no[0] += 1
        return no[0]

    def ekstra(x, bilinen):
        return {k: copy.deepcopy(v) for k, v in x.items() if k not in bilinen}

    for c in sorted(kolonlar, key=lambda c: (int(c.get("kat", 1)), int(c.get("no", 0)))):
        kat = int(c.get("kat", 1))
        r = {"tur": "kolon", "kesit": c.get("kesit"), "aci": 90 if str(c.get("yon", "x")).lower() == "y" else 0, "kat": kat}
        r.update(ekstra(c, ("no", "aks", "kat", "kesit", "yon")))
        r.update({"no": yeni(), "i": {"aks": list(c.get("aks") or []), "kat": kat - 1}, "j": {"aks": list(c.get("aks") or []), "kat": kat},
                  "kaynak": {"aks_kat": "kolon", "no": int(c.get("no", 0))}})
        cubuklar.append(r)
    kiris_cubuk = {}
    for k in sorted(kirisler, key=lambda k: (int(k.get("kat", 1)), int(k.get("no", 0)))):
        kat = int(k.get("kat", 1))
        bas, son = k.get("bas") or [], k.get("son") or []
        try:
            bx, by, sx, sy = sira_x.index(str(bas[0])), sira_y.index(str(bas[1])), sira_x.index(str(son[0])), sira_y.index(str(son[1]))
        except (ValueError, IndexError):
            raise MatrisHatasi(f"Kiriş {k.get('no')}: bas/son aks adresi geçersiz ({bas!r} → {son!r}).") from None
        if by == sy and bx != sx:
            uclar = [([sira_x[i], sira_y[by]], [sira_x[i + 1], sira_y[by]]) for i in range(min(bx, sx), max(bx, sx))]
        elif bx == sx and by != sy:
            uclar = [([sira_x[bx], sira_y[i]], [sira_x[bx], sira_y[i + 1]]) for i in range(min(by, sy), max(by, sy))]
        else:
            raise MatrisHatasi(f"Kiriş {k.get('no')}: uçları aynı aks çizgisi üzerinde değil.")
        nolar = []
        for p, (a, b) in enumerate(uclar, start=1):
            r = {"tur": "kiris", "kesit": k.get("kesit"), "aci": 0, "kat": kat}
            r.update(ekstra(k, ("no", "kat", "bas", "son", "kesit")))
            r.update({"no": yeni(), "i": {"aks": a, "kat": kat}, "j": {"aks": b, "kat": kat},
                      "kaynak": {"aks_kat": "kiris", "no": int(k.get("no", 0)), "parca": p}})
            cubuklar.append(r)
            nolar.append(r["no"])
        kiris_cubuk[int(k.get("no", 0))] = nolar
    dolu = {int(p.get("no", 0)) for p in paneller}
    panel_no = {}
    for d in sorted(dosemeler, key=lambda d: (int(d.get("kat", 1)), int(d.get("no", 0)))):
        kat = int(d.get("kat", 1))
        kose = d.get("kose") or [[], []]
        try:
            xa, ya = sira_x.index(str(kose[0][0])), sira_y.index(str(kose[0][1]))
            xb, yb = sira_x.index(str(kose[1][0])), sira_y.index(str(kose[1][1]))
        except (ValueError, IndexError):
            raise MatrisHatasi(f"Döşeme {d.get('no')}: köşe aks adresleri geçersiz ({kose!r}).") from None
        x0, x1, y0, y1 = min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb)
        koseler = [{"aks": [sira_x[i], sira_y[j]], "kat": kat} for i, j in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        dx = S["a1"][sira_x[x1]] - S["a1"][sira_x[x0]]
        dy = S["a2"][sira_y[y1]] - S["a2"][sira_y[y0]]
        tek = "tek-13" if dx >= dy - 1e-9 else "tek-24"
        mod = str(d.get("dagitim") or "otomatik").lower()
        oran = max(dx, dy) / max(min(dx, dy), 1e-9)
        dag = "iki" if mod == "cift" else (tek if mod == "tek" else ("iki" if oran <= 2 + 1e-9 else tek))
        n = int(d.get("no", 0))
        if n <= 0 or n in dolu:
            n = max(dolu | {0}) + 1
        dolu.add(n)
        p = {"no": n, "kose": koseler, "tur": "doseme", "kalinlik": d.get("h", 0.12) if d.get("h") is not None else 0.12,
             "g": d.get("g_ek") if d.get("g_ek") is not None else (d.get("kaplama") if d.get("kaplama") is not None else 0.0)}
        if d.get("q") is not None:
            p["q"] = d.get("q")
        p.update({"kullanim": d.get("kullanim") or "konut", "kar": kat == ust, "dagitim": dag, "kat": kat})
        p.update(ekstra(d, ("no", "kat", "kose", "h", "g_ek", "kaplama", "q", "kullanim", "dagitim")))
        p["kaynak"] = {"aks_kat": "doseme", "no": int(d.get("no", 0))}
        paneller.append(p)
        panel_no[int(d.get("no", 0))] = n
    yeni_ek = []
    for y in ek:
        tur = str(y.get("tur", "")).lower()
        if tur == "kiris" and int(y.get("kiris", -1)) in kiris_cubuk:
            q = -Y._sayi(y.get("q", 0.0), "ek yük q")
            for cn in kiris_cubuk[int(y["kiris"])]:
                yeni_ek.append({"tur": "cubuk", "cubuk": cn, "durum": y.get("durum", "G"), "yon": "Z", "q1": q, "q2": q})
        elif tur == "dugum" and y.get("aks") is not None and y.get("dugum") is None:
            r = {k: v for k, v in y.items() if k not in ("aks", "kat")}
            r["dugum"] = {"aks": y["aks"], "kat": y.get("kat", 1)}
            yeni_ek.append(r)
        elif tur == "doseme" and int(y.get("doseme", -1)) in panel_no:
            r = {k: v for k, v in y.items() if k != "doseme"}
            r.update({"tur": "panel", "panel": panel_no[int(y["doseme"])]})
            yeni_ek.append(r)
        else:
            yeni_ek.append(y)
    B.uyarilar.append(f"Aks–kat elemanları genel modele çevrildi: {len(kolonlar)} kolon, "
                      f"{sum(len(v) for v in kiris_cubuk.values())} kiriş parçası → çubuk; {len(dosemeler)} döşeme → panel.")
    return cubuklar, paneller, yeni_ek


def _serbestlik_oku(v, ad):
    if v in (None, "", {}, []):
        return {"i": [], "j": []}
    if not isinstance(v, dict) or set(v) - {"i", "j"}:
        raise MatrisHatasi(f"{ad}: 'serbest' {{\"i\": [\"My\", \"Mz\"], \"j\": [...]}} biçiminde olmalı (N, Vy, Vz, T, My, Mz).")
    out = {}
    for uc in ("i", "j"):
        liste = v.get(uc) or []
        if isinstance(liste, str):
            liste = [p for p in liste.replace(",", " ").split() if p]
        s = []
        for a in liste:
            a = {"Mx": "T"}.get(str(a).strip(), str(a).strip())
            if a not in _SERBEST_ADLAR:
                raise MatrisHatasi(f"{ad}: bilinmeyen uç serbestliği {a!r} ({uc} ucu); geçerli: {', '.join(_SERBEST_ADLAR)}.")
            if a not in s:
                s.append(a)
        out[uc] = [a for a in _SERBEST_ADLAR if a in s]
    return out


def _lam_bina(Pi, Pj, aci):
    """Yerel eksenler (bina koordinatında satırlar x′, y′, z′): motor kuralı (se._lam3b) + aci."""
    a, b = Y._motor_koordinat(*Pi), Y._motor_koordinat(*Pj)
    d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    L = _boy(d)
    lam = se._lam3b(d[0] / L, d[1] / L, d[2] / L, True, aci)
    return [list(Y._bina_vek(s)) for s in lam]


def _oku(bina):
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError as e:
            raise MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
    if not isinstance(bina, dict):
        raise MatrisHatasi("Bina bir sözlük (ya da JSON metni) olmalı.")
    B = SimpleNamespace(ham=bina, uyarilar=[], serbest=True)
    B.baslik = str(bina.get("baslik") or "Bina modeli")
    B.aciklama = str(bina.get("aciklama") or "")
    B.sistem = str(bina.get("sistem") or "celik").strip().lower()
    if B.sistem not in ("betonarme", "celik"):
        raise MatrisHatasi(f"sistem {B.sistem!r} tanımsız; 'betonarme' ya da 'celik' olmalı.")
    birim = bina.get("birim") if isinstance(bina.get("birim"), dict) else {}
    B.birim = {"kuvvet": str(birim.get("kuvvet", "kN")), "uzunluk": str(birim.get("uzunluk", "m"))}
    if B.birim != {"kuvvet": "kN", "uzunluk": "m"}:
        raise MatrisHatasi("Bina modülü kN ve m ile çalışır; birim alanını kN, m yapın.")
    _akslari_oku(B, bina)
    # malzemeler, kesitler, duvarlar
    mal = bina.get("malzemeler")
    if not isinstance(mal, dict) or not mal:
        raise MatrisHatasi('Malzeme yok: "malzemeler": {"S275": {"kutuphane": "S275"}} gibi en az bir malzeme tanımlayın.')
    B.malzemeler = {str(ad): Y._malzeme(str(ad), k) for ad, k in mal.items()}
    kes = bina.get("kesitler")
    if not isinstance(kes, dict) or not kes:
        raise MatrisHatasi('Kesit yok: "kesitler": {"IPE300": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"}}.')
    B.kesitler = {}
    for ad, k in kes.items():
        B.kesitler[str(ad)] = _kesit_kart(str(ad), k, B)
    for ad, k in kes.items():
        if B.kesitler[str(ad)] is None:
            B.kesitler[str(ad)] = _vute_kart(str(ad), k, B)
    B.duvarlar = {}
    for ad, kayit in (bina.get("duvarlar") or {}).items():
        if not isinstance(kayit, dict):
            raise MatrisHatasi(f"Duvar {ad!r} bir sözlük olmalı.")
        if "kutuphane" in kayit:
            an = str(kayit["kutuphane"]).strip()
            if an not in yv.DUVARLAR:
                raise MatrisHatasi(f"Duvar {ad!r}: kütüphanede {an!r} yok. Seçenekler: {', '.join(yv.DUVARLAR)}.")
            d = yv.DUVARLAR[an]
            B.duvarlar[str(ad)] = {"ad": str(ad), "kutuphane": an, "deger": d["deger"], "aciklama": d["ad"], "dogrulandi": d["dogrulandi"]}
        else:
            B.duvarlar[str(ad)] = {"ad": str(ad), "kutuphane": None, "aciklama": str(kayit.get("ad", ad)), "dogrulandi": True,
                                   "deger": Y._sayi(kayit.get("kN_m2"), f"Duvar {ad!r}: kN_m2", pozitif=True)}
    an = bina.get("analiz") if isinstance(bina.get("analiz"), dict) else {}
    nokta = Y._tam(an.get("diyagram_nokta", Y.DIYAGRAM_NOKTA), "analiz.diyagram_nokta")
    gost = an.get("gosterilecek", bina.get("gosterilecek"))
    koz = str(an.get("kiris_oz", "net")).strip().lower()
    B.analiz = {"catlamis_rijitlik": None if an.get("catlamis_rijitlik") is None else bool(an.get("catlamis_rijitlik")),
                "diyagram_nokta": max(3, min(41, nokta)), "gosterilecek": [str(x) for x in gost] if gost is not None else None,
                "celik_Lb": str(an.get("celik_Lb", "otomatik")).strip().lower(), "kiris_oz": koz if koz in ("net", "brut") else "net",
                "vute_parca": max(1, min(6, Y._tam(an.get("vute_parca", 3), "analiz.vute_parca"))),
                "diyafram": an.get("diyafram"), "yalniz_cekme_yineleme": Y._tam(an.get("yalniz_cekme_yineleme", 10), "analiz.yalniz_cekme_yineleme")}
    B.kombinasyon_kumesi = str(bina.get("kombinasyon_kumesi") or ("ts500" if B.sistem == "betonarme" else "cythye_ydkt")).strip().lower()
    if B.kombinasyon_kumesi not in yv.KOMBINASYONLAR:
        raise MatrisHatasi(f"kombinasyon_kumesi {B.kombinasyon_kumesi!r} tanımsız; seçenekler: {', '.join(yv.KOMBINASYONLAR)}.")
    # temeller (aks–kat temel kuralı: kat 0 Z aksındaki GLOBAL aks kesişimleri)
    t = bina.get("temeller") if isinstance(bina.get("temeller"), dict) else {}
    var = t.get("varsayilan") if isinstance(t.get("varsayilan"), dict) else {}
    zem = t.get("zemin") if isinstance(t.get("zemin"), dict) else {}
    mesnet = str(t.get("mesnet") or "ankastre").strip().lower()
    if mesnet not in ("ankastre", "mafsal", "elastik"):
        raise MatrisHatasi(f"temeller.mesnet {mesnet!r}; 'ankastre', 'mafsal' ya da 'elastik' olmalı.")
    B.temeller = {"tip": str(t.get("tip") or "tekil"), "mesnet": mesnet,
                  "varsayilan": {"B": float(var.get("B", 1.5)), "L": float(var.get("L", 1.5)), "h": float(var.get("h", 0.6))},
                  "zemin": {"q_em": float(zem.get("q_em", 200.0)), "k0": float(zem.get("k0", 20000.0))}, "ozel": {}}
    for o in t.get("ozel") or []:
        if isinstance(o, dict) and isinstance(o.get("aks"), (list, tuple)):
            B.temeller["ozel"][tuple(str(a) for a in o["aks"])] = {"B": float(o.get("B", B.temeller["varsayilan"]["B"])),
                                                                   "L": float(o.get("L", B.temeller["varsayilan"]["L"]))}
    # düğümler
    coz = _Cozucu(B, bina.get("dugumler"))
    coz.kayitlari_kaydet()
    B.coz = coz
    ham_c, ham_p, ham_ek = _aks_kat_donustur(bina, B)
    _cubuklari_oku(B, ham_c, coz)
    if not B.katlar:
        zmin = min(d["Z"] for d in coz.dugum.values())
        zmax = max(d["Z"] for d in coz.dugum.values())
        B.katlar = [{"no": 0, "ad": "Taban", "kot": zmin, "h": 0.0, "z": None}]
        if zmax - zmin > 0.3:
            B.katlar.append({"no": 1, "ad": "Tepe", "kot": zmax, "h": zmax - zmin, "z": None})
        B.uyarilar.append("Z akslarında kat (seviye) işareti yok: en alt düğüm kotu kat 0, en üst kat 1 sayıldı (kütle ve deprem için "
                          "Z aksına \"kat\" verin).")
    B.kat = {kt["no"]: kt for kt in B.katlar}
    B.nk = len(B.katlar) - 1
    _panelleri_oku(B, ham_p, coz)
    _mesnetleri_oku(B, bina, coz)
    B.ek_yukler_ham = ham_ek
    _ek_yukleri_oku(B, ham_ek, coz)
    _kren_oku(B, bina)
    # kar/rüzgâr/deprem kartları: yapi okuyucusu (n önerisi panellerin kullanım sınıflarından)
    B.dosemeler = [{"kullanim": p["kullanim"]} for p in B.paneller if p["q"] > 0 and p["kullanim"] in yv.TS498_HAREKETLI]
    Y._yuk_durumlarini_oku(B, bina)
    B.dosemeler = []
    zorunlu = B.sistem == "betonarme" and B.deprem is not None
    if B.analiz["catlamis_rijitlik"] is None:
        B.analiz["catlamis_rijitlik"] = zorunlu
    _dugum_seviyeleri(B)
    _yuzen_denetle(B, coz)
    return B


def _cubuklari_oku(B, ham, coz):
    B.cubuklar, B.cubuk_no = [], {}
    if not ham:
        raise MatrisHatasi("Modelde çubuk yok: en az bir kolon/kiriş/çubuk tanımlayın (cubuklar listesi ya da aks–kat elemanları).")
    ciftler = {}
    for k, c in enumerate(ham, start=1):
        if not isinstance(c, dict):
            raise MatrisHatasi(f"{k}. çubuk sözlük olmalı.")
        no = Y._tam(c.get("no", k), f"{k}. çubuk: no")
        if no in B.cubuk_no:
            raise MatrisHatasi(f"Çubuk numarası {no} tekrarlı.")
        ad = f"Çubuk {no}"
        i, j = coz.no(c.get("i"), f"{ad}: i ucu"), coz.no(c.get("j"), f"{ad}: j ucu")
        if i == j:
            raise MatrisHatasi(f"{ad}: iki ucu aynı düğüm ({i}); sıfır boylu çubuk olamaz.")
        Pi, Pj = (coz.dugum[i]["X"], coz.dugum[i]["Y"], coz.dugum[i]["Z"]), (coz.dugum[j]["X"], coz.dugum[j]["Y"], coz.dugum[j]["Z"])
        L = _boy(_vek(Pi, Pj))
        kesit = str(c.get("kesit") or "").strip()
        if kesit not in B.kesitler:
            raise MatrisHatasi(f"{ad}: kesit {kesit!r} 'kesitler' sözlüğünde yok" + (" (kesitsiz çubuk: önce kesit atayın)" if not kesit else "")
                               + f". Tanımlı: {', '.join(B.kesitler)}.")
        dx = _birim(_vek(Pi, Pj))
        tur = str(c.get("tur") or "").strip().lower()
        if not tur:
            tur = "kolon" if abs(dx[2]) > 0.99 else ("kiris" if abs(dx[2]) < 0.02 else "diger")
        if tur not in _TURLER:
            raise MatrisHatasi(f"{ad}: tur {tur!r} tanımsız; seçenekler: {', '.join(_TURLER)}.")
        aci = Y._sayi(c.get("aci", 0.0) if c.get("aci") is not None else 0.0, f"{ad}: aci (derece)")
        anah = (min(i, j), max(i, j))
        if anah in ciftler:
            B.uyarilar.append(f"Çubuk {ciftler[anah]} ve {no} aynı iki düğümü bağlıyor (çakışan çubuk); ikisi de rijitliğe katıldı.")
        ciftler[anah] = no
        Kk = c.get("K")
        if Kk is not None:
            if isinstance(Kk, (int, float)):
                Kk = [float(Kk), float(Kk)]
            if not isinstance(Kk, (list, tuple)) or len(Kk) != 2:
                raise MatrisHatasi(f"{ad}: K [K_güçlü, K_zayıf] olmalı.")
            Kk = [Y._sayi(Kk[0], f"{ad}: K"), Y._sayi(Kk[1], f"{ad}: K")]
        duvar = c.get("duvar")
        if duvar not in (None, ""):
            duvar = str(duvar).strip()
            if duvar not in B.duvarlar:
                raise MatrisHatasi(f"{ad}: duvar {duvar!r} 'duvarlar' sözlüğünde yok.")
        else:
            duvar = None
        kat = c.get("kat")
        r = {"no": no, "i": i, "j": j, "tur": tur, "kesit": kesit, "aci": aci, "serbest": _serbestlik_oku(c.get("serbest"), ad),
             "yalniz_cekme": bool(c.get("yalniz_cekme")), "kat": None if kat in (None, "") else Y._tam(kat, f"{ad}: kat"),
             "grup": c.get("grup"), "Lb": None if c.get("Lb") in (None, "") else Y._sayi(c.get("Lb"), f"{ad}: Lb (m)", pozitif=True),
             "K": Kk, "kaynak": c.get("kaynak"), "duvar": duvar,
             "duvar_h": None if c.get("duvar_h") in (None, "") else Y._sayi(c.get("duvar_h"), f"{ad}: duvar_h (m)", pozitif=True),
             "L": L, "Pi": Pi, "Pj": Pj, "lam": _lam_bina(Pi, Pj, aci), "dx": dx}
        if r["yalniz_cekme"] and B.kesitler[kesit]["tip"] == "dikdortgen":
            B.uyarilar.append(f"{ad}: yalnız çekme betonarme kesitte anlamsız; çelik çapraz için kullanın.")
        B.cubuklar.append(r)
        B.cubuk_no[no] = r
    B.cubuklar.sort(key=lambda c: c["no"])


def _panel_geometri(P, ad):
    """Newell normali, alan, düzlemsellik ve dışbükeylik; panel düzleminde 2B koordinatlar."""
    n = [0.0, 0.0, 0.0]
    m = len(P)
    for k in range(m):
        a, b = P[k], P[(k + 1) % m]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    A = 0.5 * _boy(n)
    if A < 1e-6:
        raise MatrisHatasi(f"{ad}: köşeler bir doğru üzerinde (alan sıfır).")
    nh = _birim(n)
    sapma = max(abs(_ic(nh, _vek(P[0], q))) for q in P)
    if sapma > 0.005:
        raise MatrisHatasi(f"{ad}: köşeler aynı düzlemde değil (en büyük sapma {sapma * 1000:.0f} mm > 5 mm). Paneli düzlemsel "
                           "parçalara (ör. iki üçgen) bölün.")
    e1 = _birim(_vek(P[0], P[1]))
    e2 = _dis(nh, e1)
    Q = [(_ic(_vek(P[0], q), e1), _ic(_vek(P[0], q), e2)) for q in P]
    isaret = []
    for k in range(m):
        a, b, c = Q[k], Q[(k + 1) % m], Q[(k + 2) % m]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) > 1e-9:
            isaret.append(cr > 0)
    disbukey = len(set(isaret)) <= 1
    return {"normal": nh, "alan": A, "Q": Q, "e1": e1, "e2": e2, "disbukey": disbukey}


def _kenar_zinciri(B, komsu, a, b):
    """Panel kenarı a→b boyunca uç uca çubuk zinciri: [(cubuk no, u0, u1, ters)] (u kenar boyunca m) ve boşluklar."""
    D = B.coz.dugum
    Pa, Pb = (D[a]["X"], D[a]["Y"], D[a]["Z"]), (D[b]["X"], D[b]["Y"], D[b]["Z"])
    e = _vek(Pa, Pb)
    L = _boy(e)
    eh = _birim(e)
    cur, ucur, parcalar, gor = a, 0.0, [], set()
    while cur != b:
        en = None
        for cno, diger in komsu.get(cur, ()):
            if cno in gor:
                continue
            Po = (D[diger]["X"], D[diger]["Y"], D[diger]["Z"])
            r = _vek(Pa, Po)
            u = _ic(r, eh)
            d = _boy(_vek(_top(Pa, _olc(eh, u)), Po))
            if d > TOL or u <= ucur + TOL or u > L + TOL:
                continue
            if en is None or u < en[2]:
                en = (cno, diger, u)
        if en is None:
            return parcalar, [[_r6(ucur), _r6(L)]], L
        cno, diger, u = en
        gor.add(cno)
        c = B.cubuk_no[cno]
        parcalar.append((cno, ucur, min(u, L), c["i"] != cur))
        cur, ucur = diger, u
    return parcalar, [], L


def _panelleri_oku(B, ham, coz):
    B.paneller, B.panel_no = [], {}
    komsu = {}
    for c in B.cubuklar:
        komsu.setdefault(c["i"], []).append((c["no"], c["j"]))
        komsu.setdefault(c["j"], []).append((c["no"], c["i"]))
    B.komsu = komsu
    D = coz.dugum
    xs = [d["X"] for d in D.values()]
    ys = [d["Y"] for d in D.values()]
    B.plan_merkez = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    for k, p in enumerate(ham, start=1):
        if not isinstance(p, dict):
            raise MatrisHatasi(f"{k}. panel sözlük olmalı.")
        no = Y._tam(p.get("no", k), f"{k}. panel: no")
        ad = f"Panel {no}"
        if no in B.panel_no:
            raise MatrisHatasi(f"Panel numarası {no} tekrarlı.")
        kose = p.get("kose")
        if not isinstance(kose, (list, tuple)) or len(kose) < 3:
            raise MatrisHatasi(f"{ad}: en az üç köşe (REF listesi) gerekir.")
        nolar = [coz.no(r, f"{ad}: köşe {i + 1}") for i, r in enumerate(kose)]
        if len(set(nolar)) != len(nolar):
            raise MatrisHatasi(f"{ad}: köşeler tekrarlı düğüm içeriyor ({nolar}).")
        P = [(D[n]["X"], D[n]["Y"], D[n]["Z"]) for n in nolar]
        g = _panel_geometri(P, ad)
        tur = str(p.get("tur") or "doseme").strip().lower()
        if tur not in _PANEL_TURLERI:
            raise MatrisHatasi(f"{ad}: tur {tur!r}; 'doseme', 'cati' ya da 'cephe' olmalı.")
        nh = g["normal"]
        if abs(nh[2]) >= 0.3:
            if nh[2] < 0:
                nh = _olc(nh, -1.0)
        else:
            mx = sum(q[0] for q in P) / len(P) - B.plan_merkez[0]
            my = sum(q[1] for q in P) / len(P) - B.plan_merkez[1]
            if nh[0] * mx + nh[1] * my < 0:
                nh = _olc(nh, -1.0)
        cos_a = abs(nh[2])
        kal = Y._sayi(p.get("kalinlik", 0.12 if tur == "doseme" else 0.0) if p.get("kalinlik") is not None else 0.0,
                      f"{ad}: kalinlik (m)", pozitif=True)
        gv = p.get("g", 0.0)
        if isinstance(gv, str) and gv.strip() in yv.KAPLAMALAR:
            kap = yv.KAPLAMALAR[gv.strip()]
            g_ek, g_kay, g_dogru = kap["deger"], f"{kap['ad']} ({kap['kaynak']})", kap["dogrulandi"]
        else:
            g_ek = Y._sayi(gv if gv not in (None, "") else 0.0, f"{ad}: g (ek sabit yük, kN/m²)", pozitif=True)
            g_kay, g_dogru = "kullanıcı değeri", True
        kullanim = str(p.get("kullanim") or ("konut" if tur == "doseme" else "")).strip().lower()
        if p.get("q") is not None:
            q, q_kay, q_dogru = Y._sayi(p.get("q"), f"{ad}: q (kN/m²)", pozitif=True), "kullanıcı değeri", True
        elif kullanim in yv.TS498_HAREKETLI:
            qk = yv.TS498_HAREKETLI[kullanim]
            q, q_kay, q_dogru = qk["deger"], qk["kaynak"], qk["dogrulandi"]
        elif kullanim:
            raise MatrisHatasi(f"{ad}: kullanım sınıfı {kullanim!r} TS 498 çizelgesinde yok. Seçenekler: {', '.join(yv.TS498_HAREKETLI)}; "
                               "ya da q değerini doğrudan verin.")
        else:
            q, q_kay, q_dogru = 0.0, "verilmedi (0)", True
        dag = str(p.get("dagitim") or "iki").strip().lower()
        if dag in ("otomatik", "cift", "tek"):
            if len(P) == 4:
                l13 = (_boy(_vek(P[0], P[1])) + _boy(_vek(P[2], P[3]))) / 2.0
                l24 = (_boy(_vek(P[1], P[2])) + _boy(_vek(P[3], P[0]))) / 2.0
                tek = "tek-13" if l13 >= l24 - 1e-9 else "tek-24"
                oran = max(l13, l24) / max(min(l13, l24), 1e-9)
                dag = "iki" if dag == "cift" else (tek if dag == "tek" else ("iki" if oran <= 2 + 1e-9 else tek))
            else:
                dag = "iki"
        if dag not in _DAGITIMLAR:
            raise MatrisHatasi(f"{ad}: dagitim {dag!r}; 'iki', 'tek-13', 'tek-24' ya da 'yok' olmalı.")
        if dag.startswith("tek") and len(P) != 4:
            raise MatrisHatasi(f"{ad}: tek doğrultulu dağıtım ({dag}) dört köşeli panel ister (köşe sayısı {len(P)}).")
        if dag == "iki" and not g["disbukey"]:
            raise MatrisHatasi(f"{ad}: iki doğrultulu (açıortay) dağıtım dışbükey panel ister; paneli dışbükey parçalara bölün.")
        tasiyan = {"iki": list(range(len(P))), "tek-13": [0, 2], "tek-24": [1, 3], "yok": []}[dag]
        kenarlar = []
        for e in range(len(P)):
            a, b = nolar[e], nolar[(e + 1) % len(P)]
            parca, bosluk, L = _kenar_zinciri(B, komsu, a, b)
            if e in tasiyan and bosluk:
                raise MatrisHatasi(f"{ad} ({tur}): {e + 1}. kenarında ({a} → {b}, {L:.2f} m) çubuk yok ya da zincir eksik "
                                   f"({', '.join(f'{x0:.2f}–{x1:.2f} m' for x0, x1 in bosluk)}). Panel yükü yalnız kenarındaki "
                                   "çubuklara aktarılabilir: eksik kirişi/aşığı çizin, dağıtımı değiştirin (tek-13 / tek-24) ya da "
                                   "'yok' seçin.")
            kenarlar.append({"kenar": e + 1, "dugumler": [a, b], "L": L, "parcalar": parca, "tam": not bosluk, "tasiyan": e in tasiyan})
        kar = p.get("kar")
        kar = (tur == "cati") if kar is None else bool(kar)
        rz = p.get("ruzgar")
        if rz is True:
            rz = {"cp": "otomatik"}
        if rz is None and tur in ("cati", "cephe"):
            rz = {"cp": "otomatik"}
        if rz not in (None, False) and not isinstance(rz, dict):
            raise MatrisHatasi(f"{ad}: ruzgar {{\"cp\": \"otomatik\" | [cp_+X, cp_-X, cp_+Y, cp_-Y]}} ya da false olmalı.")
        if isinstance(rz, dict):
            cp = rz.get("cp", "otomatik")
            if cp != "otomatik" and not (isinstance(cp, (list, tuple)) and len(cp) == 4):
                raise MatrisHatasi(f"{ad}: ruzgar.cp 'otomatik' ya da dört sayı [cp_+X, cp_-X, cp_+Y, cp_-Y] olmalı.")
            rz = {"cp": cp if cp == "otomatik" else [Y._sayi(v, f"{ad}: cp") for v in cp]}
        else:
            rz = None
        kat = p.get("kat")
        r = {"no": no, "kose": nolar, "P": P, "tur": tur, "kalinlik": kal, "g_ek": g_ek, "g_kaynak": g_kay, "g_dogrulandi": g_dogru,
             "q": q, "q_kaynak": q_kay, "q_dogrulandi": q_dogru, "kullanim": kullanim, "kar": kar, "ruzgar": rz, "dagitim": dag,
             "kat": None if kat in (None, "") else Y._tam(kat, f"{ad}: kat"), "normal": nh, "alan": g["alan"], "cos_a": cos_a,
             "egim": math.degrees(math.acos(min(1.0, cos_a))), "geo": g, "kenarlar": kenarlar, "ek_g": 0.0, "ek_q": 0.0,
             "kaynak": p.get("kaynak"), "adres": f"P{no}"}
        B.paneller.append(r)
        B.panel_no[no] = r


def _mesnetleri_oku(B, bina, coz):
    B.mesnetler = {}
    for k, m in enumerate(bina.get("mesnetler") or [], start=1):
        if not isinstance(m, dict):
            raise MatrisHatasi(f"mesnetler[{k}] sözlük olmalı: {{\"dugum\": REF, \"ux\": true, ...}}.")
        n = coz.no(m.get("dugum"), f"mesnetler[{k}]")
        bay = {a: bool(m.get(a, False)) for a in ("ux", "uy", "uz", "rx", "ry", "rz")}
        if n in B.mesnetler:
            for a in bay:
                B.mesnetler[n][a] = B.mesnetler[n][a] or bay[a]
            continue
        if not any(bay.values()):
            continue
        tip = "ankastre" if all(bay.values()) else ("mafsal" if bay["ux"] and bay["uy"] and bay["uz"] and not any(
            bay[a] for a in ("rx", "ry", "rz")) else "ozel")
        B.mesnetler[n] = dict(bay, tip=tip, kaynak="mesnetler", yay=None)
    z0 = B.katlar[0]["kot"] if B.katlar else None
    tip = B.temeller["mesnet"]
    k0 = B.temeller["zemin"]["k0"]
    for d in coz.dugum.values():
        if d["no"] in B.mesnetler or d.get("sistem") != "GLOBAL" or z0 is None or abs(d["Z"] - z0) > 1e-6:
            continue
        r = tip != "mafsal"
        kayit = {"ux": True, "uy": True, "uz": True, "rx": r, "ry": r, "rz": r, "tip": tip, "kaynak": "temel", "yay": None,
                 "aks": list(d["aks"])}
        tem = B.temeller["ozel"].get(tuple(d["aks"]), B.temeller["varsayilan"])
        kayit["B"], kayit["L"] = tem["B"], tem["L"]
        if tip == "elastik":
            Bt, Lt = tem["B"], tem["L"]
            kayit.update({"uz": False, "rx": False, "ry": False, "rz": True,
                          "yay": {"kZ": k0 * Bt * Lt, "krX": k0 * Bt * Lt ** 3 / 12.0, "krY": k0 * Lt * Bt ** 3 / 12.0}})
        B.mesnetler[d["no"]] = kayit


def _ek_yukleri_oku(B, ham, coz):
    B.ek_cubuk, B.ek_dugum = [], []
    B.ek_kar_var = False
    for k, y in enumerate(ham, start=1):
        if not isinstance(y, dict):
            raise MatrisHatasi(f"{k}. ek yük sözlük olmalı.")
        tur = str(y.get("tur", "")).strip().lower()
        durum = str(y.get("durum", "G")).strip().upper()
        if durum not in ("G", "Q", "S"):
            raise MatrisHatasi(f"{k}. ek yük: durum {durum!r}; 'G', 'Q' ya da 'S' olmalı (rüzgâr, deprem ve kren yükleri "
                               "yuk_durumlari / deprem / kren kayıtlarından üretilir).")
        if durum == "S":
            B.ek_kar_var = True
        ad = f"{k}. ek yük"
        if tur == "cubuk":
            cno = Y._tam(y.get("cubuk"), f"{ad}: cubuk")
            if cno not in B.cubuk_no:
                raise MatrisHatasi(f"{ad}: çubuk {cno} yok.")
            c = B.cubuk_no[cno]
            L = c["L"]
            yon = str(y.get("yon") or "Z").strip()
            yerel = yon in ("x", "y", "z") or yon.endswith("′") or yon.endswith("'")
            ey = yon.replace("′", "").replace("'", "").lower() if yerel else yon.upper()
            if ey not in ("X", "Y", "Z", "x", "y", "z"):
                raise MatrisHatasi(f"{ad}: yon {yon!r}; global 'X', 'Y', 'Z' ya da yerel \"x′\", \"y′\", \"z′\" olmalı.")
            if yerel:
                vek = tuple(c["lam"]["xyz".index(ey)])
            else:
                vek = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}[ey]
            olc = L if y.get("oransal") else 1.0
            carpan = 1.0
            if y.get("izdusum") and not yerel:
                carpan = math.sqrt(max(0.0, 1.0 - _ic(c["dx"], vek) ** 2))
            if y.get("x") is not None and y.get("x1") is None and y.get("q1") is None and y.get("q") is None:
                P = Y._sayi(y.get("P", y.get("F", 0.0)), f"{ad}: P (kN)")
                x = Y._sayi(y.get("x"), f"{ad}: x") * olc
                B.ek_cubuk.append({"cubuk": cno, "durum": durum, "vek": vek, "parcalar": _tekil_parca(L, x, P), "tekil": (x, P)})
                continue
            q1 = y.get("q1", y.get("q", 0.0))
            q2 = y.get("q2", q1)
            q1, q2 = Y._sayi(q1, f"{ad}: q1") * carpan, Y._sayi(q2, f"{ad}: q2") * carpan
            x1 = Y._sayi(y.get("x1", 0.0) or 0.0, f"{ad}: x1") * olc
            x2 = L if y.get("x2") in (None, "") else Y._sayi(y.get("x2"), f"{ad}: x2") * olc
            if not (-1e-9 <= x1 < x2 <= L + 1e-6):
                raise MatrisHatasi(f"{ad}: yük aralığı 0 ≤ x1 < x2 ≤ L = {L:.3f} m olmalı (x1 = {x1}, x2 = {x2}).")
            B.ek_cubuk.append({"cubuk": cno, "durum": durum, "vek": vek, "parcalar": [(max(0.0, x1), min(L, x2), q1, q2)]})
        elif tur == "dugum":
            ref = y.get("dugum")
            if ref is None and y.get("aks") is not None:
                ref = {"aks": y.get("aks"), "kat": y.get("kat", 1)}
            n = B.coz.no(ref, ad)
            F = [Y._sayi(y.get(a, 0.0), f"{ad}: {a}") for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")]
            B.ek_dugum.append({"dugum": n, "durum": durum, "F": F})
        elif tur == "panel":
            pn = Y._tam(y.get("panel"), f"{ad}: panel")
            if pn not in B.panel_no:
                raise MatrisHatasi(f"{ad}: panel {pn} yok.")
            B.panel_no[pn]["ek_g"] += Y._sayi(y.get("g", 0.0), f"{ad}: g (kN/m²)")
            B.panel_no[pn]["ek_q"] += Y._sayi(y.get("q", 0.0), f"{ad}: q (kN/m²)")
        else:
            raise MatrisHatasi(f"{ad}: tur {tur!r}; 'cubuk', 'dugum' ya da 'panel' olmalı (aks–kat modelinde 'kiris', 'doseme').")


def _tekil_parca(L, x, P):
    """Çubuk üzerindeki tekil yük → çok kısa düzgün yayılı yük (ε = min(0,01·L, 0,02 m)); eşdeğer düğüm yükleri ε → 0'da tekil yükünkine
    yakınsar, moment diyagramı yalnız ε içinde yuvarlanır."""
    e = min(0.01 * L, 0.02)
    a = min(max(x - e / 2.0, 0.0), L - e)
    return [(a, a + e, P / e, P / e)]


def _kren_oku(B, bina):
    B.kren = []
    for k, r in enumerate(bina.get("kren") or [], start=1):
        if not isinstance(r, dict):
            raise MatrisHatasi(f"kren[{k}] sözlük olmalı.")
        no = Y._tam(r.get("no", k), f"kren[{k}]: no")
        ad = f"Kren {no}"
        yol = [Y._tam(x, f"{ad}: yol") for x in (r.get("yol") or [])]
        if not yol:
            raise MatrisHatasi(f"{ad}: yol (kren kirişi çubuk numaraları, uç uca) boş.")
        for c in yol:
            if c not in B.cubuk_no:
                raise MatrisHatasi(f"{ad}: yol çubuğu {c} yok.")
        # zincir sırası ve yön
        parcalar = []
        c0 = B.cubuk_no[yol[0]]
        if len(yol) > 1:
            c1 = B.cubuk_no[yol[1]]
            bas = c0["i"] if c0["i"] not in (c1["i"], c1["j"]) else c0["j"]
        else:
            bas = c0["i"]
        s = 0.0
        cur = bas
        for cno in yol:
            c = B.cubuk_no[cno]
            if cur not in (c["i"], c["j"]):
                raise MatrisHatasi(f"{ad}: yol çubukları uç uca değil (çubuk {cno} önceki çubuğun ucuna bağlanmıyor).")
            ters = c["j"] == cur
            parcalar.append({"cubuk": cno, "s0": s, "L": c["L"], "ters": ters})
            s += c["L"]
            cur = c["i"] if ters else c["j"]
        D = B.coz.dugum
        Pb, Ps = (D[bas]["X"], D[bas]["Y"], D[bas]["Z"]), (D[cur]["X"], D[cur]["Y"], D[cur]["Z"])
        t = _birim(_vek(Pb, Ps))
        nyat = _birim(_dis((0.0, 0.0, 1.0), t))
        te = r.get("tekerlek") if isinstance(r.get("tekerlek"), dict) else {}
        tek = {"P_maks": Y._sayi(te.get("P_maks"), f"{ad}: tekerlek.P_maks (kN)", pozitif=True),
               "P_min": Y._sayi(te.get("P_min", 0.0), f"{ad}: tekerlek.P_min (kN)", pozitif=True),
               "H_yanal": Y._sayi(te.get("H_yanal", 0.0), f"{ad}: tekerlek.H_yanal (kN)", pozitif=True),
               "H_fren": Y._sayi(te.get("H_fren", 0.0), f"{ad}: tekerlek.H_fren (kN)", pozitif=True),
               "aralik": Y._sayi(te.get("aralik", 0.0), f"{ad}: tekerlek.aralik (m)", pozitif=True),
               "adet": max(1, Y._tam(te.get("adet", 1), f"{ad}: tekerlek.adet"))}
        if (tek["adet"] - 1) * tek["aralik"] > s - 1e-6:
            raise MatrisHatasi(f"{ad}: tekerlek grubu ({tek['adet']} × {tek['aralik']} m) yol boyundan ({s:.2f} m) uzun.")
        B.kren.append({"no": no, "yol": yol, "parcalar": parcalar, "uzunluk": s, "t": t, "n": nyat, "tekerlek": tek,
                       "dinamik": Y._sayi(r.get("dinamik", 1.0), f"{ad}: dinamik", pozitif=True, sifir_olur=False),
                       "konum_sayisi": max(1, min(25, Y._tam(r.get("konum_sayisi", 9), f"{ad}: konum_sayisi"))),
                       "kopru": r.get("kopru"), "kaynak": r.get("kaynak")})
    # köprü eşleştirme: aynı "kopru" değeri; yoksa ardışık paralel çiftler
    B.kopruler = []
    gor = set()
    gruplar = {}
    for kr in B.kren:
        if kr["kopru"] is not None:
            gruplar.setdefault(str(kr["kopru"]), []).append(kr)
    for g in gruplar.values():
        if len(g) > 2:
            raise MatrisHatasi(f"Kren köprüsü {g[0]['kopru']!r}: en çok iki ray (yol) olabilir.")
        B.kopruler.append(g)
        gor.update(id(x) for x in g)
    kalan = [kr for kr in B.kren if id(kr) not in gor]
    while kalan:
        a = kalan.pop(0)
        es = next((b for b in kalan if abs(abs(_ic(a["t"], b["t"])) - 1.0) < 1e-6), None)
        if es is not None:
            kalan.remove(es)
            B.kopruler.append([a, es])
        else:
            B.kopruler.append([a])


def _dugum_seviyeleri(B):
    """Kütle seviyesi: Z bir kata ≤ 0,3 m ise o kat; değilse en üst katın üstündekiler en üst kata, iki kat arasındakiler
    en yakın kata; en alt katın altındakiler hiçbir kata (kat 0)."""
    kotlar = [(kt["no"], kt["kot"]) for kt in B.katlar]
    for d in B.coz.dugum.values():
        Z = d["Z"]
        tam = next((k for k, z in kotlar if abs(Z - z) < 1e-4), None)
        d["seviye_tam"] = tam
        if tam is not None:
            d["kat"] = tam
            continue
        yakin = min(kotlar, key=lambda kz: (abs(Z - kz[1]), -kz[0]))
        if abs(Z - yakin[1]) <= _SEVIYE_TOL:
            d["kat"] = yakin[0]
        elif Z > kotlar[-1][1]:
            d["kat"] = kotlar[-1][0]
        elif Z < kotlar[0][1]:
            d["kat"] = kotlar[0][0]
        else:
            d["kat"] = yakin[0]


def _yuzen_denetle(B, coz):
    kullanilan = set()
    for c in B.cubuklar:
        kullanilan.update((c["i"], c["j"]))
    for p in B.paneller:
        for n in p["kose"]:
            if n not in kullanilan:
                raise MatrisHatasi(f"Panel {p['no']}: köşe düğümü {n} hiçbir çubuğa bağlı değil (yüzen düğüm). Panel köşeleri çubuk "
                                   "uçlarında olmalıdır.")
    for n in list(B.mesnetler):
        if n not in kullanilan:
            if B.mesnetler[n]["kaynak"] == "temel":
                del B.mesnetler[n]
            else:
                raise MatrisHatasi(f"Mesnet düğümü {n} hiçbir çubuğa bağlı değil (yüzen düğüm).")
    for y in B.ek_dugum:
        if y["dugum"] not in kullanilan:
            raise MatrisHatasi(f"Düğüm yükü düğüm {y['dugum']}'e verilmiş ama bu düğüm hiçbir çubuğa bağlı değil (yüzen düğüm); yük ancak "
                               "çubuk uçlarına verilebilir.")
    sil = [n for n in coz.dugum if n not in kullanilan]
    if sil:
        acik = [n for n in sil if n in coz.kayit]
        if acik:
            B.uyarilar.append(f"Hiçbir çubuğa bağlı olmayan düğüm kayıtları modele alınmadı (yüzen düğüm): {', '.join(map(str, acik[:12]))}"
                              + (" …" if len(acik) > 12 else "") + ".")
        for n in sil:
            del coz.dugum[n]
    if not B.mesnetler:
        raise MatrisHatasi("Yapıda mesnet yok: kat 0 Z aksındaki aks kesişimleri temele oturur (temeller.mesnet) ya da 'mesnetler' "
                           "listesiyle mesnet verin.")


# ============================================================================
# 5) Panel → çubuk yük dağıtımı
# ============================================================================
def _alan2(Q):
    s = 0.0
    for k in range(len(Q)):
        a, b = Q[k], Q[(k + 1) % len(Q)]
        s += a[0] * b[1] - b[0] * a[1]
    return s / 2.0


def _iki_kenar(Q, e):
    """İki doğrultulu (açıortay / en yakın kenar) dağıtım: e kenarına düşen bölge, kenar boyunca u noktasından içeri dik
    derinlik d(u) = min_f g_f(u) (doğrusal fonksiyonların alt zarfı). Birim alan yükü için yük şiddeti q(u) = d(u) (m).
    Dikdörtgende d(u) = min(u, L − u, l_k/2): TS 500 45° kuralının üçgen/trapez yükleri. Dönüş [(u0, u1, d0, d1)]."""
    m = len(Q)
    yon = 1.0 if _alan2(Q) > 0 else -1.0
    A, Bq = Q[e], Q[(e + 1) % m]
    tx, ty = Bq[0] - A[0], Bq[1] - A[1]
    L = math.hypot(tx, ty)
    tx, ty = tx / L, ty / L
    nx, ny = -ty * yon, tx * yon
    dogrular = []
    for f in range(m):
        if f == e:
            continue
        Af, Bf = Q[f], Q[(f + 1) % m]
        fx, fy = Bf[0] - Af[0], Bf[1] - Af[1]
        Lf = math.hypot(fx, fy)
        if Lf < 1e-12:
            continue
        fx, fy = fx / Lf, fy / Lf
        mx, my = -fy * yon, fx * yon
        c = mx * nx + my * ny
        if c > 1 - 1e-9:
            continue
        sabit = (mx * (A[0] - Af[0]) + my * (A[1] - Af[1])) / (1 - c)
        egim = (mx * tx + my * ty) / (1 - c)
        dogrular.append((sabit, egim))
    if not dogrular:
        return []
    adaylar = {0.0, L}
    for i in range(len(dogrular)):
        for j in range(i + 1, len(dogrular)):
            (a1, b1), (a2, b2) = dogrular[i], dogrular[j]
            if abs(b1 - b2) > 1e-12:
                u = (a2 - a1) / (b1 - b2)
                if 1e-9 < u < L - 1e-9:
                    adaylar.add(u)
    us = sorted(adaylar)

    def d(u):
        return max(0.0, min(a + b * u for a, b in dogrular))
    out = []
    for u0, u1 in zip(us, us[1:]):
        if u1 - u0 <= 1e-9:
            continue
        p = (u0, u1, d(u0), d(u1))
        if out:      # aynı eğimli ardışık parçalar birleştirilir (zarfın kırılmayan kesişim noktaları)
            a = out[-1]
            if abs((a[3] - a[2]) / (a[1] - a[0]) - (p[3] - p[2]) / (p[1] - p[0])) < 1e-9:
                out[-1] = (a[0], p[1], a[2], p[3])
                continue
        out.append(p)
    return out


def _tek_kenar(Q, e, tasiyan):
    """Tek doğrultulu dağıtım (dört köşeli panel, çift doğrusal eşleme X(s, t)): tek-13'te t < ½ bölgesi 1. kenara, t > ½ 3. kenara;
    tek-24'te s > ½ 2. kenara, s < ½ 4. kenara. J(s, t) düzlemsel dörtgende doğrusaldır → kenar boyunca yük doğrusal (kesin).
    Dikdörtgende taşıyan kenara q = p·l_k/2 düzgün."""
    P0, P1, P2, P3 = Q
    a = (P1[0] - P0[0], P1[1] - P0[1])
    b = (P2[0] - P3[0] - a[0], P2[1] - P3[1] - a[1])
    c = (P3[0] - P0[0], P3[1] - P0[1])
    d_ = b

    def det(u, v):
        return u[0] * v[1] - u[1] * v[0]
    J0, J1, J2 = det(a, c), det(a, d_), det(b, c)
    L = [math.hypot(P1[0] - P0[0], P1[1] - P0[1]), math.hypot(P2[0] - P1[0], P2[1] - P1[1]),
         math.hypot(P3[0] - P2[0], P3[1] - P2[1]), math.hypot(P0[0] - P3[0], P0[1] - P3[1])]

    def int_t(s, t0, t1):
        return abs((t1 - t0) * (J0 + J1 * s) + J2 * (t1 * t1 - t0 * t0) / 2.0)

    def int_s(t, s0, s1):
        return abs((s1 - s0) * (J0 + J2 * t) + J1 * (s1 * s1 - s0 * s0) / 2.0)
    if e == 0 and tasiyan == "tek-13":
        return [(0.0, L[0], int_t(0.0, 0.0, 0.5) / L[0], int_t(1.0, 0.0, 0.5) / L[0])]
    if e == 2 and tasiyan == "tek-13":
        return [(0.0, L[2], int_t(1.0, 0.5, 1.0) / L[2], int_t(0.0, 0.5, 1.0) / L[2])]
    if e == 1 and tasiyan == "tek-24":
        return [(0.0, L[1], int_s(0.0, 0.5, 1.0) / L[1], int_s(1.0, 0.5, 1.0) / L[1])]
    if e == 3 and tasiyan == "tek-24":
        return [(0.0, L[3], int_s(1.0, 0.0, 0.5) / L[3], int_s(0.0, 0.0, 0.5) / L[3])]
    return []


def _kenar_cubuga(segs, parcalar, B):
    """Kenar boyunca yük parçaları → zincirdeki çubuklara (çubuk yerel x′, i ucundan)."""
    out = []
    for cno, ua, ub, ters in parcalar:
        Lc = B.cubuk_no[cno]["L"]
        liste = []
        for u0, u1, f0, f1 in segs:
            lo, hi = max(u0, ua), min(u1, ub)
            if hi - lo <= 1e-9:
                continue
            fl = f0 + (f1 - f0) * (lo - u0) / (u1 - u0)
            fh = f0 + (f1 - f0) * (hi - u0) / (u1 - u0)
            if not ters:
                x1, x2, q1, q2 = lo - ua, hi - ua, fl, fh
            else:
                x1, x2, q1, q2 = ub - hi, ub - lo, fh, fl
            x1, x2 = max(0.0, min(x1, Lc)), max(0.0, min(x2, Lc))
            if x2 - x1 > 1e-9 and (abs(q1) > 0 or abs(q2) > 0):
                liste.append((x1, x2, q1, q2))
        if liste:
            out.append((cno, liste))
    return out


def _panel_dagit(B, p):
    """Panelin birim alan yükü için: {"cubuklar": [(cno, [(x1, x2, f1, f2)])], "dugumler": {no: pay (m²)}, "kenarlar": [...]}."""
    Q = p["geo"]["Q"]
    sonuc, dug = [], {}
    kenar_ozet = []
    for e, k in enumerate(p["kenarlar"]):
        if not k["tasiyan"]:
            kenar_ozet.append({"kenar": k["kenar"], "cubuklar": [x[0] for x in k["parcalar"]], "pay": 0.0, "sekil": "yok"})
            continue
        segs = _iki_kenar(Q, e) if p["dagitim"] == "iki" else _tek_kenar(Q, e, p["dagitim"])
        pay = sum((u1 - u0) * (d0 + d1) / 2.0 for u0, u1, d0, d1 in segs)
        cub = _kenar_cubuga(segs, k["parcalar"], B)
        sonuc += cub
        if p["dagitim"] == "iki":
            tepe = max([max(s[2], s[3]) for s in segs] + [0.0])
            plato = sum(s[1] - s[0] for s in segs if abs(s[2] - tepe) < 1e-9 and abs(s[3] - tepe) < 1e-9)
            sekil = "trapez" if plato > 1e-6 else "ucgen"
        else:
            sekil = "duzgun" if segs and abs(segs[0][2] - segs[0][3]) < 1e-9 else "dogrusal"
        kenar_ozet.append({"kenar": k["kenar"], "cubuklar": [x[0] for x in cub], "pay": pay, "sekil": sekil,
                           "parcalar_birim": [[_r(v) for v in s] for s in segs]})
    if p["dagitim"] == "yok":
        for n in p["kose"]:
            dug[n] = dug.get(n, 0.0) + p["alan"] / len(p["kose"])
    return {"cubuklar": sonuc, "dugumler": dug, "kenarlar": kenar_ozet}


# ============================================================================
# 6) Yükler: öz ağırlık, duvar, paneller (G, Q, S), ek yükler, rüzgâr (W), kren (K)
# ============================================================================
def _parcalar(B):
    """Her çubuğun FE parçaları (vute: n parça, ortalama yükseklikli kesit): [{x0, x1, A, Iy, Iz, J, h}]."""
    n_v = B.analiz["vute_parca"]
    B.parca = {}
    vute_var = False
    for c in B.cubuklar:
        k = B.kesitler[c["kesit"]]
        L = c["L"]
        if k["tip"] != "vute":
            B.parca[c["no"]] = [{"x0": 0.0, "x1": L, "A": k["A"], "Iy": k["I_zayif"], "Iz": k["I_guclu"], "J": k["J"], "h": k.get("h")}]
            continue
        vute_var = True
        t = B.kesitler[k["temel"]]
        boy = k["boy"] if k["boy"] and k["boy"] < L else L
        if k["boy"] and abs(k["boy"] - L) > 0.05 * L:
            B.uyarilar.append(f"Çubuk {c['no']}: vute boyu ({k['boy']:.2f} m) çubuk boyundan ({L:.2f} m) farklı; vute derin uçtan "
                              f"{boy:.2f} m boyunca doğrusal alındı.")
        lst = []
        for i in range(n_v):
            x0, x1 = L * i / n_v, L * (i + 1) / n_v
            xm = (x0 + x1) / 2.0
            s_ = xm if k["derin_uc"] == "i" else L - xm
            h = t["h"] + k["ek_yukseklik"] * max(0.0, 1.0 - s_ / boy)
            dk = _derin_kesit(t, h)
            lst.append({"x0": x0, "x1": x1, "A": dk["A"], "Iy": dk["I_zayif"], "Iz": dk["I_guclu"], "J": dk["J"], "h": h})
        B.parca[c["no"]] = lst
    if vute_var:
        B.uyarilar.append(f"Vute (değişken kesit) çubukları {n_v} parçaya bölünüp her parça ortalama yükseklikteki eşdeğer kesitle "
                          "modellendi (yaklaşık; kaynaklı I: başlıklar aynı, gövde uzar). Tahkikte moment kesit yüksekliğiyle "
                          "ölçeklenir (M·h₀/h).")


def _yukleri_hazirla(B):
    YK = SimpleNamespace(cubuk={c["no"]: {} for c in B.cubuklar}, dugum={}, paneller=[], durumlar_ek=[])
    durumlar = ["G", "Q"] + (["S"] if B.kar else [])

    def c_ekle(cno, durum, parcalar, vek, etiket):
        for x1, x2, q1, q2 in parcalar:
            if abs(q1) < 1e-15 and abs(q2) < 1e-15:
                continue
            YK.cubuk[cno].setdefault(durum, []).append((x1, x2, q1, q2, tuple(vek), etiket))

    def d_ekle(n, durum, F):
        h = YK.dugum.setdefault(n, {}).setdefault(durum, [0.0] * 6)
        for i in range(6):
            h[i] += F[i]

    YK.c_ekle, YK.d_ekle = c_ekle, d_ekle
    asagi = (0.0, 0.0, -1.0)
    # panel dağıtımları
    t_dos = {}
    for p in B.paneller:
        p["dag"] = _panel_dagit(B, p)
        if p["kalinlik"] > 0:
            for cno, _ in p["dag"]["cubuklar"]:
                t_dos[cno] = max(t_dos.get(cno, 0.0), p["kalinlik"])
    # öz ağırlık ve duvar
    for c in B.cubuklar:
        k = B.kesitler[c["kesit"]]
        gam = k["gamma"]
        net = None
        t = t_dos.get(c["no"], 0.0)
        if (B.analiz["kiris_oz"] == "net" and k["tip"] == "dikdortgen" and c["tur"] == "kiris" and 0.0 < t < k["h"]):
            net = k["b"] * (k["h"] - t)
        c["A_oz"] = net if net is not None else None
        c["t_doseme"] = t if net is not None else 0.0
        for pr in B.parca[c["no"]]:
            A = net if net is not None else pr["A"]
            c_ekle(c["no"], "G", [(pr["x0"], pr["x1"], gam * A, gam * A)], asagi, "oz")
        if c["duvar"]:
            if c["duvar_h"] is not None:
                h = c["duvar_h"]
            else:
                kat = c["kat"] if c["kat"] is not None else B.coz.dugum[c["i"]].get("seviye_tam")
                if kat is None or kat not in B.kat or kat == 0:
                    raise MatrisHatasi(f"Çubuk {c['no']}: duvar yüksekliği için kat bulunamadı; 'duvar_h' (m) verin.")
                h = B.kat[kat]["h"] - (k.get("h") or 0.0)
            if h <= 0:
                raise MatrisHatasi(f"Çubuk {c['no']}: duvar yüksekliği {h:.2f} m ≤ 0; duvar_h verin.")
            c["h_duvar"] = h
            w = B.duvarlar[c["duvar"]]["deger"] * h
            c_ekle(c["no"], "G", [(0.0, c["L"], w, w)], asagi, "duvar")
        else:
            c["h_duvar"] = 0.0
    # paneller
    sk = B.kar["Sk"] * B.kar["Ce"] * B.kar["Ct"] if B.kar else 0.0
    yd = (B.ham.get("yuk_durumlari") or {}).get("S") or {}
    mu_sabit = B.kar["mu"] if (B.kar and (yd.get("mu") is not None or yd.get("alpha") is not None)) else None
    for p in B.paneller:
        gs = Y.GAMMA_BA * p["kalinlik"] + p["g_ek"] + p["ek_g"]
        qh = p["q"] + p["ek_q"]
        p["g_yuzey"] = gs
        p["mu"] = (mu_sabit if mu_sabit is not None else yv.kar_mu1(p["egim"])) if (B.kar and p["kar"]) else 0.0
        p["s"] = p["mu"] * sk
        yogun = {"G": gs, "Q": qh * p["cos_a"], "S": p["s"] * p["cos_a"]}
        p["toplam"] = {d: yogun[d] * p["alan"] for d in ("G", "Q", "S")}
        for d in durumlar:
            v = yogun[d]
            if abs(v) < 1e-15:
                continue
            for cno, parcalar in p["dag"]["cubuklar"]:
                c_ekle(cno, d, [(x1, x2, v * f1, v * f2) for x1, x2, f1, f2 in parcalar], asagi, f"panel:{p['no']}")
            for n, pay in p["dag"]["dugumler"].items():
                d_ekle(n, d, [0.0, 0.0, -v * pay, 0.0, 0.0, 0.0])
    # ek yükler
    for y in B.ek_cubuk:
        if y["durum"] in durumlar:
            c_ekle(y["cubuk"], y["durum"], y["parcalar"], y["vek"], "ek")
    for y in B.ek_dugum:
        if y["durum"] in durumlar:
            d_ekle(y["dugum"], y["durum"], y["F"])
    YK.durumlar = durumlar
    _toplamlar(B, YK)
    return YK


def _cubuk_tepkileri(c, kayitlar):
    """Bir çubuğun yük kayıtlarından basit kiriş uç tepkileri (bina vektörleri): Ri, Rj (her biri 3 bileşen)."""
    L = c["L"]
    Ri, Rj = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    for x1, x2, q1, q2, vek, _ in kayitlar:
        F = (q1 + q2) / 2.0 * (x2 - x1)
        if abs(F) < 1e-15:
            Mx = 0.0
        else:   # ∫ q x dx (trapez)
            Mx = (x2 - x1) * (q1 * (2 * x1 + x2) + q2 * (x1 + 2 * x2)) / 6.0
        fj = Mx / L
        fi = F - fj
        for a in range(3):
            Ri[a] += fi * vek[a]
            Rj[a] += fj * vek[a]
    return Ri, Rj


def _toplamlar(B, YK):
    """Düğüm ağırlıkları (düşey, basit kiriş tepkileriyle; kütle ve kat tablosu için) ve yük toplamları."""
    YK.dugum_agirlik = {}
    YK.cubuk_ozet = {}
    for c in B.cubuklar:
        oz = {}
        for d, kay in YK.cubuk[c["no"]].items():
            if d not in ("G", "Q", "S"):
                continue
            Ri, Rj = _cubuk_tepkileri(c, kay)
            for n, R in ((c["i"], Ri), (c["j"], Rj)):
                h = YK.dugum_agirlik.setdefault(n, {"G": 0.0, "Q": 0.0, "S": 0.0})
                h[d] += -R[2]
            parca = {}
            for x1, x2, q1, q2, vek, et in kay:
                anah = et.split(":")[0]
                parca[anah] = parca.get(anah, 0.0) + (q1 + q2) / 2.0 * (x2 - x1) * (-vek[2])
            parca["toplam_kN"] = sum(parca.values())
            oz[d] = parca
        YK.cubuk_ozet[c["no"]] = oz
    for n, dd in YK.dugum.items():
        for d, F in dd.items():
            if d in ("G", "Q", "S"):
                h = YK.dugum_agirlik.setdefault(n, {"G": 0.0, "Q": 0.0, "S": 0.0})
                h[d] += -F[2]
    YK.toplam = {d: sum(h[d] for h in YK.dugum_agirlik.values()) for d in ("G", "Q", "S")}
    katlar = []
    for kt in B.katlar:
        s = {"G": 0.0, "Q": 0.0, "S": 0.0}
        for n, h in YK.dugum_agirlik.items():
            if B.coz.dugum[n]["kat"] == kt["no"]:
                for d in s:
                    s[d] += h[d]
        katlar.append({"kat": kt["no"], "ad": kt["ad"], "kot": kt["kot"], "h": kt["h"], **s, "w": s["G"] + s["Q"]})
    YK.katlar = katlar


def _ruzgar_panel(B, YK):
    """TS 498:2021 md. 14 / Şekil 1: panel normaline basınç p = c_p·q(z); otomatik c_p: rüzgâra bakan duvar +0,8, arka duvar ve
    yan duvarlar −0,4; rüzgâra bakan eğimli çatı yüzü (1,2·sin α − 0,4), rüzgâr altı çatı ve düz çatı −0,4. q(z) Çizelge 4
    basamağı (z: panelin en üst noktasının taban üstü yüksekliği)."""
    z0 = B.katlar[0]["kot"]
    yonler = {"W+X": (1.0, 0.0), "W-X": (-1.0, 0.0), "W+Y": (0.0, 1.0), "W-Y": (0.0, -1.0)}
    durumlar = {ad: {"cubuk": {}, "dugum": {}} for ad in yonler}
    ozet = []
    for p in B.paneller:
        if not p["ruzgar"]:
            continue
        z = max(q[2] for q in p["P"]) - z0
        qz = yv.ruzgar_q(max(z, 0.0))
        if B.ruzgar and B.ruzgar.get("sarp"):
            qz = max(qz, 1.1)
        n = p["normal"]
        kayit = {"panel": p["no"], "tur": p["tur"], "z": z, "q": qz, "cp": {}}
        for i, (ad, (dx, dy)) in enumerate(yonler.items()):
            if p["ruzgar"]["cp"] != "otomatik":
                cp = p["ruzgar"]["cp"][i]
            elif abs(n[2]) < 0.3:
                nd = n[0] * dx + n[1] * dy
                cp = 0.8 if nd < -0.5 else -0.4
            else:
                hn = math.hypot(n[0], n[1])
                if hn < 1e-6:
                    cp = -0.4
                else:
                    hd = (n[0] * dx + n[1] * dy) / hn
                    cp = (1.2 * math.sin(math.radians(p["egim"])) - 0.4) if hd < -0.5 else -0.4
            kayit["cp"][ad] = cp
            if abs(cp) < 1e-12:
                continue
            v = cp * qz
            vek = _olc(n, -1.0)
            for cno, parcalar in p["dag"]["cubuklar"]:
                durumlar[ad]["cubuk"].setdefault(cno, []).extend((x1, x2, v * f1, v * f2, vek, f"ruzgar:{p['no']}")
                                                                 for x1, x2, f1, f2 in parcalar)
            for nn, pay in p["dag"]["dugumler"].items():
                h = durumlar[ad]["dugum"].setdefault(nn, [0.0] * 6)
                for a in range(3):
                    h[a] += v * pay * vek[a]
        ozet.append(kayit)
    toplam = {}
    for ad, dd in durumlar.items():
        F = [0.0, 0.0, 0.0]
        for cno, kay in dd["cubuk"].items():
            for x1, x2, q1, q2, vek, _ in kay:
                for a in range(3):
                    F[a] += (q1 + q2) / 2.0 * (x2 - x1) * vek[a]
        for h in dd["dugum"].values():
            for a in range(3):
                F[a] += h[a]
        toplam[ad] = F
    return durumlar, {"yontem": "panel", "paneller": ozet, "toplam": {ad: [_r(v) for v in F] for ad, F in toplam.items()},
                      "kaynak": "TS 498:2021 md. 14.3 Çizelge 4 (q), Şekil 1 (c_p: duvar +0,8 / −0,4; rüzgâra bakan eğimli çatı "
                                "1,2·sin α − 0,4; rüzgâr altı −0,4); basınç panel normaline, panel dağıtımıyla çubuklara",
                      "not": "Çok açıklıklı çatıda her çatı yüzü kendi eğimi ve yönüyle Şekil 1'e göre alındı (öğretici yaklaşım); iç basınç "
                             "ve münferit eleman artırımı (×1,25, md. 14.2.3) uygulanmadı."}


def _kren_durumlari(B):
    """Kren (K) alt durumları: her köprü × konum × (a: 1. rayda P_maks, b: 2. rayda P_maks). Düşey tekerlek yükleri dinamik
    katsayıyla, yanal kuvvet raya dik yatay, fren kuvveti ray boyunca (P_maks tarafında). Tekerlek yükü çubuk ekseninde
    (ray dışmerkezliği ve burulma ihmal)."""
    durumlar, ozet = {}, []
    for ki, kopru in enumerate(B.kopruler, start=1):
        tek = kopru[0]["tekerlek"]
        phi = kopru[0]["dinamik"]
        n_k = kopru[0]["konum_sayisi"]
        S = min(r["uzunluk"] for r in kopru)
        grup = (tek["adet"] - 1) * tek["aralik"]
        for k in range(n_k):
            s0 = (S - grup) * (k / (n_k - 1) if n_k > 1 else 0.5)
            for var in ("a", "b"):
                ad = f"K{ki}.{k + 1}{var}"
                d = {"cubuk": {}, "dugum": {}}
                isaret = 1.0 if var == "a" else -1.0
                for ri, ray in enumerate(kopru):
                    ana = (ri == 0) == (var == "a")
                    P = (tek["P_maks"] if ana else tek["P_min"]) * phi
                    for w in range(tek["adet"]):
                        s = s0 + w * tek["aralik"]
                        prc = next((x for x in ray["parcalar"] if x["s0"] - 1e-9 <= s <= x["s0"] + x["L"] + 1e-9), ray["parcalar"][-1])
                        x = s - prc["s0"]
                        if prc["ters"]:
                            x = prc["L"] - x
                        bil = [((0.0, 0.0, -1.0), P), (ray["n"], isaret * tek["H_yanal"])]
                        if ana:
                            bil.append((ray["t"], isaret * tek["H_fren"]))
                        for vek, F in bil:
                            if abs(F) < 1e-12:
                                continue
                            d["cubuk"].setdefault(prc["cubuk"], []).extend(
                                (x1, x2, q1, q2, vek, "kren") for x1, x2, q1, q2 in _tekil_parca(prc["L"], x, F))
                durumlar[ad] = d
        ozet.append({"kopru": ki, "kren": [r["no"] for r in kopru], "konum_sayisi": n_k, "tekerlek": dict(tek), "dinamik": phi,
                     "yol_uzunlugu": S, "durumlar": [f"K{ki}.{k + 1}{v}" for k in range(n_k) for v in ("a", "b")]})
    return durumlar, ozet


# ============================================================================
# 7) Kütle seviyeleri (TBDY Denk. 4.16) — çubuk ve panel kütleleri uç düğümlerine, düğümler seviyelere
# ============================================================================
def _kutleler(B, YK, n=0.3, kar_payi=0.3):
    g = 9.81
    sonuc = []
    for kt in B.katlar:
        kat = kt["no"]
        if kat == 0:
            continue
        w = {}
        G = Q = S = 0.0
        for no, h in YK.dugum_agirlik.items():
            d = B.coz.dugum[no]
            if d["kat"] != kat:
                continue
            v = h["G"] + n * h["Q"] + kar_payi * h["S"]
            if abs(v) > 0:
                w[(no, 0)] = w.get((no, 0), 0.0) + v
            G, Q, S = G + h["G"], Q + h["Q"], S + h["S"]
        W = sum(w.values())
        if W <= 1e-9:
            continue
        D = B.coz.dugum
        X = sum(v * D[k[0]]["X"] for k, v in w.items()) / W
        Yc = sum(v * D[k[0]]["Y"] for k, v in w.items()) / W
        xs = [D[k[0]]["X"] for k in w]
        ys = [D[k[0]]["Y"] for k in w]
        sonuc.append({"kat": kat, "kot": kt["kot"], "H": kt["kot"] - B.katlar[0]["kot"], "h": kt["h"], "w": W, "m": W / g, "X": X, "Y": Yc,
                      "BX": max(xs) - min(xs), "BY": max(ys) - min(ys), "dugum_w": w, "G": G, "Q": Q, "S": S})
    return sonuc


# ============================================================================
# 8) Ağ ve motor modeli (cerceve3b): parçalar, mesnetler, otomatik dönme tutucuları, diyaframlar, çatlamış kopya
# ============================================================================
def _diyafram_modu(B, kat):
    an = B.analiz["diyafram"]
    if isinstance(an, dict) and an.get(str(kat)) is not None:
        v = str(an.get(str(kat))).strip().lower()
    elif isinstance(an, str):
        v = an.strip().lower()
    else:
        v = None
    if v is not None:
        if v not in ("rijit", "esnek"):
            raise MatrisHatasi(f"analiz.diyafram (kat {kat}) {v!r}; 'rijit' ya da 'esnek' olmalı.")
        return v, "analiz.diyafram"
    istek = B.deprem["diyafram"] if B.deprem else "rijit"
    dosemeli = any(p["kalinlik"] > 0 and all(B.coz.dugum[n].get("seviye_tam") == kat for n in p["kose"]) for p in B.paneller)
    if istek == "rijit" and not dosemeli:
        return "esnek", "seviyede betonarme döşeme paneli yok (sac/hafif çatı) → esnek"
    return istek, "deprem.diyafram"


def _ag_kur(B, kutle=None):
    D = B.coz.dugum
    dugumler, dno = [], {}

    def adres(d):
        if d.get("tur") == "aks":
            on = "" if d.get("sistem") == "GLOBAL" else f"{d['sistem']}:"
            return f"{on}{d['aks'][0]}{d['aks'][1]}/{d.get('z')}"
        if d.get("tur") == "bolme":
            return f"D{d['no']} (bölme)"
        if d.get("tur") == "kesisim":
            return f"D{d['no']} (kesişim)"
        return f"D{d['no']}"

    for no in sorted(D):
        d = D[no]
        kat = d["kat"]
        r = {"no": no, "X": d["X"], "Y": d["Y"], "Z": d["Z"], "adres": adres(d), "kat": kat, "aks": d.get("aks") if d.get("sistem") == "GLOBAL" else None,
             "efendi": False, "key": (no, 0, kat), "tur": d.get("tur"), "seviye_tam": d.get("seviye_tam"), "ic": False,
             "ad": d.get("ad")}
        dugumler.append(r)
        dno[no] = r
    # parçalar → FE elemanları
    catlamis = bool(B.analiz["catlamis_rijitlik"]) and B.deprem is not None
    ck = yv.TBDY_ETKIN_RIJITLIK["kolon"]["egilme"] if catlamis else 1.0
    cb = yv.TBDY_ETKIN_RIJITLIK["kiris"]["egilme"] if catlamis else 1.0
    elemanlar, model_el = [], []
    ic_no = _IC_DUGUM
    eno = 0
    for c in B.cubuklar:
        prc = B.parca[c["no"]]
        ks = B.kesitler[c["kesit"]]
        mal = B.malzemeler[ks["malzeme"]]
        beton = mal["tur"] == "beton"
        uclar = [c["i"]]
        for p in prc[:-1]:
            ic_no += 1
            P = _top(c["Pi"], _olc(c["dx"], p["x1"]))
            r = {"no": ic_no, "X": P[0], "Y": P[1], "Z": P[2], "adres": f"Ç{c['no']} ara düğümü", "kat": None, "aks": None,
                 "efendi": False, "key": (ic_no, 0, None), "tur": "ic", "seviye_tam": None, "ic": True, "ad": None}
            dugumler.append(r)
            dno[ic_no] = r
            uclar.append(ic_no)
        uclar.append(c["j"])
        c["fe"] = []
        for k, p in enumerate(prc):
            eno += 1
            p["fe"] = eno
            c["fe"].append(eno)
            serbest = {}
            if k == 0 and c["serbest"]["i"]:
                serbest["i"] = list(c["serbest"]["i"])
            if k == len(prc) - 1 and c["serbest"]["j"]:
                serbest["j"] = list(c["serbest"]["j"])
            carp = (ck if c["tur"] == "kolon" else cb) if beton else 1.0
            e = {"no": eno, "dugumler": [uclar[k], uclar[k + 1]], "tur": c["tur"], "kaynak_no": c["no"], "cubuk": c["no"], "parca": k + 1,
                 "kat": c["kat"], "L": p["x1"] - p["x0"], "kesit": c["kesit"], "lam": c["lam"],
                 "adres": f"Ç{c['no']} ({c['tur']}) {dno[c['i']]['adres']}→{dno[c['j']]['adres']}" + (f" [{k + 1}/{len(prc)}]" if len(prc) > 1 else ""),
                 "rijitlik_carpani": carp, "kaynak": {"tur": "cubuk", "no": c["no"], "parca": k + 1}}
            elemanlar.append(e)
            me = {"no": eno, "dugumler": [uclar[k], uclar[k + 1]], "E": mal["E"], "G": mal["G"], "A": p["A"], "Iy": p["Iy"], "Iz": p["Iz"],
                  "J": p["J"]}
            if abs(c["aci"]) > 1e-12:
                me["aci"] = c["aci"]
            if serbest:
                me["serbest"] = serbest
            if c["yalniz_cekme"]:
                me["yalniz_cekme"] = True
            model_el.append(me)
    n_kole = len(dugumler)
    # mesnetler + otomatik dönme tutucuları (bütün çubuk uçları mafsallı düğüm)
    mesnetler, model_mes, yaylar = [], [], []
    for no in sorted(B.mesnetler):
        m = B.mesnetler[no]
        mesnetler.append({"dugum": no, "tip": m["tip"], "aks": m.get("aks"), "B": m.get("B"), "L": m.get("L"), "kaynak": m["kaynak"],
                          "ux": m["ux"], "uy": m["uy"], "uz": m["uz"], "rx": m["rx"], "ry": m["ry"], "rz": m["rz"]})
        mm = {"dugum": no}
        for a_b, a_m in (("ux", "ux"), ("uy", "uz"), ("uz", "uy"), ("rx", "rx"), ("ry", "rz"), ("rz", "ry")):
            if m[a_b]:
                mm[a_m] = True
        model_mes.append(mm)
        if m.get("yay"):
            yaylar.append({"dugum": no, "ky": m["yay"]["kZ"], "krx": m["yay"]["krX"], "krz": m["yay"]["krY"]})
    uc_say = {}
    for me in model_el:
        for uc, n in zip(("i", "j"), me["dugumler"]):
            s = (me.get("serbest") or {}).get(uc, [])
            h = uc_say.setdefault(n, [0, 0])
            h[0] += 1
            if "My" in s and "Mz" in s:
                h[1] += 1
    donme = []
    mes_idx = {m["dugum"]: m for m in model_mes}
    for n, (top_, maf) in uc_say.items():
        if top_ and top_ == maf:
            m = mes_idx.get(n)
            if m and m.get("rx") and m.get("ry") and m.get("rz"):
                continue
            if m is None:
                m = {"dugum": n}
                model_mes.append(m)
                mes_idx[n] = m
            m.update({"rx": True, "ry": True, "rz": True})
            donme.append(n)
    if donme:
        B.uyarilar.append(f"{len(donme)} düğümde bağlı bütün çubuk uçları mafsallı (My, Mz serbest): düğüm dönmesini hiçbir çubuk "
                          f"tutmadığından dönmeler sıfır alındı (mekanizma değil; çubuk iç kuvvetlerini değiştirmez): "
                          f"{', '.join(map(str, donme[:10]))}{' …' if len(donme) > 10 else ''}.")
    # diyaframlar
    diyaframlar, efendi, mod = [], {}, {}
    istek = B.deprem is not None and kutle is not None
    for kk in (kutle or []):
        kat = kk["kat"]
        m, neden = _diyafram_modu(B, kat)
        mod[kat] = {"mod": m, "neden": neden}
        if not istek or m != "rijit":
            continue
        koleler = [d["no"] for d in dugumler if d.get("seviye_tam") == kat and not d["ic"]]
        if len(koleler) < 2:
            mod[kat] = {"mod": "esnek", "neden": "seviyede ikiden az düğüm"}
            continue
        no = _EFENDI + kat
        x, y, z = Y._motor_koordinat(kk["X"], kk["Y"], kk["kot"])
        diyaframlar.append({"dugumler": koleler, "ana": {"no": no, "x": x, "y": y, "z": z}, "ad": f"Kat {kat}"})
        efendi[kat] = no
        r = {"no": no, "X": kk["X"], "Y": kk["Y"], "Z": kk["kot"], "adres": f"KM/k{kat}", "kat": kat, "aks": None, "efendi": True,
             "key": None, "tur": "efendi", "seviye_tam": kat, "ic": False, "ad": None}
        dugumler.append(r)
        dno[no] = r
    nsd = 6 * n_kole
    if nsd > EN_FAZLA_SD:
        raise MatrisHatasi(f"Model {n_kole} düğüm × 6 = {nsd} serbestlik derecesi; tarayıcıda çözüm için en fazla {EN_FAZLA_SD}. "
                           "Modeli küçültün (bölme düğümlerini azaltın, vute parça sayısını düşürün: analiz.vute_parca).")
    model_dg = []
    for d in dugumler:
        d["m"] = Y._motor_koordinat(d["X"], d["Y"], d["Z"])
        if not d["efendi"]:
            model_dg.append({"no": d["no"], "x": d["m"][0], "y": d["m"][1], "z": d["m"][2]})
    model = {"tip": "cerceve3b", "hesap": "sayisal", "baslik": B.baslik + " — genel model", "birim": dict(B.birim),
             "dugumler": model_dg, "elemanlar": model_el, "mesnetler": model_mes, "yukler": [], "yayili": []}
    if yaylar:
        model["yaylar"] = yaylar
    if diyaframlar:
        model["diyaframlar"] = diyaframlar
    model_c = None
    if catlamis:
        model_c = dict(model, baslik=B.baslik + " — çatlamış kesit (deprem birleşimleri)",
                       elemanlar=[dict(me, Iy=me["Iy"] * e["rijitlik_carpani"], Iz=me["Iz"] * e["rijitlik_carpani"])
                                  for me, e in zip(model_el, elemanlar)])
    # göreli kat ötelemesi için alt düğüm eşlemesi (aynı plan konumu, bir alt kat seviyesinde)
    dugum_key = {}
    plan = {}
    for d in dugumler:
        if d["efendi"] or d["ic"] or d.get("seviye_tam") is None:
            continue
        plan[(round(d["X"], 3), round(d["Y"], 3), d["seviye_tam"])] = d["no"]
    for d in dugumler:
        if d["efendi"] or d["ic"] or d.get("seviye_tam") is None:
            continue
        dugum_key[(d["no"], 0, d["kat"])] = d["no"]
        alt = plan.get((round(d["X"], 3), round(d["Y"], 3), d["seviye_tam"] - 1))
        if alt is not None:
            dugum_key[(d["no"], 0, d["kat"] - 1)] = alt
    ag = {"dugumler": dugumler, "elemanlar": elemanlar, "mesnetler": mesnetler, "sd_sayisi": nsd, "mod": "sayisal",
          "dugum_key": dugum_key, "dno": dno, "efendi": efendi, "diyaframlar": diyaframlar, "n_kole": n_kole,
          "diyafram_istek": istek, "diyafram_destek": True, "diyafram_mod": mod, "rijitlik_carpani": {"kolon": ck, "kiris": cb},
          "model_c": model_c, "donme_tutulan": donme, "fe_cubuk": {e["no"]: e["cubuk"] for e in elemanlar}}
    return ag, model


class _MekanizmaAtla:
    """Model, _mekanizma_duzelt'te Cholesky ile pozitif tanımlı bulunduysa motorun özdeğerli mekanizma denetimi (O(n³), büyük
    modelde çözümün en pahalı adımı) bu blok içinde atlanır."""

    def __init__(self, etkin):
        self.etkin = etkin

    def __enter__(self):
        if self.etkin:
            self.eski = se._mekanizma_kontrol
            se._mekanizma_kontrol = lambda M_: None
        return self

    def __exit__(self, *a):
        if self.etkin:
            se._mekanizma_kontrol = self.eski
        return False


def _mekanizma_duzelt(B, ag, model):
    """Rijitlik matrisinin tekilliğini çözümden önce sınar (Cholesky; başarısızsa ölçeklenmiş özdeğerler). Yalnız DÖNME içeren
    sıfır enerjili modlar (ör. mafsallı tabanlı kolonun ve mafsallı kirişlerin oluşturduğu burulma zinciri) o dönmeyi tutarak
    giderilir (uyarı); öteleme içeren mod gerçek mekanizmadır → öğretici hata (hareket eden düğümlerle)."""
    eklenen = []
    mes = {m["dugum"]: m for m in model["mesnetler"]}
    adlar = ("ux", "uy", "uz", "rx", "ry", "rz")
    bina_ad = {"ux": "X ötelemesi", "uy": "düşey öteleme", "uz": "Y ötelemesi", "rx": "X ekseni etrafında dönme",
               "ry": "düşey eksen etrafında dönme", "rz": "Y ekseni etrafında dönme"}
    for _ in range(6):
        M = se._model_oku(dict(model, hesap="sayisal", yukler=[], yayili=[]))
        eski = se._mekanizma_kontrol
        se._mekanizma_kontrol = lambda M_: None
        try:
            se._hazirla(M)
        finally:
            se._mekanizma_kontrol = eski
        if not M.serbest_r:
            break
        Ks = M.K_r[np.ix_(M.serbest_r, M.serbest_r)]
        dg = np.diag(Ks).astype(float)

        def tam_sd(j):
            return M.ind[M.serbest_r[j]] if M.T is not None else M.serbest_r[j]
        pozitif = dg[dg > 0]
        esik = 1e-9 * float(np.median(pozitif)) if pozitif.size else 1.0
        zayif = [tam_sd(j) for j in np.flatnonzero(dg <= esik)]
        if zayif:          # rijitliği (neredeyse) sıfır serbestlik: ölçekleme bunu gizler, ayrıca yakalanır
            oteleme = [t for t in zayif if t % 6 < 3]
            if oteleme:
                dugum = sorted({M.dugumler[t // 6].no for t in oteleme})
                bil = sorted({bina_ad[adlar[t % 6]] for t in oteleme})
                raise MatrisHatasi(
                    f"Yapı mekanizma: düğüm(ler) {', '.join(map(str, dugum[:8]))} ({', '.join(bil)}) hiçbir rijitlikle tutulmuyor. "
                    "Bir düğüme bağlı bütün çubuklar mafsallıysa düğüm, çubukların düzlemine dik doğrultuda serbestçe hareket eder "
                    "(ör. X çaprazın kesişim düğümünde dört yarım çubuğun hepsi mafsallı); çubuklardan birini sürekli bırakın, eksik "
                    "çubuğu/mesneti ekleyin ya da çapraz düzenini (stabilite) denetleyin.")
            for t in zayif:
                no, a = M.dugumler[t // 6].no, adlar[t % 6]
                m = mes.get(no)
                if m is None:
                    m = {"dugum": no}
                    model["mesnetler"].append(m)
                    mes[no] = m
                m[a] = True
                eklenen.append((no, a))
            continue
        olc = 1.0 / np.sqrt(np.maximum(dg, 1e-300))
        S = Ks * olc[:, None] * olc[None, :]
        try:
            Lc = np.linalg.cholesky((S + S.T) / 2.0)
            if float(np.min(np.diag(Lc))) ** 2 > 1e-10 and float(np.min(dg)) > 1e-14 * float(np.max(np.abs(dg))):
                break
        except np.linalg.LinAlgError:
            pass
        w, V = np.linalg.eigh((S + S.T) / 2.0)
        sifir = [k for k in range(len(w)) if w[k] <= 1e-10]
        if not sifir:
            break
        yeni = set()
        for k in sifir:
            v = V[:, k]
            i = int(np.argmax(np.abs(v)))
            onemli = [j for j in np.flatnonzero(np.abs(v) > 0.2 * abs(v[i]))]
            tam = [M.ind[M.serbest_r[j]] if M.T is not None else M.serbest_r[j] for j in onemli]
            if any(t % 6 < 3 for t in tam):
                dugum = sorted({M.dugumler[t // 6].no for t in tam if t % 6 < 3})
                bil = sorted({bina_ad[adlar[t % 6]] for t in tam if t % 6 < 3})
                raise MatrisHatasi(
                    f"Yapı mekanizma: düğüm(ler) {', '.join(map(str, dugum[:8]))} ({', '.join(bil)}) hiçbir rijitlikle tutulmuyor. "
                    "Bir düğüme bağlı bütün çubuklar mafsallıysa düğüm, çubukların düzlemine dik doğrultuda serbestçe hareket eder "
                    "(ör. X çaprazın kesişim düğümünde dört yarım çubuğun hepsi mafsallı); çubuklardan birini sürekli bırakın, eksik "
                    "çubuğu/mesneti ekleyin ya da çapraz düzenini (stabilite) denetleyin.")
            t = tam[0] if len(tam) == 1 else (M.ind[M.serbest_r[i]] if M.T is not None else M.serbest_r[i])
            yeni.add((M.dugumler[t // 6].no, adlar[t % 6]))
        if not yeni:
            break
        for no, a in yeni:
            m = mes.get(no)
            if m is None:
                m = {"dugum": no}
                model["mesnetler"].append(m)
                mes[no] = m
            m[a] = True
            eklenen.append((no, a))
    ag["pozitif_tanimli"] = True
    if eklenen:
        ag["donme_tutulan"] = sorted(set(ag["donme_tutulan"]) | {n for n, _ in eklenen})
        B.uyarilar.append("Yalnız dönme içeren sıfır rijitlikli mod(lar) bulundu (ör. mafsallı tabanlı kolonla mafsallı kirişlerin burulma "
                          "zinciri): dönme tutuldu — " + ", ".join(f"düğüm {n} ({bina_ad[a]})" for n, a in eklenen[:8])
                          + (" …" if len(eklenen) > 8 else "") + ". Gerçekte taban levhası / birleşim bu dönmeyi tutar.")
    return eklenen


def _motor_yayili(B, cno, kayitlar, carpan=1.0):
    """Çubuk düzeyi yük kayıtları (x1, x2, q1, q2, bina yön vektörü) → FE parçalarına global yönlü motor kayıtları
    (bina X → gx, bina Y → −gz, bina Z → gy)."""
    out = []
    prc = B.parca[cno]
    for x1, x2, q1, q2, vek, _ in kayitlar:
        bil = [(vek[0], "gx"), (-vek[1], "gz"), (vek[2], "gy")]
        for p in prc:
            lo, hi = max(x1, p["x0"]), min(x2, p["x1"])
            if hi - lo <= 1e-9:
                continue
            ql = q1 + (q2 - q1) * (lo - x1) / (x2 - x1)
            qh = q1 + (q2 - q1) * (hi - x1) / (x2 - x1)
            for c, yon in bil:
                if abs(c) < 1e-12:
                    continue
                out.append({"eleman": p["fe"], "q1": carpan * c * ql, "q2": carpan * c * qh, "x1": lo - p["x0"], "x2": hi - p["x0"],
                            "yon": yon})
    return out


def _motor_durum(B, cubuk, dugum):
    """{cno: [kayıt]}, {dugum: F6 (bina)} → motor yük durumu {"yukler", "yayili", "yayili_esdeger"}."""
    yayili = []
    for cno, kay in cubuk.items():
        yayili += _motor_yayili(B, cno, kay)
    yukler = []
    for n, F in dugum.items():
        if any(abs(v) > 0 for v in F):
            Fm, Mm = Y._motor_vek(F[:3]), Y._motor_vek(F[3:])
            yukler.append({"dugum": n, "Fx": Fm[0], "Fy": Fm[1], "Fz": Fm[2], "Mx": Mm[0], "My": Mm[1], "Mz": Mm[2]})
    return {"yukler": yukler, "yayili": yayili, "yayili_esdeger": []}


# ============================================================================
# 9) Yalnız çekme: kombinasyon başına doğrudan, yinelemeli çözüm (etkin küme başına rijitlik önbelleği)
# ============================================================================
_DURUM_ALANLARI = ("K", "K_eleman", "T", "ind", "kol", "n_r", "K_r", "sabit_r", "serbest_r", "kole_sd", "oto_sd")


def _yc_coz(model, durumlar, istasyon_durumlari, nokta, en_fazla=10):
    """Yalnız-çekme çubuklu modeli her durum için ayrı ve yinelemeli çözer (se.coz_yalniz_cekme ile aynı kural: basınçtaki
    yalnız-çekme çubukları çıkarılır, uzaması çekmeye dönen devre dışı çubuklar geri alınır, ≤ en_fazla çözüm). Fark: aynı
    etkin küme için rijitlik ve tersi önbellekte tutulur (çok kombinasyonda hız). İstasyonlar istasyon_durumlari ile ortak."""
    tum = dict(istasyon_durumlari)
    tum.update(durumlar)
    girdi = {ad: {"yukler": d["yukler"], "yayili": d["yayili"]} for ad, d in tum.items()}
    M, adlar, yukler, adet = se._coklu_hazirla(model, girdi, nokta, ad="coz_yalniz_cekme")
    sabit_x = se._ortak_istasyonlar(M, adet, [yukler[ad][1:] for ad in adlar])
    yc = [e for e in M.elemanlar if e.yalniz_cekme]
    onbellek = {}

    def kur(pasif):
        key = frozenset(pasif)
        for e in M.elemanlar:
            e.etkin = e.idx not in pasif
        if key in onbellek:
            st = onbellek[key]
            for a in _DURUM_ALANLARI:
                setattr(M, a, st[a])
            return st
        se._K_kur(M)
        se._diyafram_kur(M)
        Kff = M.K_r[np.ix_(M.serbest_r, M.serbest_r)]
        try:
            inv = np.linalg.inv(Kff) if M.serbest_r else np.zeros((0, 0))
        except np.linalg.LinAlgError:
            raise MatrisHatasi("mekanizma") from None
        if M.serbest_r:
            sinama = Kff @ (inv @ np.ones(len(M.serbest_r)))
            if not np.all(np.isfinite(inv)) or np.max(np.abs(sinama - 1.0)) > 1e-5:
                raise MatrisHatasi("mekanizma")
        st = {a: getattr(M, a) for a in _DURUM_ALANLARI}
        st["inv"] = inv
        onbellek[key] = st
        return st

    def coz(st):
        F = se._F_indirgenmis(M)
        u = np.zeros(M.n_r)
        for i, v in M.cokme.items():
            u[M.kol[i]] = v
        if M.serbest_r:
            rhs = F[M.serbest_r]
            if M.cokme:
                rhs = rhs - M.K_r[np.ix_(M.serbest_r, M.sabit_r)] @ u[M.sabit_r]
            u[M.serbest_r] = st["inv"] @ rhs
        return u

    sonuc = {}
    for ad in durumlar:
        se._yuk_durumu_yukle(M, *yukler[ad])
        pasif, gecmis, uyarilar, yineleme, kararli = set(), [], [], 0, None
        while True:
            try:
                st = kur(pasif)
            except MatrisHatasi:
                if kararli is None:
                    raise MatrisHatasi(f"Yalnız çekme çözümü ({ad}): bütün çubuklar etkinken yapı mekanizma.") from None
                uyarilar.append(f"Mekanizma: basınçtaki yalnız-çekme çubukları (FE {', '.join(str(M.elemanlar[i].no) for i in sorted(pasif))}) "
                                "çıkarılınca yapı kararsız kalıyor; son kararlı etkin kümenin çözümü verildi.")
                pasif = kararli[0]
                st = kur(pasif)
                break
            yineleme += 1
            u_r = coz(st)
            M.u_r = u_r
            M.u = u_r.copy() if M.T is None else M.T @ u_r
            se._eleman_kuvvetleri(M)
            kararli = (set(pasif), u_r)
            tol = 1e-9 * max([1.0] + [abs(float(e.N)) for e in M.elemanlar])
            yeni = set()
            for e in yc:
                if e.etkin:
                    if float(e.N) < -tol:
                        yeni.add(e.idx)
                elif float(e.N_sanal) <= tol:
                    yeni.add(e.idx)
            if yeni == pasif:
                break
            if yineleme >= en_fazla:
                uyarilar.append(f"Yakınsamadı: {en_fazla} yinelemede etkin çubuk kümesi kararlı olmadı; son çözüm verildi.")
                break
            if yeni in gecmis:
                uyarilar.append("Salınım: etkin çubuk kümesi daha önce denenmiş bir kümeye döndü; son çözüm verildi.")
                break
            gecmis.append(set(pasif))
            pasif = yeni
        kur(kararli[0])
        kisa = se._durum_sonuclari(M, kararli[1], adet, sabit_x)
        kisa["etkin_degil"] = sorted(M.elemanlar[i].no for i in kararli[0])
        kisa["yineleme"] = yineleme
        kisa["uyarilar"] = uyarilar
        sonuc[ad] = kisa
    for e in M.elemanlar:
        e.etkin = True
    return sonuc, len(onbellek)


def _yalniz_cekme_coz(B, ag, model, durumlar, paket, kombinasyonlar, deprem):
    """Yalnız-çekme çubuğu olan modelde dayanım, deprem, servis ve öteleme birleşimleri süperpozisyonla değil, birleşik yük
    durumu olarak doğrudan çözülür; sonuçlar pakete '#ad' adıyla girer ve birleşimin çözüm katsayısı {'#ad': 1}. Deprem
    birleşimleri (ve onlara giren G, Q, S) çatlamış kesitli modelle (varsa). Öteleme tablosu saf E± durumlarının doğrudan
    çözümünden yeniden kurulur."""
    nokta = B.analiz["diyagram_nokta"]
    brut, catl = {}, {}
    for k in kombinasyonlar:
        if not k["uygulandi"]:
            continue
        kat = {d.replace(Y._CATLAMIS_EK, ""): v for d, v in k["cozum"].items()}
        kayit = Y._yuk_kayit_birlesim(durumlar, kat)
        hedef = catl if (ag.get("model_c") is not None and k["tur"] in ("deprem", "drift")) else brut
        hedef["#" + k["ad"]] = kayit
    e_saf = {}
    if deprem:
        for ad in ("EX+", "EX-", "EY+", "EY-"):
            if ad in durumlar:
                e_saf["#E:" + ad] = durumlar[ad]
        (catl if ag.get("model_c") is not None else brut).update(e_saf)
    istasyon = {ad: d for ad, d in durumlar.items() if not Y._birim_mi(ad)}
    sonuc, kume = {}, 0
    for m, grup in ((model, brut), (ag.get("model_c"), catl)):
        if not grup:
            continue
        r, n = _yc_coz(m, grup, istasyon, nokta, B.analiz["yalniz_cekme_yineleme"])
        sonuc.update(r)
        kume += n
    ozet = {}
    for ad, k in sonuc.items():
        paket.ekle(ad, Y._kisa_bina(_kisa_normal(k), ag))
        ozet[ad[1:]] = {"etkin_degil": k["etkin_degil"], "yineleme": k["yineleme"], "uyarilar": k["uyarilar"]}
    for k in kombinasyonlar:
        if k["uygulandi"]:
            k["cozum"] = {"#" + k["ad"]: 1.0}
    if deprem and e_saf:
        _drift_yeniden(B, ag, deprem, paket)
    yc = [c["no"] for c in B.cubuklar if c["yalniz_cekme"]]
    return {"var": True, "cubuklar": yc, "kombinasyonlar": ozet, "etkin_kume_sayisi": kume,
            "aciklama": "Yalnız çekme çubuğu basınçta devre dışı kalır: çubuğun rijitliği yük işaretine bağlıdır, yapı doğrusal değildir. "
                        "Doğrusal olmayan çözümde süperpozisyon geçersizdir: G ve Q'nun ayrı çözümlerini toplayıp kombinasyon kurmak, "
                        "hangi çaprazın çalıştığını yanlış verir. Bu yüzden her dayanım, deprem, servis ve öteleme birleşimi kendi "
                        "toplam yüküyle baştan, yinelemeli çözüldü (basınca düşen çubuk çıkarılır, kalan sistem yeniden çözülür, etkin "
                        "küme değişmeyene dek). Tekil yük durumları (G, Q, W…) tabloda doğrusal ön çözümdür (bütün çubuklar etkin); "
                        "periyot ve deprem kuvvetleri de bu doğrusal modelden hesaplandı."}


def _kisa_normal(k):
    """se KISA (motor) → yapi._kisa_bina girdisi (yapi._durumlari_coz ile aynı normalleştirme; N için istasyon dizisi Nx)."""
    elemanlar = []
    for e in k["elemanlar"]:
        diy = e.get("diyagram", e)
        kayit = {"no": e["no"], "uc_kuvvetleri": [float(x) for x in e["uc_kuvvetleri"]], "x": [float(x) for x in diy["x"]]}
        for ad_ in Y._DIYAGRAM:
            v = diy.get("Nx") if ad_ == "N" and isinstance(diy.get("Nx"), (list, tuple)) else diy.get(ad_)
            if v is None:
                kayit[ad_] = [0.0] * len(kayit["x"])
            elif isinstance(v, (int, float)):
                kayit[ad_] = [float(v)] * len(kayit["x"])
            else:
                kayit[ad_] = [float(x) for x in v]
        elemanlar.append(kayit)
    return {"u": [float(x) for x in k["u"]],
            "tepkiler": [{a: float(t.get(a, 0.0)) for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")} | {"dugum": t["dugum"]} for t in k["tepkiler"]],
            "elemanlar": elemanlar, "denge": {a: float(k["denge"].get(a, 0.0)) for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")},
            "yaylar": [dict(y) for y in k.get("yaylar") or []]}


def _drift_yeniden(B, ag, deprem, paket):
    """Göreli kat ötelemesi (TBDY md. 4.9.1): saf E± durumlarının doğrudan (yalnız-çekme) çözümüyle yeniden."""
    R, I = deprem["R"], deprem["I"]
    uyar = []
    for yon in ("X", "Y"):
        y = yon.lower()
        v = deprem[yon]
        if f"#E:E{yon}+" not in paket.durum:
            continue
        dp_ = Y._delta_katlar(B, ag, paket, paket.durum[f"#E:E{yon}+"], yon)
        dm_ = Y._delta_katlar(B, ag, paket, paket.durum[f"#E:E{yon}-"], yon)
        for s in deprem["katlar"]:
            kat = s["kat"]
            D_max = max(dp_[kat]["max"], dm_[kat]["max"]) * v["olcek_drift"]
            delta = R / I * D_max
            oran = v["lambda"] * delta / s["h"] if s["h"] else 0.0
            s.update({f"delta_{y}": D_max, f"delta_etkin_{y}": delta, f"oran_{y}": oran, f"uygun_{y}": oran <= v["sinir"] + 1e-12})
        kotu = [s["kat"] for s in deprem["katlar"] if not s[f"uygun_{y}"]]
        if kotu:
            uyar.append(f"{yon} yönü (yalnız-çekme doğrudan çözüm): göreli kat ötelemesi sınırı aşıldı — kat(lar) {kotu}.")
    for s in deprem["katlar"]:
        s["uygun"] = bool(s.get("uygun_x", True) and s.get("uygun_y", True))
    deprem["drift_yontemi"] = "yalnız-çekme doğrudan çözüm (E± durumları ayrı ayrı)"
    deprem["uyarilar"] = list(deprem["uyarilar"]) + uyar


# ============================================================================
# 10) Kren kombinasyonları ve zarfı
# ============================================================================
def _kren_kombinasyonlari(liste, kren_adlar):
    """Q ailesi: hareketli yük içeren her dayanım/servis birleşimi, her kren alt durumu için bir kez daha, K aynı Q katsayısıyla
    (Türk yönetmeliklerinde ayrı kren katsayısı yok; öğretici varsayım). Deprem birleşimlerine kren kaldırma yükü girmez
    (TBDY 4.5.9.2: kütleye de katılmaz)."""
    if not kren_adlar:
        return liste
    out = []
    for k in liste:
        out.append(k)
        if not k["uygulandi"] or k["tur"] not in ("dayanim", "servis"):
            continue
        gq = k["katsayilar"].get("Q", 0.0)
        if gq <= 0:
            continue
        for ka in kren_adlar:
            ks = dict(k["katsayilar"])
            ks[ka] = gq
            out.append(dict(k, ad=Y._komb_adi(ks), katsayilar=ks, kren=ka,
                            yon=dict(k.get("yon") or {}, K=ka),
                            **{"not": (k.get("not") + "; " if k.get("not") else "") + f"kren {ka}: Q ile aynı katsayı ({_f(gq, 2)}), öğretici varsayım"}))
    return out


def _kren_veri(B, paket, ozet, ag):
    if not ozet:
        return None
    adlar = [a for o in ozet for a in o["durumlar"] if a in paket.durum]
    z = Y._zarf_paket(paket, [{"ad": a, "katsayilar": {a: 1.0}, "cozum": {a: 1.0}, "uygulandi": True, "tur": "dayanim"} for a in adlar])
    yol = {c for kr in B.kren for c in kr["yol"]}
    fe = {fe_ for c in yol for fe_ in B.cubuk_no[c]["fe"]}
    return {"kopruler": [dict(o, tekerlek={a: _r(v) for a, v in o["tekerlek"].items()}) for o in ozet],
            "durumlar": adlar,
            "zarf": [{a: (_r6(v) if isinstance(v, float) else v) for a, v in e.items()} for e in z["elemanlar"] if e["no"] in fe],
            "kaynak": "Türk yönetmeliklerinde kren yük katsayısı yok (TS 498:2021 kapsam dışı; TBDY 4.5.9.2 yalnız kütle kuralı). "
                      "Öğretici varsayım: düşey tekerlek yükü × dinamik katsayı, yanal ve fren kuvvetleri tekerlekte; K, Q ailesiyle "
                      "aynı katsayıyla birleşimlere girer (TS EN 1991-3 ve üretici verisiyle doğrulanmalı).",
            "aciklama": "Her konum ve köprü yönü (a: 1. rayda P_maks, b: 2. rayda P_maks) ayrı bir yük durumudur; zarf bütün alt "
                        "durumların uç değerleri."}


# ============================================================================
# 11) Yük akışı (kolon tablosu, mesnet/temel tablosu, korunum, panel → çubuk bantları)
# ============================================================================
def _uc_N(kisa_e, uc):
    """Basınç + eksenel kuvvet: i ucunda f[0], j ucunda −f[6]."""
    f = kisa_e["uc_kuvvetleri"]
    return f[0] if uc == "i" else -f[6]


def _akis(B, YK, ag, durumlar_kisa):
    G, Q = durumlar_kisa["G"], durumlar_kisa["Q"]
    eG = {e["no"]: e for e in G["elemanlar"]}
    eQ = {e["no"]: e for e in Q["elemanlar"]}
    D = B.coz.dugum
    kolonlar = []
    ust_kolon = {}
    for c in B.cubuklar:
        if c["tur"] == "kolon":
            alt, ust = (c["i"], c["j"]) if D[c["i"]]["Z"] <= D[c["j"]]["Z"] else (c["j"], c["i"])
            ust_kolon.setdefault(alt, []).append(c)
    for c in B.cubuklar:
        if c["tur"] != "kolon":
            continue
        alt_i = D[c["i"]]["Z"] <= D[c["j"]]["Z"]
        fe = c["fe"][0] if alt_i else c["fe"][-1]
        uc = "i" if alt_i else "j"
        ust = c["j"] if alt_i else c["i"]
        NG, NQ = _uc_N(eG[fe], uc), _uc_N(eQ[fe], uc)
        uG = uQ = 0.0
        for c2 in ust_kolon.get(ust, []):
            alt2_i = D[c2["i"]]["Z"] <= D[c2["j"]]["Z"]
            fe2 = c2["fe"][0] if alt2_i else c2["fe"][-1]
            uG += _uc_N(eG[fe2], "i" if alt2_i else "j")
            uQ += _uc_N(eQ[fe2], "i" if alt2_i else "j")
        kolonlar.append({"no": c["no"], "kat": c["kat"] if c["kat"] is not None else D[ust]["kat"], "adres": ag["dno"][ust]["adres"],
                         "eleman": fe, "N_G": NG - uG, "N_Q": NQ - uQ, "N_kum_G": NG, "N_kum_Q": NQ, "kaynak": c.get("kaynak")})
    desG, desQ = Y._mesnet_kuvvetleri(G), Y._mesnet_kuvvetleri(Q)
    temeller = []
    q_em = B.temeller["zemin"]["q_em"]
    h_t = B.temeller["varsayilan"]["h"]
    for m in ag["mesnetler"]:
        tg, tq = desG.get(m["dugum"]), desQ.get(m["dugum"])
        if tg is None or tq is None:
            continue
        kol = next((c["no"] for c in B.cubuklar if c["tur"] == "kolon" and m["dugum"] in (c["i"], c["j"])), None)
        r = {"dugum": m["dugum"], "kolon_no": kol, "aks": m.get("aks"), "tip": m["tip"], "N_G": tg["FZ"], "N_Q": tq["FZ"],
             "MX": tg["MX"] + tq["MX"], "MY": tg["MY"] + tq["MY"]}
        if m.get("kaynak") == "temel":
            Bt, Lt = m["B"], m["L"]
            N = tg["FZ"] + tq["FZ"] + Y.GAMMA_BA * Bt * Lt * h_t
            sig_m = 6.0 * abs(r["MX"]) / (Bt * Lt * Lt) + 6.0 * abs(r["MY"]) / (Lt * Bt * Bt)
            smax, smin = N / (Bt * Lt) + sig_m, N / (Bt * Lt) - sig_m
            eX, eY = (abs(r["MY"]) / N, abs(r["MX"]) / N) if N > 1e-9 else (0.0, 0.0)
            r.update({"B": Bt, "L": Lt, "h": h_t, "N_servis": N, "sigma_max": smax, "sigma_min": smin, "e_X": eX, "e_Y": eY,
                      "q_em": q_em, "DC": smax / q_em if q_em else 0.0, "cekirdek_icinde": eX <= Bt / 6.0 + 1e-12 and eY <= Lt / 6.0 + 1e-12})
        temeller.append(r)
    korunum = {}
    for d, kisa in durumlar_kisa.items():
        if d not in ("G", "Q", "S"):
            continue
        tep = sum(t["FZ"] for t in kisa["tepkiler"])
        yay = sum(y["kuvvet"] for y in kisa["yaylar"] if y.get("bilesen") == "Fy")
        parca = {"paneller": sum(p["toplam"][d] for p in B.paneller if p["dagitim"] != "yok") + sum(
                     p["toplam"][d] for p in B.paneller if p["dagitim"] == "yok"),
                 "cubuk_oz": sum(o.get(d, {}).get("oz", 0.0) for o in YK.cubuk_ozet.values()),
                 "duvarlar": sum(o.get(d, {}).get("duvar", 0.0) for o in YK.cubuk_ozet.values())}
        parca["ek"] = YK.toplam[d] - sum(parca.values())
        parca.update({"toplam": YK.toplam[d], "temel": tep, "yay": yay, "kolon_taban": tep + yay})
        korunum[d] = parca
    sankey = []
    for p in B.paneller:
        if p["toplam"]["G"] <= 0:
            continue
        for cno, parcalar in p["dag"]["cubuklar"]:
            kN = p["g_yuzey"] * sum((x2 - x1) * (f1 + f2) / 2.0 for x1, x2, f1, f2 in parcalar)
            sankey.append({"kaynak": f"P{p['no']}", "hedef": f"Ç{cno}", "durum": "G", "kN": kN})
    if len(sankey) > 600:
        sankey = sorted(sankey, key=lambda s: -s["kN"])[:600]
    return {"kolonlar": kolonlar, "temeller": temeller, "korunum": korunum, "sankey": sankey}


# ============================================================================
# 12) Tasarım: bütün çubuklar (kolon, kiriş, çapraz, makas, aşık, kren, bağ, diğer; eğik betonarme)
# ============================================================================
_I_N, _I_V, _I_M, _I_VZ, _I_MY = 0, 1, 2, 3, 4


def _tasarim_baglam(B, ag, paket, kombinasyonlar):
    kombs = [k for k in kombinasyonlar if k["uygulandi"] and k["tur"] in ("dayanim", "deprem")]
    adlar_d = list(paket.durum)
    G = np.zeros((len(kombs), len(adlar_d)))
    for i, k in enumerate(kombs):
        for d, g in k.get("cozum", k["katsayilar"]).items():
            if d in paket.durum:
                G[i, adlar_d.index(d)] = g
    D = np.array([paket.durum[d]["diy"] for d in adlar_d]) if adlar_d else np.zeros((0, paket.L))
    return SimpleNamespace(B=B, ag=ag, paket=paket, kombs=kombs, adlar=[k["ad"] for k in kombs],
                           deprem=[k["tur"] == "deprem" for k in kombs], C=G @ D,
                           idx={no: j for j, no in enumerate(paket.el_no)}, sonuclar={}, serbest=True)


def _capraz_duzen(B, c):
    kay = c.get("kaynak") or {}
    if isinstance(kay, dict) and kay.get("uretec") is not None:
        u = next((x for x in (B.ham.get("uretecler") or []) if isinstance(x, dict) and x.get("no") == kay.get("uretec")), None)
        if u and u.get("tur") == "capraz":
            return {"X": "X", "tek-/": "tek", "tek-\\": "tek", "V": "V", "ters-V": "ters_V", "K": "K"}.get(u.get("tip"), "tek")
    g = str(c.get("grup") or "").upper().replace("_", "-")
    if "TERS" in g and "V" in g:
        return "ters_V"
    if g in ("V", "V-CAPRAZ") or g.endswith("-V"):
        return "V"
    if "X" in g.split("-") or g.startswith("X"):
        return "X"
    if g in ("K", "K-CAPRAZ") or g.startswith("K-"):
        return "K"
    return "tek"


def _suneklik(B):
    if not B.deprem:
        return None
    s = yv.TBDY_TASIYICI[B.deprem["tasiyici"]]["suneklik"]
    return "SDS" if s == "sinirli" else "SDY"


def _dosemeli(B, c):
    """Üst başlık yanal tutulu mu: çubuk bir döşeme ya da çatı panelinin yükünü taşıyor (döşeme plağı / çatı kaplaması üst başlığa
    bağlı). Pozitif momentte L_b = 0, negatif momentte L_b = boy alınır."""
    return any(p["tur"] in ("doseme", "cati") and any(cno == c["no"] for cno, _ in p["dag"]["cubuklar"]) for p in B.paneller)


def _bloklar(T, c):
    """[(blok (nk, 6, ns), x (çubuk boyunca), ölçek (vute: h0/h), parça)]"""
    out = []
    ks = T.B.kesitler[c["kesit"]]
    h0 = T.B.kesitler[ks["temel"]]["h"] if ks["tip"] == "vute" else None
    for p in T.B.parca[c["no"]]:
        b = Y._blok(T, p["fe"])
        xs = np.array(T.paket.el_x[T.idx[p["fe"]]]) + p["x0"]
        olcek = (h0 / p["h"]) if (h0 and p.get("h")) else 1.0
        out.append((b, xs, olcek, p))
    return out


def _on_ele(kuv, anahtarlar, n=3, en_cok=14):
    """Kombinasyon ön elemesi (hız): her büyüklükte (|N|, |Mx|, |My|, |V| …) en büyük n kombinasyon ve normalize toplamı en büyük
    n kombinasyon tutulur; belirleyen kombinasyon (etkileşimde bile) neredeyse her zaman bunlardandır. En çok ``en_cok`` kayıt."""
    if len(kuv) <= en_cok:
        return kuv
    sec = []
    enb = {a: max(abs(k.get(a, 0.0)) for k in kuv) or 1.0 for a in anahtarlar}
    for a in anahtarlar:
        sec += sorted(range(len(kuv)), key=lambda i: -abs(kuv[i].get(a, 0.0)))[:n]
    sec += sorted(range(len(kuv)), key=lambda i: -sum(abs(kuv[i].get(a, 0.0)) / enb[a] for a in anahtarlar))[:n + 1]
    tut = sorted(set(sec))[:en_cok]
    return [kuv[i] for i in tut]


def _celik_kuvvet(T, bl, i, ad):
    Nv = np.concatenate([-b[i, _I_N, :] for b, _, _, _ in bl])
    return {"ad": ad, "N": float(Nv[int(np.argmax(np.abs(Nv)))]),
            "Mx": float(max(np.max(np.abs(b[i, _I_M, :])) * o for b, _, o, _ in bl)),
            "My": float(max(np.max(np.abs(b[i, _I_MY, :])) for b, _, _, _ in bl)),
            "V": float(max(np.max(np.abs(b[i, _I_V, :])) for b, _, _, _ in bl))}


def _cubuk_tasarla(ts, T, c, anl=None, bilgi=None):
    """Bir çubuğun tahkiki → (§11 kaydı, uyarılar, ek). bilgi: kesit önerisi için kullanılan parametreler (dışarı yazılır)."""
    B = T.B
    ks = B.kesitler[c["kesit"]]
    kt = B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
    mal = B.malzemeler[kt["malzeme"]]
    bl = _bloklar(T, c)
    L = c["L"]
    kayit = {"no": c["no"], "kat": c["kat"], "adres": f"Ç{c['no']} ({c['tur']})", "kesit": c["kesit"]}
    fe = list(c["fe"])
    uy = []
    yontem = "GKT" if B.kombinasyon_kumesi == "cythye_gkt" else "YDKT"
    varsayim = []
    bilgi = bilgi if bilgi is not None else {}
    if mal["tur"] == "celik":
        kb = {"sistem": "celik", "malzeme_ad": kt["malzeme"]}
        profil = kt["profil"]
        ihi = profil in yv.PROFILLER
        mafsal2 = all("My" in c["serbest"][u] and "Mz" in c["serbest"][u] for u in ("i", "j"))
        cubuk_kontrol = c["tur"] in _CUBUK_TURLERI or not ihi
        K = c["K"] or [1.0, 1.0]
        if c["K"] is None:
            varsayim.append("K = 1 (güçlü ve zayıf eksen)")
        if cubuk_kontrol:
            kuv = []
            for i, ad in enumerate(T.adlar):
                Nv = np.concatenate([-b[i, _I_N, :] for b, _, _, _ in bl])
                Nc, Nt = float(np.max(Nv)), float(-np.min(Nv))
                if Nc > 1e-9:
                    kuv.append({"ad": ad, "N": Nc})
                if Nt > 1e-9:
                    kuv.append({"ad": ad + " (çekme)", "N": -Nt})
                if Nc <= 1e-9 and Nt <= 1e-9:
                    kuv.append({"ad": ad, "N": 0.0})
            bas = _on_ele([k for k in kuv if k["N"] > 0], ["N"], n=3, en_cok=4)
            cek = _on_ele([k for k in kuv if k["N"] <= 0], ["N"], n=3, en_cok=4)
            kuv = bas + cek
            Mmax = max(float(np.max(np.abs(b[:, _I_M, :]))) for b, _, _, _ in bl) if len(T.adlar) else 0.0
            if Mmax > 1.0 and not mafsal2:
                uy.append(f"Çubuk tahkikinde eğilme momenti (|M| ≤ {_f(Mmax, 1)} kN·m) yok sayıldı (eksenel çubuk kabulü); uçları mafsallı "
                          "yapın ya da I/H kesitle eğilmeli eleman tahkiki kullanın.")
            tc = None
            if c["tur"] == "capraz" and B.deprem:
                tc = {"suneklik": _suneklik(B), "duzen": _capraz_duzen(B, c)}
            if c["tur"] == "capraz" and _capraz_duzen(B, c) == "K":
                uy.append("K çapraz düzeni (çaprazlar kolon ortasına bağlı): TBDY 2018 md. 9.6.4.2 / 9.7.4.2 uyarınca deprem yükü "
                          "taşıyan sistemde kullanılamaz; yalnız rüzgâr/stabilite bağı olarak kullanın.")
            r = ts.celik_cubuk_kontrol(profil, mal["kutuphane"], L=L, K=tuple(K), kuvvetler=kuv, yalniz_cekme=c["yalniz_cekme"],
                                       yontem=yontem, tbdy_capraz=tc, anl=anl)
            bilgi.update({"kontrol": "cubuk", "L": L, "K": tuple(K), "kuvvetler": kuv, "yalniz_cekme": c["yalniz_cekme"],
                          "tbdy_capraz": tc, "yontem": yontem})
            en = max(r["kombinasyonlar"], key=lambda x: x["dc"]) if r["kombinasyonlar"] else None
            kont = []
            for x in r["kontroller"]:
                ad_, komb = x["ad"], None
                if en and ad_.startswith(en["ad"] + ": "):
                    komb, ad_ = en["ad"].replace(" (çekme)", ""), ad_[len(en["ad"]) + 2:]
                kosul = ad_.startswith("Narinlik") or ad_.startswith("TBDY")
                et = "narinlik" if ad_.startswith("Narinlik") else ("TBDY çapraz" if ad_.startswith("TBDY") else
                                                                     ("eksenel (çekme)" if "çekme" in ad_ else "eksenel (basınç)"))
                kont.append(Y._kontrol_kaydi(x, komb, ad_, et, kosul=kosul))
            ozet = {"kontrol": "çubuk (eksenel)", "profil": r["profil"], "L_m": L, "K": list(K), "yontem": r["yontem"],
                    "Tc_kN": r["cekme"]["Tc_kN"], "Pc_kN": (r["basinc"] or {}).get("Pc_kN"),
                    "narinlik_basinc": ((r["narinlik"] or {}).get("basinc") or {}).get("oran"),
                    "narinlik_cekme": ((r["narinlik"] or {}).get("cekme") or {}).get("oran"),
                    "N_kN": en["N"] if en else 0.0, "yalniz_cekme": c["yalniz_cekme"]}
            if tc:
                ozet["tbdy_capraz"] = tc
            uy += list(r["uyarilar"])
        else:
            Lb = c["Lb"]
            dos = _dosemeli(B, c) and B.analiz["celik_Lb"] == "otomatik" and c["tur"] in ("kiris", "asik")
            if Lb is None:
                Lb = L
                varsayim.append("L_b = çubuk boyu" + (" (negatif moment); pozitif momentte döşeme/çatı kaplaması üst başlığı tutar → L_b = 0"
                                                      if dos else ""))
            kren = c["tur"] == "kren"
            kuv = _on_ele([_celik_kuvvet(T, bl, i, ad) for i, ad in enumerate(T.adlar)], ["N", "Mx", "My", "V"])

            def kontrol(Lb_, kuv_, anl_):
                return ts.celik_eleman_kontrol(profil, mal["kutuphane"], L=L, Lb=Lb_, K=tuple(K), kuvvetler=kuv_, yontem=yontem,
                                               kren=kren, anl=anl_)
            if dos:
                kp, kn = [], []
                for i, k in enumerate(kuv):
                    Mp = max(float(np.max(b[i, _I_M, :])) * o for b, _, o, _ in bl)
                    Mn = max(float(np.max(-b[i, _I_M, :])) * o for b, _, o, _ in bl)
                    kp.append(dict(k, Mx=max(Mp, 0.0)))
                    kn.append(dict(k, Mx=max(Mn, 0.0)))
                rp, rn = kontrol(0.0, kp, None), kontrol(Lb, kn, None)
                if rn["dc"] >= rp["dc"]:
                    r, kuv_k, Lb_k = rn, kn, Lb
                else:
                    r, kuv_k, Lb_k = rp, kp, 0.0
                if anl is not None:
                    r = kontrol(Lb_k, kuv_k, anl)
            else:
                r = kontrol(Lb, kuv, anl)
                kuv_k, Lb_k = kuv, Lb
            bilgi.update({"kontrol": "eleman", "L": L, "Lb": Lb_k, "K": tuple(K), "kuvvetler": kuv_k, "kren": kren, "yontem": yontem})
            en = max(r["kombinasyonlar"], key=lambda x: x["dc"]) if r["kombinasyonlar"] else None
            kont = []
            for x in r["kontroller"]:
                ad_, komb = x["ad"], None
                if en and ad_.startswith(en["ad"] + ": "):
                    komb, ad_ = en["ad"], ad_[len(en["ad"]) + 2:]
                narin = ad_.startswith("Narinlik")
                kont.append(Y._kontrol_kaydi(x, komb, ad_, Y._celik_etiket(ad_, en["dal"] if en else None), kosul=narin))
            eg, bs, kk = r["egilme"], r["basinc"], r["kesme"]
            sinif = r["sinif"]
            ozet = {"kontrol": "eleman (ÇYTHYE 11.1)", "profil": profil, "sinif": f"eğilme: {sinif.get('egilme', '?')}; basınç: "
                    f"{sinif.get('basinc', '?')}" if isinstance(sinif, dict) else str(sinif),
                    "Mc_kNm": eg["Mc_kNm"], "Mcy_kNm": eg["Mcy_kNm"], "Pc_kN": bs["Pc_kN"], "Vc_kN": kk["Vc_kN"], "L_m": L, "Lb_m": Lb_k,
                    "K": list(K), "yontem": r["yontem"], "N_kN": en["N"] if en else 0.0, "Mx_kNm": en["Mx"] if en else 0.0,
                    "My_kNm": en["My"] if en else 0.0, "V_kN": en["V"] if en else 0.0}
            if ks["tip"] == "vute":
                ozet["vute"] = f"temel {profil}, derin uçta +{_f(ks['ek_yukseklik'] * 1000, 0)} mm; M·h₀/h ile ölçeklendi"
            uy += list(r["uyarilar"])
        T.sonuclar[c["no"]] = {"r": r, "bilgi": bilgi}
        etkin = [x for x in kont if not x["kosul"] or not x["saglandi"]] or kont
        durum = "yeterli" if max(x["dc"] for x in etkin) <= 1.0 + 1e-9 else "kesit büyüt"
    elif mal["tur"] == "beton":
        if kt["tip"] != "dikdortgen":
            raise MatrisHatasi(f"Kesit {c['kesit']!r}: beton malzemeli kesit dikdörtgen olmalı.")
        don = kt.get("donati")
        donati = B.malzemeler[str(don)]["kutuphane"] if (don and str(don) in B.malzemeler and B.malzemeler[str(don)]["tur"] == "donati") \
            else (str(don) if don and str(don) in yv.DONATILAR else "B420C")
        pas = float(kt.get("pas") if kt.get("pas") is not None else 0.03)
        kb = {"sistem": "betonarme", "malzeme_ad": kt["malzeme"]}
        egim = abs(c["dx"][2])
        tur_ba = "kolon" if c["tur"] == "kolon" else ("kiris" if egim < 0.087 else "egik")
        kuv = []
        for i, ad in enumerate(T.adlar):
            dep = T.deprem[i]
            if tur_ba == "kiris":
                Mmax = max(float(np.max(b[i, _I_M, :])) * o for b, _, o, _ in bl)
                Mmin = min(float(np.min(b[i, _I_M, :])) * o for b, _, o, _ in bl)
                V = max(float(np.max(np.abs(b[i, _I_V, :]))) for b, _, _, _ in bl)
                Nv = np.concatenate([-b[i, _I_N, :] for b, _, _, _ in bl])
                N = float(Nv[int(np.argmax(np.abs(Nv)))])
                if Mmax > 1e-9:
                    kuv.append({"ad": ad + " (M+)", "N": N, "Mx": Mmax, "My": 0.0, "V": V, "deprem": dep})
                if Mmin < -1e-9:
                    kuv.append({"ad": ad + " (M−)", "N": N, "Mx": Mmin, "My": 0.0, "V": V, "deprem": dep})
                if Mmax <= 1e-9 and Mmin >= -1e-9:
                    kuv.append({"ad": ad, "N": N, "Mx": 0.0, "My": 0.0, "V": V, "deprem": dep})
            else:
                V = max(float(np.max(np.abs(b[i, _I_V, :]))) for b, _, _, _ in bl)
                for uc, (b, _, o, _), s in (("i", bl[0], 0), ("j", bl[-1], -1)):
                    kuv.append({"ad": f"{ad} ({uc})", "N": -float(b[i, _I_N, s]), "Mx": float(b[i, _I_M, s]) * o,
                                "My": float(b[i, _I_MY, s]), "V": V, "deprem": dep})
        kuv = _on_ele(kuv, ["N", "Mx", "My", "V"], n=3, en_cok=16) if tur_ba != "kiris" else (
            _on_ele([k for k in kuv if k["Mx"] >= 0], ["Mx", "V", "N"], en_cok=8) + _on_ele([k for k in kuv if k["Mx"] < 0], ["Mx", "V", "N"], en_cok=8))
        r = ts.betonarme_eleman_kontrol(kt["b"], kt["h"], pas + Y._PAS_EK, mal["kutuphane"], donati, kuv, tur=tur_ba,
                                        tbdy=bool(B.deprem), anl=anl)
        bilgi.update({"kontrol": "betonarme", "tur": "kolon" if tur_ba == "kolon" else "kiris", "kuvvetler": kuv,
                      "malzeme": {"beton": mal["kutuphane"], "donati": donati}, "b": kt["b"], "h": kt["h"]})
        kont = []
        for x in r["kontroller"]:
            kosul = any(s in x["ad"] for s in ("koşulu", "en az", "En az", "boyut", "Narinlik", "aralık"))
            kont.append(Y._kontrol_kaydi(x, None, x["ad"], x["ad"].split(":")[0], kosul=kosul))
        ozet = {"kontrol": {"kiris": "kiriş (TS 500 eğilme + kesme)", "kolon": "kolon (N–M)", "egik": "eğik eleman (TS 500 Denk. 7.2)"}[tur_ba],
                "As_toplam_cm2": r.get("As_toplam_cm2"), "As_kaynak": r.get("As_kaynak"), "b_mm": r["b_mm"], "h_mm": r["h_mm"],
                "esik_kN": r["esik_kN"]}
        if r.get("egilme_alt"):
            ozet["As_alt_cm2"] = r["egilme_alt"].get("As_gerekli_cm2")
        if r.get("egilme_ust"):
            ozet["As_ust_cm2"] = r["egilme_ust"].get("As_gerekli_cm2")
        uy += list(r["uyarilar"])
        T.sonuclar[c["no"]] = {"r": r, "bilgi": bilgi}
        durum = r["durum"] if r["durum"] in ("yeterli", "donatı artır", "kesit büyüt") else "yeterli"
    else:
        raise MatrisHatasi(f"Kesit {c['kesit']!r}: malzeme {mal['tur']} ile eleman tahkiki yok (çelik ya da beton olmalı).")
    for x in kont:
        if len(x["kaynak"]) > 110:
            x["kaynak"] = x["kaynak"][:107] + "…"
    k = Y._kayit_kur(c["tur"], kayit, kb, fe, kont, durum, ozet)
    k["kontroller"] = k["kontroller"][:6]
    k.update({"cubuk": c["no"], "grup": c.get("grup"), "L": _r(L), "varsayimlar": varsayim, "kaynak": c.get("kaynak")})
    return k, uy, {}


def _tasarim(ts, T):
    B = T.B
    kayitlar, uyarilar = [], {}
    if T.kombs:
        for c in B.cubuklar:
            try:
                k, uy, _ = _cubuk_tasarla(ts, T, c)
            except MatrisHatasi as h:
                k = {"no": c["no"], "cubuk": c["no"], "tur": c["tur"], "kat": c["kat"], "adres": f"Ç{c['no']} ({c['tur']})", "kesit": c["kesit"],
                     "malzeme": None, "sistem": None, "fe_elemanlar": list(c["fe"]), "dc": None, "durum": "hesaplanamadı",
                     "belirleyen": None, "kontroller": [], "ozet": {}, "hata": str(h)}
                uy = [f"tahkik yapılamadı — {h}"]
            kayitlar.append(k)
            for u in uy:
                uyarilar.setdefault(u, []).append(k["adres"])
    gecerli = [k for k in kayitlar if k["dc"] is not None]
    sirali = sorted(gecerli, key=lambda k: -k["dc"])
    dag = {ad: 0 for ad, _ in Y._DC_ARALIKLARI}
    for k in gecerli:
        dag[next(ad for ad, ust in Y._DC_ARALIKLARI if k["dc"] < ust)] += 1
    tekil = [f"{u} ({', '.join(a[:3])}{f' … +{len(a) - 3} eleman' if len(a) > 3 else ''})" for u, a in uyarilar.items()]
    if len(tekil) > 14:
        tekil = tekil[:14] + [f"… ve {len(tekil) - 14} uyarı daha (her elemanın ayrıntısında)."]
    genel = []
    if any(T.deprem):
        genel.append("Deprem birleşimleri (TBDY 2018) tahkike girdi; kapasite tasarımı (çaprazlı çerçevede T = R_y F_y A_g, P1 = 1,14 F_cre A_g "
                     "mekanizma kuvvetleri, güçlü kolon–zayıf kiriş, birleşimler) bu araçta yok: sonuçlar ön boyutlandırmadır.")
    if any(k["tur"] == "capraz" for k in gecerli) and B.deprem:
        genel.append(f"Çapraz koşulları TBDY 2018 {'md. 9.6 (SDY)' if _suneklik(B) == 'SDY' else 'md. 9.7 (SDS)'}: KL/i ≤ 200, Tablo 9.3 "
                     "genişlik/kalınlık; K düzeni yasak; yalnız çekme çaprazı SDY'de yasak, SDS'de KL/i ≤ 300.")
    ks_varsayim = sorted({v for k in gecerli for v in k.get("varsayimlar", [])})
    varsayimlar = [
        "Çelik: ÇYTHYE 2018 " + ("GKT" if B.kombinasyon_kumesi == "cythye_gkt" else "YDKT") + "; kolon, kiriş, aşık, kren ve bağ "
        "kirişi I/H kesitlerde eğilmeli eleman (Bölüm 11 etkileşim), çapraz ve makas çubukları ile basit kesitler (kutu, boru, "
        "korniyer, U) eksenel çubuk (Bölüm 7–8). Kombinasyon başına eleman boyunca en büyük |N|, |M|, |V| (aynı kombinasyon).",
        "Varsayılan burkulma ve yanal burulma boyları (çubukta Lb / K verilmezse): " + ("; ".join(ks_varsayim) or "—") + ". İkinci "
        "mertebe etkileri (B1/B2) yok; yanal ötelemesi önlenmemiş çerçeve kolonunda K > 1 olabilir — çubuğa K verin.",
        "Kren kirişi: yanal kuvvet momenti yalnız üst başlıkça taşınır (öğretici yaklaşım); yorulma ve tekerlek yerel basıncı yok.",
        "Betonarme: TS 500 (eğik eleman: |N_d| ≤ 0,1 f_ck A_c ise kiriş gibi, değilse N–M), TBDY sınırları deprem varsa.",
        f"Tahkik kombinasyonları: dayanım ve deprem birleşimleri ({len(T.kombs)} adet); servis ve öteleme birleşimleri tahkike girmez.",
    ]
    return {
        "yontem": {"betonarme": "TS 500:2000 (+TBDY 2018 Bölüm 7 sınırları)",
                   "celik": f"ÇYTHYE 2018 {'GKT' if B.kombinasyon_kumesi == 'cythye_gkt' else 'YDKT'} (+TBDY 2018 Bölüm 9 çapraz koşulları)"},
        "varsayimlar": varsayimlar, "kombinasyon_sayisi": len(T.adlar), "elemanlar": kayitlar,
        "en_buyuk_dc": sirali[0]["dc"] if sirali else 0.0, "kritik": [k["no"] for k in sirali[:5]],
        "kritik_elemanlar": [{"tur": k["tur"], "no": k["no"], "adres": k["adres"], "dc": k["dc"],
                              "kontrol": (k["belirleyen"] or {}).get("kontrol"), "kombinasyon": (k["belirleyen"] or {}).get("kombinasyon")}
                             for k in sirali[:10]],
        "dc_dagilimi": dag, "uyarilar": genel + tekil,
        "Lb_K_varsayimlari": ks_varsayim,
    }


# ============================================================================
# 13) Kesit önerisi
# ============================================================================
def _oner_cubuk(ts, T, c):
    """Tek çubuk için öneri: çelikte aynı aileden D/C ≤ 1 en hafif profil (tasarim.celik_kesit_oner, aynı iç kuvvetlerle),
    betonarmede tasarim.betonarme_kesit_oner. Dönüş {kesit, profil, oneri, gerekce, dc_once, dc_oneri, degisim}."""
    B = T.B
    if c["no"] not in T.sonuclar:
        _cubuk_tasarla(ts, T, c)
    s = T.sonuclar[c["no"]]
    bilgi, r = s["bilgi"], s["r"]
    ks = B.kesitler[c["kesit"]]
    kt = B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
    out = {"cubuk": c["no"], "tur": c["tur"], "kesit": c["kesit"], "dc_once": _r5(min(r["dc"], 99.0)), "grup": c.get("grup")}
    if bilgi.get("kontrol") in ("eleman", "cubuk"):
        aile = kt.get("aile")
        if not aile:
            out.update({"oneri": None, "gerekce": ["Kesit ailesi belirlenemedi."]})
            return out
        p = {"L": bilgi["L"], "K": tuple(bilgi["K"]), "kontrol": bilgi["kontrol"],
             "yontem": bilgi["yontem"]}
        if bilgi["kontrol"] == "eleman":
            p.update({"Lb": bilgi["Lb"], "kren": bilgi.get("kren", False)})
        else:
            p.update({"yalniz_cekme": bilgi.get("yalniz_cekme", False)})
            if bilgi.get("tbdy_capraz"):
                p["tbdy_capraz"] = bilgi["tbdy_capraz"]
        kuv = bilgi["kuvvetler"]
        if bilgi["kontrol"] == "cubuk":
            kuv = [{"ad": k["ad"], "N": k["N"]} for k in kuv]
        mal = B.malzemeler[kt["malzeme"]]["kutuphane"]
        try:
            o = ts.celik_kesit_oner(aile, mal, parametreler=p, kuvvetler=kuv, baslangic=kt["profil"], aile_degistir=False)
        except (KeyError, MatrisHatasi):
            o = ts.celik_kesit_oner(aile, mal, parametreler=p, kuvvetler=kuv, aile_degistir=False)
        oneri, dc_o, agr, gerekce = o["oneri"], o["dc"], o["agirlik_kg_m"], list(o["gerekce"])
        if oneri is None and bilgi["kontrol"] == "cubuk":
            # ailede yeterli kesit yok (ör. TBDY Tablo 9.3 genişlik/kalınlık sınırı): öteki eksenel kesit aileleri denenir
            o2 = ts.celik_kesit_oner(aile, mal, parametreler=p, kuvvetler=kuv, aile_degistir=True)
            if o2.get("aile_degistir"):
                ad_ = o2["aile_degistir"]
                oneri, agr = ad_["oneri"], ad_["agirlik_kg_m"]
                dc_o = next((a["dc"] for a in o2["alternatifler"] if a["oneri"] == oneri), dc_o)
                gerekce.append("Aile değişti: " + ad_["neden"])
        out.update({"oneri": oneri, "profil": kt["profil"], "dc_oneri": _r5(min(dc_o, 99.0)), "agirlik_kg_m": agr,
                    "gerekce": gerekce, "degisim": o["degisim"], "durum": o["durum"] if oneri == o["oneri"] else "aile değişti",
                    "aile": aile, "sistem": "celik", "malzeme": kt["malzeme"]})
        if oneri is not None and oneri.replace(" ", "").upper() == str(kt["profil"]).replace(" ", "").upper():
            out["degisim"] = "aynı"
            out["gerekce"].append("Mevcut kesit en hafif yeterli kesit (değişiklik yok).")
        return out
    if bilgi.get("kontrol") == "betonarme":
        tur = bilgi["tur"]
        kuv = [{k_: v for k_, v in k.items() if k_ in ("ad", "N", "Mx", "My", "V", "deprem")} for k in bilgi["kuvvetler"]]
        o = ts.betonarme_kesit_oner(tur, kuv, bilgi["malzeme"], mevcut_b=bilgi["b"], mevcut_h=bilgi["h"])
        on = o.get("oneri") or {}
        out.update({"oneri": (f"{_f(on['b'] * 100, 0)}x{_f(on['h'] * 100, 0)}" if on.get("b") else None), "b": on.get("b"), "h": on.get("h"),
                    "gerekce": o.get("gerekce", []), "durum": o.get("durum"), "sistem": "betonarme", "malzeme": kt["malzeme"],
                    "donati": kt.get("donati"), "pas": kt.get("pas")})
        return out
    out.update({"oneri": None, "gerekce": ["Bu çubuk için öneri yok."]})
    return out


def _agirlik(o):
    if o.get("sistem") == "celik":
        return o.get("agirlik_kg_m") or 0.0
    return (o.get("b") or 0.0) * (o.get("h") or 0.0)


def _oneri_uygula(bina, oneriler, B):
    """Önerileri bina JSON'una uygular (kopya). Aynı (kesit, tür) grubundaki çubuklara grubun en ağır önerisi verilir (kesit
    sayısı az kalsın). Vute çubuğunda temel profili değişen yeni bir vute kesiti yazılır. Dönüş (yeni bina, değişiklikler)."""
    b = copy.deepcopy(bina)
    kes = b.setdefault("kesitler", {})
    gruplar = {}
    for o in oneriler:
        if o.get("oneri") is None:
            continue
        gruplar.setdefault((o["kesit"], o["tur"]), []).append(o)
    degisen = []
    cubuk_kesit = {}
    for (kesit, tur), lst in gruplar.items():
        en = max(lst, key=_agirlik)
        eski = kes.get(kesit) or {}
        if en.get("degisim") == "aynı" or (en["sistem"] == "betonarme" and eski.get("b") == en.get("b") and eski.get("h") == en.get("h")):
            continue
        if en["sistem"] == "celik":
            ad = en["oneri"].replace(" ", "")
            if eski.get("tip") == "vute":
                temel = str(eski.get("temel"))
                yeni_temel = ad if ad != (kes.get(temel) or {}).get("profil", "").replace(" ", "") else temel
                if yeni_temel not in kes:
                    kes[yeni_temel] = {"tip": "profil", "profil": en["oneri"], "malzeme": en["malzeme"]}
                ad = f"{kesit}-{yeni_temel}" if yeni_temel != temel else kesit
                if ad not in kes:
                    kes[ad] = dict(eski, temel=yeni_temel)
            elif ad not in kes or (kes[ad].get("profil", "").replace(" ", "") != ad):
                ad = ad if ad not in kes else f"{ad}-{en['malzeme']}"
                kes.setdefault(ad, {"tip": "profil", "profil": en["oneri"], "malzeme": en["malzeme"]})
        else:
            ad = f"B{_f(en['b'] * 100, 0)}x{_f(en['h'] * 100, 0)}"
            kes.setdefault(ad, {"tip": "dikdortgen", "b": en["b"], "h": en["h"], "malzeme": en["malzeme"],
                                **({"donati": en["donati"]} if en.get("donati") else {}), **({"pas": en["pas"]} if en.get("pas") else {})})
        if ad == kesit:
            continue
        for o in lst:
            cubuk_kesit[o["cubuk"]] = ad
        degisen.append({"kesit": kesit, "tur": tur, "yeni": ad, "oneri": en["oneri"], "cubuklar": sorted(o["cubuk"] for o in lst)})
    # çubuklara (ya da aks–kat elemanlarına) yaz
    for c in b.get("cubuklar") or []:
        if c.get("no") in cubuk_kesit:
            c["kesit"] = cubuk_kesit[c["no"]]
    for c in B.cubuklar:
        if c["no"] not in cubuk_kesit:
            continue
        kay = c.get("kaynak") or {}
        if isinstance(kay, dict) and kay.get("aks_kat") in ("kolon", "kiris"):
            liste = b.get("kolonlar" if kay["aks_kat"] == "kolon" else "kirisler") or []
            for e in liste:
                if int(e.get("no", -1)) == kay["no"]:
                    e["kesit"] = cubuk_kesit[c["no"]]
    return b, degisen


# ============================================================================
# 14) Çıktı verisi (yapi şemasıyla geriye uyumlu + genel model alanları)
# ============================================================================
def _veri(B, YK, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol, *, deprem, ruzgar, kutle, ozetler,
          gosterilecek, kimlik, kren, yalniz):
    S = Y._sonlu
    D = B.coz.dugum
    bina = {
        "baslik": B.baslik, "sistem": B.sistem, "model": "genel",
        "akslar": {k: [dict(a) for a in v] for k, v in B.akslar.items()},
        "aks_sistemleri": [{"ad": s["ad"], "tur": s["tur"], "orijin": list(s["orijin"]), "aci": s["aci"]} for ad, s in B.sistemler.items()
                           if ad != "GLOBAL"],
        "katlar": [{"no": k["no"], "ad": k["ad"], "kot": k["kot"], "h": k["h"], "z": k.get("z")} for k in B.katlar],
        "seviyeler": [{"kat": k["no"], "kot": k["kot"], "ad": k["ad"], "diyafram": (ag["diyafram_mod"].get(k["no"]) or {}).get("mod"),
                       "neden": (ag["diyafram_mod"].get(k["no"]) or {}).get("neden")} for k in B.katlar],
        "kolonlar": [], "kirisler": [], "dosemeler": [],
        "duvarlar": {ad: {"kutuphane": d["kutuphane"], "deger": d["deger"], "aciklama": d["aciklama"], "dogrulandi": d["dogrulandi"]}
                     for ad, d in B.duvarlar.items()},
        "temeller": {"tip": B.temeller["tip"], "mesnet": B.temeller["mesnet"], "zemin": dict(B.temeller["zemin"]),
                     "varsayilan": dict(B.temeller["varsayilan"]),
                     "liste": [{"dugum": t["dugum"], "kolon_no": t["kolon_no"], "aks": t["aks"], "B": t.get("B"), "L": t.get("L")}
                               for t in akis["temeller"]]},
        "deprem": copy.deepcopy(B.deprem), "kar": copy.deepcopy(B.kar), "ruzgar": copy.deepcopy(B.ruzgar),
        "kombinasyon_kumesi": B.kombinasyon_kumesi, "analiz": {k: v for k, v in B.analiz.items()},
    }
    kutuphane_ozeti = {
        "malzemeler": {ad: {"E_kNm2": m["E"], "G_kNm2": m["G"], "gamma": m["gamma"], "tur": m["tur"], "kutuphane": m["kutuphane"],
                            **({"fck": m["fck"]} if m["tur"] == "beton" else {}), **({"Fy": m["Fy"]} if m["tur"] == "celik" else {})}
                       for ad, m in B.malzemeler.items()},
        "kesitler": {ad: {"tip": k["tip"], "b": k.get("b"), "h": k.get("h"), "profil": k.get("profil"), "A": _r(k["A"]), "Iy": _r(k["I_guclu"]),
                          "Iz": _r(k["I_zayif"]), "J": _r(k["J"]), "Wpl": _r(k.get("Wpl") or 0.0), "malzeme": k["malzeme"],
                          **({"temel": k["temel"], "ek_yukseklik": k["ek_yukseklik"], "boy": k["boy"]} if k["tip"] == "vute" else {})}
                     for ad, k in B.kesitler.items()},
    }
    ag_veri = {
        "dugumler": [{"no": d["no"], "X": _r(d["X"]), "Y": _r(d["Y"]), "Z": _r(d["Z"]), "adres": d["adres"], "kat": d["kat"], "aks": d["aks"],
                      "efendi": d["efendi"], "tur": d["tur"], "ic": d["ic"], "seviye_tam": d["seviye_tam"],
                      **({"ad": d["ad"]} if d.get("ad") else {}),
                      **({"sistem": D[d["no"]].get("sistem"), "z_aksi": D[d["no"]].get("z")} if d["no"] in D and D[d["no"]].get("tur") == "aks" else {})}
                     for d in ag["dugumler"]],
        "elemanlar": [{"no": e["no"], "dugumler": e["dugumler"], "tur": e["tur"], "kaynak_no": e["kaynak_no"], "cubuk": e["cubuk"],
                       "parca": e["parca"], "kat": e["kat"], "L": _r(e["L"]), "kesit": e["kesit"], "lam": [[_r6(x) for x in s] for s in e["lam"]],
                       "adres": e["adres"], "rijitlik_carpani": e["rijitlik_carpani"]} for e in ag["elemanlar"]],
        "cubuklar": [{"no": c["no"], "i": c["i"], "j": c["j"], "tur": c["tur"], "kesit": c["kesit"], "L": _r(c["L"]), "aci": c["aci"],
                      "serbest": c["serbest"], "yalniz_cekme": c["yalniz_cekme"], "kat": c["kat"], "grup": c.get("grup"), "fe": c["fe"],
                      "Lb": c["Lb"], "K": c["K"], "kaynak": c.get("kaynak"),
                      **({"duvar": c["duvar"], "h_duvar": _r(c["h_duvar"])} if c["duvar"] else {})} for c in B.cubuklar],
        "paneller": [{"no": p["no"], "kose": p["kose"], "tur": p["tur"], "kalinlik": p["kalinlik"], "alan": _r(p["alan"]),
                      "alan_yatay": _r(p["alan"] * p["cos_a"]), "egim": _r(p["egim"]), "normal": [_r6(v) for v in p["normal"]],
                      "kat": p["kat"], "dagitim": p["dagitim"], "g": _r(p["g_yuzey"]), "q": _r(p["q"] + p["ek_q"]), "s": _r(p["s"]),
                      "mu": _r(p["mu"]), "kullanim": p["kullanim"], "kaynak": p.get("kaynak"),
                      "kenarlar": [{"kenar": k["kenar"], "dugumler": k["dugumler"], "uzunluk": _r(k["L"]), "tasiyan": k["tasiyan"],
                                    "tam": k["tam"], "cubuklar": [x[0] for x in k["parcalar"]]} for k in p["kenarlar"]]}
                     for p in B.paneller],
        "mesnetler": [{"dugum": m["dugum"], "tip": m["tip"], "kaynak": m["kaynak"], **{a: m[a] for a in ("ux", "uy", "uz", "rx", "ry", "rz")}}
                      for m in ag["mesnetler"]],
        "diyaframlar": [{"ad": d["ad"], "ana": d["ana"]["no"], "dugumler": list(d["dugumler"]), "X": _r(d["ana"]["x"]),
                         "Y": _r(-d["ana"]["z"]), "Z": _r(d["ana"]["y"])} for d in ag["diyaframlar"]],
        "diyafram": "rijit" if ag["efendi"] else "esnek", "diyafram_seviye": {str(k): v for k, v in ag["diyafram_mod"].items()},
        "donme_tutulan": ag["donme_tutulan"], "rijitlik_carpani": dict(ag["rijitlik_carpani"]),
        "sd_sayisi": ag["sd_sayisi"], "mod": "sayisal", "cozum_yolu": yol,
    }
    cubuk_yuk = []
    for c in B.cubuklar:
        oz = YK.cubuk_ozet.get(c["no"]) or {}
        cubuk_yuk.append({"no": c["no"], "L": _r(c["L"]), **{d: {a: _r(v) for a, v in oz.get(d, {}).items()} for d in YK.durumlar}})
    yukler = {
        "dosemeler": [], "kirisler": [], "kolonlar": [],
        "paneller": [{"no": p["no"], "tur": p["tur"], "alan": _r(p["alan"]), "egim": _r(p["egim"]), "dagitim": p["dagitim"],
                      "g": _r(p["g_yuzey"]), "q": _r(p["q"] + p["ek_q"]), "s": _r(p["s"]), "mu": _r(p["mu"]),
                      "G_toplam": _r(p["toplam"]["G"]), "Q_toplam": _r(p["toplam"]["Q"]), "S_toplam": _r(p["toplam"]["S"]),
                      "q_kaynak": p["q_kaynak"], "g_kaynak": p["g_kaynak"],
                      "kenarlar": [{a: (_r(v) if isinstance(v, float) else v) for a, v in k.items()} for k in p["dag"]["kenarlar"]]}
                     for p in B.paneller],
        "cubuklar": cubuk_yuk,
        "katlar": [{"kat": k["kat"], "kot": k["kot"], "h": k["h"], "G": _r(k["G"]), "Q": _r(k["Q"]), "S": _r(k["S"]), "w": _r(k["w"])}
                   for k in YK.katlar],
        "toplam": {d: _r(v) for d, v in YK.toplam.items()},
    }
    akis_veri = {
        "kolonlar": [{a: (_r(v) if isinstance(v, float) else v) for a, v in k.items()} for k in akis["kolonlar"]],
        "temeller": [{a: (_r(v) if isinstance(v, float) else v) for a, v in t.items()} for t in akis["temeller"]],
        "korunum": {d: {a: _r(v) for a, v in p.items()} for d, p in akis["korunum"].items()},
        "sankey": [dict(s, kN=_r6(s["kN"])) for s in akis["sankey"]],
    }
    uyarilar = list(dict.fromkeys(B.uyarilar))
    for p in B.paneller:
        if not p["q_dogrulandi"]:
            uyarilar.append(f"Doğrulanmamış kütüphane değeri kullanıldı: TS498_HAREKETLI.{p['kullanim']} (panel P{p['no']})")
        if not p["g_dogrulandi"]:
            uyarilar.append(f"Doğrulanmamış kütüphane değeri kullanıldı: KAPLAMALAR (panel P{p['no']}): {p['g_kaynak']}")
    uyarilar = list(dict.fromkeys(uyarilar))
    en_dc = max((t.get("DC", 0.0) for t in akis["temeller"]), default=0.0)
    if deprem:
        for u in deprem["uyarilar"]:
            if u not in uyarilar:
                uyarilar.append(u)
    if B.kar and not B.kar["dogrulandi"]:
        uyarilar.append("Kar bölgesi Ek 1 il/ilçe listesinden (doğrulanmamış) alındı.")
    if kren:
        uyarilar.append("Kren yükleri öğretici varsayımla (Türk yönetmeliklerinde kren kuralı yok): üretici verisi ve TS EN 1991-3 ile "
                        "doğrulayın.")
    fe_model = S(dict(model, yukler=durumlar["G"]["yukler"], yayili=durumlar["G"]["yayili"]))
    uygulanan = [k for k in kombinasyonlar if k["uygulandi"] and k["tur"] != "drift"]
    kar_veri = None
    if B.kar:
        cati = [p for p in B.paneller if p["kar"]]
        kar_veri = S({"bolge": B.kar["bolge"], "rakim": B.kar["rakim"], "Sk": B.kar["Sk"], "mu": B.kar["mu"], "s": B.kar["s"], "Ce": B.kar["Ce"],
                      "Ct": B.kar["Ct"], "alpha": B.kar["alpha"], "cati_alani": sum(p["alan"] * p["cos_a"] for p in cati),
                      "S_toplam": YK.toplam["S"], "kat": B.nk, "Sk_kaynak": B.kar["Sk_kaynak"],
                      "mu_kaynak": "TS EN 1991-1-3 Tablo 5.2 μ1(α): her kar panelinin kendi eğiminden (0–30°: 0,8; 30–60°: 0,8(60 − α)/30)",
                      "paneller": [{"no": p["no"], "egim": p["egim"], "mu": p["mu"], "s": p["s"]} for p in cati],
                      "kaynak": B.kar["kaynak"], "dogrulandi": B.kar["dogrulandi"]})
    kmb_ozet = {ad: {"enb": {a: _r5(v) for a, v in o["enb"].items()}, "u_enb": {a: _r5(v) for a, v in o["u_enb"].items()},
                     "FZ_tepki": _r6(o["FZ_tepki"]), "denge_enb": float(f"{o['denge_enb']:.2g}")} for ad, o in (ozetler or {}).items()}
    tam = {"G", "Q"} | set(gosterilecek)
    cikti_durum = {ad: k for ad, k in durumlar_kisa.items() if not (ad.startswith("K") and "." in ad)}
    veri = {
        "tur": "bina", "surum": 3, "model": "genel", "baslik": B.baslik, "sistem": B.sistem, "birim": dict(B.birim), "cozum_kimligi": kimlik,
        "bina": bina, "kutuphane_ozeti": kutuphane_ozeti, "ag": ag_veri, "yukler": yukler,
        "durumlar": {ad: Y._kisa_veri(k, diyagram=ad in tam) for ad, k in cikti_durum.items()},
        "kombinasyonlar": [dict(r, **({"kren": k["kren"]} if k.get("kren") else {}))
                           for r, k in zip(Y._kombinasyon_veri(kombinasyonlar), kombinasyonlar)],
        "kombinasyon_ozet": kmb_ozet, "gosterilecek": list(gosterilecek),
        "sonuclar": {ad: Y._kisa_veri(k, u_dahil=False) for ad, k in sonuclar.items()},
        "zarf": {"kombinasyonlar": zarf["kombinasyonlar"], "kombinasyon_sayisi": len(zarf["kombinasyonlar"]),
                 "elemanlar": [{a: (_r6(v) if isinstance(v, float) else v) for a, v in z.items()} for z in zarf["elemanlar"]]},
        "akis": akis_veri,
        "deprem": S(deprem) if deprem else None,
        "ruzgar": S(ruzgar) if ruzgar else None,
        "kar": kar_veri,
        "kren": S(kren) if kren else None,
        "yalniz_cekme": yalniz or {"var": False},
        "kutle_merkezi": [{"kat": k["kat"], "X": _r(k["X"]), "Y": _r(k["Y"]), "w": _r(k["w"]), "m": _r(k["m"]), "BX": _r(k["BX"]), "BY": _r(k["BY"])}
                          for k in (kutle or [])],
        "rijitlik_merkezi": [],
        "ozet": {"sd_sayisi": ag["sd_sayisi"], "dugum": len(ag["dugumler"]), "eleman": len(ag["elemanlar"]), "cubuk": len(B.cubuklar),
                 "panel": len(B.paneller), "durum_sayisi": len(cikti_durum), "kombinasyon_sayisi": len(uygulanan),
                 "gosterilen_sayisi": len(sonuclar),
                 "drift_kombinasyon_sayisi": sum(1 for k in kombinasyonlar if k["uygulandi"] and k["tur"] == "drift"),
                 "toplam_G": _r(YK.toplam["G"]), "toplam_Q": _r(YK.toplam["Q"]), "toplam_S": _r(YK.toplam["S"]),
                 "en_buyuk_temel_DC": _r(en_dc), "uyarilar": uyarilar,
                 "deprem_etkin": bool(deprem), "ruzgar_etkin": bool(ruzgar), "kar_etkin": bool(B.kar), "kren_etkin": bool(kren),
                 "yalniz_cekme": bool(yalniz), "diyafram": "rijit" if ag["efendi"] else "esnek",
                 "catlamis_rijitlik": B.analiz["catlamis_rijitlik"]},
        "uyarilar": uyarilar,
        "fe_model": fe_model,
    }
    return veri


# ============================================================================
# 15) Anlatım
# ============================================================================
def _tablo(b, s):
    return Y._tablo(b, s)


def _anlatim(B, YK, ag, durumlar_kisa, kombinasyonlar, zarf, akis, deprem, ruzgar, kren, yalniz, tas, T, yol, anl):
    anl.baslik(B.baslik, 2)
    if B.aciklama:
        anl.metin(B.aciklama)
    se._basla(anl, 1, "Aks sistemi, düğümler, çubuklar ve paneller",
              "Model bir aks ızgarası üzerine kurulur: her düğüm bir X × Y × Z aks kesişimi ya da bir çubuğun bölme/kesişim noktasıdır. "
              "Akslar taşınınca düğümler (bölme düğümleri dahil) birlikte taşınır; böylece geometri tek bir yerden (aks tablosu) yönetilir.")
    anl.metin("**Akslar:**\n\n" + _tablo(["Yön", "Akslar (ad = konum, m)"],
                                          [[y.upper(), ", ".join(f"{a['ad']} = {_f(a['konum'])}" + (f" (kat {a['kat']})" if "kat" in a else "")
                                                                 for a in B.akslar[y]) or "—"] for y in ("x", "y", "z")]))
    say = {}
    for d in B.coz.dugum.values():
        say[d.get("tur", "aks")] = say.get(d.get("tur", "aks"), 0) + 1
    anl.metin(f"**Düğümler:** {len(B.coz.dugum)} ({', '.join(f'{v} {k}' for k, v in say.items())}); **çubuklar:** {len(B.cubuklar)}; "
              f"**paneller:** {len(B.paneller)}; **mesnetler:** {len(B.mesnetler)}.")
    turler = {}
    for c in B.cubuklar:
        turler.setdefault(c["tur"], []).append(c)
    anl.metin("**Çubuk türleri:**\n\n" + _tablo(["Tür", "Adet", "Kesitler", "Uç serbestliği"],
                                                [[t, len(lst), ", ".join(sorted({c['kesit'] for c in lst})),
                                                  f"{sum(1 for c in lst if c['serbest']['i'] or c['serbest']['j'])} mafsallı"
                                                  + (f", {sum(1 for c in lst if c['yalniz_cekme'])} yalnız çekme" if any(c['yalniz_cekme'] for c in lst) else "")]
                                                 for t, lst in sorted(turler.items())]))
    if ag["donme_tutulan"]:
        anl.metin(f"Bütün çubuk uçları mafsallı {len(ag['donme_tutulan'])} düğümde dönme serbestlikleri tutuldu: o düğümün dönmesini "
                  "hiçbir çubuk tutmaz (rijitlik matrisinde sıfır satır); dönmeyi sıfırlamak iç kuvvetleri değiştirmez.")
    se._basla(anl, 2, "Paneller → çubuklar: yük dağıtımı",
              "Döşeme, çatı ve cephe panelleri yüklerini kenarlarındaki çubuklara aktarır. İki doğrultulu panelde her nokta en yakın "
              "kenara gider (açıortay bölgeleri); dikdörtgende bu TS 500 md. 11.4.3'ün 45° kuralıdır: kısa kenara üçgen, uzun kenara "
              "trapez yük. Tek doğrultulu panel yükünü iki karşı kenara yarı yarıya verir. Eğik panelde öz ve sabit yük yüzey alanına, "
              "hareketli yük ve kar yatay izdüşüme göre hesaplanır.")
    anl.mat(r"q(u) = p\cdot d(u),\quad d(u) = \min_f \frac{d_f(A + u\,\mathbf{t})}{1 - \mathbf{n}_f\cdot\mathbf{n}},\qquad "
            r"\textstyle\sum_{\text{kenar}} \int_0^{L} d(u)\,du = A_{panel}")
    sat = []
    for p in B.paneller[:12]:
        sat.append([f"P{p['no']}", p["tur"], p["dagitim"], _f(p["alan"], 2), _f(p["egim"], 1), _f(p["g_yuzey"], 2), _f(p["q"] + p["ek_q"], 2),
                    _f(p["s"], 2), _f(p["toplam"]["G"], 1)])
    if sat:
        anl.metin("**Paneller** (ilk 12; g yüzey alanına, q ve s yatay izdüşüme, kN/m²):\n\n" + _tablo(
            ["Panel", "Tür", "Dağıtım", "Alan (m²)", "Eğim (°)", "g", "q", "s", "G (kN)"], sat))
    anl.metin("**Yük toplamları:** " + ", ".join(f"{d} = {_f(v, 1)} kN" for d, v in YK.toplam.items() if d in YK.durumlar) + ".")
    se._basla(anl, 3, "Ağ, mesnetler ve diyaframlar",
              "Çubuklar uzay çerçeve elemanlarıdır (her düğümde 6 serbestlik). Uç serbestlikleri (mafsal) eleman rijitliğinde statik "
              "yoğunlaştırmayla uygulanır. Kat 0 Z aksındaki aks kesişimleri temele oturur.")
    anl.metin(f"{ag['n_kole']} düğüm × 6 = **{ag['sd_sayisi']} SD**, {len(ag['elemanlar'])} sonlu eleman; diyafram: "
              + ", ".join(f"kat {k}: {v['mod']} ({v['neden']})" for k, v in ag["diyafram_mod"].items()) + ".")
    se._basla(anl, 4, "Yük durumları",
              "Her yük türü ayrı bir durumdur; rijitlik matrisi bir kez kurulur, bütün durumlar aynı anda çözülür.")
    anl.metin("Durumlar: " + ", ".join(f"`{d}`" for d in durumlar_kisa) + f". Çözüm yolu: {yol}.")
    if ruzgar and ruzgar.get("yontem") == "panel":
        anl.metin("**Rüzgâr (TS 498:2021 md. 14):** " + ruzgar["kaynak"] + ". " + ruzgar["not"])
    if kren:
        anl.metin(f"**Kren (K):** {len(kren['durumlar'])} alt durum (konum × köprü yönü). " + kren["kaynak"])
    Y._adim_7(B, deprem, anl)
    if yalniz:
        se._basla(anl, 8, "Yalnız çekme çubukları: doğrusal olmayan çözüm", yalniz["aciklama"])
        sat = [[ad, len(v["etkin_degil"]), v["yineleme"]] for ad, v in list(yalniz["kombinasyonlar"].items())[:12]]
        anl.metin(_tablo(["Birleşim", "Devre dışı çubuk", "Yineleme"], sat))
    se._basla(anl, 9, "Kombinasyonlar ve zarf",
              "Doğrusal çözümde kombinasyon, yük durumlarının katsayılı toplamıdır (yeniden çözüm gerekmez); zarf her kesitte bütün "
              "kombinasyonların en büyük ve en küçük değeridir.")
    uyg = [k for k in kombinasyonlar if k["uygulandi"]]
    anl.metin(f"Kombinasyon kümesi `{B.kombinasyon_kumesi}`: {len(uyg)} uygulanan birleşim"
              + (f" ({sum(1 for k in uyg if k.get('kren'))} kren varyantı)" if kren else "") + ".")
    se._basla(anl, 10, "Denge ve korunum", "Σ uygulanan düşey yük = Σ mesnet tepkisi (yay kuvvetleri dahil), her durumda.")
    anl.metin(_tablo(["Durum", "Σ yük (kN)", "Σ tepki (kN)", "Paneller", "Çubuk öz", "Duvar", "Ek"],
                     [[d, _f(p["toplam"], 2), _f(p["kolon_taban"], 2), _f(p["paneller"], 1), _f(p["cubuk_oz"], 1), _f(p["duvarlar"], 1),
                       _f(p["ek"], 1)] for d, p in akis["korunum"].items()]))
    if tas is not None:
        se._basla(anl, 12, "Kesit tahkikleri", "Her çubuk kendi türüne göre tahkik edilir: çelikte ÇYTHYE (eğilmeli eleman ya da "
                  "eksenel çubuk), betonarmede TS 500; çaprazlarda TBDY 2018 Bölüm 9 koşulları.")
        anl.metin("**Varsayımlar:**\n\n" + "\n".join(f"- {v}" for v in tas["varsayimlar"]))
        gec = sorted((k for k in tas["elemanlar"] if k["dc"] is not None), key=lambda k: -k["dc"])
        anl.metin("**En kritik 10 çubuk:**\n\n" + _tablo(
            ["Çubuk", "Kesit", "Kontrol", "Kombinasyon", "D/C", "Durum"],
            [[k["adres"], k["kesit"], k["belirleyen"]["kontrol"], f"`{k['belirleyen']['kombinasyon']}`" if k["belirleyen"]["kombinasyon"] else "–",
              _f(k["dc"], 3), k["durum"]] for k in gec[:10]]))
        for u in tas["uyarilar"][:6]:
            anl.uyari(u)


# ============================================================================
# 16) Ana işlev
# ============================================================================
def bina_coz(bina, *, goster=None, anlat=True):
    """Genel (surum 3) bina modelini çözer. Dönüş ``mo.Sonuc``: ``.veri`` (yapi.bina_coz şemasıyla uyumlu + genel model alanları:
    ag.cubuklar, ag.paneller, yukler.paneller/cubuklar, kren, yalniz_cekme, bina.seviyeler, uyarilar), ``.ic`` (tembel kombinasyon,
    eleman tahkiki ve kesit önerisi için paket)."""
    B = _oku(bina)
    _parcalar(B)
    YK = _yukleri_hazirla(B)
    kutle = dep = None
    if B.deprem:
        kutle = _kutleler(B, YK, n=B.deprem["n"], kar_payi=yv.TBDY_KUTLE_KATILIM_KULLANIM["kar"] if B.kar else 0.0)
        if not kutle:
            raise MatrisHatasi("Deprem açık ama kat seviyelerinde kütle yok (kat 1 ve üstü Z akslarına düğüm bağlı değil).")
        dep = Y._deprem_on(B, None, kutle)
    ag, model = _ag_kur(B, kutle)
    _mekanizma_duzelt(B, ag, model)
    B.ag = ag
    durumlar = {}
    for d in YK.durumlar:
        cub = {cno: kay[d] for cno, kay in YK.cubuk.items() if kay.get(d)}
        dug = {n: dd[d] for n, dd in YK.dugum.items() if d in dd}
        durumlar[d] = _motor_durum(B, cub, dug)
    ruzgar = None
    if B.ruzgar:
        if any(p["ruzgar"] for p in B.paneller):
            wd, ruzgar = _ruzgar_panel(B, YK)
            for ad, dd in wd.items():
                durumlar[ad] = _motor_durum(B, dd["cubuk"], dd["dugum"])
        else:
            wd, ruzgar = Y._ruzgar_durumlari(B, ag)
            ruzgar["yontem"] = "kat"
            durumlar.update(wd)
    kren_ozet, kren_adlar = None, []
    if B.kren:
        kd, kren_ozet = _kren_durumlari(B)
        for ad, dd in kd.items():
            durumlar[ad] = _motor_durum(B, dd["cubuk"], dd["dugum"])
        kren_adlar = list(kd)
    if dep is not None:
        ed, _ = Y._deprem_birim_durumlari(B, ag, dep)
        durumlar.update(ed)
    yc_var = any(c["yalniz_cekme"] for c in B.cubuklar)
    with warnings.catch_warnings(), _MekanizmaAtla(ag.get("pozitif_tanimli", False)):
        warnings.simplefilter("ignore")
        if ag.get("model_c") is None:
            kisa_m, yol = Y._durumlari_coz(B, model, durumlar, ag)
        else:
            brut = {ad: d for ad, d in durumlar.items() if not Y._birim_mi(ad)}
            catl = {ad: d for ad, d in durumlar.items() if Y._birim_mi(ad)}
            catl.update({ad + Y._CATLAMIS_EK: durumlar[ad] for ad in ("G", "Q", "S") if ad in durumlar})
            catl.update({"~x" + ad: d for ad, d in brut.items() if ad not in ("G", "Q", "S") and d["yayili"]})   # ortak istasyonlar
            kisa_m, yol = Y._durumlari_coz(B, model, brut, ag)
            kisa_c, _ = Y._durumlari_coz(B, ag["model_c"], catl, ag)
            kisa_m.update({ad: k for ad, k in kisa_c.items() if not ad.startswith("~x")})
            yol += " ×2 (brüt K: G, Q, S, W, K; çatlamış K: deprem durumları ve G~c, Q~c, S~c)"
    durumlar_kisa = {ad: Y._kisa_bina(k, ag) for ad, k in kisa_m.items()}
    paket = Y._Paket(durumlar_kisa)
    deprem = Y._deprem_son(B, ag, dep, paket, durumlar) if dep else None
    for ad in list(paket.durum):
        if Y._birim_mi(ad):
            durumlar.pop(ad, None)
            durumlar_kisa.pop(ad, None)
            paket.durum.pop(ad, None)
        elif ad.endswith(Y._CATLAMIS_EK):
            durumlar_kisa.pop(ad, None)
    for ad in ("EX+", "EX-", "EY+", "EY-", "EZ"):
        if ad in paket.durum:
            durumlar_kisa[ad] = paket.kisa(paket.durum[ad])
    kombinasyonlar = _kren_kombinasyonlari(Y._kombinasyon_listesi(B, set(paket.durum) - set(kren_adlar)), kren_adlar)
    for k in kombinasyonlar:
        k["cozum"] = Y._cozum_katsayilari(k, paket)
    yalniz = None
    if yc_var:
        with _MekanizmaAtla(ag.get("pozitif_tanimli", False)):
            yalniz = _yalniz_cekme_coz(B, ag, model, durumlar, paket, kombinasyonlar, deprem)
        yol += "; yalnız çekme: birleşimler doğrudan, yinelemeli"
    zarf = Y._zarf_paket(paket, kombinasyonlar)
    ozetler = {k["ad"]: paket.ozet(paket.birlesim(k["cozum"])) for k in kombinasyonlar if k["uygulandi"]}
    gosterilecek = Y._gosterilecek_sec(B, kombinasyonlar, zarf)
    komb_kat = {k["ad"]: k["cozum"] for k in kombinasyonlar if k["uygulandi"]}
    sonuclar = {ad: paket.kisa(paket.birlesim(komb_kat[ad])) for ad in gosterilecek}
    akis = _akis(B, YK, ag, durumlar_kisa)
    kren = _kren_veri(B, paket, kren_ozet, ag) if kren_ozet else None
    kimlik = Y._cozum_kimligi(B)
    veri = _veri(B, YK, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol, deprem=deprem, ruzgar=ruzgar,
                 kutle=kutle, ozetler=ozetler, gosterilecek=gosterilecek, kimlik=kimlik, kren=kren, yalniz=yalniz)
    ts = _tasarim_mod()
    T = tas = None
    if ts is not None:
        T = _tasarim_baglam(B, ag, paket, kombinasyonlar)
        tas = _tasarim(ts, T)
        veri["tasarim"] = tas
        veri["ozet"]["en_buyuk_dc"] = tas["en_buyuk_dc"]
    if B.analiz["gosterilecek"] is None and veri["sonuclar"] and len(json.dumps(veri, ensure_ascii=False)) > Y.YANIT_BUTCESI:
        veri["sonuclar"], veri["gosterilecek"] = {}, []
        veri["ozet"]["gosterilen_sayisi"] = 0
        veri["ozet"]["sonuclar_tembel"] = True
    _boyut_sinirla(veri, durumlar_kisa)
    anl = mo.Anlatim()
    if anlat:
        _anlatim(B, YK, ag, durumlar_kisa, kombinasyonlar, zarf, akis, deprem, ruzgar, kren, yalniz, tas, T, yol, anl)
    else:
        anl.baslik(B.baslik, 2)
    sonuc = mo.Sonuc(sp.Matrix(kisa_m["G"]["u"]), anl, "u_G", "", "")
    sonuc.veri = veri
    sonuc.ic = {"kimlik": kimlik, "paket": paket, "kombinasyonlar": komb_kat, "durumlar": set(paket.durum), "tasarim": T,
                "serbest": True, "bina": B.ham, "B": B, "tas": tas}
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc


YANIT_SINIRI = 1_600_000     # karakter: büyük modelde (yüzlerce çubuk) yanıt bu sınırı aşarsa ayrıntılar tembel bırakılır


def _boyut_sinirla(veri, durumlar_kisa, sinir=YANIT_SINIRI):
    """Büyük modelde yanıt boyutu: önce tasarım kontrol satırları 3'e iner, yetmezse G ve Q durumları da ince kayıt olur (tam
    diyagramlar bina_kombinasyon ile tembel alınır)."""
    boy = lambda: len(json.dumps(veri, ensure_ascii=False))  # noqa: E731
    if boy() <= sinir:
        return
    if veri.get("tasarim"):
        for k in veri["tasarim"]["elemanlar"]:
            k["kontroller"] = k["kontroller"][:3]
        veri["ozet"]["tasarim_kisaltildi"] = True
    if boy() <= sinir:
        return
    for ad in ("G", "Q"):
        if ad in durumlar_kisa:
            veri["durumlar"][ad] = Y._kisa_veri(durumlar_kisa[ad], diyagram=False)
    veri["ozet"]["durumlar_tembel"] = True
    if boy() <= sinir:
        return
    for k in veri["durumlar"].values():          # çok büyük model: ince kayıtlarda yalnız enb (uç kuvvetleri tembel)
        k["elemanlar"] = [{"no": e["no"], "enb": e["enb"]} for e in k["elemanlar"]]
    veri["ozet"]["uc_kuvvetleri_tembel"] = True


def eleman_tasarim(ic, tur, no, goster=None):
    """Köprü ``bina_eleman_tasarim`` (genel model): çubuk no'suyla (aks–kat modelinden gelen bina için ``tur`` "kolon"/"kiris" ve
    aks–kat no'su da kabul edilir) anlatımlı tahkik."""
    T = ic.get("tasarim")
    ts = _tasarim_mod()
    if T is None or ts is None:
        raise MatrisHatasi("Kesit tahkik modülü (tasarim.py) yüklenemedi.")
    if not T.kombs:
        raise MatrisHatasi("Uygulanan dayanım kombinasyonu yok; kesit tahkiki yapılamaz.")
    B = T.B
    c = _cubuk_bul(B, tur, no)
    anl = mo.Anlatim()
    anl.baslik(f"Çubuk {c['no']} ({c['tur']}, {c['kesit']}): kesit tahkiki", 2)
    anl.metin(f"Tahkik kombinasyonları ({len(T.adlar)}): " + ", ".join(f"`{a}`" for a in T.adlar[:12]) + (" …" if len(T.adlar) > 12 else ""))
    k, uy, ek = _cubuk_tasarla(ts, T, c, anl)
    anl.sonuc(rf"\text{{D/C}}_{{max}} = {_f(k['dc'], 3)}", f"Durum: **{k['durum']}** — belirleyen: {k['belirleyen']['kontrol']}")
    mo.son_anlatim = anl
    anl.goster(goster)
    s = mo.Sonuc(k["dc"], anl, f"cubuk {c['no']}")
    s.veri = dict(k, uyarilar=uy)
    return s


def _cubuk_bul(B, tur, no):
    no = Y._tam(no, "eleman no")
    tur = str(tur or "cubuk").strip().lower()
    if tur in ("kolon", "kiris"):
        for c in B.cubuklar:
            kay = c.get("kaynak") or {}
            if isinstance(kay, dict) and kay.get("aks_kat") == tur and int(kay.get("no", -1)) == no:
                return c
    if no in B.cubuk_no:
        return B.cubuk_no[no]
    raise MatrisHatasi(f"Çubuk {no} bu modelde yok.")


def kesit_oner(bina=None, *, ic=None, hedef="hepsi", yinele=0):
    """Kesit önerisi (köprü ``bina_kesit_oner``): her hedef çubuk için öneri, gerekçe ve D/C önce/sonra. ``yinele`` > 0 ise öneriler
    binaya uygulanıp yeniden çözülür (rijitlik değişince iç kuvvetler değişir; en çok 3 tur) ve önerilen bina JSON'u döner.
    hedef: "hepsi" | [{"tur": "cubuk"|"kolon"|"kiris"|..., "no": n}]."""
    ts = _tasarim_mod()
    if ts is None:
        raise MatrisHatasi("Kesit önerisi için tasarim.py gerekir.")
    try:
        yinele = max(0, min(3, int(yinele or 0)))
    except (TypeError, ValueError):
        raise MatrisHatasi("yinele 0…3 arasında bir tam sayı olmalı.") from None
    if ic is None or not ic.get("serbest"):
        if bina is None:
            bina = (ic or {}).get("bina")
        if bina is None:
            raise MatrisHatasi("Kesit önerisi için bina ya da çözüm kimliği gerekir.")
        r = bina_coz(bina, anlat=False)
        ic = r.ic
    bina_ham = copy.deepcopy(ic["bina"])
    turlar = []
    sonuc_oneriler = None
    for tur_no in range(yinele + 1):
        T = ic["tasarim"]
        B = T.B
        if hedef == "hepsi" or hedef is None:
            hedefler = list(B.cubuklar)
        else:
            if not isinstance(hedef, list):
                raise MatrisHatasi('hedef "hepsi" ya da [{"tur", "no"}] listesi olmalı.')
            hedefler = [_cubuk_bul(B, h.get("tur"), h.get("no")) for h in hedef]
        dc_once = {k["cubuk"]: k["dc"] for k in (ic.get("tas") or _tasarim(ts, T))["elemanlar"] if k.get("dc") is not None}
        oneriler = []
        for c in hedefler:
            try:
                oneriler.append(_oner_cubuk(ts, T, c))
            except MatrisHatasi as h:
                oneriler.append({"cubuk": c["no"], "tur": c["tur"], "kesit": c["kesit"], "oneri": None, "gerekce": [str(h)]})
        dc_maks = max(dc_once.values(), default=0.0)
        kayit = {"tur": tur_no, "dc_maks": _r5(dc_maks), "oneri_sayisi": sum(1 for o in oneriler if o.get("oneri"))}
        if sonuc_oneriler is None:
            sonuc_oneriler = oneriler
        if tur_no == yinele:
            turlar.append(kayit)
            break
        yeni, degisen = _oneri_uygula(bina_ham, oneriler, B)
        kayit["degisen"] = degisen
        turlar.append(kayit)
        if not degisen:
            break
        bina_ham = yeni
        r = bina_coz(bina_ham, anlat=False)
        ic = r.ic
        ic["tas"] = r.veri.get("tasarim")
    son = ic.get("tas") or (ic["tasarim"] and _tasarim(ts, ic["tasarim"]))
    dc_son = {k["cubuk"]: k["dc"] for k in son["elemanlar"] if k.get("dc") is not None}
    for o in sonuc_oneriler:
        o["dc_sonra"] = _r5(dc_son[o["cubuk"]]) if (yinele and o["cubuk"] in dc_son) else o.get("dc_oneri")
    return {"oneriler": sonuc_oneriler, "turlar": turlar, "dc_once": turlar[0]["dc_maks"],
            "dc_sonra": _r5(max(dc_son.values(), default=0.0)) if yinele else None,
            "bina": bina_ham if yinele else None, "cozum_kimligi": ic.get("kimlik"),
            "aciklama": "Öneri aynı iç kuvvetlerle yapılır (rijitlik değişmeden); 'yinele' ile öneri uygulanıp model yeniden çözülür, "
                        "çünkü kesit değişince çerçevenin rijitliği ve iç kuvvet dağılımı da değişir. Aynı (kesit, tür) grubundaki "
                        "çubuklara grubun en ağır önerisi verilir."}


def deprem_onizleme(bina):
    """Köprü ``bina_deprem`` (genel model): çözümsüz spektrum, kat kütleleri, V_tE, F_iE (ampirik T_pA)."""
    B = _oku(bina)
    _parcalar(B)
    YK = _yukleri_hazirla(B)
    kutle = _kutleler(B, YK, n=B.deprem["n"], kar_payi=yv.TBDY_KUTLE_KATILIM_KULLANIM["kar"] if B.kar else 0.0)
    if not kutle or sum(k["m"] * k["H"] for k in kutle) <= 0:
        raise MatrisHatasi("Deprem önizlemesi için kat seviyelerinde kütle yok.")
    dep = Y._deprem_on(B, None, kutle)
    veri = Y._deprem_ozet(B, None, dep)
    veri["uyarilar"] = list(dict.fromkeys(list(B.uyarilar) + veri["uyarilar"]))
    return Y._sonlu(veri)
