# -*- coding: utf-8 -*-
"""Aks sistemi tabanlı düğüm–çubuk–panel modeli (bina JSON ``surum: 3``) — Matris Öğren bina motorunun genel katmanı.

``yapi.bina_coz`` bina ``surum >= 3`` ise (ya da ``cubuklar`` / ``paneller`` / ``dugumler`` / ``mesnetler`` / ``uretecler``
listesi doluysa ya da REF düğüm yükü, çubuk / panel ek yükü varsa: ``yapi._serbest_mi``, arayüzdeki ``s3Var`` ile aynı kural)
buraya yönlendirir. Aks–kat elemanları (kolonlar, kirisler, dosemeler) varsa önce aynı kurallarla genel listeye çevrilir
(``docs/model_ops.js`` ``genellestir`` ile birebir), böylece aynı bina iki yoldan aynı sonucu verir. Temel: tekil (en alt
seviyedeki aks kesişimleri temel mesnetidir), mütemadi ya da radye (aynı düğümler temel.py'nin Winkler ağına bağlanır: temel
kirişleri GLOBAL X/Y aksları boyunca, radye GLOBAL aks zarfı + taşma üzerinde; aks–kat motoruyla aynı işlevler, ``_temel_gorunum``).

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
# çubuk türlerinin Türkçe adları (bina.js CUBUK_TURLERI küçük harfle; adres metinleri 'Ç13 (kiriş)'; makine alanı tur değişmez)
TUR_ADI = {"kolon": "kolon", "kiris": "kiriş", "capraz": "çapraz", "makas-ust": "makas üst başlık", "makas-alt": "makas alt başlık",
           "makas-dikme": "makas dikmesi", "makas-diyagonal": "makas diyagonali", "asik": "aşık", "kren": "kren kirişi", "bag": "bağ",
           "diger": "diğer"}


def _tur_adi(tur):
    return TUR_ADI.get(tur, tur)
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
    """Bina genel (surum 3) yolla mı çözülür — tek kural ``yapi._serbest_mi``: surum ≥ 3; cubuklar / paneller / dugumler /
    mesnetler / uretecler listelerinden biri dolu; ya da REF düğüm yükü / çubuk / panel ek yükü var."""
    return Y._serbest_mi(bina)


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
        self.meta = {}            # kayıt no → konum türü (girdi sözlüğü değiştirilmez: çözüm kimliği girdinin özetidir)
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
        self.meta[no] = meta
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
            self.ekle(no, P, self.meta.get(no, {}), self.kayit[no].get("ad"))

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
            p = ts.kesit_ozellik(tip, kayit.get("boyutlar") if kayit.get("boyutlar") is not None else _boyutlar_ust(ad, tip, kayit))
    except MatrisHatasi as h:
        raise MatrisHatasi(f"Kesit {ad!r}: {h} (I/H profiller: IPE, HEA, HEB; basit kesitler: KUTU, BORU, L, 2L, UPN).") from None
    hh = (p.get("H") or p.get("D") or p.get("h") or p.get("b") or 0.0) / 1000.0
    bb = (p.get("B") or p.get("D") or p.get("b") or 0.0) / 1000.0
    aile = {"kutu": "KUTU", "boru": "BORU", "L": "L", "2L": "2L", "U": "UPN"}.get(p["tip"], p["tip"])
    return {"ad": ad, "tip": "basit", "malzeme": mad, "E": m["E"], "G": m["G"], "gamma": m["gamma"], "b": bb, "h": hh,
            "A": p["A"] * 1e-4, "I_guclu": p["Iy"] * 1e-8, "I_zayif": p["Iz"] * 1e-8, "J": max(p["It"], 1e-6) * 1e-8,
            "Wpl": p["Wply"] * 1e-6, "Wel": p["Wely"] * 1e-6, "profil": p["ad"], "g_kg": p["g"], "aile": aile,
            "dogrulandi": True, "kaynak": p.get("kaynak")}


def _boyutlar_ust(ad, tip, kayit):
    """Üst düzey alanlı basit kesit lehçesi (IFC/arayüz örnekleri): {"tip": "boru", "D": 0.1143, "t": 0.004} (m) ya da
    {"tip": "2L", "h": 60, "b": 60, "t": 6, "ara": 10} (mm) → tasarim.kesit_ozellik boyutları (mm). Birim kesit başına dış
    boyuttan (D / h / b) seçilir: dış boyut < 5 ise bütün değerler metre (×1000), değilse mm — böylece mm verilen ince et
    kalınlığı (t = 4 mm) metre sanılmaz."""
    t = str(tip).strip().lower()
    al = lambda *anahtar: next((kayit.get(a) for a in anahtar if kayit.get(a) not in (None, "")), None)  # noqa: E731
    dis = [Y._sayi(al(a), f"Kesit {ad!r}: {a}", pozitif=True, sifir_olur=False) for a in ("D", "d", "h", "H", "b", "B")
           if al(a) is not None]
    metre = bool(dis) and max(dis) < 5.0

    def mm(*anahtar, zorunlu=True):
        v = al(*anahtar)
        if v is None:
            if zorunlu:
                raise MatrisHatasi(f"Kesit {ad!r} ({tip}): {'/'.join(anahtar)} boyutu eksik.")
            return None
        x = Y._sayi(v, f"Kesit {ad!r}: {anahtar[0]}", pozitif=True, sifir_olur=False)
        return x * 1000.0 if metre else x
    if t == "kutu":
        H = mm("h", "H")
        B_ = mm("b", "B", zorunlu=False) or H
        return {"H": H, "B": B_, "t": mm("t")}
    if t == "boru":
        return {"D": mm("D", "d"), "t": mm("t")}
    if t in ("l", "2l"):
        b_ = mm("b", "h")
        h_ = mm("h", zorunlu=False)
        if h_ is not None and abs(h_ - b_) > 1e-6:
            raise MatrisHatasi(f"Kesit {ad!r}: yalnız eşit kollu korniyer desteklenir (h = b).")
        out = {"b": b_, "t": mm("t")}
        if t == "2l":
            s_ = al("ara", "s")
            if s_ is not None:
                s_ = Y._sayi(s_, f"Kesit {ad!r}: ara (sırt aralığı)", pozitif=True)
                out["s"] = s_ * 1000.0 if metre else s_
        return out
    if t == "u":
        return {"h": mm("h"), "b": mm("b"), "tw": mm("tw"), "tf": mm("tf")}
    return None


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
    """Bina JSON → normalize model ``B``. Temel: tekil (en alt seviyedeki aks kesişimleri temel mesnetidir) ya da mütemadi /
    radye (aynı düğümler temel.py Winkler ağına bağlanır; ``_temel_oku``, ``_temel_agi``)."""
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError as e:
            raise MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
    if not isinstance(bina, dict):
        raise MatrisHatasi("Bina bir sözlük (ya da JSON metni) olmalı.")
    if bina.get("tur") not in (None, "bina") or ("tip" in bina and "akslar" not in bina):
        raise MatrisHatasi(f"Bu bir bina modeli değil (tur = {bina.get('tur', bina.get('tip'))!r}). "
                           "Sonlu eleman modelleri (kafes, çerçeve…) için se_coz kullanın.")
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
    # temeller (C3: en alt Z seviyesindeki bütün aks kesişimleri — her aks sisteminde — temele oturur; _mesnetleri_oku)
    t = bina.get("temeller") if isinstance(bina.get("temeller"), dict) else {}
    var = t.get("varsayilan") if isinstance(t.get("varsayilan"), dict) else {}
    zem = t.get("zemin") if isinstance(t.get("zemin"), dict) else {}
    mesnet = str(t.get("mesnet") or "ankastre").strip().lower()
    if mesnet not in ("ankastre", "mafsal", "elastik"):
        raise MatrisHatasi(f"temeller.mesnet {mesnet!r}; 'ankastre', 'mafsal' ya da 'elastik' olmalı.")
    tip = _temel_tipi(t)
    B.temeller = {"tip": tip, "mesnet": mesnet,
                  "varsayilan": {"B": float(var.get("B", 1.5)), "L": float(var.get("L", 1.5)), "h": float(var.get("h", 0.6))},
                  "zemin": {"q_em": float(zem.get("q_em", 200.0)), "k0": float(zem.get("k0", 20000.0))}, "ozel": {}}
    for o in t.get("ozel") or []:      # GLOBAL akslarda anahtar (x, y); ek aks sisteminde (sistem, x, y)
        if isinstance(o, dict) and isinstance(o.get("aks"), (list, tuple)):
            sistem = str(o.get("sistem") or "GLOBAL").strip() or "GLOBAL"
            anahtar = tuple(str(a) for a in o["aks"])
            if sistem != "GLOBAL":
                anahtar = (sistem,) + anahtar
            B.temeller["ozel"][anahtar] = {"B": float(o.get("B", B.temeller["varsayilan"]["B"])),
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
    _temel_oku(B, t)
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
            A_plan = abs(_alan2([(x[0], x[1]) for x in P]))
            if kullanim == "balkon" and A_plan > 10.0:      # TS 498:2021 Çizelge 6 satır 4: > 10 m² balkon (aks–kat ile aynı)
                q = 5.0 + 0.35 * (A_plan - 10.0)
                q_kay = f"TS 498:2021 md. 15.1 Çizelge 6 satır 4: balkon > 10 m² → 5,0 + 0,35·(A − 10) = 5,0 + 0,35·({A_plan:.2f} − 10)"
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
             "egim": math.degrees(math.acos(min(1.0, cos_a))), "geo": g, "kenarlar": kenarlar, "ek_g": 0.0, "ek_q": 0.0, "ek_s": 0.0,
             "kaynak": p.get("kaynak"), "adres": f"P{no}"}
        B.paneller.append(r)
        B.panel_no[no] = r


# yaylı mesnet (C13): bina eksenlerinde yay anahtarı → tuttuğu yön; motor ekseni anahtarı (bina X → motor x, Y → −z, Z → y) ve
# motor yay kuvveti bileşeni (yaylar[].bilesen)
_YAY_YON = {"kx": "ux", "ky": "uy", "kz": "uz", "krx": "rx", "kry": "ry", "krz": "rz"}
_YAY_MOTOR = {"kx": "kx", "ky": "kz", "kz": "ky", "krx": "krx", "kry": "krz", "krz": "kry"}
_MOTOR_BILESEN = {"kx": "Fx", "ky": "Fy", "kz": "Fz", "krx": "Mx", "kry": "My", "krz": "Mz"}


def _mesnet_tipi(bay, yay):
    if yay:
        return "yay"
    return "ankastre" if all(bay.values()) else ("mafsal" if bay["ux"] and bay["uy"] and bay["uz"] and not any(
        bay[a] for a in ("rx", "ry", "rz")) else "ozel")


def _mesnetleri_oku(B, bina, coz):
    B.mesnetler = {}
    for k, m in enumerate(bina.get("mesnetler") or [], start=1):
        if not isinstance(m, dict):
            raise MatrisHatasi(f"mesnetler[{k}] sözlük olmalı: {{\"dugum\": REF, \"ux\": true, ...}}.")
        n = coz.no(m.get("dugum"), f"mesnetler[{k}]")
        bay = {a: bool(m.get(a, False)) for a in ("ux", "uy", "uz", "rx", "ry", "rz")}
        yay = {}
        for a in _YAY_YON:              # yaylı mesnet: kx, ky, kz (kN/m), krx, kry, krz (kN·m/rad), bina eksenlerinde, > 0
            v = m.get(a)
            if v is None:
                continue
            try:
                x = float(v) if not isinstance(v, bool) else float("nan")
            except (TypeError, ValueError):
                x = float("nan")
            if not math.isfinite(x) or x <= 0:
                raise MatrisHatasi(f"mesnetler[{k}]: {a} pozitif bir sayı olmalı (kN/m ya da kN·m/rad).")
            yay[a] = x
        if n in B.mesnetler:
            for a in bay:
                B.mesnetler[n][a] = B.mesnetler[n][a] or bay[a]
            if yay:
                B.mesnetler[n]["yay"] = dict(B.mesnetler[n].get("yay") or {}, **yay)
            bay = {a: B.mesnetler[n][a] for a in bay}
            yay = B.mesnetler[n].get("yay") or {}
        for a, yon in _YAY_YON.items():
            if a in yay and bay[yon]:
                raise MatrisHatasi(f"mesnetler[{k}]: {yon} hem tutulu hem yaylı verilemez ({a}).")
        if n in B.mesnetler:
            B.mesnetler[n]["tip"] = _mesnet_tipi(bay, yay)
            continue
        if not any(bay.values()) and not yay:
            continue
        B.mesnetler[n] = dict(bay, tip=_mesnet_tipi(bay, yay), kaynak="mesnetler", yay=yay or None)
    # temel kuralı (C3): EN ALT Z seviyesindeki (kat 0) her aks kesişimi — hangi aks sisteminde olursa olsun ({aks, z} ya da
    # {sistem, aks, z}) — temeller.mesnet ile mesnetlenir (açık mesnet kaydı yoksa); bölme, kesişim ve koordinat düğümleri asla.
    z0 = B.katlar[0]["kot"] if B.katlar else None
    tip = B.temeller["mesnet"]
    k0 = B.temeller["zemin"]["k0"]
    B.temel_dugumleri = []
    for d in coz.dugum.values():
        if d["no"] in B.mesnetler or d.get("tur") != "aks" or not d.get("aks") or z0 is None or abs(d["Z"] - z0) > 1e-6:
            continue
        if B.temeller["tip"] != "tekil":      # mütemadi / radye: aks kesişimi tabanı Winkler temel ağına bağlanır (sabit mesnet yok)
            B.temel_dugumleri.append(d["no"])
            continue
        sistem = d.get("sistem") or "GLOBAL"
        r = tip != "mafsal"
        kayit = {"ux": True, "uy": True, "uz": True, "rx": r, "ry": r, "rz": r, "tip": tip, "kaynak": "temel", "yay": None,
                 "aks": list(d["aks"]), "sistem": sistem}
        anahtar = tuple(d["aks"]) if sistem == "GLOBAL" else (sistem,) + tuple(d["aks"])
        tem = B.temeller["ozel"].get(anahtar, B.temeller["varsayilan"])
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
            # {"tur": "panel", "panel": n, "durum": "G" | "Q" | "S", "p": kN/m² (düşey, aşağı +)} — p kendi durumuna eklenir.
            # Eski biçim {"g", "q"}: durum G (ya da yok) → g G'ye, q Q'ya; durum Q ya da S → g + q o duruma.
            pn = Y._tam(y.get("panel"), f"{ad}: panel")
            if pn not in B.panel_no:
                raise MatrisHatasi(f"{ad}: panel {pn} yok.")
            pr = B.panel_no[pn]
            alan = {"G": "ek_g", "Q": "ek_q", "S": "ek_s"}
            if y.get("p") not in (None, ""):
                pr[alan[durum]] += Y._sayi(y.get("p"), f"{ad}: p (kN/m², aşağı +)")
            g_ = Y._sayi(y.get("g", 0.0) if y.get("g") not in (None, "") else 0.0, f"{ad}: g (kN/m²)")
            q_ = Y._sayi(y.get("q", 0.0) if y.get("q") not in (None, "") else 0.0, f"{ad}: q (kN/m²)")
            if durum == "G" or "durum" not in y:
                pr["ek_g"] += g_
                pr["ek_q"] += q_
            else:
                pr[alan[durum]] += g_ + q_
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
    B.temel_dugumleri = [n for n in getattr(B, "temel_dugumleri", []) if n in kullanilan]
    sil = [n for n in coz.dugum if n not in kullanilan]
    if sil:
        acik = [n for n in sil if n in coz.kayit]
        if acik:
            B.uyarilar.append(f"Hiçbir çubuğa bağlı olmayan düğüm kayıtları modele alınmadı (yüzen düğüm): {', '.join(map(str, acik[:12]))}"
                              + (" …" if len(acik) > 12 else "") + ".")
        for n in sil:
            del coz.dugum[n]
    if B.temeller["tip"] != "tekil" and not B.temel_dugumleri:
        raise MatrisHatasi(f"temeller.tip = {B.temeller['tip']!r}: temele oturan aks kesişimi yok (en alt Z seviyesinde çubuk ucu olan aks "
                           "kesişimi bulunmadı); kolon tabanlarını en alt seviyedeki aks kesişimlerine bağlayın.")
    if not B.mesnetler and not B.temel_dugumleri:
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
        yogun = {"G": gs, "Q": qh * p["cos_a"], "S": (p["s"] + p["ek_s"]) * p["cos_a"]}
        p["yogun"] = yogun                      # kN/m² (plan düzlemine dik düşey): yük akışı kenarları (_akis) da bunu kullanır
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
    # kat ağırlık tablosu (veri.yukler.katlar; aks–kat kuralı): iki ucu farklı seviyedeki çubuğun (kolon, eğik çubuk) bütün yükü
    # (öz ağırlık, duvar) üst ucunun katına; düğüm yükleri düğümün katına. Deprem kütlesi (dugum_agirlik, _kutleler) değişmez.
    D = B.coz.dugum
    kat_yuk = {kt["no"]: {"G": 0.0, "Q": 0.0, "S": 0.0} for kt in B.katlar}
    for c in B.cubuklar:
        di, dj = D[c["i"]], D[c["j"]]
        ust = dj if dj["Z"] > di["Z"] + 1e-9 else di
        h = kat_yuk.setdefault(ust["kat"], {"G": 0.0, "Q": 0.0, "S": 0.0})
        for d, kay in YK.cubuk[c["no"]].items():
            if d in h:
                Ri, Rj = _cubuk_tepkileri(c, kay)
                h[d] += -(Ri[2] + Rj[2])
    for n, dd in YK.dugum.items():
        h = kat_yuk.setdefault(D[n]["kat"], {"G": 0.0, "Q": 0.0, "S": 0.0})
        for d, F in dd.items():
            if d in h:
                h[d] += -F[2]
    YK.katlar = [{"kat": kt["no"], "ad": kt["ad"], "kot": kt["kot"], "h": kt["h"], **kat_yuk[kt["no"]],
                  "w": kat_yuk[kt["no"]]["G"] + kat_yuk[kt["no"]]["Q"]} for kt in B.katlar]


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


# ============================================================================
# 7b) Mütemadi / radye temel (temel.py): aks–kat görünümü (BT) üzerinden aynı ağ, yük, sonuç ve anlatım işlevleri
# ============================================================================
TEMEL_MAFSAL_NOTU = "Genel modelde mafsallı taban için kolon çubuğunun alt ucuna serbest: My, Mz verin."
TEMEL_ILK_NO = 50001             # temel.py ara düğümleri (aks kesişimi dışındaki ağ noktaları) bu numaradan başlar
_TEMEL_BLOK = 10000              # ara düğüm numara bloğu [ilk_no, ilk_no + 10000) modelde boş seçilir
_TEMEL_TIPLERI = {"tekil": "tekil", "surekli": "surekli", "sürekli": "surekli", "mutemadi": "surekli", "mütemadi": "surekli",
                  "radye": "radye"}


def _tm():
    """temel.py (mütemadi / radye temel); bulunamazsa None (yalnız tekil temel çalışır)."""
    try:
        return importlib.import_module("temel")
    except ImportError:
        return None


def _temel_tipi(t):
    """temeller.tip → 'tekil' | 'surekli' | 'radye' (temel.tip_oku: sürekli / mutemadi / mütemadi eş anlamlı)."""
    tm = _tm()
    if tm is not None:
        tip = tm.tip_oku(t.get("tip"))
    else:
        tip = _TEMEL_TIPLERI.get(str(t.get("tip") or "tekil").strip().lower())
        if tip is None:
            raise MatrisHatasi(f"temeller.tip {t.get('tip')!r} tanımsız; 'tekil', 'surekli' ya da 'radye' olmalı.")
    if tip != "tekil" and tm is None:
        raise MatrisHatasi(f"temeller.tip = {tip!r} için temel.py modülü gerekli (bu kurulumda yok); tekil temel kullanın.")
    return tip


def _temel_oku(B, t):
    """temel.oku ile aynı doğrulama ve varsayılanlar (yapi.py ile aynı): zemin ek alanları (gamma, q_k) her tipte; mütemadi /
    radyede yapılandırma (surekli | radye), temel betonu, donatısı ve varsayımlar B.temeller'e."""
    tm = _tm()
    if tm is None:
        return
    ek = tm.oku(_temel_gorunum(B, ilk=True), t)
    B.temeller["zemin"].update({a: v for a, v in ek["zemin_ek"].items() if v is not None})
    if B.temeller["tip"] != "tekil":
        for a in ("surekli", "radye", "beton", "donati", "varsayim"):
            if a in ek:
                B.temeller[a] = ek[a]
        B.temeller["varsayim"] = list(B.temeller.get("varsayim") or []) + [TEMEL_MAFSAL_NOTU]


def _kolon_boyutlari(B, c, lam):
    """Kolon kesitinin bina X ve Y doğrultusundaki boyutları (bX, bY): kesit yüksekliği h yerel y′, genişliği b yerel z′ boyunca
    (aks–kat: yon x → bX = h, bY = b; aci 90 → takas). Vute temel kesitiyle; b/h yoksa √A."""
    ks = B.kesitler[c["kesit"]]
    kt = (B.kesitler.get(ks.get("temel")) or ks) if ks.get("tip") == "vute" else ks
    kok = math.sqrt(kt["A"]) if kt.get("A") else 0.3
    b = kt.get("b") or kok
    h = kt.get("h") or kok
    y, z = lam[1], lam[2]
    return abs(y[0]) * h + abs(z[0]) * b, abs(y[1]) * h + abs(z[1]) * b


def _kolon_yonu(B, c):
    """Kolonun güçlü ekseninin çalıştığı doğrultu (aks–kat 'yon'): aks–kat kaynağı varsa o kolonun yon'u; yoksa yerel eksen
    açısından (aci 0 → 'x', 90 → 'y', başka → '<aci>°')."""
    kay = c.get("kaynak") or {}
    if kay.get("aks_kat") == "kolon":
        for k in (B.ham.get("kolonlar") or []) if isinstance(B.ham, dict) else []:
            if isinstance(k, dict) and str(k.get("no")) == str(kay.get("no")) and k.get("yon") is not None:
                return str(k["yon"]).strip().lower()
    a = float(c.get("aci") or 0.0)
    if abs(a % 180.0) < 1e-9 or abs(a % 180.0 - 180.0) < 1e-9:
        return "x"
    if abs(a % 180.0 - 90.0) < 1e-9:
        return "y"
    return f"{a:g}°"


def _adres_kisa(d, seviye=True):
    """Aks düğümü adresi: 'A1/±0.00' (ek sistemde 'R:PQ/±0.00'); seviye=False → 'A1' / 'R:PQ'."""
    if d.get("tur") == "aks" and d.get("aks"):
        on = "" if d.get("sistem") in (None, "GLOBAL") else f"{d['sistem']}:"
        return f"{on}{d['aks'][0]}{d['aks'][1]}" + (f"/{d.get('z')}" if seviye else "")
    return f"D{d['no']}"


def _malzeme_adi(B, ks):
    return ks.get("malzeme") or (B.kesitler.get(ks.get("temel")) or {}).get("malzeme")


def _temel_gorunum(B, ilk=False, ag=None):
    """temel.py'nin beklediği aks–kat arayüzü (BT; ``SimpleNamespace``): GLOBAL X/Y aksları konuma göre sıralı (xk, xad, yk, yad;
    ax, ay = {ad: sıra}), kat {0: kot_0}, temeller / malzemeler / kesitler (B'ye başvuru), taban_ixy {temel düğümü: (ix, iy)},
    kolonlar (taban kolonu olan her temel düğümü için kat 1 kaydı: no = çubuk no, ix, iy, aks, adres 'Ç5 (A1)', bX, bY, eleman =
    tabandaki FE parçası — ``ag`` yoksa None —, uc 'i' | 'j', lam, malzeme, dugum, cubuk), kolon_key {(ix, iy, 1): kayıt},
    kolon_no {çubuk no: kayıt}, sanal (eklenen sanal ızgara çizgisi sayısı).

    GLOBAL ızgaranın 1 mm yakınındaki ek aks sistemi tabanları o aks kesişimi sayılır. Izgara dışındaki tabanlar: kirişsiz radyede
    düğümden geçen sanal çizgiler (x=<X>, y=<Y>) eklenir; mütemadi temelde ve kirişli radyede öğretici hata. ``ilk=True``: okuma
    aşaması (temel.oku için aks adları ve kolon malzemeleri). Çözülmemiş modelde de çalışır (tablolar)."""
    S = B.sistemler["GLOBAL"]
    xs = sorted(((S["a1"][a], a) for a in S["s1"]), key=lambda v: v[0])
    ys = sorted(((S["a2"][a], a) for a in S["s2"]), key=lambda v: v[0])
    BT = SimpleNamespace(malzemeler=B.malzemeler, temeller=B.temeller, kesitler=B.kesitler, serbest=True, sanal=0)
    BT.kat = {0: {"kot": B.katlar[0]["kot"] if B.katlar else 0.0}}

    def eksenler():
        BT.xk, BT.xad = [v for v, _ in xs], [a for _, a in xs]
        BT.yk, BT.yad = [v for v, _ in ys], [a for _, a in ys]
        BT.ax = {a: i for i, a in enumerate(BT.xad)}
        BT.ay = {a: i for i, a in enumerate(BT.yad)}

    if ilk:          # okuma aşaması: akslar (temeller.surekli.akslar doğrulaması) ve temel betonu seçimi (kolon malzemeleri)
        eksenler()
        BT.kolonlar = []
        for c in B.cubuklar:
            if c["tur"] == "kolon":
                mad = _malzeme_adi(B, B.kesitler.get(c["kesit"]) or {})
                if mad in B.malzemeler:
                    BT.kolonlar.append({"kat": c.get("kat") or 1, "malzeme": mad})
        return BT
    D = B.coz.dugum
    tabanlar = [(n, D[n]["X"], D[n]["Y"]) for n in getattr(B, "temel_dugumleri", []) if n in D]

    def ara(liste, v):
        en = min(range(len(liste)), key=lambda i: abs(liste[i][0] - v), default=None)
        return en if en is not None and abs(liste[en][0] - v) <= TOL else None
    disarida = [(n, X, Y_) for n, X, Y_ in tabanlar if ara(xs, X) is None or ara(ys, Y_) is None]
    tip = B.temeller["tip"]
    if disarida:
        kirisli = tip == "radye" and (B.temeller.get("radye") or {}).get("kiris")
        if tip == "surekli" or kirisli:
            liste = ", ".join(f"{n} ({_adres_kisa(D[n])})" for n, _, _ in disarida[:6]) + (" …" if len(disarida) > 6 else "")
            raise MatrisHatasi(f"{'Mütemadi temel' if tip == 'surekli' else 'Kirişli radye'}: taban düğümü {liste} GLOBAL X/Y aks "
                               "kesişiminde değil (ek aks sistemi). Temel kirişleri yalnız GLOBAL akslar boyunca kurulur: bu düğüme "
                               "'mesnetler' listesiyle mesnet verin, kirişsiz radye ya da tekil temel seçin.")
        for n, X, Y_ in disarida:        # kirişsiz radye: düğümden geçen sanal ızgara çizgileri
            if ara(xs, X) is None:
                xs.append((X, f"x={_f(X, 3)}"))
                BT.sanal += 1
            if ara(ys, Y_) is None:
                ys.append((Y_, f"y={_f(Y_, 3)}"))
                BT.sanal += 1
        xs.sort(key=lambda v: v[0])
        ys.sort(key=lambda v: v[0])
    eksenler()
    BT.taban_ixy = {n: (ara(xs, X), ara(ys, Y_)) for n, X, Y_ in tabanlar}
    BT.kolonlar, BT.kolon_key, BT.kolon_no = [], {}, {}
    gorulen = set()
    for c in sorted(B.cubuklar, key=lambda c: c["no"]):
        if c["tur"] != "kolon":
            continue
        for uc, n, m in (("i", c["i"], c["j"]), ("j", c["j"], c["i"])):
            if n not in BT.taban_ixy or n in gorulen or D[m]["Z"] <= D[n]["Z"] + 1e-6:
                continue
            ix, iy = BT.taban_ixy[n]
            if (ix, iy, 1) in BT.kolon_key:
                continue
            gorulen.add(n)
            fe = ((c["fe"][0] if uc == "i" else c["fe"][-1]) if c.get("fe") else None) if ag is not None else None
            e = ag["eno"].get(fe) if (ag is not None and fe is not None) else None
            lam = e["lam"] if e else c["lam"]
            bX, bY = _kolon_boyutlari(B, c, lam)
            kol = {"no": c["no"], "ix": ix, "iy": iy, "kat": 1, "aks": [BT.xad[ix], BT.yad[iy]],
                   "adres": f"Ç{c['no']} ({_adres_kisa(D[n], seviye=False)})", "bX": bX, "bY": bY, "eleman": fe, "uc": uc, "lam": lam,
                   "malzeme": _malzeme_adi(B, B.kesitler[c["kesit"]]), "dugum": n, "cubuk": c["no"]}
            BT.kolonlar.append(kol)
            BT.kolon_key[(ix, iy, 1)] = kol
            BT.kolon_no[c["no"]] = kol
    return BT


def _temel_kisa(info):
    """Y._kisa_veri için temel ağı alanları (yapi._veri_olustur ile aynı): radye şeritleri diyagramsız (ince), temel kirişi
    parçaları 3 noktalı (seyrek), temel düğümü yayları yazılmaz (yaysiz; taban basıncı veri.temel'de, yay_ozet'te toplamları)."""
    if info is None:
        return {"ince": set(), "seyrek": set(), "yaysiz": set()}
    return {"ince": set(info.ince), "seyrek": set(info.seyrek), "yaysiz": set(info.dno)}


def _temel_yuk(B, YK, info, g):
    """Temel öz ağırlığı (temel.py info.yuk_G, motor ekseninde: yerel yayılı q ve düğüm yükleri) G durumuna; kat 0 satırına ve
    toplam G'ye W (yapi._yuk_durumlari + temel.yuk_kaydet ile aynı). Temel kütlesi deprem kütlesi değildir (kat 0)."""
    g["yayili"] += [dict(y) for y in info.yuk_G["yayili"]]
    g["yayili_esdeger"] += [dict(y) for y in info.yuk_G["yayili"]]
    for y in info.yuk_G["yukler"]:
        var = next((x for x in g["yukler"] if x["dugum"] == y["dugum"]), None)
        if var is None:
            g["yukler"].append(dict(y))
        else:
            for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz"):
                var[a] = var.get(a, 0.0) + y[a]
    W = info.W
    YK.toplam["G"] += W
    for k in YK.katlar:
        if k["kat"] == 0:
            k["G"] += W
            k["w"] += W
    YK.temel_oz = W


def _temel_sonuclari(B, ag, paket, kombinasyonlar, YK):
    """temel.sonuclar (veri.temel; aks–kat ile aynı işlev, BT görünümüyle) + genel model yük akışı: temele inen düşey kuvvet
    temel ağı düğümlerine bağlanan bütün çubuk uçlarından (kolon, çapraz, bağ…) ve bu düğümlere doğrudan verilen düğüm
    yüklerinden toplanır (servis G + Q). kolon_N_kolonlar: yalnız taban kolonları (temel.py sayısı); aks–kat modelinde ikisi aynı."""
    tm = _tm()
    info = ag["temel"]
    veri, ic = tm.sonuclar(info.BT, ag, paket, kombinasyonlar)
    ya = veri["yuk_akisi"]
    kat = {d: 1.0 for d in ("G", "Q") if d in paket.durum}
    e_idx = {no: j for j, no in enumerate(paket.el_no)}
    net = set(info.dno)
    F = 0.0
    for e in ag["elemanlar"]:
        if e.get("cubuk") is None:
            continue
        uclar = [k for k, n in enumerate(e["dugumler"]) if n in net]
        if not uclar:
            continue
        u = np.zeros(12)
        for d, gm in kat.items():
            u += gm * np.asarray(paket.durum[d]["uc"][e_idx[e["no"]]], dtype=float)
        lamT = np.asarray(e["lam"], dtype=float).T
        for k in uclar:          # eleman ucuna düğümden gelen kuvvet (yerel → bina); yukarı + = düğüme (temele) aşağı yük
            F += float((lamT @ u[6 * k:6 * k + 3])[2])
    dug = 0.0
    for n in net:
        for d, gm in kat.items():
            Fd = YK.dugum.get(n, {}).get(d)
            if Fd is not None:
                dug -= gm * Fd[2]
    km = tm._Kmb(paket, info)
    w = -km.uz(kat)
    zemin = float(info.k0 * np.dot(w, [r["A"] for r in info.dugumler]))      # Σ p·A (yuvarlatılmamış)
    ya["kolon_N_kolonlar"] = ya["kolon_N"]
    ya["kolon_N"] = tm._r(F + dug, 7)
    ya["dugum_yuku"] = tm._r(dug, 7)
    ya["fark"] = tm._r(zemin - (F + dug) - info.W, 5)
    return veri, ic


def _temel_ilk_no(B, dno):
    """temel.py ara düğümleri için ilk numara: 50001'den başlayıp [ilk_no, ilk_no + 10000) bloğunda model düğümü olmayan ilk değer
    (kullanıcı 50001… numaralı düğüm kaydı verdiyse çakışma olmaz)."""
    mevcut = sorted({n for n in (set(dno) | set(B.coz.dugum) | set(B.coz.kayit) | {_EFENDI + k["no"] for k in B.katlar})
                     if n >= TEMEL_ILK_NO})
    ilk = TEMEL_ILK_NO
    for n in mevcut:
        if n >= ilk + _TEMEL_BLOK:
            break
        if n >= ilk:
            ilk = n + 1
    return ilk


def _temel_agi(B, dugumler, dno, elemanlar, model_el, eno):
    """temel.ag_kur ile mütemadi / radye temel ağı (aks–kat görünümü BT). GLOBAL aks kesişimindeki ağ noktaları mevcut düğümü
    kullanır (temel düğümü = C3 tabanı) ya da aks–kat numara kuralıyla (20·ix + iy + 1) yaratılır; sanal çizgi noktaları 500001…,
    öteki ağ noktaları ``_temel_ilk_no``'dan. Yeni elemanlar 'cubuk': None, yerel eksen lam bina koordinatında. Dönüş (eno, info)."""
    tm = _tm()
    coz = B.coz
    S = B.sistemler["GLOBAL"]
    BT = _temel_gorunum(B, ag={"eno": {e["no"]: e for e in elemanlar}})
    z0 = BT.kat[0]["kot"]
    z_ad = B.katlar[0].get("z") or B.katlar[0]["ad"]
    tip_ad = "mütemadi temel" if B.temeller["tip"] == "surekli" else "radye"
    ilk_no = _temel_ilk_no(B, dno)
    konum = {}
    for d in dugumler:
        if not d["ic"] and not d["efendi"] and abs(d["Z"] - z0) <= 1e-6:
            konum.setdefault((round(d["X"], 3), round(d["Y"], 3)), d["no"])
    acik = {n for n, m in B.mesnetler.items() if m.get("kaynak") != "temel"}
    tab_ters = {ixy: n for n, ixy in BT.taban_ixy.items()}

    def bul(X, Yy):
        for dx in (0.0, -0.001, 0.001):
            for dy in (0.0, -0.001, 0.001):
                n = konum.get((round(X + dx, 3), round(Yy + dy, 3)))
                if n is not None and math.hypot(dno[n]["X"] - X, dno[n]["Y"] - Yy) <= TOL:
                    return n
        return None

    def mesnet_hatasi(n):
        raise MatrisHatasi(f"Düğüm {n} ({dno[n]['adres']}) açık mesnetli ('mesnetler') ve {tip_ad} ağının üzerinde. Açık mesnedi "
                           "kaldırın (düğüm temele oturur) ya da tekil temel seçin.")

    def bos(a):
        return (a not in dno and a not in coz.dugum and a not in coz.kayit and not ilk_no <= a < ilk_no + _TEMEL_BLOK)

    def dugum(ix, iy, kat):
        X, Yy = BT.xk[ix], BT.yk[iy]
        n = tab_ters.get((ix, iy))
        if n is None:
            n = bul(X, Yy)
        if n is not None:
            if n in acik:
                mesnet_hatasi(n)
            return n
        xad, yad = BT.xad[ix], BT.yad[iy]
        gercek = xad in S["a1"] and yad in S["a2"]
        aday = None
        if gercek:
            i1, i2 = S["s1"].index(xad), S["s2"].index(yad)
            if i2 < 20 and bos(20 * i1 + i2 + 1):
                aday = 20 * i1 + i2 + 1
        if aday is None:
            coz._sira += 1
            while not bos(coz._sira):
                coz._sira += 1
            aday = coz._sira
        coz.ekle(aday, (X, Yy, z0), {"tur": "aks", "sistem": "GLOBAL", "aks": [xad, yad], "z": z_ad, "ix": i1, "iy": i2}
                 if gercek else {"tur": "temel"})
        r = {"no": aday, "X": X, "Y": Yy, "Z": z0, "adres": f"{xad}{yad}/{z_ad}" if gercek else f"T({_f(X)}; {_f(Yy)})", "kat": 0,
             "aks": [xad, yad] if gercek else None, "efendi": False, "key": (aday, 0, 0), "tur": "temel", "seviye_tam": 0,
             "ic": False, "ad": None}
        dugumler.append(r)
        dno[aday] = r
        konum[(round(X, 3), round(Yy, 3))] = aday
        return aday

    eno0 = eno
    once = len(dugumler)
    eno, info = tm.ag_kur(BT, dugum, dugumler, elemanlar, model_el, eno, en_fazla=EN_FAZLA_SD, ilk_no=ilk_no)
    tm.sayilar_sd_denetimi(BT, dugumler, info, EN_FAZLA_SD)
    for r in dugumler[once:]:          # temel.py'nin eklediği ara düğümler genel model kaydı alanlarıyla
        for a, v in (("tur", "temel"), ("seviye_tam", 0), ("ic", False), ("ad", None)):
            r.setdefault(a, v)
        r["key"] = (r["no"], 0, 0)
        dno[r["no"]] = r
    for r in info.dugumler:            # açık mesnet bir ağ noktasıyla çakışıyorsa (aks kesişimi dışındaki ağ noktaları dahil)
        n = bul(r["X"], r["Y"])
        if n is not None and n in acik:
            mesnet_hatasi(n)
    for e in elemanlar:
        if e["no"] > eno0:
            a, b = dno[e["dugumler"][0]], dno[e["dugumler"][1]]
            e["lam"] = _lam_bina((a["X"], a["Y"], a["Z"]), (b["X"], b["Y"], b["Z"]), 0)
            e["cubuk"] = None
    kopuk = [n for n in B.temel_dugumleri if n not in info.dno]
    if kopuk:
        n = kopuk[0]
        kolonsuz = all(k["dugum"] != n for k in BT.kolonlar)
        raise MatrisHatasi(f"{'Mütemadi temel' if B.temeller['tip'] == 'surekli' else 'Radye'}: taban düğümü {n} ({dno[n]['adres']}) "
                           "temel ağına bağlanmadı (altında temel kirişi yok). Aksı temeller.surekli.akslar listesine ekleyin, yon = "
                           "'xy' seçin ya da bu düğüme 'mesnetler' ile mesnet verin."
                           + (" (düğüm kolon taşımıyor: temel kirişinin uçları kolonlara göre belirlenir)" if kolonsuz else ""))
    bag = [c["no"] for c in B.cubuklar if abs(coz.dugum[c["i"]]["Z"] - z0) <= 1e-6 and abs(coz.dugum[c["j"]]["Z"] - z0) <= 1e-6]
    if bag:
        B.uyarilar.append(f"{', '.join(f'Ç{n}' for n in bag[:8])}{' …' if len(bag) > 8 else ''} temel seviyesinde: temel ağıyla paralel "
                          "çalışır (rijitlik ve öz ağırlık ayrıca sayılır); bağ kirişi istemiyorsanız silin.")
    if BT.sanal:
        info.notlar.append(f"Ek aks sistemindeki {sum(1 for ix, iy in BT.taban_ixy.values() if BT.xad[ix].startswith('x=') or BT.yad[iy].startswith('y='))} "
                           f"taban düğümü için radye ızgarasına {BT.sanal} sanal çizgi eklendi (x=…, y=…). Farklı oturma denetimi ızgara "
                           "komşuluğuna bakar: sanal çizgiyle ayrılan kolon çiftleri bu (bilgi) denetimde karşılaştırılmaz.")
    info.BT = BT
    return eno, info


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
                 "adres": f"Ç{c['no']} ({_tur_adi(c['tur'])}) {dno[c['i']]['adres']}→{dno[c['j']]['adres']}" + (f" [{k + 1}/{len(prc)}]" if len(prc) > 1 else ""),
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
    temel_info = None
    if B.temeller["tip"] != "tekil":
        eno, temel_info = _temel_agi(B, dugumler, dno, elemanlar, model_el, eno)
    n_kole = len(dugumler)
    # mesnetler + otomatik dönme tutucuları (bütün çubuk uçları mafsallı düğüm)
    mesnetler, model_mes, yaylar = [], [], []
    yay_tur = {}                  # (düğüm, motor bileşeni) → yaylar[].tur ('yay-mesnet' | 'diyafram-mesnet'; C12)
    for no in sorted(B.mesnetler):
        m = B.mesnetler[no]
        acik_yay = m.get("yay") if m["kaynak"] != "temel" else None
        mesnetler.append({"dugum": no, "tip": m["tip"], "aks": m.get("aks"), "sistem": m.get("sistem"), "B": m.get("B"), "L": m.get("L"),
                          "kaynak": m["kaynak"], "ux": m["ux"], "uy": m["uy"], "uz": m["uz"], "rx": m["rx"], "ry": m["ry"], "rz": m["rz"],
                          **({"yay": dict(acik_yay)} if acik_yay else {})})
        mm = {"dugum": no}
        for a_b, a_m in (("ux", "ux"), ("uy", "uz"), ("uz", "uy"), ("rx", "rx"), ("ry", "rz"), ("rz", "ry")):
            if m[a_b]:
                mm[a_m] = True
        if len(mm) > 1:
            model_mes.append(mm)
        if acik_yay:              # yaylı mesnet (C13): bina → motor eksenleri
            yaylar.append({"dugum": no, **{_YAY_MOTOR[a]: v for a, v in acik_yay.items()}})
            for a in acik_yay:
                yay_tur[(no, _MOTOR_BILESEN[_YAY_MOTOR[a]])] = "yay-mesnet"
        elif m.get("yay"):        # tekil temel 'elastik' (temeller.mesnet)
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
    ceza = None
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
        for n in koleler:          # rijit diyafram: köle düğümün düzlem içi serbestlikleri (ux, uy, rz) efendiye bağlı
            m = B.mesnetler.get(n)
            if m and m.get("kaynak") == "mesnetler" and (m["ux"] or m["uy"] or m["rz"]):
                # mesnet köle serbestliğine verilemez (sonlu_eleman): ceza rijitlikli yay olur, K_r = TᵀKT ile efendiye bağlanır (C14)
                if ceza is None:
                    ceza = _diyafram_ceza_rijitligi(model_el, elemanlar)
                mm = mes_idx.get(n)
                if mm is not None:
                    for a_m in ("ux", "uz", "ry"):
                        mm.pop(a_m, None)
                    if len(mm) == 1:
                        model_mes.remove(mm)
                        del mes_idx[n]
                yy = {"dugum": n}
                for a_b, a_m, bil, kk_ in (("ux", "kx", "Fx", ceza[0]), ("uy", "kz", "Fz", ceza[0]), ("rz", "kry", "My", ceza[1])):
                    if m[a_b]:
                        yy[a_m] = kk_
                        yay_tur[(n, bil)] = "diyafram-mesnet"
                yaylar.append(yy)
                B.uyarilar.append(f"Düğüm {n} ({dno[n]['adres']}) rijit diyaframlı {B.kat[kat]['ad']} seviyesinde: ux/uy/rz mesnedi "
                                  "diyafram bağıyla (ceza rijitliği) uygulandı; bu nokta bütün katın yatay hareketini tutar.")
        no = _EFENDI + kat
        x, y, z = Y._motor_koordinat(kk["X"], kk["Y"], kk["kot"])
        diyaframlar.append({"dugumler": koleler, "ana": {"no": no, "x": x, "y": y, "z": z}, "ad": f"Kat {kat}"})
        efendi[kat] = no
        r = {"no": no, "X": kk["X"], "Y": kk["Y"], "Z": kk["kot"], "adres": f"KM/k{kat}", "kat": kat, "aks": None, "efendi": True,
             "key": None, "tur": "efendi", "seviye_tam": kat, "ic": False, "ad": None}
        dugumler.append(r)
        dno[no] = r
    nsd = 6 * n_kole
    if nsd - (temel_info.tutulu_sd if temel_info is not None else 0) > EN_FAZLA_SD:
        raise MatrisHatasi(f"Model {n_kole} düğüm × 6 = {nsd} serbestlik derecesi; tarayıcıda çözüm için en fazla {EN_FAZLA_SD}. "
                           "Modeli küçültün (bölme düğümlerini azaltın, vute parça sayısını düşürün: analiz.vute_parca).")
    model_dg = []
    for d in dugumler:
        d["m"] = Y._motor_koordinat(d["X"], d["Y"], d["Z"])
        if not d["efendi"]:
            model_dg.append({"no": d["no"], "x": d["m"][0], "y": d["m"][1], "z": d["m"][2]})
    if temel_info is not None:
        model_mes += [dict(m) for m in temel_info.model_mesnet]
        yaylar += [dict(y) for y in temel_info.model_yay]
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
          "model_c": model_c, "donme_tutulan": donme, "fe_cubuk": {e["no"]: e["cubuk"] for e in elemanlar}, "temel": temel_info,
          "yay_tur": yay_tur}
    return ag, model


def _yay_turu_yaz(ag, kisalar):
    """Yay kuvveti kayıtlarına tür (C12): 'yay-mesnet' (yaylı açık mesnet, C13) ya da 'diyafram-mesnet' (rijit diyaframlı seviyedeki
    ux/uy/rz mesnedinin ceza yayı, C14); temel / Winkler yaylarında alan yok."""
    tur = ag.get("yay_tur") or {}
    if not tur:
        return
    for k in kisalar:
        for y in k["yaylar"]:
            t = tur.get((y["dugum"], y.get("bilesen")))
            if t:
                y["tur"] = t


def _diyafram_ceza_rijitligi(model_el, elemanlar):
    """Rijit diyaframlı seviyedeki ux/uy/rz mesnedinin ceza yayları (C14): k_t = 1e6·max(E·A/L) (kN/m), k_r = 1e6·max(E·max(Iy, Iz)/L)
    (kN·m/rad), bütün sonlu elemanlar üzerinden."""
    kt = kr = 0.0
    for me, e in zip(model_el, elemanlar):
        L = e["L"] if e.get("L") else 1.0
        kt = max(kt, me["E"] * me["A"] / L)
        kr = max(kr, me["E"] * max(me["Iy"], me["Iz"]) / L)
    return 1e6 * kt, 1e6 * kr


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
    temeller, mesnetler = [], []
    q_em = B.temeller["zemin"]["q_em"]
    h_t = B.temeller["varsayilan"]["h"]
    for m in ag["mesnetler"]:
        tg, tq = desG.get(m["dugum"]), desQ.get(m["dugum"])
        if tg is None or tq is None:
            continue
        ortak = {"dugum": m["dugum"], "adres": ag["dno"][m["dugum"]]["adres"], "tip": m["tip"], "N_G": tg["FZ"], "N_Q": tq["FZ"],
                 "MX": tg["MX"] + tq["MX"], "MY": tg["MY"] + tq["MY"], **({"yay": dict(m["yay"])} if m.get("yay") else {})}
        if m.get("kaynak") != "temel":         # açık mesnet kaydı (mesnetler listesi): temel değildir, ayrı tabloda
            mesnetler.append(ortak)
            continue
        kol = next((c["no"] for c in B.cubuklar if c["tur"] == "kolon" and m["dugum"] in (c["i"], c["j"])), None)
        r = dict(ortak, kolon_no=kol, aks=m.get("aks"))
        if m.get("sistem") not in (None, "GLOBAL"):
            r["sistem"] = m["sistem"]
        Bt, Lt = m["B"], m["L"]
        N_temel = Y.GAMMA_BA * Bt * Lt * h_t
        N = tg["FZ"] + tq["FZ"] + N_temel
        sig_m = 6.0 * abs(r["MX"]) / (Bt * Lt * Lt) + 6.0 * abs(r["MY"]) / (Lt * Bt * Bt)
        smax, smin = N / (Bt * Lt) + sig_m, N / (Bt * Lt) - sig_m
        eX, eY = (abs(r["MY"]) / N, abs(r["MX"]) / N) if N > 1e-9 else (0.0, 0.0)
        r.update({"B": Bt, "L": Lt, "h": h_t, "N_temel": N_temel, "N_servis": N, "sigma_max": smax, "sigma_min": smin, "e_X": eX,
                  "e_Y": eY, "q_em": q_em, "DC": smax / q_em if q_em else 0.0,
                  "cekirdek_icinde": eX <= Bt / 6.0 + 1e-12 and eY <= Lt / 6.0 + 1e-12})
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
        if getattr(YK, "temel_oz", 0.0) and d == "G":
            parca["temel_oz"] = YK.temel_oz          # temel kirişi / radye öz ağırlığı (kat 0; temel.py W)
        parca["ek"] = YK.toplam[d] - sum(parca.values())
        parca.update({"toplam": YK.toplam[d], "temel": tep, "yay": yay, "kolon_taban": tep + yay})
        korunum[d] = parca
    # akış şeması (C15), her düşey yük durumunda (G, Q ve kar varsa S): panel → çubuk bantları (çubuğa düşen pay = yoğunluk × Σ
    # kenar dağıtım alanı; veri.yukler.cubuklar[].<durum>.panel ile aynı sayı) ve düğüm kuralıyla çubuk → çubuk, çubuk → mesnet,
    # düğüm yükü → çubuk / mesnet kenarları (_dugum_akimlari). Her durumda en çok 600 panel bandı ve 600 öteki kenar (en büyükler);
    # atılan kenar sayısı sankey_kesildi'de.
    sankey, kesildi = [], {}
    for d in ("G", "Q", "S"):
        if d not in durumlar_kisa:
            continue
        bantlar = []
        for p in B.paneller:
            v = (p.get("yogun") or {}).get(d, p["g_yuzey"] if d == "G" else 0.0)
            if v <= 1e-12 or p["toplam"][d] <= 0:
                continue
            for cno, parcalar in p["dag"]["cubuklar"]:
                kN = v * sum((x2 - x1) * (f1 + f2) / 2.0 for x1, x2, f1, f2 in parcalar)
                if kN > 1e-12:
                    bantlar.append({"kaynak": f"P{p['no']}", "hedef": f"Ç{cno}", "durum": d, "kN": kN, "tur": "panel-cubuk"})
        kenar = {}
        for n, (gir, cik) in _dugum_akimlari(B, YK, ag, durumlar_kisa[d], d).items():
            top = sum(x for _, x in cik)
            if top <= 1e-12:
                continue
            for a_, x in gir:
                for b_, y in cik:
                    kN = x * y / top
                    if kN >= 1e-9:
                        anahtar = (a_, b_)
                        kenar[anahtar] = kenar.get(anahtar, 0.0) + kN
        oteki = [{"kaynak": a_, "hedef": b_, "durum": d, "kN": kN,
                  "tur": ("dugum-" if a_.startswith("D") else "cubuk-") + ("mesnet" if b_.startswith("M") else "cubuk")}
                 for (a_, b_), kN in kenar.items()]
        atilan = max(0, len(bantlar) - _SANKEY_SINIRI) + max(0, len(oteki) - _SANKEY_SINIRI)
        if atilan:
            kesildi[d] = atilan
        sankey += sorted(bantlar, key=lambda s: -s["kN"])[:_SANKEY_SINIRI] if len(bantlar) > _SANKEY_SINIRI else bantlar
        sankey += sorted(oteki, key=lambda s: -s["kN"])[:_SANKEY_SINIRI]
    out = {"kolonlar": kolonlar, "temeller": temeller, "mesnetler": mesnetler, "korunum": korunum, "sankey": sankey}
    if kesildi:
        out["sankey_kesildi"] = kesildi
    return out


_SANKEY_SINIRI = 600          # durum başına en çok panel bandı ve en çok öteki kenar (C15)


def _dugum_akimlari(B, YK, ag, kisa, d):
    """Akış şemasının düğüm kuralı (C15), bir yük durumunda: her çubuk ucu düğümü n için {n: (girenler, çıkanlar)}, öğeler
    (kimlik, kN > 0). f_b: b çubuğunun ucunun düğüme uyguladığı düşey kuvvet (bina Z, aşağı +; eleman uç kuvvetinin λᵀ ile bina
    eksenine izdüşümü). P_n: düğüm yükü (aşağı +), R_n: mesnet tepkisi + yay kuvveti (yukarı +). Girenler: f_b > 0 çubuklar
    ('Ç{b}') ve P_n > 0 ise 'D{n}'; çıkanlar: f_b < 0 çubuklar (−f_b) ve R_n > 0 ise 'M{n}'. Mütemadi / radye ağı düğümünde tek
    çıkan 'M{n}' gelen her şeyi alır (temel elemanları çubuk değildir). Çubuk içi FE düğümleri (vute ara düğümü) atlanır."""
    el = {e["no"]: e for e in kisa["elemanlar"]}
    agel = {e["no"]: e for e in ag["elemanlar"]}
    net = set(ag["temel"].dno) if ag.get("temel") is not None else set()
    akim = {}
    for c in B.cubuklar:
        for n, fe, k in ((c["i"], c["fe"][0], 0), (c["j"], c["fe"][-1], 1)):
            u = el[fe]["uc_kuvvetleri"]
            lam = agel[fe]["lam"]
            f = lam[0][2] * u[6 * k] + lam[1][2] * u[6 * k + 1] + lam[2][2] * u[6 * k + 2]
            akim.setdefault(n, []).append((c["no"], f))
    R = {}
    for t in kisa["tepkiler"]:
        R[t["dugum"]] = R.get(t["dugum"], 0.0) + t["FZ"]
    for y in kisa["yaylar"]:
        if y.get("bilesen") == "Fy":
            R[y["dugum"]] = R.get(y["dugum"], 0.0) + y["kuvvet"]
    out = {}
    for n, lst in akim.items():
        P = -float((YK.dugum.get(n) or {}).get(d, [0.0] * 6)[2])
        gir = [(f"Ç{b}", f) for b, f in lst if f > 1e-12] + ([(f"D{n}", P)] if P > 1e-12 else [])
        cik = [(f"Ç{b}", -f) for b, f in lst if f < -1e-12]
        if n in net:
            M = sum(x for _, x in gir) - sum(x for _, x in cik)
        else:
            M = R.get(n, 0.0)
        if M > 1e-12:
            cik.append((f"M{n}", M))
        out[n] = (gir, cik)
    return out


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
    GQ = np.zeros(paket.L)
    for d in ("G", "Q"):
        if d in paket.durum:
            GQ = GQ + paket.durum[d]["diy"]
    return SimpleNamespace(B=B, ag=ag, paket=paket, kombs=kombs, adlar=[k["ad"] for k in kombs],
                           deprem=[k["tur"] == "deprem" for k in kombs], C=G @ D, GQ=GQ,
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
    M = np.abs(np.array([[float(k.get(a, 0.0)) for a in anahtarlar] for k in kuv]))      # (kayıt, büyüklük)
    enb = M.max(axis=0)
    enb[enb == 0.0] = 1.0
    sec = set()
    for j in range(len(anahtarlar)):
        sec.update(np.argsort(-M[:, j], kind="stable")[:n].tolist())
    sec.update(np.argsort(-(M / enb).sum(axis=1), kind="stable")[:n + 1].tolist())
    tut = sorted(sec)[:en_cok]
    return [kuv[i] for i in tut]


def _kolon_on_ele(ts, kuv, kt, d_ust, beton, donati, n=10, en_cok=16, As=None):
    """Kolon noktaları (her kombinasyonun iki ucu): bütün noktalar ρ = 0,01 (ya da verilen ``As``, cm²) ile bir kez N–M'den geçirilir,
    D/C'si en büyük ``n`` nokta ve büyüklük ön elemesinin seçtikleri (kesme için) tutulur. Büyüklükle eleme düşük N – büyük M
    noktalarını (0,9G ± E) kaçırır; aks–kat motoru (yapi._kolon_ba) da en büyük D/C'li 10 noktayla tarar."""
    if len(kuv) <= en_cok:
        return kuv
    sec = {id(k) for k in _on_ele(kuv, ["N", "Mx", "My", "V"], n=3, en_cok=en_cok)}
    try:
        on = ts.kolon_kontrol([k["N"] for k in kuv], [k["Mx"] for k in kuv], [k["My"] for k in kuv], kt["b"], kt["h"],
                              As or 0.01 * kt["b"] * kt["h"] * 1e4, d_ust, beton, donati, adlar=[k["ad"] for k in kuv], tbdy=False,
                              ham=True)
        sira = sorted(range(len(kuv)), key=lambda i: -on["noktalar"][i]["dc"])[:n]
        sec |= {id(kuv[i]) for i in sira}
    except MatrisHatasi:
        pass
    return [k for k in kuv if id(k) in sec]


def _celik_satirlari(r, on=""):
    """celik_eleman_kontrol satırları → §11 satırları (yapi._celik satirlar ile aynı): belirleyen kombinasyon adı satırdan ayrılır;
    döşemeli kirişte ``on`` bölge metni ('pozitif M, L_b = 0' | 'negatif M, L_b = …, C_b = …') satır adına ' — …', etikete
    ' (pozitif M)' / ' (negatif M)' olarak eklenir (narinlik koşulu hariç)."""
    en = max(r["kombinasyonlar"], key=lambda x: x["dc"]) if r["kombinasyonlar"] else None
    out = []
    for x in r["kontroller"]:
        ad_, komb = x["ad"], None
        if en and ad_.startswith(en["ad"] + ": "):
            komb, ad_ = en["ad"], ad_[len(en["ad"]) + 2:]
        narin = ad_.startswith("Narinlik")
        et = Y._celik_etiket(ad_, en["dal"] if en else None)
        if on and not narin:
            ad_, et = f"{ad_} — {on}", f"{et} ({on.split(',')[0]})"
        out.append(Y._kontrol_kaydi(x, komb, ad_, et, kosul=narin))
    return out, en


def _en_buyuk_dayanim(sat):
    return [max((x for x in sat if not x["kosul"]), key=lambda x: x["dc"])] if any(not x["kosul"] for x in sat) else []


def _celik_kuvvet(T, bl, i, ad):
    Nv = np.concatenate([-b[i, _I_N, :] for b, _, _, _ in bl])
    return {"ad": ad, "N": float(Nv[int(np.argmax(np.abs(Nv)))]),
            "Mx": float(max(np.max(np.abs(b[i, _I_M, :])) * o for b, _, o, _ in bl)),
            "My": float(max(np.max(np.abs(b[i, _I_MY, :])) for b, _, _, _ in bl)),
            "V": float(max(np.max(np.abs(b[i, _I_V, :])) for b, _, _, _ in bl))}


def _celik_kuvvetleri(T, bl):
    """Bütün kombinasyonlar için _celik_kuvvet (vektörel; sonuç aynı): [{ad, N, Mx, My, V}]."""
    nk = len(T.adlar)
    if not nk:
        return []
    Nm = np.concatenate([-b[:, _I_N, :] for b, _, _, _ in bl], axis=1)
    N = Nm[np.arange(nk), np.argmax(np.abs(Nm), axis=1)]
    Mx = np.max(np.stack([np.max(np.abs(b[:, _I_M, :]), axis=1) * o for b, _, o, _ in bl]), axis=0)
    My = np.max(np.stack([np.max(np.abs(b[:, _I_MY, :]), axis=1) for b, _, _, _ in bl]), axis=0)
    V = np.max(np.stack([np.max(np.abs(b[:, _I_V, :]), axis=1) for b, _, _, _ in bl]), axis=0)
    return [{"ad": ad, "N": float(N[i]), "Mx": float(Mx[i]), "My": float(My[i]), "V": float(V[i])} for i, ad in enumerate(T.adlar)]


def _cubuk_tasarla(ts, T, c, anl=None, bilgi=None, kt_yerine=None):
    """Bir çubuğun tahkiki → (§11 kaydı, uyarılar, ek). bilgi: kesit önerisi için kullanılan parametreler (dışarı yazılır).
    ``kt_yerine``: tahkik bu kesit kartıyla (aynı iç kuvvetler) yapılır — kesit önerisinin D/C'si (``_oner_cubuk``)."""
    B = T.B
    ks = B.kesitler[c["kesit"]]
    kt = kt_yerine if kt_yerine is not None else (B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks)
    mal = B.malzemeler[kt["malzeme"]]
    bl = _bloklar(T, c)
    L = c["L"]
    kayit = {"no": c["no"], "kat": c["kat"], "adres": f"Ç{c['no']} ({_tur_adi(c['tur'])})", "kesit": c["kesit"]}
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
                                       yontem=yontem, tbdy_capraz=tc, anl=anl, ham=anl is None)
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
                varsayim.append("L_b = çubuk boyu" + (" (negatif moment, C_b moment diyagramından — ÇYTHYE Denk. 9.1); pozitif momentte "
                                                      "döşeme/çatı kaplaması üst başlığı tutar → L_b = 0" if dos else ""))
            kren = c["tur"] == "kren"
            tum = _celik_kuvvetleri(T, bl)
            kuv = None if dos else _on_ele(tum, ["N", "Mx", "My", "V"])
            Cb_k = 1.0

            def kontrol(Lb_, kuv_, anl_, Cb_=1.0):
                return ts.celik_eleman_kontrol(profil, mal["kutuphane"], L=L, Lb=Lb_, K=tuple(K), kuvvetler=kuv_, yontem=yontem,
                                               kren=kren, Cb=Cb_, anl=anl_, ham=anl_ is None)
            if dos:
                # döşeme yalnız ÜST başlığı tutar: pozitif momentte L_b = 0; negatif momentte L_b = boy, C_b moment diyagramından
                # (ÇYTHYE Denk. 9.1; yapi._celik ile aynı kural). Pozitif / negatif momentler her kombinasyonda ayrı ayrı.
                xs_c = np.concatenate([xs for _, xs, _, _ in bl])
                M_c = np.concatenate([b[:, _I_M, :] * o for b, _, o, _ in bl], axis=1)       # (kombinasyon, istasyon)
                Mp_v, Mn_v = np.max(M_c, axis=1), np.max(-M_c, axis=1)
                kp = [dict(k, Mx=max(float(Mp_v[i]), 0.0)) for i, k in enumerate(tum)]
                kn = [dict(k, Mx=max(float(Mn_v[i]), 0.0)) for i, k in enumerate(tum)]
                Mn_max = float(np.max(Mn_v)) if len(tum) else 0.0
                Cb_n = 1.0
                if c["Lb"] is None and Mn_max > 1e-9:
                    sec = np.flatnonzero((Mn_v > 1e-9) & (Mn_v >= 0.1 * Mn_max))      # önemli negatif momentli kombinasyonlar
                    cb_aday = []
                    for i in sec:
                        Mm = float(np.max(np.abs(M_c[i])))
                        if Mm > 1e-12:
                            ceyrek = [min(abs(float(np.interp(f * L, xs_c, M_c[i]))), Mm) for f in (0.25, 0.5, 0.75)]
                            cb_aday.append(ts.cb_katsayisi(Mm, *ceyrek))
                    Cb_n = min(cb_aday) if cb_aday else 1.0       # güvenli taraf: en küçük C_b
                kp, kn = _on_ele(kp, ["N", "Mx", "My", "V"]), _on_ele(kn, ["N", "Mx", "My", "V"])
                rp, rn = kontrol(0.0, kp, None), kontrol(Lb, kn, None, Cb_n)
                negatif = Mn_max > 1e-6
                sp_, en_p = _celik_satirlari(rp, "pozitif M, L_b = 0")
                sn_, en_n = _celik_satirlari(rn, f"negatif M, L_b = {_f(Lb)} m, C_b = {_f(Cb_n, 2)}") if negatif else ([], None)
                if negatif and Y._dc_dayanim(rn) > Y._dc_dayanim(rp):      # dayanım D/C'si (sağlanan narinlik hariç), yapi._celik gibi
                    r, kuv_k, Lb_k, Cb_k, en, bolge = rn, kn, Lb, Cb_n, en_n, "negatif"
                    kont = sn_ + _en_buyuk_dayanim(sp_)          # öteki bölgenin özeti: en büyük D/C'li dayanım satırı
                else:
                    r, kuv_k, Lb_k, en, bolge = rp, kp, 0.0, en_p, "pozitif"
                    kont = sp_ + (_en_buyuk_dayanim(sn_) if negatif else [])
                bolge_ozet = {"bolge": bolge, "Lb_neg_m": Lb if negatif else None, "Cb_neg": Cb_n if negatif else None,
                              "Mc_neg_kNm": rn["egilme"]["Mc_kNm"] if negatif else None, "dc_pozitif": Y._dc_dayanim(rp),
                              "dc_negatif": Y._dc_dayanim(rn) if negatif else None}
                if anl is not None:
                    r = kontrol(Lb_k, kuv_k, anl, Cb_k)
            else:
                r = kontrol(Lb, kuv, anl)
                kuv_k, Lb_k = kuv, Lb
                kont, en = _celik_satirlari(r)
                bolge_ozet = {}
            bilgi.update({"kontrol": "eleman", "L": L, "Lb": Lb_k, "K": tuple(K), "kuvvetler": kuv_k, "kren": kren, "yontem": yontem,
                          "Cb": Cb_k})
            eg, bs, kk = r["egilme"], r["basinc"], r["kesme"]
            sinif = r["sinif"]
            ozet = {"kontrol": "eleman (ÇYTHYE 11.1)", "profil": profil, "sinif": f"eğilme: {sinif.get('egilme', '?')}; basınç: "
                    f"{sinif.get('basinc', '?')}" if isinstance(sinif, dict) else str(sinif),
                    "Mc_kNm": eg["Mc_kNm"], "Mcy_kNm": eg["Mcy_kNm"], "Pc_kN": bs["Pc_kN"], "Vc_kN": kk["Vc_kN"], "L_m": L, "Lb_m": Lb_k,
                    "Cb": Cb_k,
                    "K": list(K), "yontem": r["yontem"], "N_kN": en["N"] if en else 0.0, "Mx_kNm": en["Mx"] if en else 0.0,
                    "My_kNm": en["My"] if en else 0.0, "V_kN": en["V"] if en else 0.0, **bolge_ozet}
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
        kuv, ad_komb = [], {}
        for i, ad in enumerate(T.adlar):
            dep = T.deprem[i]
            n0 = len(kuv)
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
            for k_ in kuv[n0:]:
                ad_komb[k_["ad"]] = ad
        kuv_tum = kuv
        # kolon boyuna donatısı (yapi._kolon_ba ile aynı kural): kesitte As / donati_orani verilmişse o, yoksa ρ = 0,01 varsayımı;
        # D/C bu donatıyla, gerekli ρ ayrıca (ρ taraması) özette — aynı bina iki motorda aynı D/C ve durum ("donatı artır")
        As_ver = _kolon_As(B, kt, ks, c) if tur_ba == "kolon" else None
        rho_varsayim = tur_ba == "kolon" and As_ver is None
        if rho_varsayim:
            As_ver = Y._RHO_VARSAYILAN * kt["b"] * kt["h"] * 1e4
        if tur_ba == "kolon":
            kuv = _kolon_on_ele(ts, kuv, kt, pas + Y._PAS_EK, mal["kutuphane"], donati, As=As_ver)
        elif tur_ba == "egik":
            kuv = _on_ele(kuv, ["N", "Mx", "My", "V"], n=3, en_cok=16)
        else:
            kuv = (_on_ele([k for k in kuv if k["Mx"] >= 0], ["Mx", "V", "N"], en_cok=8)
                   + _on_ele([k for k in kuv if k["Mx"] < 0], ["Mx", "V", "N"], en_cok=8))
        # ham: iç sonuç (_json ve kolon eğrileri yok; anlatımda tam yol) — kayıt satırları _kontrol_kaydi ile yalınlaşır (K-31)
        r = ts.betonarme_eleman_kontrol(kt["b"], kt["h"], pas + Y._PAS_EK, mal["kutuphane"], donati, kuv, tur=tur_ba,
                                        As_toplam=As_ver, tbdy=bool(B.deprem), anl=anl, ham=anl is None)
        bilgi.update({"kontrol": "betonarme", "tur": "kolon" if tur_ba == "kolon" else "kiris", "kuvvetler": kuv,
                      "malzeme": {"beton": mal["kutuphane"], "donati": donati}, "b": kt["b"], "h": kt["h"], "tur_ba": tur_ba,
                      "pas": pas})
        gq_N = None
        if tur_ba == "kolon" and getattr(T, "GQ", None) is not None:
            prc = B.parca[c["no"]]
            b0, b1 = Y._blok(T, prc[0]["fe"], T.GQ), Y._blok(T, prc[-1]["fe"], T.GQ)
            gq_N = max(-float(b0[_I_N, 0]), -float(b1[_I_N, -1]))
        ndm = {}
        kont = _ba_kontroller(ts, r, kuv_tum, ad_komb, tur_ba, kt, mal, gq_N, cikti=ndm)
        if ndm:
            bilgi.update({"N_dm": ndm["Ndm"], "N_dm_kaynak": ndm["kaynak"]})
        ozet = {"kontrol": {"kiris": "kiriş (TS 500 eğilme + kesme)", "kolon": "kolon (N–M)", "egik": "eğik eleman (TS 500 Denk. 7.2)"}[tur_ba],
                "As_toplam_cm2": r.get("As_toplam_cm2"), "As_kaynak": r.get("As_kaynak"), "b_mm": r["b_mm"], "h_mm": r["h_mm"],
                "esik_kN": r["esik_kN"]}
        rho_ger = None
        if tur_ba == "kolon":
            Ac_cm2 = kt["b"] * kt["h"] * 1e4
            rho = As_ver / Ac_cm2
            nm = max((x["dc"] for x in r["kontroller"] if "etkileşim" in x["ad"] or "İki eksenli" in x["ad"]), default=0.0)
            if nm <= 1.0 + 1e-9 and rho <= Y._RHO_VARSAYILAN + 1e-12:
                rho_ger = rho
            else:                                   # gerekli ρ: 0,01 … 0,04 taraması (yapi._kolon_ba _RHO_TARAMA gibi)
                try:
                    r2 = ts.betonarme_eleman_kontrol(kt["b"], kt["h"], pas + Y._PAS_EK, mal["kutuphane"], donati, kuv, tur=tur_ba,
                                                     tbdy=bool(B.deprem), ham=True)
                    nm2 = max((x["dc"] for x in r2["kontroller"] if "etkileşim" in x["ad"] or "İki eksenli" in x["ad"]), default=0.0)
                    rho_ger = r2["As_toplam_cm2"] / Ac_cm2 if (r2.get("As_toplam_cm2") and nm2 <= 1.0 + 1e-9) else None
                except MatrisHatasi:
                    rho_ger = None
            ozet.update({"As_kaynak": ("varsayım ρ = 0,01 (TS 500 md. 7.4.1 en az; kesitte As ya da donati_orani verilebilir)"
                                       if rho_varsayim else "kesitte verilen"),
                         "rho": rho, "rho_varsayim": rho_varsayim, "rho_gerekli": rho_ger,
                         "As_gerekli_cm2": rho_ger * Ac_cm2 if rho_ger is not None else None})
        if r.get("egilme_alt"):
            ozet["As_alt_cm2"] = r["egilme_alt"].get("As_gerekli_cm2")
        if r.get("egilme_ust"):
            ozet["As_ust_cm2"] = r["egilme_ust"].get("As_gerekli_cm2")
        if tur_ba == "kolon":
            # yapi._kolon_ba özet alanları (rapor §11.3 / §11.5): N maks/min (birleşim başına alt uç: aks–kat kuralı; iki uç
            # tahkik noktalarında kalır), N_dm ve sınırları, b_X × b_Y (kesitin bina X/Y izdüşümü), yön
            fcd = ts.beton_malzeme(mal["kutuphane"])["fcd"]
            D_ = B.coz.dugum
            alt = "i" if D_[c["i"]]["Z"] <= D_[c["j"]]["Z"] + 1e-9 else "j"
            N_alt = [k["N"] for k in kuv_tum if k["ad"].endswith(f" ({alt})")] or [k["N"] for k in kuv_tum]
            y_, z_ = c["lam"][1], c["lam"][2]
            bX, bY = abs(y_[0]) * kt["h"] + abs(z_[0]) * kt["b"], abs(y_[1]) * kt["h"] + abs(z_[1]) * kt["b"]
            ozet.update({"N_max_kN": max(N_alt), "N_min_kN": min(N_alt),
                         "Ndm_kN": ndm.get("Ndm"), "N_sinir_TBDY_kN": ndm.get("N040"),
                         "N_sinir_TS500_kN": 0.9 * fcd * kt["b"] * kt["h"] * 1000.0, "bX": bX, "bY": bY, "yon": _kolon_yonu(B, c)})
        else:
            # yapi._kiris_ba özet alanları (rapor §11.2 / §11.5): mesnet (üst) ve açıklık (alt) M_d, donatı önerisi, V_d, etriye
            eu, ea, kk = r.get("egilme_ust"), r.get("egilme_alt"), r.get("kesme")
            et = (kk or {}).get("oneri")
            ozet.update({"Md_mesnet": eu["Md_kNm"] if eu else 0.0, "oneri_ust": ((eu or {}).get("oneri") or {}).get("metin"),
                         "Md_aciklik": ea["Md_kNm"] if ea else 0.0, "oneri_alt": ((ea or {}).get("oneri") or {}).get("metin"),
                         "Vd": kk["Vd_kN"] if kk else 0.0, "etriye": f"Φ{et['cap']}/{et['s_mm'] / 10:.0f}" if et else None,
                         "d_m": kt["h"] - (pas + Y._PAS_EK), "b": kt["b"], "h": kt["h"]})
        uy += list(r["uyarilar"])
        T.sonuclar[c["no"]] = {"r": r, "bilgi": bilgi}
        durum = r["durum"] if r["durum"] in ("yeterli", "donatı artır", "kesit büyüt") else "yeterli"
        boyut_eksenel = any(not x["saglandi"] and x["_etiket"] in ("boyut", "eksenel (0,9 fcd Ac)", "TBDY Ndm ≤ 0,40 fck Ac")
                            for x in kont)
        if tur_ba == "kolon":                       # yapi._kolon_ba ile aynı durum kuralı
            dc_k = max(x["dc"] for x in kont)
            durum = ("kesit büyüt" if boyut_eksenel or (dc_k > 1.0 + 1e-9 and rho_ger is None)
                     else ("donatı artır" if dc_k > 1.0 + 1e-9 else "yeterli"))
        elif boyut_eksenel:
            durum = "kesit büyüt"
    else:
        raise MatrisHatasi(f"Kesit {c['kesit']!r}: malzeme {mal['tur']} ile eleman tahkiki yok (çelik ya da beton olmalı).")
    for x in kont:
        if len(x["kaynak"]) > 110:
            x["kaynak"] = x["kaynak"][:107] + "…"
    k = Y._kayit_kur(c["tur"], kayit, kb, fe, kont, durum, ozet)
    _belirleyen_once(k, kont)
    k["kontroller"] = k["kontroller"][:6]
    k.update({"cubuk": c["no"], "grup": c.get("grup"), "L": _r(L), "varsayimlar": varsayim, "kaynak": c.get("kaynak")})
    return k, uy, {}


def _kolon_As(B, kt, ks, c):
    """Kolon boyuna donatısı kesitte verilmişse (yapi._kolon_ba ile aynı alanlar): ``As`` (toplam, cm²) ya da ``donati_orani``
    (ρ = As/Ac) → As (cm²); verilmemişse None (tasarim ρ = 0,01 … 0,04 tarar, gerekli ρ ile). Kesit önerisi kartında
    (``kt_yerine``) alanlar kartın kendisindedir; öteki kartlarda bina girdisindeki kesit kaydından okunur."""
    ad = ks["temel"] if ks.get("tip") == "vute" else c["kesit"]
    ham = kt if any(kt.get(a) is not None for a in ("As", "donati_orani")) else ((B.ham.get("kesitler") or {}).get(ad) or {})
    if not isinstance(ham, dict):
        return None
    Ac_cm2 = kt["b"] * kt["h"] * 1e4
    if ham.get("As") is not None:
        return Y._sayi(ham["As"], f"Kesit {ad!r}: As (toplam boyuna donatı, cm²)", pozitif=True, sifir_olur=False)
    if ham.get("donati_orani") is not None:
        rho = Y._sayi(ham["donati_orani"], f"Kesit {ad!r}: donati_orani (ρ = As/Ac)", pozitif=True, sifir_olur=False)
        if rho >= 0.2:
            raise MatrisHatasi(f"Kesit {ad!r}: donati_orani = {rho} çok büyük; oran girilir (%1 → 0.01).")
        return rho * Ac_cm2
    return None


# betonarme dayanım satırları (beyaz liste; satır adının önekleri atılmış kısmında aranır: _kontrol_kuyrugu). Geri kalan her satır — donatı
# oranı sınırları, en az etriye, etriye/çubuk aralığı, boyut alt sınırları, |N_d| ≤ 0,1 f_ck A_c eğilme elemanı koşulu — yönetmelik
# koşuludur (kosul): yalnız sağlanmadığında D/C'yi belirler (aks–kat motoru yapi._kiris_ba / _kolon_ba ile aynı kural).
_BA_DAYANIM = ("Eğilme taşıma gücü", "Kesme üst sınırı", "Kesme dayanımı", "etkileşim", "İki eksenli", "Nd ≤ 0,9", "Ndm ≤ 0,40",
               "Denk. 7.2")
_BA_ONEKLER = ("Kesme (", "Açıklık (", "Mesnet (")


def _kontrol_kuyrugu(ad_, adlar):
    """tasarim.betonarme_eleman_kontrol satır adından tahkikin kendi adı (sınıflandırma kuyruğu). Atılan önekler: 'N–M: ' ve onu
    izleyen kombinasyon adı + ': ' (``adlar`` uzundan kısaya: en uzun eşleşme), 'Kesme (<kombinasyon>): ', 'Açıklık (…): ',
    'Mesnet (…): '. Tahkik adının kendi içindeki ': ' korunur ('İki eksenli eğilme (Bresler: 1/Nr = …)', 'TBDY: Ndm ≤ …'):
    eskiden son ': ' ekinden bölünüyordu ve Bresler satırı beyaz listeyi kaçırıp sağlanan bir koşul sayılıyordu (D/C dışı)."""
    if ad_.startswith("N–M: "):
        kalan = ad_[len("N–M: "):]
        a = next((a for a in adlar if kalan.startswith(a + ": ")), None)
        return kalan[len(a) + 2:] if a is not None else kalan
    for on in _BA_ONEKLER:
        if ad_.startswith(on):
            a = next((a for a in adlar if ad_.startswith(f"{on}{a}): ")), None)
            if a is not None:
                return ad_[len(on) + len(a) + 3:]
            if "): " in ad_:
                return ad_.split("): ", 1)[1]
    return ad_


def _ba_kontroller(ts, r, kuv_tum, ad_komb, tur_ba, kt, mal, gq_N=None, cikti=None):
    """tasarim.betonarme_eleman_kontrol satırları → §11 satırları: dayanım / koşul ayrımı (beyaz liste), satırın kombinasyonu
    (ad ekinden ya da belirleyen kuvvetten) ve aks–kat motoruyla aynı etiketler. Kolonda (yapi._kolon_ba ile aynı) TBDY en küçük
    boyut ≥ 300 mm (koşul) ve N_dm ≤ 0,40 f_ck A_c (dayanım) satırları: N_dm bütün deprem kombinasyonlarının (ön elemeden önce)
    en büyük N'i; deprem kombinasyonu yoksa G + Q (``gq_N``). ``cikti`` (sözlük) verilirse kolonda kullanılan N_dm, kaynağı
    ("deprem" | "G+Q" | "bütün") ve 0,40 f_ck A_c sınırı yazılır (rapor özeti ve kesit önerisi aynı N_dm'i kullanır)."""
    eg = [x for x in r.get("kombinasyonlar") or [] if x.get("yol") == "eğilme"]
    k_acik = max((x for x in eg if x["Mx"] > 0), key=lambda x: x["Mx"], default=None)
    k_mes = min((x for x in eg if x["Mx"] < 0), key=lambda x: x["Mx"], default=None)
    k_N = max(eg, key=lambda x: abs(x["N"]), default=None)
    adlar = sorted(ad_komb, key=len, reverse=True)
    ndm_satiri = tur_ba == "kolon"

    def komb(x):
        return ad_komb.get(x["ad"], x["ad"]) if x is not None else None

    kont = []
    for x in r["kontroller"]:
        ad_ = x["ad"]
        kuyruk = _kontrol_kuyrugu(ad_, adlar)
        if ndm_satiri and "Ndm ≤ 0,40" in kuyruk:
            continue                                   # aşağıda bütün deprem kombinasyonlarından tek satır
        dayanim = any(s in kuyruk for s in _BA_DAYANIM)
        kb_ = None
        if ad_.startswith("N–M: "):
            kalan = ad_[len("N–M: "):]
            kb_ = next((ad_komb[a] for a in adlar if kalan.startswith(a + ": ")), None)
        elif ad_.startswith("Kesme ("):
            kb_ = next((ad_komb[a] for a in adlar if ad_.startswith(f"Kesme ({a}): ")), None)
        elif ad_.startswith("Açıklık"):
            kb_ = komb(k_acik)
        elif ad_.startswith("Mesnet"):
            kb_ = komb(k_mes)
        elif "Eğilme elemanı koşulu" in ad_:
            kb_ = komb(k_N)
        if "etkileşim" in kuyruk or "İki eksenli" in kuyruk:
            et = "N–M"
        elif "Nd ≤ 0,9" in kuyruk:
            et = "eksenel (0,9 fcd Ac)"
        elif "Ndm ≤ 0,40" in kuyruk:
            et = "TBDY Ndm ≤ 0,40 fck Ac"
        elif "Eğilme taşıma gücü" in kuyruk:
            et = "eğilme (açıklık, alt)" if ad_.startswith("Açıklık") else "eğilme (mesnet, üst)"
        elif "Kesme dayanımı" in kuyruk:
            et = "kesme"
        elif "Kesme üst sınırı" in kuyruk:
            et = "kesme (üst sınır)"
        elif "ρ" in kuyruk and ad_.startswith("N–M"):
            et = "donatı oranı"
        elif x.get("birim") == "mm" and "aralığı" not in kuyruk:
            et = "boyut"
        else:
            et = ad_
        kont.append(Y._kontrol_kaydi(x, kb_, ad_, et, kosul=not dayanim))
    if ndm_satiri:
        bm = ts.beton_malzeme(mal["kutuphane"])
        Ac = kt["b"] * kt["h"]
        N040 = 0.40 * bm["fck"] * Ac * 1000.0
        if not any("en küçük boyutu ≥ 300" in x["ad"] for x in kont):
            kont.append(Y._yeni_kontrol("TBDY: kolon en küçük boyutu ≥ 300 mm", 300.0, min(kt["b"], kt["h"]) * 1000.0,
                                        ts.K_TS500["kolon_boyut_tbdy"], "mm", etiket="boyut", kosul=True))
        dep = [k for k in kuv_tum if k.get("deprem")]
        if dep:
            pdm = max(dep, key=lambda k: k["N"])
            Ndm, kdm, not_ = pdm["N"], ad_komb.get(pdm["ad"], pdm["ad"]), ""
        elif gq_N is not None:
            Ndm, kdm, not_ = gq_N, "G+Q", "; deprem durumu yok: Ndm ≈ G + Q (E = 0)"
        else:
            pdm = max(kuv_tum, key=lambda k: k["N"], default=None)
            Ndm, kdm = (pdm["N"], ad_komb.get(pdm["ad"], pdm["ad"])) if pdm else (0.0, None)
            not_ = "; deprem kombinasyonu yok: bütün kombinasyonlar"
        kont.append(Y._yeni_kontrol("TBDY: Ndm ≤ 0,40 fck Ac", max(Ndm, 0.0), N040, ts.K_TS500["N040"] + not_, "kN", kdm,
                                    "TBDY Ndm ≤ 0,40 fck Ac"))
        if cikti is not None:
            cikti.update({"Ndm": max(Ndm, 0.0), "N040": N040, "kombinasyon": kdm,
                          "kaynak": "deprem" if dep else ("G+Q" if gq_N is not None else "bütün")})
    return kont


def _belirleyen_once(k, kont):
    """Eleman D/C'sini belirleyen satırı (``_kayit_kur`` kuralı: dayanım satırları ve sağlanmayan koşullar arasında en büyük D/C)
    kontrol listesinin başına alır; yanıt kısaltmasında (ilk 6 / 3 satır) kaybolmaz. Liste dışında kaldıysa yeniden eklenir."""
    if not kont:
        return k
    etkin = [x for x in kont if not x["kosul"] or not x["saglandi"]] or kont
    en = max(etkin, key=lambda x: x["dc"])
    satir = {a: v for a, v in en.items() if a[0] != "_" and (a != "kosul" or v)}
    liste = k["kontroller"]
    i = next((j for j, x in enumerate(liste) if x == satir), None)
    if i is None:
        liste.insert(0, satir)
    elif i:
        liste.insert(0, liste.pop(i))
    return k


def _tasarim(ts, T):
    B = T.B
    kayitlar, uyarilar = [], {}
    if T.kombs:
        for c in B.cubuklar:
            try:
                k, uy, _ = _cubuk_tasarla(ts, T, c)
            except MatrisHatasi as h:
                k = {"no": c["no"], "cubuk": c["no"], "tur": c["tur"], "kat": c["kat"], "adres": f"Ç{c['no']} ({_tur_adi(c['tur'])})", "kesit": c["kesit"],
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
    # varsayımlar modelde bulunan sisteme göre (rapor §11.1 betonarme + ortak, §12.1 çelik + ortak; aks–kat motoru gibi):
    # yalnız betonarme modelde ÇYTHYE / burkulma / kren satırları, yalnız çelik modelde TS 500 satırı yazılmaz
    sistemler = {k.get("sistem") for k in kayitlar}
    celik_var, ba_var = "celik" in sistemler, "betonarme" in sistemler
    if not (celik_var or ba_var):                # hiçbir eleman tahkik edilemedi: malzemeden
        mal_tur = {B.malzemeler[B.kesitler[c["kesit"]].get("malzeme")]["tur"] for c in B.cubuklar
                   if B.kesitler.get(c["kesit"], {}).get("malzeme") in B.malzemeler}
        celik_var, ba_var = "celik" in mal_tur, "beton" in mal_tur
    gruplar = {"celik": [], "betonarme": [], "ortak": []}
    if celik_var:
        gruplar["celik"] += [
            "Çelik: ÇYTHYE 2018 " + ("GKT" if B.kombinasyon_kumesi == "cythye_gkt" else "YDKT") + "; kolon, kiriş, aşık, kren ve bağ "
            "kirişi I/H kesitlerde eğilmeli eleman (Bölüm 11 etkileşim), çapraz ve makas çubukları ile basit kesitler (kutu, boru, "
            "korniyer, U) eksenel çubuk (Bölüm 7–8). Kombinasyon başına eleman boyunca en büyük |N|, |M|, |V| (aynı kombinasyon).",
            "Varsayılan burkulma ve yanal burulma boyları (çubukta Lb / K verilmezse): " + ("; ".join(ks_varsayim) or "—") + ". İkinci "
            "mertebe etkileri (B1/B2) yok; yanal ötelemesi önlenmemiş çerçeve kolonunda K > 1 olabilir — çubuğa K verin."]
        if B.kren:
            gruplar["celik"].append("Kren kirişi: yanal kuvvet momenti yalnız üst başlıkça taşınır (öğretici yaklaşım); yorulma ve "
                                    "tekerlek yerel basıncı yok.")
    if ba_var:
        gruplar["betonarme"].append(
            "Betonarme: TS 500 (eğik eleman: |N_d| ≤ 0,1 f_ck A_c ise kiriş gibi, değilse N–M), TBDY sınırları deprem varsa; donatı "
            "ağırlık merkezi = paspayı + 20 mm. Kolon: her birleşimin iki ucundaki eş zamanlı (N, Mx, My) noktaları; TBDY N_dm = "
            "deprem birleşimlerindeki en büyük N (deprem yoksa G + Q).")
        if any(k.get("sistem") == "betonarme" and k["tur"] == "kolon" and (k.get("ozet") or {}).get("rho_varsayim") for k in kayitlar):
            gruplar["betonarme"].append("Kolon boyuna donatısı kesitte (donati_orani ya da As, cm²) verilmediyse ρ = %1 (TS 500 md. "
                                        "7.4.1 / TBDY 2018 md. 7.3.2 en az değeri); 'gerekli ρ' 0,01 → 0,04 taranır.")
    gruplar["ortak"].append(f"Tahkik kombinasyonları: dayanım ve deprem birleşimleri ({len(T.kombs)} adet); servis ve öteleme "
                            "birleşimleri tahkike girmez.")
    varsayimlar = gruplar["celik"] + gruplar["betonarme"] + gruplar["ortak"]
    return {
        "yontem": {"betonarme": "TS 500:2000 (+TBDY 2018 Bölüm 7 sınırları)",
                   "celik": f"ÇYTHYE 2018 {'GKT' if B.kombinasyon_kumesi == 'cythye_gkt' else 'YDKT'} (+TBDY 2018 Bölüm 9 çapraz koşulları)"},
        "varsayimlar": varsayimlar, "varsayim_gruplari": gruplar, "kombinasyon_sayisi": len(T.adlar), "elemanlar": kayitlar,
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
_ONER_DOGRULAMA = 12      # öneri kaydın bütün kurallarıyla yetmezse denenen en çok üst profil / büyük kesit sayısı


def _oner_cubuk(ts, T, c, dc_kayit=None):
    """Tek çubuk için öneri (C4): çelikte aynı aileden D/C ≤ 1 en hafif profil (tasarim.celik_kesit_oner, aynı iç kuvvetlerle),
    betonarmede tasarim.betonarme_kesit_oner. ``dc_once``: §11 kaydının D/C'si (``dc_kayit``; tasarım tablosundaki değer),
    ``dc_oneri``: önerilen kesitle aynı kuralla (_cubuk_tasarla → kayıt D/C'si: sağlanan koşul satırları hariç). Dönüş {cubuk, tur,
    kesit, oneri, sistem, malzeme, b, h, kaynak, gerekce, dc_once, dc_oneri, degisim, ...}; ``uygula`` kesit_oner'de eklenir."""
    B = T.B
    if dc_kayit is None or c["no"] not in T.sonuclar:
        k0, _, _ = _cubuk_tasarla(ts, T, c)
        dc_kayit = k0["dc"] if dc_kayit is None else dc_kayit
    s = T.sonuclar[c["no"]]
    bilgi = s["bilgi"]
    ks = B.kesitler[c["kesit"]]
    kt = B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
    out = {"cubuk": c["no"], "tur": c["tur"], "kesit": c["kesit"], "dc_once": _r5(min(dc_kayit, 99.0)) if dc_kayit is not None else None,
           "grup": c.get("grup"), "kaynak": c.get("kaynak"), "oneri": None, "dc_oneri": None, "degisim": None,
           "sistem": "betonarme" if bilgi.get("kontrol") == "betonarme" else "celik", "malzeme": kt.get("malzeme"),
           "b": kt.get("b") if kt.get("tip") == "dikdortgen" else None, "h": kt.get("h") if kt.get("tip") == "dikdortgen" else None}

    def kayit_dc(kart):
        """Önerilen kartla aynı iç kuvvetlerle §11 kaydının D/C'si (T.sonuclar korunur)."""
        eski = T.sonuclar.get(c["no"])
        try:
            k2, _, _ = _cubuk_tasarla(ts, T, c, kt_yerine=kart)
            return k2["dc"]
        except MatrisHatasi:
            return None
        finally:
            if eski is not None:
                T.sonuclar[c["no"]] = eski

    if bilgi.get("kontrol") in ("eleman", "cubuk"):
        aile = kt.get("aile")
        if not aile:
            out.update({"gerekce": ["Kesit ailesi belirlenemedi."]})
            return out
        p = {"L": bilgi["L"], "K": tuple(bilgi["K"]), "kontrol": bilgi["kontrol"],
             "yontem": bilgi["yontem"]}
        if bilgi["kontrol"] == "eleman":
            p.update({"Lb": bilgi["Lb"], "kren": bilgi.get("kren", False), "Cb": bilgi.get("Cb", 1.0)})
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
        ayni = oneri is not None and oneri.replace(" ", "").upper() == str(kt["profil"]).replace(" ", "").upper()
        degisim = o["degisim"] if oneri == o["oneri"] else None
        if ayni:
            degisim = "aynı"
        elif oneri is not None and degisim is None:
            g0 = kt.get("g_kg")
            degisim = "aynı" if not g0 or agr is None or abs(agr - g0) < 1e-9 else ("büyüt" if agr > g0 else "küçült")
        def profil_dc(ad_p):
            try:
                kart = _kesit_kart("__oneri__", {"tip": "profil", "profil": ad_p, "malzeme": kt["malzeme"]}, B)
            except MatrisHatasi:
                return None
            return kayit_dc(kart)

        dc_oneri = None
        durum = o["durum"] if oneri == o["oneri"] else "aile değişti"
        if oneri is not None:
            dc_oneri = dc_kayit if ayni else profil_dc(oneri)
            if dc_oneri is not None and dc_oneri > 1.0 + 1e-9 and not ayni:
                # tarama tek parametre takımıyla yapılır (ör. döşemeli kirişte belirleyen moment bölgesinin L_b'si); kaydın bütün
                # kurallarıyla (iki moment bölgesi, kren, TBDY) yetmeyen öneri verilmez: aynı ailede bir sonraki ağır profiller denenir
                ilk, ilk_dc = oneri, dc_oneri
                bulundu = None
                try:
                    aile_o = ts._aile_coz(oneri)[0]
                    liste = ts._aile_listesi(aile_o)
                except (AttributeError, KeyError, MatrisHatasi):
                    liste = []
                adlar = [a for a, _ in liste]
                n_ilk = next((i for i, a in enumerate(adlar) if a.replace(" ", "").upper() == ilk.replace(" ", "").upper()), None)
                for ad_p, g_p in (liste[n_ilk + 1:n_ilk + 1 + _ONER_DOGRULAMA] if n_ilk is not None else []):
                    ayni_p = ad_p.replace(" ", "").upper() == str(kt["profil"]).replace(" ", "").upper()
                    d_p = dc_kayit if ayni_p else profil_dc(ad_p)
                    if d_p is not None and d_p <= 1.0 + 1e-9:
                        bulundu = (ad_p, g_p, d_p, ayni_p)
                        break
                if bulundu is not None:
                    oneri, agr, dc_oneri, ayni = bulundu
                    g0 = (o.get("mevcut") or {}).get("agirlik_kg_m") or kt.get("g_kg")
                    degisim = "aynı" if ayni else (("büyüt" if agr > g0 else "küçült") if g0 else None)
                    durum = "doğrulandı (bir üst profil)"
                    gerekce.append(f"{ilk} kaydın bütün kurallarıyla yetersiz (D/C = {_f(ilk_dc, 3)} > 1: ör. döşemeli kirişte negatif "
                                   f"moment bölgesi L_b = boy); aynı iç kuvvetlerle D/C ≤ 1 sağlayan ilk profil {oneri} "
                                   f"(D/C = {_f(dc_oneri, 3)}).")
                else:
                    gerekce.append(f"{ilk} kaydın bütün kurallarıyla yetersiz (D/C = {_f(ilk_dc, 3)} > 1) ve ailede sonraki "
                                   f"{_ONER_DOGRULAMA} profil de yetmedi: öneri yok.")
                    oneri = agr = dc_oneri = degisim = None
                    durum = "ailede yeterli profil yok"
            elif dc_oneri is None:          # kart kurulamadı: tasarim'ın ham D/C'si (koşul satırları dahil, güvenli yanda)
                dc_oneri = dc_o
        out.update({"oneri": oneri, "profil": kt["profil"], "dc_oneri": _r5(min(dc_oneri, 99.0)) if dc_oneri is not None else None,
                    "agirlik_kg_m": agr, "gerekce": gerekce, "degisim": degisim, "durum": durum, "aile": aile})
        if ayni:
            out["gerekce"].append("Mevcut kesit en hafif yeterli kesit (değişiklik yok).")
        return out
    if bilgi.get("kontrol") == "betonarme":
        tur = bilgi["tur"]
        kuv = [{k_: v for k_, v in k.items() if k_ in ("ad", "N", "Mx", "My", "V", "deprem")} for k in bilgi["kuvvetler"]]
        # öneri, tahkikle aynı donatı ağırlık merkezi derinliğiyle (paspayı + etriye + çubuk yarıçapı = pas + 20 mm; tasarim'ın
        # kiriş varsayılanı 40 mm, kolon 50 mm) — yoksa önerilen kesit kendi tahkikinde yetmeyebilir
        kis = {"paspayi": float(bilgi.get("pas", 0.03)) + Y._PAS_EK}
        # TBDY 7.3.1.2 boyutlandırması, kaydın 'Ndm ≤ 0,40 fck Ac' satırıyla aynı N_dm ile (bütün deprem birleşimlerinin en büyüğü,
        # ön elemeden önce; deprem birleşimi yoksa G + Q). Eskiden deprem yokken gerekçe 'N_dm = 0 → A_c ≥ 0 cm²' derdi.
        ndm = {"Ndm": bilgi["N_dm"], "Ndm_kaynak": bilgi.get("N_dm_kaynak")} if (tur == "kolon" and bilgi.get("N_dm") is not None) else {}
        o = ts.betonarme_kesit_oner(tur, kuv, bilgi["malzeme"], mevcut_b=bilgi["b"], mevcut_h=bilgi["h"], kisitlar=kis, **ndm)
        on = o.get("oneri") or {}
        gerekce = list(o.get("gerekce", []))
        durum = o.get("durum")
        dc_oneri = degisim = None

        def kart(on_):
            """Önerilen b × h kartı; kolonda önerinin gerekli boyuna donatı oranıyla (tasarım tablosu, kesit tanımı gibi:
            aks–kat motoru verilmeyen ρ'yu 0,01 alır)."""
            k_ = dict(kt, b=on_["b"], h=on_["h"])
            if tur == "kolon":
                k_.update({"donati_orani": on_.get("rho") or Y._RHO_VARSAYILAN, "As": None})
            return k_

        As0 = _kolon_As(B, kt, ks, c) if tur == "kolon" else None
        rho0 = As0 / (kt["b"] * kt["h"] * 1e4) if As0 else Y._RHO_VARSAYILAN

        def dc_ayni(on_):
            """Kesit aynı: kaydın D/C'si; kolonda öneri daha çok boyuna donatı istiyorsa o donatıyla (b × h değişmez)."""
            if tur == "kolon" and (on_.get("rho") or Y._RHO_VARSAYILAN) > rho0 + 1e-9:
                return kayit_dc(kart(on_))
            return dc_kayit

        if on.get("b"):
            ayni = abs(on["b"] - kt["b"]) < 1e-9 and abs(on["h"] - kt["h"]) < 1e-9
            dc_oneri = dc_ayni(on) if ayni else kayit_dc(kart(on))
            ilk = (on["b"], on["h"], dc_oneri)
            for _ in range(_ONER_DOGRULAMA):
                # kaydın bütün kurallarıyla (koşul satırları, kesme, TBDY) yetmiyor: bir adım büyük kesit (kiriş h, kolon en küçük boyut)
                if ayni or dc_oneri is None or dc_oneri <= 1.0 + 1e-9:
                    break
                if tur == "kiris":
                    kis["h_min"] = on["h"] + 0.05
                else:
                    kis["b_min"] = min(on["b"], on["h"]) + 0.05
                try:
                    o2 = ts.betonarme_kesit_oner(tur, kuv, bilgi["malzeme"], mevcut_b=bilgi["b"], mevcut_h=bilgi["h"], kisitlar=kis,
                                                 **ndm)
                except MatrisHatasi:
                    break
                on2 = o2.get("oneri") or {}
                if not on2.get("b"):
                    break
                on = on2
                ayni = abs(on["b"] - kt["b"]) < 1e-9 and abs(on["h"] - kt["h"]) < 1e-9
                dc_oneri = dc_ayni(on) if ayni else kayit_dc(kart(on))
            if (on["b"], on["h"]) != ilk[:2]:
                if dc_oneri is not None and dc_oneri <= 1.0 + 1e-9:
                    gerekce.append(f"{_f(ilk[0] * 1000, 0)} × {_f(ilk[1] * 1000, 0)} mm kaydın bütün kurallarıyla yetersiz (D/C = "
                                   f"{_f(ilk[2], 3)} > 1); D/C ≤ 1 sağlayan ilk büyük kesit {_f(on['b'] * 1000, 0)} × "
                                   f"{_f(on['h'] * 1000, 0)} mm (D/C = {_f(dc_oneri, 3)}).")
                    durum = "doğrulandı (bir üst kesit)"
            if dc_oneri is not None and dc_oneri > 1.0 + 1e-9 and not ayni:
                gerekce.append(f"Önerilen {_f(on['b'] * 1000, 0)} × {_f(on['h'] * 1000, 0)} mm kaydın bütün kurallarıyla yetersiz "
                               f"(D/C = {_f(dc_oneri, 3)} > 1): öneri yok.")
                on, dc_oneri, durum = {}, None, "yeterli kesit bulunamadı"
            else:
                A0, A1 = kt["b"] * kt["h"], on["b"] * on["h"]
                degisim = "aynı" if ayni else ("büyüt" if A1 > A0 + 1e-12 else ("küçült" if A1 < A0 - 1e-12 else
                                                                                   ("büyüt" if on["h"] > kt["h"] else "küçült")))
                rho_on = on.get("rho") or Y._RHO_VARSAYILAN
                if ayni and tur == "kolon" and rho_on > rho0 + 1e-9:
                    # b × h yeterli ama mevcut boyuna donatıyla değil (K1 "donatı"): kesit tanımına gerekli ρ yazılır (uygula null değil)
                    degisim = "donatı"
                    gerekce.append(f"Değişiklik yalnız boyuna donatıda: ρ = {_f(rho0, 4)} → {_f(rho_on, 4)} (b × h aynı); kesit "
                                   f"tanımına donati_orani = {_f(rho_on, 4)} yazılır.")
        out.update({"oneri": (f"{_f(on['b'] * 100, 0)}x{_f(on['h'] * 100, 0)}" if on.get("b") else None), "b": on.get("b"), "h": on.get("h"),
                    "b_once": kt["b"], "h_once": kt["h"], "dc_oneri": _r5(min(dc_oneri, 99.0)) if dc_oneri is not None else None,
                    "degisim": degisim, "gerekce": gerekce, "durum": durum,
                    "donati": kt.get("donati"), "pas": kt.get("pas")})
        if tur == "kolon" and on.get("b"):
            # gerekli boyuna donatı oranı (ρ > 0,01 ise — "donatı" değişiminde her zaman — uygula tanımına yazılır: aks–kat motoru
            # verilmeyen ρ'yu 0,01 alır); rho_once: mevcut kesitin oranı (verilmemişse 0,01)
            out["donati_orani"] = round(float(on.get("rho") or Y._RHO_VARSAYILAN), 6)
            out["rho_once"] = round(float(rho0), 6)
        return out
    out.update({"gerekce": ["Bu çubuk için öneri yok."]})
    return out


def _agirlik(o):
    if o.get("sistem") == "celik":
        return o.get("agirlik_kg_m") or 0.0
    return (o.get("b") or 0.0) * (o.get("h") or 0.0)


def _oneri_kesit(kes, kesit, en):
    """Önerinin bina kesitlerindeki karşılığı (kes: bina JSON ``kesitler`` sözlüğü; YERİNDE eklenir): (ad, tanım, yeni, ek). Çelik:
    profil adı ("IPE330"; adı başka profile ayrılmışsa ad-malzeme); vute çubuğunda temel profili değişen yeni vute kartı
    "<VUTE>-<IPE330>" (temel profil kartı da ``ek``te); betonarme "B30x50". Değişiklik yoksa (aynı kesit) ad == kesit."""
    eski = kes.get(kesit) or {}
    ek = {}
    if en["sistem"] == "celik":
        ad = en["oneri"].replace(" ", "")
        if eski.get("tip") == "vute":
            temel = str(eski.get("temel"))
            yeni_temel = ad if ad != (kes.get(temel) or {}).get("profil", "").replace(" ", "") else temel
            if yeni_temel not in kes:
                kes[yeni_temel] = {"tip": "profil", "profil": en["oneri"], "malzeme": en["malzeme"]}
                ek[yeni_temel] = kes[yeni_temel]
            ad = f"{kesit}-{yeni_temel}" if yeni_temel != temel else kesit
            yeni = ad not in kes
            if yeni:
                kes[ad] = dict(eski, temel=yeni_temel)
            return ad, kes[ad], yeni, ek
        if ad in kes and (kes[ad].get("profil", "").replace(" ", "") != ad or kes[ad].get("malzeme") != en["malzeme"]):
            ad = f"{ad}-{en['malzeme']}"
        yeni = ad not in kes
        kes.setdefault(ad, {"tip": "profil", "profil": en["oneri"], "malzeme": en["malzeme"]})
        return ad, kes[ad], yeni, ek
    ad = f"B{_f(en['b'] * 100, 0)}x{_f(en['h'] * 100, 0)}"
    rho = en.get("donati_orani")
    donati_degisimi = en.get("degisim") == "donatı"
    # kolon: gerekli ρ > 0,01 kesitte yazılır; yalnız donatı değişiminde (b × h aynı) her zaman
    rho = rho if rho is not None and (rho > Y._RHO_VARSAYILAN + 1e-9 or donati_degisimi) else None
    if rho is not None:
        ad += f"-ρ%{rho * 100:.2f}"
    if donati_degisimi and rho is not None and eski and str(eski.get("tip", "dikdortgen")).strip().lower() == "dikdortgen":
        # K1 "donatı": mevcut kart + donati_orani (As verilmişse düşer: ρ yeni toplam donatıyı tanımlar)
        tanim = {a: v for a, v in eski.items() if a not in ("As", "donati_orani")}
        tanim.update({"tip": "dikdortgen", "donati_orani": rho})
        for a in ("b", "h", "malzeme"):
            tanim.setdefault(a, en[a])
    else:
        tanim = {"tip": "dikdortgen", "b": en["b"], "h": en["h"], "malzeme": en["malzeme"],
                 **({"donati": en["donati"]} if en.get("donati") else {}), **({"pas": en["pas"]} if en.get("pas") else {}),
                 **({"donati_orani": rho} if rho is not None else {})}
    if ad in kes and any(kes[ad].get(a) != tanim.get(a) for a in ("tip", "b", "h", "malzeme", "donati_orani", "As")):
        ad = f"{ad}-{en['malzeme']}"
    yeni = ad not in kes
    kes.setdefault(ad, tanim)
    return ad, kes[ad], yeni, ek


def _uygula_bilgisi(kesitler, o):
    """C4 ``uygula``: {"ad": atanacak kesit adı, "tanim": kesitler girdisi, "yeni": tanım eklenmeli mi, "ek_kesitler": önce eklenecek
    öteki kesitler (vute temel profili)} ya da (öneri yok / değişiklik yok) None. Bina değiştirilmez."""
    if o.get("oneri") is None or o.get("degisim") in (None, "aynı"):
        return None
    kes = copy.deepcopy(kesitler or {})
    ad, tanim, yeni, ek = _oneri_kesit(kes, o["kesit"], o)
    if ad == o["kesit"]:
        return None
    r = {"ad": ad, "tanim": copy.deepcopy(tanim), "yeni": bool(yeni)}
    if ek:
        r["ek_kesitler"] = copy.deepcopy(ek)
    return r


_RHO_ADIM, _RHO_EN_COK = 0.0025, 0.04        # grup boyuna donatı oranı taraması (TBDY 2018 md. 7.3.2.1: ρ ≤ 0,04)


def _rho_kart(k):
    """Kesit kartının (bina JSON kesitler girdisi) boyuna donatı oranı: donati_orani, ya da As/(b·h); verilmemişse 0,01."""
    try:
        if k.get("donati_orani") is not None:
            return float(k["donati_orani"])
        if k.get("As") is not None:
            return float(k["As"]) / (float(k["b"]) * float(k["h"]) * 1e4)
    except (TypeError, ValueError, ZeroDivisionError, AttributeError):
        pass
    return Y._RHO_VARSAYILAN


def _grup_rho(tt, lst, b, h, rho, dc_cikti=None):
    """Betonarme kolon grubu kartının (b × h) boyuna donatı oranı: her üye bu kartla, KENDİ iç kuvvetleriyle §11 kaydının bütün
    kurallarıyla yeniden doğrulanır; D/C > 1 olan üye için ρ 0,0025 adımla artırılır (en çok 0,04). Dönüş (ρ, yetmeyen çubuklar):
    0,04 ile de yetmeyen (boyut / eksenel sınırı, N–M) üyeler ayrıca döner. T.sonuclar korunur. ``dc_cikti`` (sözlük) verilirse
    son ρ ile doğrulanmış üyelerin D/C'leri {çubuk no: dc} yazılır (daha düşük ρ ile doğrulananlar yazılmaz)."""
    ts, T = tt
    B = T.B
    rho = min(max(float(rho), Y._RHO_VARSAYILAN), _RHO_EN_COK)
    yetmeyen = []
    son = {}
    for c in [B.cubuk_no.get(n) for o in lst for n in (o.get("cubuklar") or [o["cubuk"]])]:
        if c is None:
            continue
        ks = B.kesitler[c["kesit"]]
        kt = B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
        eski = T.sonuclar.get(c["no"])
        try:
            while True:
                try:
                    k2, _, _ = _cubuk_tasarla(ts, T, c, kt_yerine=dict(kt, b=b, h=h, donati_orani=rho, As=None))
                    dc = k2["dc"]
                except MatrisHatasi:
                    dc = None
                if dc is not None and dc <= 1.0 + 1e-9:
                    son[c["no"]] = (rho, dc)
                    break
                if rho >= _RHO_EN_COK - 1e-12:
                    yetmeyen.append(c["no"])
                    break
                rho = min(round(rho + _RHO_ADIM, 6), _RHO_EN_COK)
        finally:
            if eski is not None:
                T.sonuclar[c["no"]] = eski
            else:
                T.sonuclar.pop(c["no"], None)
    if dc_cikti is not None:
        dc_cikti.update({no: d for no, (r_, d) in son.items() if abs(r_ - rho) < 1e-12})
    return rho, yetmeyen


def _ba_grup_karti(lst, kesit_karti, tt, kucultme):
    """Betonarme (kesit, tür) grubunun ortak kartı → (en, atla). en: grubun en büyük b × h önerisi (eşitlikte büyük ρ); onarım
    turunda (``kucultme`` False) mevcut b × h'den küçük olamaz. Kolon grubunda ρ ``_grup_rho`` ile seçilir (``tt`` yoksa üyelerin
    aynı b × h önerilerinin en büyük ρ'su); 0,04 ile de yetmeyen üye varsa üyelerin önerilerini (ve onarımda mevcut boyutu) saran
    b × h denenir. Atlama: b, h VE ρ aynıysa."""
    yakin = lambda x, y: x is not None and y is not None and abs(x - y) < 1e-9      # noqa: E731
    en = dict(max(lst, key=lambda o: (_agirlik(o), o.get("donati_orani") or 0.0)))
    b0, h0 = en.get("b_once"), en.get("h_once")
    if not kucultme and b0 and h0 and en["b"] * en["h"] < b0 * h0 - 1e-12:
        en.update({"b": b0, "h": h0})
    kolon = any(o.get("donati_orani") is not None for o in lst)
    rho_eski = _rho_kart(kesit_karti) if kolon else None
    if kolon:
        rho = max([o.get("donati_orani") or Y._RHO_VARSAYILAN for o in lst if yakin(o.get("b"), en["b"]) and yakin(o.get("h"), en["h"])]
                  or [Y._RHO_VARSAYILAN])
        if not kucultme and yakin(en["b"], b0) and yakin(en["h"], h0):
            rho = max(rho, rho_eski)                    # onarım turunda mevcut donatı da azalmaz
        if tt is not None:
            rho1, yet = _grup_rho(tt, lst, en["b"], en["h"], rho)
            if yet:
                bz = max([o["b"] for o in lst if o.get("b")] + ([b0] if (not kucultme and b0) else []))
                hz = max([o["h"] for o in lst if o.get("h")] + ([h0] if (not kucultme and h0) else []))
                if not (yakin(bz, en["b"]) and yakin(hz, en["h"])):
                    rho2, yet2 = _grup_rho(tt, lst, bz, hz, Y._RHO_VARSAYILAN)
                    if len(yet2) < len(yet):
                        en.update({"b": bz, "h": hz})
                        rho1 = rho2
            rho = rho1
        en["donati_orani"] = round(rho, 6)
    ayni_bh = yakin(en["b"], b0) and yakin(en["h"], h0)
    if ayni_bh and (not kolon or abs(en["donati_orani"] - rho_eski) < 1e-9):
        return en, True
    if ayni_bh:
        en["degisim"] = "donatı"
    elif b0 and h0:
        A0, A1 = b0 * h0, en["b"] * en["h"]
        en["degisim"] = "büyüt" if A1 > A0 + 1e-12 else ("küçült" if A1 < A0 - 1e-12 else ("büyüt" if en["h"] > h0 else "küçült"))
    en["oneri"] = f"{_f(en['b'] * 100, 0)}x{_f(en['h'] * 100, 0)}"
    return en, False


def _oneri_uygula(bina, oneriler, B, tur_tasarim=None, kucultme=True):
    """Önerileri bina JSON'una uygular (kopya). Aynı (kesit, tür) grubundaki çubuklara grubun ortak kartı verilir (kesit sayısı az
    kalsın): çelikte en ağır öneri; betonarmede en büyük b × h ve kolonda üyeler yeniden doğrulanarak seçilen grup ρ'su
    (``_ba_grup_karti``; ``tur_tasarim`` = (tasarim modülü, tasarım bağlamı)). ``kucultme`` False (onarım turu): hiçbir grup
    küçültülmez. Vute çubuğunda temel profili değişen yeni bir vute kesiti yazılır. Dönüş (yeni bina, değişiklikler)."""
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
        eski = kes.get(kesit) or {}
        if lst[0].get("sistem") == "betonarme":
            kart_eski = (kes.get(str(eski.get("temel"))) or {}) if str(eski.get("tip", "")).strip().lower() == "vute" else eski
            en, atla = _ba_grup_karti(lst, kart_eski, tur_tasarim, kucultme)
            if atla:
                continue
        else:
            en = max(lst, key=_agirlik)
            if en.get("degisim") == "aynı" or (not kucultme and en.get("degisim") == "küçült"):
                continue
        ad, _, _, _ = _oneri_kesit(kes, kesit, en)
        if ad == kesit:
            continue
        for o in lst:
            for n in o.get("cubuklar") or [o["cubuk"]]:
                cubuk_kesit[n] = ad
        d = {"kesit": kesit, "tur": tur, "yeni": ad, "oneri": en["oneri"], "degisim": en.get("degisim"),
             "cubuklar": sorted(n for o in lst for n in (o.get("cubuklar") or [o["cubuk"]]))}
        if en.get("donati_orani") is not None and lst[0].get("sistem") == "betonarme":
            d["donati_orani"] = en["donati_orani"]
        degisen.append(d)
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
          gosterilecek, kimlik, kren, yalniz, temel_veri=None):
    S = Y._sonlu
    D = B.coz.dugum
    tk = _temel_kisa(ag.get("temel"))
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
                               for t in akis["temeller"]],
                     **({"surekli": {a: v for a, v in B.temeller["surekli"].items() if a != "kesit"}} if B.temeller["tip"] == "surekli" else {}),
                     **({"radye": dict(B.temeller["radye"])} if B.temeller["tip"] == "radye" else {})},
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
                      "kat": p["kat"], "dagitim": p["dagitim"], "g": _r(p["g_yuzey"]), "q": _r(p["q"] + p["ek_q"]), "s": _r(p["s"] + p["ek_s"]),
                      "mu": _r(p["mu"]), "kullanim": p["kullanim"], "kaynak": p.get("kaynak"),
                      "kenarlar": [{"kenar": k["kenar"], "dugumler": k["dugumler"], "uzunluk": _r(k["L"]), "tasiyan": k["tasiyan"],
                                    "tam": k["tam"], "cubuklar": [x[0] for x in k["parcalar"]]} for k in p["kenarlar"]]}
                     for p in B.paneller],
        "mesnetler": [{"dugum": m["dugum"], "tip": m["tip"], "kaynak": m["kaynak"], **{a: m[a] for a in ("ux", "uy", "uz", "rx", "ry", "rz")},
                       **({"yay": dict(m["yay"])} if m.get("yay") else {})} for m in ag["mesnetler"]],
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
                      "g": _r(p["g_yuzey"]), "q": _r(p["q"] + p["ek_q"]), "s": _r(p["s"] + p["ek_s"]), "mu": _r(p["mu"]),
                      "G_toplam": _r(p["toplam"]["G"]), "Q_toplam": _r(p["toplam"]["Q"]), "S_toplam": _r(p["toplam"]["S"]),
                      "q_kaynak": p["q_kaynak"], "g_kaynak": p["g_kaynak"], "kaynak": p.get("kaynak"),
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
        "mesnetler": [{a: (_r(v) if isinstance(v, float) else v) for a, v in t.items()} for t in akis["mesnetler"]],
        "korunum": {d: {a: _r(v) for a, v in p.items()} for d, p in akis["korunum"].items()},
        "sankey": [dict(s, kN=_r6(s["kN"])) for s in akis["sankey"]],
        **({"sankey_kesildi": dict(akis["sankey_kesildi"])} if akis.get("sankey_kesildi") else {}),
    }
    uyarilar = list(dict.fromkeys(B.uyarilar))
    for p in B.paneller:
        if not p["q_dogrulandi"]:
            uyarilar.append(f"Doğrulanmamış kütüphane değeri kullanıldı: TS498_HAREKETLI.{p['kullanim']} (panel P{p['no']})")
        if not p["g_dogrulandi"]:
            uyarilar.append(f"Doğrulanmamış kütüphane değeri kullanıldı: KAPLAMALAR (panel P{p['no']}): {p['g_kaynak']}")
    uyarilar = list(dict.fromkeys(uyarilar))
    en_dc = max((t.get("DC", 0.0) for t in akis["temeller"]), default=0.0)
    if temel_veri is not None:
        en_dc = max(en_dc, float(temel_veri["DC_zemin"]))
        for u in temel_veri["uyarilar"]:
            uyarilar.append("Temel: " + u)
        if temel_veri["en_buyuk_dc"] > 1.0 + 1e-9:
            uyarilar.append(f"Temel tahkiklerinde en büyük D/C = {temel_veri['en_buyuk_dc']:.2f} > 1 (veri.temel.tasarim).")
    if en_dc > 1.0:
        uyarilar.append(f"En büyük temel taban basıncı oranı D/C = {en_dc:.2f} > 1.")
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
        "durumlar": {ad: Y._kisa_veri(k, diyagram=ad in tam, **tk) for ad, k in cikti_durum.items()},
        "kombinasyonlar": [dict(r, **({"kren": k["kren"]} if k.get("kren") else {}))
                           for r, k in zip(Y._kombinasyon_veri(kombinasyonlar), kombinasyonlar)],
        "kombinasyon_ozet": kmb_ozet, "gosterilecek": list(gosterilecek),
        "sonuclar": {ad: Y._kisa_veri(k, u_dahil=False, **tk) for ad, k in sonuclar.items()},
        "zarf": {"kombinasyonlar": zarf["kombinasyonlar"], "kombinasyon_sayisi": len(zarf["kombinasyonlar"]),
                 "elemanlar": [{a: (_r6(v) if isinstance(v, float) else v) for a, v in z.items()} for z in zarf["elemanlar"]
                               if z["no"] not in tk["ince"]]},
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
        "temel": temel_veri if temel_veri is not None else (_tm().tekil_ozet(akis["temeller"], B.temeller["zemin"]["q_em"]) if _tm() else None),
    }
    return veri


# ============================================================================
# 15) Anlatım
# ============================================================================
def _eylem_dugumleri(yukler):
    """Motor eksenli düğüm yükleri → [{dugum, F: [FX, FY, FZ, MX, MY, MZ]}] (bina eksenleri)."""
    out = []
    for y in yukler:
        F = list(Y._bina_vek((y.get("Fx", 0.0), y.get("Fy", 0.0), y.get("Fz", 0.0)))) + \
            list(Y._bina_vek((y.get("Mx", 0.0), y.get("My", 0.0), y.get("Mz", 0.0))))
        if any(abs(v) > 1e-12 for v in F):
            out.append({"dugum": y["dugum"], "F": [_r(v) for v in F]})
    return out


def _eylemler(durumlar, kaynak, dep):
    """veri.yukler.eylemler (C16): rüzgâr, deprem ve kren durumlarının uygulanan yükleri, bina eksenlerinde. Panel rüzgârında ve
    kren alt durumlarında çubuk yükleri (x çubuğun i ucundan m; yayili q kN/m, tekil P kN, birim vektör vek yönünde) ve düğüm
    yükleri; kat kuvvetli rüzgârda ve EX±/EY±'de düğüm yükleri (rijit diyaframda efendi düğüme kuvvet ve burulma momenti);
    EZ = G_carpani × G (TBDY Denk. 4.10)."""
    out = {}
    for ad, dd in kaynak.items():
        cubuklar = []
        for cno in sorted(dd["cubuk"]):
            yayili, tekil = [], []
            for x1, x2, q1, q2, vek, et in dd["cubuk"][cno]:
                v = [_r(x) for x in vek]
                if et == "kren":           # tekerlek yükü (motorda çok kısa düzgün yük: _tekil_parca) → tekil yük
                    tekil.append({"x": _r((x1 + x2) / 2.0), "P": _r(q1 * (x2 - x1)), "vek": v})
                else:
                    yayili.append({"x1": _r(x1), "x2": _r(x2), "q1": _r(q1), "q2": _r(q2), "vek": v})
            cubuklar.append({"no": cno, "yayili": yayili, "tekil": tekil})
        dug = [{"dugum": n, "F": [_r(v) for v in F]} for n, F in sorted(dd["dugum"].items()) if any(abs(v) > 1e-12 for v in F)]
        out[ad] = {"cubuklar": cubuklar, "dugumler": dug}
    for ad in ("W+X", "W-X", "W+Y", "W-Y", "EX+", "EX-", "EY+", "EY-"):
        if ad in durumlar and ad not in out:
            out[ad] = {"cubuklar": [], "dugumler": _eylem_dugumleri(durumlar[ad]["yukler"])}
    if "EZ" in durumlar and dep is not None:
        out["EZ"] = {"cubuklar": [], "dugumler": [], "G_carpani": _r(2.0 / 3.0 * dep["sp"]["SDS"])}
    return out


def _tablo(b, s):
    return Y._tablo(b, s)


def _anlatim(B, YK, ag, durumlar_kisa, kombinasyonlar, zarf, akis, deprem, ruzgar, kren, yalniz, tas, T, yol, anl, temel=(None, None)):
    anl.baslik(B.baslik, 2)
    if B.aciklama:
        anl.metin(B.aciklama)
    n = [0]

    def adim():          # adım numaraları ardışık (koşullu adımlar — yalnız çekme, kesit tahkikleri — atlanınca boşluk kalmaz)
        n[0] += 1
        return n[0]
    se._basla(anl, adim(), "Aks sistemi, düğümler, çubuklar ve paneller",
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
                                                [[_tur_adi(t), len(lst), ", ".join(sorted({c['kesit'] for c in lst})),
                                                  f"{sum(1 for c in lst if c['serbest']['i'] or c['serbest']['j'])} mafsallı"
                                                  + (f", {sum(1 for c in lst if c['yalniz_cekme'])} yalnız çekme" if any(c['yalniz_cekme'] for c in lst) else "")]
                                                 for t, lst in sorted(turler.items())]))
    if ag["donme_tutulan"]:
        anl.metin(f"Bütün çubuk uçları mafsallı {len(ag['donme_tutulan'])} düğümde dönme serbestlikleri tutuldu: o düğümün dönmesini "
                  "hiçbir çubuk tutmaz (rijitlik matrisinde sıfır satır); dönmeyi sıfırlamak iç kuvvetleri değiştirmez.")
    se._basla(anl, adim(), "Paneller → çubuklar: yük dağıtımı",
              "Döşeme, çatı ve cephe panelleri yüklerini kenarlarındaki çubuklara aktarır. İki doğrultulu panelde her nokta en yakın "
              "kenara gider (açıortay bölgeleri); dikdörtgende bu TS 500 md. 11.4.3'ün 45° kuralıdır: kısa kenara üçgen, uzun kenara "
              "trapez yük. Tek doğrultulu panel yükünü iki karşı kenara yarı yarıya verir. Eğik panelde öz ve sabit yük yüzey alanına, "
              "hareketli yük ve kar yatay izdüşüme göre hesaplanır.")
    anl.mat(r"q(u) = p\cdot d(u),\quad d(u) = \min_f \frac{d_f(A + u\,\mathbf{t})}{1 - \mathbf{n}_f\cdot\mathbf{n}},\qquad "
            r"\textstyle\sum_{\text{kenar}} \int_0^{L} d(u)\,du = A_{panel}")
    sat = []
    for p in B.paneller[:12]:
        sat.append([f"P{p['no']}", p["tur"], p["dagitim"], _f(p["alan"], 2), _f(p["egim"], 1), _f(p["g_yuzey"], 2), _f(p["q"] + p["ek_q"], 2),
                    _f(p["s"] + p["ek_s"], 2), _f(p["toplam"]["G"], 1)])
    if sat:
        anl.metin("**Paneller** (ilk 12; g yüzey alanına, q ve s yatay izdüşüme, kN/m²):\n\n" + _tablo(
            ["Panel", "Tür", "Dağıtım", "Alan (m²)", "Eğim (°)", "g", "q", "s", "G (kN)"], sat))
    anl.metin("**Yük toplamları:** " + ", ".join(f"{d} = {_f(v, 1)} kN" for d, v in YK.toplam.items() if d in YK.durumlar) + ".")
    se._basla(anl, adim(), "Ağ, mesnetler ve diyaframlar",
              "Çubuklar uzay çerçeve elemanlarıdır (her düğümde 6 serbestlik). Uç serbestlikleri (mafsal) eleman rijitliğinde statik "
              "yoğunlaştırmayla uygulanır. En alt Z seviyesindeki (kat 0) aks kesişimleri — ek aks sistemleri dahil — temele oturur "
              "(temeller.mesnet); bölme ve kesişim düğümleri oturmaz, onlara 'mesnetler' listesiyle mesnet verilir.")
    anl.metin(f"{ag['n_kole']} düğüm × 6 = **{ag['sd_sayisi']} SD**, {len(ag['elemanlar'])} sonlu eleman; diyafram: "
              + ", ".join(f"kat {k}: {v['mod']} ({v['neden']})" for k, v in ag["diyafram_mod"].items()) + ".")
    ti = ag.get("temel")
    if ti is not None:            # mütemadi / radye: aks–kat anlatımıyla aynı metin (yapi._adim_6)
        n_tk = sum(1 for e in ti.elemanlar if e["tur"] == "temel-kirisi")
        n_rs = len(ti.elemanlar) - n_tk
        anl.metin(f"**Temel ({'mütemadi' if ti.tip == 'surekli' else 'radye'}):** kot_0'da {len(ti.dugumler)} temel düğümü, "
                  f"{n_tk} temel kirişi parçası" + (f", {n_rs} radye şeridi" if n_rs else "") + ". Kolon tabanları sabit mesnet "
                  "değildir; temel düğümüne bağlanır, her temel düğümünde düşey Winkler yayı k_z = k0·A_etki vardır"
                  + (" ve temel düzlemi içindeki hareketler (X, Y ötelemeleri, düşey eksen etrafında dönme) tutuludur; eğilme "
                     "dönmeleri serbesttir." if ti.yatay == "tutulu" else " ve yatay yaylar vardır.")
                  + f" Temel kirişleri GLOBAL X/Y aksları boyunca (radye: GLOBAL aks zarfı + taşma) kurulur; aks kesişimi dışındaki "
                  f"temel düğümleri {ti.ilk_no}'den numaralanır."
                  + (f" Ek aks sistemindeki taban düğümleri için ızgaraya {ti.BT.sanal} sanal çizgi (x=…, y=…) eklendi." if ti.BT.sanal else "")
                  + " Ayrıntı: 'Temel ve zemin' adımı.")
    se._basla(anl, adim(), "Yük durumları",
              "Her yük türü ayrı bir durumdur; rijitlik matrisi bir kez kurulur, bütün durumlar aynı anda çözülür.")
    anl.metin("Durumlar: " + ", ".join(f"`{d}`" for d in durumlar_kisa) + f". Çözüm yolu: {yol}.")
    if ruzgar and ruzgar.get("yontem") == "panel":
        anl.metin("**Rüzgâr (TS 498:2021 md. 14):** " + ruzgar["kaynak"] + ". " + ruzgar["not"])
    if kren:
        anl.metin(f"**Kren (K):** {len(kren['durumlar'])} alt durum (konum × köprü yönü). " + kren["kaynak"])
    Y._adim_7(B, deprem, anl, no=adim())
    if yalniz:
        se._basla(anl, adim(), "Yalnız çekme çubukları: doğrusal olmayan çözüm", yalniz["aciklama"])
        sat = [[ad, len(v["etkin_degil"]), v["yineleme"]] for ad, v in list(yalniz["kombinasyonlar"].items())[:12]]
        anl.metin(_tablo(["Birleşim", "Devre dışı çubuk", "Yineleme"], sat))
    se._basla(anl, adim(), "Kombinasyonlar ve zarf",
              "Doğrusal çözümde kombinasyon, yük durumlarının katsayılı toplamıdır (yeniden çözüm gerekmez); zarf her kesitte bütün "
              "kombinasyonların en büyük ve en küçük değeridir.")
    uyg = [k for k in kombinasyonlar if k["uygulandi"]]
    anl.metin(f"Kombinasyon kümesi `{B.kombinasyon_kumesi}`: {len(uyg)} uygulanan birleşim"
              + (f" ({sum(1 for k in uyg if k.get('kren'))} kren varyantı)" if kren else "") + ".")
    se._basla(anl, adim(), "Denge ve korunum", "Σ uygulanan düşey yük = Σ mesnet tepkisi (yay kuvvetleri dahil), her durumda.")
    toz = any("temel_oz" in p for p in akis["korunum"].values())
    anl.metin(_tablo(["Durum", "Σ yük (kN)", "Σ tepki (kN)", "Paneller", "Çubuk öz", "Duvar"] + (["Temel öz"] if toz else []) + ["Ek"],
                     [[d, _f(p["toplam"], 2), _f(p["kolon_taban"], 2), _f(p["paneller"], 1), _f(p["cubuk_oz"], 1), _f(p["duvarlar"], 1)]
                      + ([_f(p.get("temel_oz", 0.0), 1)] if toz else []) + [_f(p["ek"], 1)] for d, p in akis["korunum"].items()]))
    if tas is not None:
        se._basla(anl, adim(), "Kesit tahkikleri", "Her çubuk kendi türüne göre tahkik edilir: çelikte ÇYTHYE (eğilmeli eleman ya da "
                  "eksenel çubuk), betonarmede TS 500; çaprazlarda TBDY 2018 Bölüm 9 koşulları.")
        anl.metin("**Varsayımlar:**\n\n" + "\n".join(f"- {v}" for v in tas["varsayimlar"]))
        gec = sorted((k for k in tas["elemanlar"] if k["dc"] is not None), key=lambda k: -k["dc"])
        anl.metin("**En kritik 10 çubuk:**\n\n" + _tablo(
            ["Çubuk", "Kesit", "Kontrol", "Kombinasyon", "D/C", "Durum"],
            [[k["adres"], k["kesit"], k["belirleyen"]["kontrol"], f"`{k['belirleyen']['kombinasyon']}`" if k["belirleyen"]["kombinasyon"] else "–",
              _f(k["dc"], 3), k["durum"]] for k in gec[:10]]))
        for u in tas["uyarilar"][:6]:
            anl.uyari(u)
    if temel[0] is not None:
        _tm().anlatim(anl, adim(), ag["temel"].BT, ag, temel[0], temel[1], toplam_servis=YK.toplam["G"] + YK.toplam["Q"])


# ============================================================================
# 16) Ana işlev
# ============================================================================
def bina_coz(bina, *, goster=None, anlat=True, hafif=False):
    """Genel (surum 3) bina modelini çözer. Dönüş ``mo.Sonuc``: ``.veri`` (yapi.bina_coz şemasıyla uyumlu + genel model alanları:
    ag.cubuklar, ag.paneller, yukler.paneller/cubuklar, akis.mesnetler, kren, yalniz_cekme, bina.seviyeler, uyarilar), ``.ic``
    (tembel kombinasyon, eleman tahkiki, kesit önerisi ve ısı haritası — ``alan`` — için paket). Mütemadi / radye temelde
    veri.temel aks–kat motoruyla aynı şemadadır (temel.py, ``_temel_gorunum`` görünümüyle); tekil temelde temel.tekil_ozet.

    ``hafif=True`` (iç kullanım: kesit önerisinin ``genel_cozum`` ve onarım turu çözümleri, K-31): aynı çözüm ve aynı tasarım
    D/C'leri, ama yalnız {veri: {tasarim}, ic} döner — zarf, gösterilecek birleşimler, akış, temel sonuçları, eylemler, veri ve
    anlatım kurulmaz (``_hafif_sonuc``)."""
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
    if ag.get("temel") is not None:      # temel kirişi / radye öz ağırlığı (G): yapi._yuk_durumlari ile aynı kayıtlar
        _temel_yuk(B, YK, ag["temel"], durumlar["G"])
    ruzgar = None
    eylem_kaynak = {}             # C16: rüzgâr (panel) ve kren alt durumlarının çubuk / düğüm kayıtları (bina eksenleri)
    if B.ruzgar:
        if any(p["ruzgar"] for p in B.paneller):
            wd, ruzgar = _ruzgar_panel(B, YK)
            for ad, dd in wd.items():
                durumlar[ad] = _motor_durum(B, dd["cubuk"], dd["dugum"])
                eylem_kaynak[ad] = dd
        else:
            wd, ruzgar = Y._ruzgar_durumlari(B, ag)
            ruzgar["yontem"] = "kat"
            durumlar.update(wd)
    kren_ozet, kren_adlar = None, []
    if B.kren:
        kd, kren_ozet = _kren_durumlari(B)
        for ad, dd in kd.items():
            durumlar[ad] = _motor_durum(B, dd["cubuk"], dd["dugum"])
            eylem_kaynak[ad] = dd
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
    _yay_turu_yaz(ag, durumlar_kisa.values())
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
    if hafif:
        return _hafif_sonuc(B, YK, ag, model, paket, kombinasyonlar, deprem)
    zarf = Y._zarf_paket(paket, kombinasyonlar)
    ozetler = {k["ad"]: paket.ozet(paket.birlesim(k["cozum"])) for k in kombinasyonlar if k["uygulandi"]}
    gosterilecek = Y._gosterilecek_sec(B, kombinasyonlar, zarf)
    komb_kat = {k["ad"]: k["cozum"] for k in kombinasyonlar if k["uygulandi"]}
    sonuclar = {ad: paket.kisa(paket.birlesim(komb_kat[ad])) for ad in gosterilecek}
    akis = _akis(B, YK, ag, durumlar_kisa)
    kren = _kren_veri(B, paket, kren_ozet, ag) if kren_ozet else None
    kimlik = Y._cozum_kimligi(B)
    temel_veri = temel_ic = None
    if ag.get("temel") is not None:
        temel_veri, temel_ic = _temel_sonuclari(B, ag, paket, kombinasyonlar, YK)
    veri = _veri(B, YK, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol, deprem=deprem, ruzgar=ruzgar,
                 kutle=kutle, ozetler=ozetler, gosterilecek=gosterilecek, kimlik=kimlik, kren=kren, yalniz=yalniz, temel_veri=temel_veri)
    veri["yukler"]["eylemler"] = _eylemler(durumlar, eylem_kaynak, dep)
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
    tas_tam = _boyut_sinirla(veri, durumlar_kisa, temel=ag.get("temel"))
    anl = mo.Anlatim()
    if anlat:
        _anlatim(B, YK, ag, durumlar_kisa, kombinasyonlar, zarf, akis, deprem, ruzgar, kren, yalniz, tas, T, yol, anl,
                 temel=(temel_veri, temel_ic))
    else:
        anl.baslik(B.baslik, 2)
    sonuc = mo.Sonuc(sp.Matrix(kisa_m["G"]["u"]), anl, "u_G", "", "")
    sonuc.veri = veri
    sonuc.ic = {"kimlik": kimlik, "paket": paket, "kombinasyonlar": komb_kat, "durumlar": set(paket.durum), "tasarim": T,
                "serbest": True, "bina": B.ham, "B": B, "tas": tas,
                "temel": _tm().basinc_meta(ag["temel"]) if ag.get("temel") is not None else None, "oteleme_asan": _oteleme_asan(deprem),
                # alan.py (ısı haritası, eleman bilgisi): yapi.bina_coz ile aynı paket — normalize bina, ağ, motor modeli, yükler,
                # tasarım sonucu (yanıtta kısaltıldıysa tam satırlar: betonarme kullanımı kapasite satırlarını arar), kombinasyon türleri
                "alan": {"B": B, "ag": ag, "model": model, "Y": YK, "tasarim": tas_tam if tas_tam is not None else tas,
                         "komb_tur": {k["ad"]: k["tur"] for k in kombinasyonlar if k["uygulandi"]}}}
    if tas_tam is not None:      # yanıtta kontrol satırları kısaltıldı: rapor bütün satırları bundan yazar (köprü bina_rapor)
        sonuc.ic["tas_tam"] = tas_tam
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc


def _hafif_sonuc(B, YK, ag, model, paket, kombinasyonlar, deprem):
    """bina_coz(hafif=True) dönüşü: kesit önerisinin ara çözümleri için tasarım (aynı D/C'ler) ve öteleme paketi (``ic`` tam
    çözümün paketiyle aynı anahtarlar; veri yalnız {tasarim})."""
    ts = _tasarim_mod()
    T = tas = None
    if ts is not None:
        T = _tasarim_baglam(B, ag, paket, kombinasyonlar)
        tas = _tasarim(ts, T)
    ic = {"kimlik": Y._cozum_kimligi(B), "paket": paket, "durumlar": set(paket.durum), "tasarim": T, "serbest": True,
          "bina": B.ham, "B": B, "tas": tas, "oteleme_asan": _oteleme_asan(deprem), "deprem": deprem, "hafif": True,
          "kombinasyonlar": {k["ad"]: k["cozum"] for k in kombinasyonlar if k["uygulandi"]},
          "temel": _tm().basinc_meta(ag["temel"]) if ag.get("temel") is not None else None,
          "alan": {"B": B, "ag": ag, "model": model, "Y": YK, "tasarim": tas,
                   "komb_tur": {k["ad"]: k["tur"] for k in kombinasyonlar if k["uygulandi"]}}}
    return SimpleNamespace(veri={"tasarim": tas}, ic=ic)


def _oteleme_asan(deprem):
    """Göreli kat ötelemesi sınırını (TBDY 2018 md. 4.9.1) aşan katlar {"x": [kat], "y": [kat]} (deprem yoksa boş listeler).
    Kesit önerisi (``kesit_oner`` yinele) öneriden önceki ve sonraki çözümü karşılaştırır: öneriler yalnız D/C'ye göre seçilir."""
    katlar = (deprem or {}).get("katlar") or []
    return {y: [s["kat"] for s in katlar if s.get(f"uygun_{y}") is False] for y in ("x", "y")}


EYLEMLER_NOTU = "Yanıt boyutu sınırı: rüzgâr/deprem/kren eylemleri yazılmadı."
YANIT_SINIRI = 1_600_000     # karakter: büyük modelde (yüzlerce çubuk) yanıt bu sınırı aşarsa ayrıntılar tembel bırakılır


def _boyut_sinirla(veri, durumlar_kisa, sinir=YANIT_SINIRI, temel=None):
    """Büyük modelde yanıt boyutu: önce tasarım kontrol satırları 3'e iner (D/C'yi belirleyen satır ilk sıradadır), yetmezse G ve Q
    durumları da ince kayıt olur (tam diyagramlar bina_kombinasyon ile tembel alınır). Dönüş: tasarım kısaltıldıysa kısaltılmamış
    tasarım sonucunun kopyası (rapor için; ``ic["tas_tam"]``), yoksa None."""
    boy = lambda: len(json.dumps(veri, ensure_ascii=False))  # noqa: E731
    if boy() <= sinir:
        return None
    tam = None
    if veri.get("tasarim"):
        tas = veri["tasarim"]
        tam = dict(tas, elemanlar=[dict(k, kontroller=list(k["kontroller"])) for k in tas["elemanlar"]])
        for k in tas["elemanlar"]:
            k["kontroller"] = k["kontroller"][:3]
        veri["ozet"]["tasarim_kisaltildi"] = True
    if boy() <= sinir:
        return tam
    for ad in ("G", "Q"):
        if ad in durumlar_kisa:
            veri["durumlar"][ad] = Y._kisa_veri(durumlar_kisa[ad], diyagram=False, **_temel_kisa(temel))
    veri["ozet"]["durumlar_tembel"] = True
    if boy() <= sinir:
        return tam
    for k in veri["durumlar"].values():          # çok büyük model: ince kayıtlarda yalnız enb (uç kuvvetleri tembel)
        k["elemanlar"] = [{"no": e["no"], "enb": e["enb"]} if "enb" in e else e for e in k["elemanlar"]]
    veri["ozet"]["uc_kuvvetleri_tembel"] = True
    _eylemleri_sinirla(veri, boy(), sinir)
    return tam


def _eylemleri_sinirla(veri, boyut, sinir):
    """C16 boyut koruması (en son adım): rüzgâr/deprem/kren eylemleri yanıtı sınırın üstüne TEK BAŞINA taşıyorsa ya da kendileri
    sınırın dörtte birinden büyükse atılır (veri.yukler.eylemler_not). Eylemlerden bağımsız olarak zaten büyük bir yanıtta küçük
    eylem kümesi korunur (IFC'nin W/E/K yükleri için tek kaynak)."""
    e = veri["yukler"].get("eylemler")
    if not e or boyut <= sinir:
        return
    L = len(json.dumps(e, ensure_ascii=False))
    if boyut - L <= sinir or L > sinir // 4:
        veri["yukler"].pop("eylemler")
        veri["yukler"]["eylemler_not"] = EYLEMLER_NOTU


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
    anl.baslik(f"Çubuk {c['no']} ({_tur_adi(c['tur'])}, {c['kesit']}): kesit tahkiki", 2)
    anl.metin(f"Tahkik kombinasyonları ({len(T.adlar)}): " + ", ".join(f"`{a}`" for a in T.adlar[:12]) + (" …" if len(T.adlar) > 12 else ""))
    k, uy, ek = _cubuk_tasarla(ts, T, c, anl)
    anl.sonuc(rf"\text{{D/C}}_{{max}} = {_f(k['dc'], 3)}", f"Durum: **{k['durum']}** — belirleyen: {k['belirleyen']['kontrol']}")
    mo.son_anlatim = anl
    anl.goster(goster)
    s = mo.Sonuc(k["dc"], anl, f"cubuk {c['no']}")
    s.veri = dict(k, uyarilar=uy)
    return s


def _aks_kat_girdisi(B):
    """Çözülen girdi yalnız aks–kat elemanlarından mı (``cubuklar`` listesi yok: köprünün aks–kat çözümü için genel motorla
    yeniden çözüm)? O zaman 'kolon' / 'kiris' hedefleri ve öneriler aks–kat elemanına (çubuğun ``kaynak``ı) bağlanır."""
    return not (B.ham.get("cubuklar") if isinstance(B.ham, dict) else None)


def _cubuk_bul(B, tur, no, parcalar=False):
    """Tahkik / öneri hedefi → çubuk. ``tur`` "cubuk": çubuk numarası (tam eşleşme). "kolon" / "kiris": çözülen girdi yalnız aks–kat
    elemanlarından oluşuyorsa (``_aks_kat_girdisi``) aks–kat no'su (``kaynak``); genel modelde çubuk numarası (türü de
    eşleşmeli). Öteki türler (capraz, asik …): çubuk numarası. ``parcalar``: aks–kat elemanının bütün parçaları (birden çok
    açıklığa uzanan kiriş kolonlarda bölünür: kaynak.parca 1, 2, …) liste olarak; değilse ilk parça."""
    no = Y._tam(no, "eleman no")
    tur = str(tur or "cubuk").strip().lower()
    if tur in ("kolon", "kiris") and _aks_kat_girdisi(B):
        bulunan = [c for c in B.cubuklar if isinstance(c.get("kaynak"), dict) and c["kaynak"].get("aks_kat") == tur
                   and int(c["kaynak"].get("no", -1)) == no]
        if not bulunan:
            raise MatrisHatasi(f"{'Kolon' if tur == 'kolon' else 'Kiriş'} {no} bu modelde yok.")
        bulunan.sort(key=lambda c: (int(c["kaynak"].get("parca") or 1), c["no"]))
        return bulunan if parcalar else bulunan[0]
    c = B.cubuk_no.get(no)
    if c is None:
        raise MatrisHatasi(f"Çubuk {no} bu modelde yok.")
    if tur in ("kolon", "kiris") and c["tur"] != tur:
        raise MatrisHatasi(f"Çubuk {no} bir {_tur_adi(c['tur'])} ({_tur_adi(tur)} değil); çubuk numarasıyla isteyin (tur: \"cubuk\").")
    return [c] if parcalar else c


def genel_cozum(bina):
    """Aks–kat (surum 1) binasının kesit önerisi için genel motorla çözümü → ``ic`` (gerçek temel tipiyle: tekil, mütemadi ya da
    radye; ``ic["oner_uyarilari"]`` boş liste). Köprü bu paketi aks–kat çözüm kimliğiyle önbelleğe alır."""
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError as e:
            raise MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
    if not isinstance(bina, dict):
        raise MatrisHatasi("Kesit önerisi için bina bir sözlük (ya da JSON metni) olmalı.")
    r = bina_coz(copy.deepcopy(bina), anlat=False, hafif=True)
    ic = r.ic
    ic["oner_uyarilari"] = []
    return ic


def _gorunen_dc(gorunen):
    """Kullanıcının gördüğü aks–kat çözümünün (köprü önbelleği: ``ic["veri"]``) tasarım D/C'leri: {(tur, no): dc}."""
    veri = (gorunen or {}).get("veri") if isinstance(gorunen, dict) else None
    tas = (veri or {}).get("tasarim") or {}
    return {(k.get("tur"), k.get("no")): k["dc"] for k in tas.get("elemanlar") or [] if k.get("dc") is not None}


def kesit_oner(bina=None, *, ic=None, hedef="hepsi", yinele=0, gorunen=None):
    """Kesit önerisi (köprü ``bina_kesit_oner``): her hedef çubuk için öneri, gerekçe ve D/C önce/sonra. ``yinele`` > 0 ise öneriler
    binaya uygulanıp yeniden çözülür (rijitlik değişince iç kuvvetler değişir; en çok 3 tur) ve önerilen bina JSON'u döner.
    hedef: "hepsi" | [{"tur": "cubuk"|"kolon"|"kiris"|..., "no": n}].

    ``ic``: genel model paketi (``ic["serbest"]``) doğrudan kullanılır; aks–kat paketi (``yapi.bina_coz``) verilirse binası genel
    motorla yeniden çözülür (gerçek temel tipiyle) ve D/C önce, kullanıcının gördüğü aks–kat
    tasarım tablosundan (``ic["veri"]``, ``kaynak`` eşlemesiyle) alınır. ``gorunen``: aks–kat paketi zaten genel motorla çözülmüşse
    (köprü önbelleği) görünen çözümün paketi. Her öneride C4 alanları: cubuk, tur, kesit, oneri, sistem, malzeme, b, h, kaynak,
    dc_once, dc_oneri, dc_sonra, degisim, uygula; üst düzeyde uyarilar."""
    ts = _tasarim_mod()
    if ts is None:
        raise MatrisHatasi("Kesit önerisi için tasarim.py gerekir.")
    try:
        yinele = max(0, min(3, int(yinele or 0)))
    except (TypeError, ValueError):
        raise MatrisHatasi("yinele 0…3 arasında bir tam sayı olmalı.") from None
    if ic is not None and not ic.get("serbest"):
        gorunen = ic if gorunen is None else gorunen
        if bina is None:
            bina = ic.get("bina")            # köprü önbelleği; doğrudan yapi.bina_coz paketinde normalize girdi (alan.B.ham)
            if bina is None:
                bina = getattr((ic.get("alan") or {}).get("B"), "ham", None)
        ic = None
    if ic is None:
        if bina is None:
            raise MatrisHatasi("Kesit önerisi için bina ya da çözüm kimliği gerekir.")
        ic = genel_cozum(bina)
    uyarilar = list(ic.get("oner_uyarilari") or [])
    gorunen_dc = _gorunen_dc(gorunen)
    bina_ham = copy.deepcopy(ic["bina"])
    ic0_kesitler = copy.deepcopy(bina_ham.get("kesitler") or {})
    oteleme0 = ic.get("oteleme_asan")            # öneriden önce göreli kat ötelemesini aşan katlar (genel motor çözümü)
    turlar = []
    sonuc_oneriler = None
    for tur_no in range(yinele + 1):
        T = ic["tasarim"]
        if T is None:
            raise MatrisHatasi("Kesit tahkik modülü (tasarim.py) yüklenemedi.")
        B = T.B
        gruplar = _hedef_gruplari(B, hedef)
        hedefler = [c for g in gruplar for c in g]
        dc_once = {k["cubuk"]: k["dc"] for k in (ic.get("tas") or _tasarim(ts, T))["elemanlar"] if k.get("dc") is not None}
        dc_maks = max(dc_once.values(), default=0.0)
        if tur_no == 0 and gorunen_dc:
            dc_maks = max(gorunen_dc.values(), default=dc_maks)
        kayit = {"tur": tur_no, "dc_maks": _r5(dc_maks)}
        if tur_no > 0:
            # onarım turu (0. turdan sonra): yalnız D/C > 1 üyesi olan (kesit, tür) grupları büyütülür (kolonda ρ da artırılabilir);
            # hiçbir grup küçültülmez. Aşan yoksa yakınsadı; son turda (yinele) yalnız durum kaydedilir.
            asan_grup = {(c["kesit"], c["tur"]) for c in hedefler if (dc_once.get(c["no"]) or 0.0) > 1.0 + 1e-9}
            kayit["asan"] = sum(1 for c in hedefler if (dc_once.get(c["no"]) or 0.0) > 1.0 + 1e-9)
            if not asan_grup or tur_no == yinele:
                kayit["oneri_sayisi"] = 0
                turlar.append(kayit)
                break
            gruplar = [g for g in gruplar if any((c["kesit"], c["tur"]) in asan_grup for c in g)]
        oneriler = []
        for g in gruplar:
            parca = []
            kay = g[0].get("kaynak") or {}
            gor = (gorunen_dc.get((kay.get("aks_kat"), kay.get("no"))) if (tur_no == 0 and gorunen_dc and isinstance(kay, dict))
                   else None)
            for c in g:
                dc0 = gor if (gor is not None and len(g) == 1) else dc_once.get(c["no"])     # tek parça: görünen (aks–kat) D/C
                try:
                    parca.append(_oner_cubuk(ts, T, c, dc_kayit=dc0))
                except MatrisHatasi as h:
                    parca.append({"cubuk": c["no"], "tur": c["tur"], "kesit": c["kesit"], "oneri": None, "gerekce": [str(h)],
                                  "kaynak": c.get("kaynak"), "dc_once": _r5(dc0) if dc0 is not None else None, "dc_oneri": None,
                                  "degisim": None, "sistem": None, "malzeme": None, "b": None, "h": None})
            if len(g) == 1:
                o = parca[0]
            else:                       # birden çok parçalı aks–kat elemanı: tek öneri (parçaların zarfı)
                o = _zarf_onerisi(ts, T, g, parca, (bina_ham.get("kesitler") or {}).get(g[0]["kesit"]), kucultme=tur_no == 0)
                o["gerekce"] = [f"Aks–kat elemanı {len(g)} parçalı ({', '.join(f'Ç{c['no']}' for c in g)}): öneri parçaların zarfı (en "
                                "büyük gerekli kesit), D/C öneri parçaların en büyüğü."] + o["gerekce"]
            if gor is not None:
                o["dc_once"] = _r5(min(gor, 99.0))        # kullanıcının gördüğü (aks–kat motoru) D/C
            if tur_no == 0:
                o["uygula"] = _uygula_bilgisi(bina_ham.get("kesitler"), o)
            oneriler.append(o)
        kayit["oneri_sayisi"] = sum(1 for o in oneriler if o.get("oneri"))
        if sonuc_oneriler is None:
            sonuc_oneriler = oneriler
        if tur_no == yinele:
            turlar.append(kayit)
            break
        yeni, degisen = _oneri_uygula(bina_ham, oneriler, B, tur_tasarim=(ts, T), kucultme=tur_no == 0)
        kayit["degisen"] = degisen
        turlar.append(kayit)
        if not degisen:
            break
        bina_ham = yeni
        r = bina_coz(bina_ham, anlat=False, hafif=True)
        ic = r.ic
        ic["tas"] = r.veri.get("tasarim")
    son = ic.get("tas") or (ic["tasarim"] and _tasarim(ts, ic["tasarim"]))
    dc_son = {k["cubuk"]: k["dc"] for k in son["elemanlar"] if k.get("dc") is not None}
    donati_azaltma = []
    if yinele and any(t.get("degisen") for t in turlar):
        if max(dc_son.values(), default=0.0) <= 1.0 + 1e-9 and ic.get("tasarim") is not None:
            bina_ham, donati_azaltma = _rho_azalt(bina_ham, ic["tasarim"], ts, set((ic0_kesitler or {})), dc_son)
        bina_ham = _kullanilmayan_kesitleri_sil(bina_ham, set(ic0_kesitler or {}))
    for o in sonuc_oneriler:
        son_ = [dc_son[n] for n in (o.get("cubuklar") or [o["cubuk"]]) if n in dc_son]
        o["dc_sonra"] = _r5(max(son_)) if (yinele and son_) else o.get("dc_oneri")
    if gorunen_dc:
        uyarilar.append("D/C önce, aks–kat motorunun tasarım tablosundan (görünen çözüm); öneri ve D/C sonra genel model motoruyla.")
    dc_sonra = _r5(max(dc_son.values(), default=0.0)) if yinele else None
    if yinele and dc_sonra > 1.0 + 1e-9:
        uyarilar.append(_yakinsamadi_uyarisi(son["elemanlar"], sum(1 for t in turlar if t.get("degisen"))))
    if yinele and any(t.get("degisen") for t in turlar):
        u = _oteleme_uyarisi(oteleme0, ic.get("oteleme_asan"))
        if u:
            uyarilar.append(u)
    return {"oneriler": sonuc_oneriler, "turlar": turlar, "dc_once": turlar[0]["dc_maks"], "dc_sonra": dc_sonra,
            "bina": bina_ham if yinele else None, "cozum_kimligi": (gorunen or {}).get("kimlik") or ic.get("kimlik"),
            "donati_azaltma": donati_azaltma, "uyarilar": uyarilar, "aciklama": ONER_ACIKLAMA}


def _rho_azalt(bina, T, ts, ilk_kesitler, dc_son):
    """Yakınsamış 'yinele' sonunda (son çözümde bütün D/C ≤ 1): bu çalıştırmada eklenen betonarme kolon kartlarının boyuna donatı
    oranı, SON çözümün iç kuvvetleriyle en küçük yeterli değere indirilir (0,01'den 0,0025 adımla, her üye yeniden doğrulanır).
    ρ rijitliği değiştirmez (sonlu eleman kesiti b × h): iç kuvvetler aynı kalır, yeni D/C'ler kesindir (``dc_son`` yerinde
    güncellenir). Önerinin ρ'su eski (daha rijit) çözümün kuvvetleriyle seçildiğinden çoğu kez fazladır. Dönüş (bina, değişiklikler)."""
    B = T.B
    b = copy.deepcopy(bina)
    kes = b.get("kesitler") or {}
    degisen = []
    for ad in [a for a in kes if a not in ilk_kesitler]:
        kart = kes[ad]
        if not isinstance(kart, dict) or str(kart.get("tip", "dikdortgen")).strip().lower() != "dikdortgen":
            continue
        rho0 = _rho_kart(kart)
        if rho0 <= Y._RHO_VARSAYILAN + 1e-9 or B.kesitler.get(ad, {}).get("tip") != "dikdortgen":
            continue
        uyeler = [c for c in B.cubuklar if c["kesit"] == ad]
        if not uyeler or any(c["tur"] != "kolon" for c in uyeler):
            continue
        lst = [{"cubuk": c["no"]} for c in uyeler]
        dcs = {}
        rho, yet = _grup_rho((ts, T), lst, float(kart["b"]), float(kart["h"]), Y._RHO_VARSAYILAN, dc_cikti=dcs)
        if yet or rho >= rho0 - 1e-9:
            continue
        en = {"sistem": "betonarme", "b": float(kart["b"]), "h": float(kart["h"]), "malzeme": kart.get("malzeme"),
              "donati": kart.get("donati"), "pas": kart.get("pas"), "donati_orani": rho,
              "degisim": "donatı" if rho > Y._RHO_VARSAYILAN + 1e-9 else "küçült"}
        yeni_ad, _, _, _ = _oneri_kesit(kes, ad, en)
        if yeni_ad == ad:
            continue
        # son ρ ile _grup_rho'da doğrulanmamış (daha düşük ρ ile geçmiş) üyeler bu ρ ile yeniden (kesin D/C'ler dc_son'a yazılır)
        dcs.update(_uyeler_dc(ts, T, [c for c in uyeler if c["no"] not in dcs], dict(B.kesitler[ad], donati_orani=rho, As=None)))
        if any(d is None or d > 1.0 + 1e-9 for d in dcs.values()):
            continue
        for liste in ("cubuklar", "kolonlar", "kirisler"):
            for e in b.get(liste) or []:
                if isinstance(e, dict) and e.get("kesit") == ad:
                    e["kesit"] = yeni_ad
        dc_son.update(dcs)
        degisen.append({"kesit": ad, "yeni": yeni_ad, "donati_orani": round(rho, 6), "rho_once": round(rho0, 6),
                        "cubuklar": sorted(dcs)})
    return b, degisen


def _hedef_gruplari(B, hedef, grup=False):
    """Öneri hedefleri → çubuk grupları (her grup tek öneri alır). Aks–kat girdisinde (``_aks_kat_girdisi``) bir aks–kat kolonu /
    kirişinin bütün parçaları tek gruptur (hedef 'hepsi' de aks–kat elemanı başına bir öneri); ``grup`` (kesit grubu kipi): bütün
    hedefler tek grup. Sıra korunur, tekrarlar atılır."""
    if hedef == "hepsi" or hedef is None:
        if grup:
            raise MatrisHatasi('Grup kipi (grup: true) için hedef üye listesi verilmeli: [{"tur", "no"}, ...].')
        gruplar, anahtar = [], {}
        aks_kat = _aks_kat_girdisi(B)
        for c in B.cubuklar:
            kay = c.get("kaynak") if aks_kat else None
            if isinstance(kay, dict) and kay.get("aks_kat") in ("kolon", "kiris"):
                k = (kay["aks_kat"], int(kay.get("no", -1)))
                if k in anahtar:
                    anahtar[k].append(c)
                    continue
                anahtar[k] = [c]
                gruplar.append(anahtar[k])
            else:
                gruplar.append([c])
        return gruplar
    if not isinstance(hedef, list):
        raise MatrisHatasi('hedef "hepsi" ya da [{"tur", "no"}] listesi olmalı.')
    gruplar, gorulen = [], set()
    for h in hedef:
        if not isinstance(h, dict):
            raise MatrisHatasi('hedef öğeleri {"tur", "no"} sözlükleri olmalı.')
        g = [c for c in _cubuk_bul(B, h.get("tur"), h.get("no"), parcalar=True) if c["no"] not in gorulen]
        gorulen.update(c["no"] for c in g)
        if g:
            gruplar.append(g)
    if grup and gruplar:
        uyeler = [c for g in gruplar for c in g]
        if len({(c["kesit"], c["tur"]) for c in uyeler}) > 1:
            raise MatrisHatasi("Grup kipi: üyelerin kesiti ve türü aynı olmalı (" + ", ".join(sorted({f"{c['kesit']} / {_tur_adi(c['tur'])}"
                                                                                                 for c in uyeler})) + ").")
        gruplar = [uyeler]
    return gruplar


def _zarf_onerisi(ts, T, uyeler, lst, kesit_karti, kucultme=True):
    """Birden çok çubuğa tek öneri (aks–kat elemanının parçaları ya da kesit grubu): betonarmede ``_ba_grup_karti`` (en büyük b × h;
    kolonda üyeler doğrulanarak grup ρ'su), çelikte en ağır öneri. dc_oneri = üyelerin bu kartla, kendi iç kuvvetleriyle §11
    D/C'lerinin en büyüğü; cubuk = ilk üye, cubuklar = bütün üyeler."""
    B = T.B
    gecerli = [o for o in lst if o.get("oneri") is not None]
    no_lst = [c["no"] for c in uyeler]
    ilk = dict(lst[0])
    ilk.update({"cubuk": no_lst[0], "cubuklar": no_lst})
    if not gecerli:
        return ilk
    c0 = uyeler[0]
    ks = B.kesitler[c0["kesit"]]
    kt = B.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
    if gecerli[0].get("sistem") == "betonarme":
        en, atla = _ba_grup_karti(gecerli, kesit_karti or {}, (ts, T), kucultme)
        kart = None if atla else dict(kt, b=en["b"], h=en["h"])
        if kart is not None and en.get("donati_orani") is not None:
            kart.update({"donati_orani": en["donati_orani"], "As": None})
        if atla:
            en.update({"degisim": "aynı"})
    else:
        en = dict(max(gecerli, key=_agirlik))
        kart = None
        if en.get("degisim") != "aynı":
            try:
                kart = _kesit_kart("__oneri__", {"tip": "profil", "profil": en["oneri"], "malzeme": kt["malzeme"]}, B)
            except MatrisHatasi:
                kart = None
    if kart is not None:
        dcs = _uyeler_dc(ts, T, uyeler, kart)
    else:
        dcs = {o["cubuk"]: o.get("dc_once") for o in lst}
    gecerli_dc = [d for d in dcs.values() if d is not None]
    en.update({"cubuk": no_lst[0], "cubuklar": no_lst, "kaynak": c0.get("kaynak"),
               "dc_oneri": _r5(min(max(gecerli_dc), 99.0)) if gecerli_dc else en.get("dc_oneri"),
               "dc_once": max((o["dc_once"] for o in lst if o.get("dc_once") is not None), default=None),
               "gerekce": list(en.get("gerekce") or [])})
    if en["dc_oneri"] is not None and en["dc_oneri"] > 1.0 + 1e-9 and en.get("degisim") != "aynı":
        en["gerekce"].append(f"Ortak kartla en büyük üye D/C = {_f(en['dc_oneri'], 3)} > 1 (üyelerin iç kuvvetleri farklı).")
    return en


def _uyeler_dc(ts, T, uyeler, kart):
    """Çubukların verilen kartla (aynı iç kuvvetler) §11 D/C'leri {no: dc}; T.sonuclar korunur."""
    out = {}
    for c in uyeler:
        eski = T.sonuclar.get(c["no"])
        try:
            k2, _, _ = _cubuk_tasarla(ts, T, c, kt_yerine=kart)
            out[c["no"]] = k2["dc"]
        except MatrisHatasi:
            out[c["no"]] = None
        finally:
            if eski is not None:
                T.sonuclar[c["no"]] = eski
            else:
                T.sonuclar.pop(c["no"], None)
    return out


def _kullanilmayan_kesitleri_sil(bina, ilk_kesitler):
    """Kesit önerisinin turlarda eklediği ama son binada hiçbir çubuğun / aks–kat elemanının (ya da kullanılan vute kartının temel
    profili olarak) kullanmadığı kesit kartları silinir; kullanıcının kendi kartlarına dokunulmaz."""
    kes = bina.get("kesitler") or {}
    kullanilan = {e.get("kesit") for a in ("cubuklar", "kolonlar", "kirisler") for e in (bina.get(a) or []) if isinstance(e, dict)}
    for ad in list(kullanilan):
        k = kes.get(ad)
        if isinstance(k, dict) and str(k.get("tip", "")).strip().lower() == "vute":
            kullanilan.add(k.get("temel"))
    for ad in [a for a in kes if a not in ilk_kesitler and a not in kullanilan]:
        del kes[ad]
    return bina


ONER_ACIKLAMA = ("D/C (öneri) mevcut iç kuvvetlerle tahmindir: öneri, modelin şimdiki çözümünün iç kuvvetleriyle (rijitlik "
                 "değişmeden) yapılır. Kesit değişince çerçevenin rijitliği ve iç kuvvet dağılımı da değişir; gerçek D/C ancak model "
                 "yeniden çözülünce görülür ('yinele': öneriler uygulanıp model en çok 3 tur yeniden çözülür, 0. turdan sonra yalnız "
                 "D/C > 1 kalan gruplar büyütülür, hiçbir grup küçültülmez). Aynı (kesit, tür) grubundaki çubuklara grubun ortak "
                 "kartı verilir: çelikte en ağır öneri, betonarmede en büyük b × h; kolon grubunda boyuna donatı oranı her üye "
                 "yeniden doğrulanarak seçilir. Yakınsayınca (son çözümde bütün D/C ≤ 1) eklenen kolon kartlarının ρ'su son "
                 "çözümün iç kuvvetleriyle en küçük yeterli değere indirilir (ρ rijitliği değiştirmez; 'donati_azaltma'). Öneriler "
                 "göreli kat ötelemesini (TBDY 2018 md. 4.9.1) denetlemez; 'yinele' sonunda yeni aşan kat varsa uyarılır.")


def _oteleme_uyarisi(once, sonra):
    """Önerilen kesitlerle çözümde göreli kat ötelemesi sınırını (TBDY 2018 md. 4.9.1) yeni aşan katlar → uyarı metni (yoksa None).
    Öneriler yalnız eleman D/C'sine göre seçilir (0. tur ekonomi için küçültebilir): rijitlik azalınca öteleme sınırı aşılabilir;
    'yakınsadı' (D/C ≤ 1) bunu kapsamaz. ``once`` bilinmiyorsa (None) son çözümde aşan bütün katlar yazılır."""
    if not sonra:
        return None
    yeni = {y: sorted(set(sonra.get(y) or []) - set((once or {}).get(y) or [])) for y in ("x", "y")}
    parca = [f"{y.upper()} yönü kat {', '.join(map(str, k))}" for y, k in yeni.items() if k]
    if not parca:
        return None
    return ("Önerilen kesitlerle göreli kat ötelemesi sınırı (TBDY 2018 md. 4.9.1) aşılıyor: " + "; ".join(parca)
            + (" (öneriden önce bu katlarda sağlanıyordu)" if once is not None else "")
            + ". Öneriler yalnız eleman D/C'sine göre seçilir, rijitlik (öteleme) denetlenmez: kolon / kiriş boyutlarını artırın.")


def _yakinsamadi_uyarisi(elemanlar, tur_sayisi, en_cok=8):
    """Son çözümde D/C > 1 kalan çubuklar: "Kesit önerileri 2 turda yakınsamadı: Ç12 (1,07), kolon 7 (1,05) …" (K1)."""
    asan = sorted((k for k in elemanlar if k.get("dc") is not None and k["dc"] > 1.0 + 1e-9), key=lambda k: -k["dc"])

    def ad(k):
        kay = k.get("kaynak") or {}
        if isinstance(kay, dict) and kay.get("aks_kat") in ("kolon", "kiris"):
            return f"{'kolon' if kay['aks_kat'] == 'kolon' else 'kiriş'} {kay.get('no')}"
        return f"Ç{k.get('cubuk', k.get('no'))}"

    liste = ", ".join(f"{ad(k)} ({_f(k['dc'], 2).replace('.', ',')})" for k in asan[:en_cok]) + (
        f" … +{len(asan) - en_cok} çubuk" if len(asan) > en_cok else "")
    # hiç tur uygulanamadıysa (aşan çubukların uygulanabilir önerisi yok) "0 turda" tek başına yanıltıcı: nedeni de söylenir
    neden = " (uygulanabilir kesit değişikliği bulunamadı)" if not tur_sayisi else ""
    return (f"Kesit önerileri {tur_sayisi} turda yakınsamadı{neden}: {liste} — son çözümde D/C > 1. Bu çubukların kesitini elle "
            "büyütün ya da önerileri yeniden çalıştırın.")


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
