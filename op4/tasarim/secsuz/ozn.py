#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ozn.py — Seç & Süz taslakları için öznitelik tablosu + yön sayımı (faceted count) motoru.

Taslaklardaki her sayı buradan HESAPLANIR (elle yazılmaz): sahne.model_olustur() elemanlarından S5 benzeri bir
öznitelik tablosu kurulur; ölçüt kategorileri (Nesne türü, Kat, Kesit, …) bu tablonun sütunlarıdır.

Birleştirme kuralı (secsuz.md §5):
  * aynı kategori içindeki işaretli değerler  → VEYA (birleşim)
  * farklı kategoriler arasında              → VE   (kesişim)
  * liste değerli alanlarda (kat, aks, etiket) eleman, listesindeki herhangi bir değer işaretliyse sağlar.
Sayım: değer satırındaki n = "bu değer işaretlenirse, DİĞER kategorilerin ölçütleriyle birlikte eşleşen eleman";
        N = "evrende bu değeri taşıyan eleman" (n / N).
"""
import math
from collections import OrderedDict

from sahne import model_olustur, dc_ata, X_AKS, Y_AKS, Z_KAT, KAT_AD, AKS_X_AD, AKS_Y_AD

TUR_AD = OrderedDict([("kolon", "Kolon"), ("kiris", "Kiriş"), ("tali", "Tali kiriş"), ("asik", "Aşık"),
                      ("capraz", "Çapraz"), ("doseme", "Döşeme"), ("temel", "Temel")])


def _yakin(a, b, tol=0.02):
    return abs(a - b) <= tol


def _aks_x(x):
    for i, ax in enumerate(X_AKS):
        if _yakin(x, ax, 0.3):
            return AKS_X_AD[i]
    return None


def _aks_y(y):
    for i, ay in enumerate(Y_AKS):
        if _yakin(y, ay, 0.3):
            return AKS_Y_AD[i]
    return None


def _konum_sinifi(x, y):
    kx = _yakin(x, X_AKS[0]) or _yakin(x, X_AKS[-1])
    ky = _yakin(y, Y_AKS[0]) or _yakin(y, Y_AKS[-1])
    if kx and ky:
        return "köşe"
    if kx or ky:
        return "kenar"
    return "iç"


def oznitelikler(e):
    """Bir sahne elemanı → öznitelik sözlüğü (liste değerli alanlar liste)."""
    t = e.tur
    a = {"tur": t, "ref": e}
    a["kat"] = [KAT_AD[e.kat]]
    # kesit / malzeme
    if t == "kolon":
        a["kesit"], a["malzeme"] = "HE340A", "S355"
    elif t == "kiris":
        a["kesit"], a["malzeme"] = "IPE400", "S355"
    elif t in ("tali", "asik"):
        a["kesit"], a["malzeme"] = "IPE200", "S275"
    elif t == "capraz":
        if len(e.profil) == 4:      # çatı düzlemi yatay çaprazı
            a["kesit"], a["malzeme"] = "KUTU 80x4", "S355"
        else:
            a["kesit"], a["malzeme"] = "L100x10", "S275"
    elif t == "doseme":
        a["kesit"], a["malzeme"] = None, "C30/37"
    elif t == "temel":
        a["kesit"], a["malzeme"] = None, "C25/30"
    # düğüm noktaları (analitik): kolon/kiriş uçları aks noktalarına oturur; görsel kısaltmalar geri alınır
    p0, p1 = e.p0, e.p1
    if t == "kiris":
        if _yakin(p0[1], p1[1]):          # x yönü
            xa = min(X_AKS, key=lambda v: abs(v - p0[0])); xb = min(X_AKS, key=lambda v: abs(v - p1[0]))
            p0, p1 = (xa, p0[1], Z_KAT[e.kat]), (xb, p1[1], Z_KAT[e.kat])
        else:
            ya = min(Y_AKS, key=lambda v: abs(v - p0[1])); yb = min(Y_AKS, key=lambda v: abs(v - p1[1]))
            p0, p1 = (p0[0], ya, Z_KAT[e.kat]), (p1[0], yb, Z_KAT[e.kat])
    elif t in ("tali", "asik"):
        ya = min(Y_AKS, key=lambda v: abs(v - p0[1])); yb = min(Y_AKS, key=lambda v: abs(v - p1[1]))
        p0, p1 = (p0[0], ya, Z_KAT[e.kat]), (p1[0], yb, Z_KAT[e.kat])
    elif t == "capraz" and a["kesit"] == "L100x10":
        ya = min(Y_AKS, key=lambda v: abs(v - p0[1])); yb = min(Y_AKS, key=lambda v: abs(v - p1[1]))
        p0, p1 = (p0[0], ya, Z_KAT[e.kat - 1]), (p1[0], yb, Z_KAT[e.kat])
    elif t == "capraz":
        xa = min(X_AKS, key=lambda v: abs(v - p0[0])); xb = min(X_AKS, key=lambda v: abs(v - p1[0]))
        ya = min(Y_AKS, key=lambda v: abs(v - p0[1])); yb = min(Y_AKS, key=lambda v: abs(v - p1[1]))
        p0, p1 = (xa, ya, Z_KAT[3]), (xb, yb, Z_KAT[3])
    a["p0"], a["p1"] = p0, p1
    d = tuple(p1[i] - p0[i] for i in range(3))
    L = math.sqrt(sum(c * c for c in d))
    # doğrultu, uzunluk
    if t in ("doseme", "temel"):
        a["dogrultu"] = None
        a["uzunluk"] = None
    else:
        a["uzunluk"] = round(L, 2)
        if L > 0 and abs(d[2]) / L > 0.99:
            a["dogrultu"] = "Z'ye paralel (düşey)"
        elif abs(d[2]) < 1e-6 and abs(d[1]) < 1e-6:
            a["dogrultu"] = "X'e paralel"
        elif abs(d[2]) < 1e-6 and abs(d[0]) < 1e-6:
            a["dogrultu"] = "Y'ye paralel"
        else:
            a["dogrultu"] = "Eğik"
    # kullanım yeri (MIMARI §10.3)
    if t in ("kolon", "temel"):
        a["yer"] = _konum_sinifi(p0[0], p0[1])
    elif t == "kiris":
        if _yakin(p0[1], p1[1]):
            a["yer"] = "dış" if (_yakin(p0[1], Y_AKS[0]) or _yakin(p0[1], Y_AKS[-1])) else "iç"
        else:
            a["yer"] = "dış" if (_yakin(p0[0], X_AKS[0]) or _yakin(p0[0], X_AKS[-1])) else "iç"
    elif t in ("tali", "asik"):
        a["yer"] = "iç"
    elif t == "capraz":
        a["yer"] = "dış cephe" if a["kesit"] == "L100x10" else "çatı düzlemi"
    elif t == "doseme":
        a["yer"] = "kenar"
    # akslar (üstünde bulunduğu)
    aks = []
    if t in ("kolon", "temel"):
        aks = [_aks_x(p0[0]), _aks_y(p0[1])]
    elif t == "kiris":
        aks = [_aks_y(p0[1])] if _yakin(p0[1], p1[1]) else [_aks_x(p0[0])]
    elif t == "capraz" and a["kesit"] == "L100x10":
        aks = [_aks_x(p0[0])]
    a["aks"] = [v for v in aks if v]
    # düzlem
    dz = []
    if t not in ("doseme", "temel"):
        if _yakin(p0[2], p1[2]):
            k = Z_KAT.index(min(Z_KAT, key=lambda z: abs(z - p0[2])))
            dz.append(f"XY · {KAT_AD[k]}")
        if _yakin(p0[1], p1[1]) and _aks_y(p0[1]) and _yakin(p0[1], Y_AKS[Y_AKS.index(min(Y_AKS, key=lambda v: abs(v - p0[1])))]):
            dz.append(f"XZ · Aks {_aks_y(p0[1])}")
        if _yakin(p0[0], p1[0]) and _aks_x(p0[0]) and _yakin(p0[0], X_AKS[X_AKS.index(min(X_AKS, key=lambda v: abs(v - p0[0])))]):
            dz.append(f"YZ · Aks {_aks_x(p0[0])}")
    elif t == "doseme":
        dz.append(f"XY · {KAT_AD[e.kat]}")
    a["duzlem"] = dz
    # grup (sabit seçim kümeleri) ve etiketler
    g = []
    if t == "kiris":
        g.append("Ana çerçeve" if _yakin(p0[1], p1[1]) else "Bağ kirişleri")
    if t == "asik":
        g.append("Çatı aşıkları")
    if t == "capraz" and a["kesit"] == "L100x10":
        g.append("Cephe çaprazları")
    a["grup"] = g
    et = []
    if t in ("kolon", "kiris") and e.kat in (1, 2):
        et.append(f"imalat-{e.kat}")
    a["etiket"] = et
    # yük desenleri (ek yükler)
    y = []
    if t == "doseme":
        y += ["G · Sabit", "Q · Hareketli"]
    if t == "kiris" and e.kat == 1 and a["yer"] == "dış":
        y.append("G · Sabit")
    if t == "asik":
        y.append("S · Kar")
    a["yuk"] = y or ["(ek yük yok)"]
    # serbestlik / mesnet
    if t == "kolon":
        a["serbestlik"] = "Sürekli (rijit uçlar)"
    elif t == "temel":
        a["serbestlik"] = "Ankastre mesnet"
    elif t == "capraz" and a["kesit"] == "L100x10":
        a["serbestlik"] = "Mafsal · yalnız çekme"
    elif t == "doseme":
        a["serbestlik"] = None
    else:
        a["serbestlik"] = "İki ucu mafsal"
    return a


def tablo(dc=True):
    el, _, _ = model_olustur()
    if dc:
        dc_ata(el)
    satirlar = [oznitelikler(e) for e in el]
    for s in satirlar:
        s["dc"] = s["ref"].dc
    return satirlar


def dc_sinif(v):
    if v is None:
        return None
    for esik, ad in ((0.50, "≤ 0,50"), (0.70, "0,50 – 0,70"), (0.90, "0,70 – 0,90"), (1.00, "0,90 – 1,00")):
        if v <= esik:
            return ad
    return "> 1,00"


def uz_sinif(v):
    if v is None:
        return None
    return f"{v:.2f} m".replace(".", ",")


# kategori anahtarı → (ad, değer çıkarıcı)
KATEGORI = OrderedDict([
    ("tur", ("Nesne türü", lambda a: [TUR_AD[a["tur"]]])),
    ("kat", ("Kat", lambda a: a["kat"])),
    ("kesit", ("Kesit", lambda a: [a["kesit"]] if a["kesit"] else [])),
    ("malzeme", ("Malzeme", lambda a: [a["malzeme"]] if a["malzeme"] else [])),
    ("yer", ("Kullanım yeri", lambda a: [f"{TUR_AD[a['tur']]} › {a['yer']}"] if a.get("yer") else [])),
    ("aks", ("Aks", lambda a: a["aks"])),
    ("dogrultu", ("Doğrultu", lambda a: [a["dogrultu"]] if a["dogrultu"] else [])),
    ("duzlem", ("Düzlem", lambda a: a["duzlem"])),
    ("uzunluk", ("Uzunluk", lambda a: [uz_sinif(a["uzunluk"])] if a["uzunluk"] else [])),
    ("grup", ("Grup / süzgeç", lambda a: a["grup"])),
    ("etiket", ("Etiket", lambda a: a["etiket"])),
    ("yuk", ("Yük deseni", lambda a: a["yuk"])),
    ("serbestlik", ("Mesnet / serbestlik", lambda a: [a["serbestlik"]] if a["serbestlik"] else [])),
    ("dc", ("D/C aralığı", lambda a: [dc_sinif(a["dc"])] if a["dc"] is not None else [])),
])


class Suzgec:
    """Etkin ölçütler: {kategori: set(değer)}; ek koşullar (Gelişmiş): [(ad, fn)]."""

    def __init__(self, satirlar, olcut=None, ek=None):
        self.satirlar = satirlar
        self.olcut = {k: set(v) for k, v in (olcut or {}).items() if v}
        self.ek = ek or []

    def _uyar(self, a, haric=None):
        for k, degerler in self.olcut.items():
            if k == haric:
                continue
            vals = KATEGORI[k][1](a)
            if not any(v in degerler for v in vals):
                return False
        for _, fn in self.ek:
            if not fn(a):
                return False
        return True

    def eslesen(self):
        return [a for a in self.satirlar if self._uyar(a)]

    def sayim(self, k):
        """Kategori k için OrderedDict değer → (n, N); n: diğer ölçütlerle, N: evrende."""
        n, N = {}, {}
        fn = KATEGORI[k][1]
        for a in self.satirlar:
            vals = fn(a)
            uyar = self._uyar(a, haric=k)
            for v in vals:
                N[v] = N.get(v, 0) + 1
                if uyar:
                    n[v] = n.get(v, 0) + 1
        return OrderedDict((v, (n.get(v, 0), N[v])) for v in N)

    def deger_sayisi(self, k):
        return len(self.sayim(k))


def ozet(eslesen):
    """'20 kolon · 31 kiriş' biçiminde tür dağılımı."""
    sayac = OrderedDict()
    for t in TUR_AD:
        c = sum(1 for a in eslesen if a["tur"] == t)
        if c:
            sayac[t] = c
    ad = {"kolon": "kolon", "kiris": "kiriş", "tali": "tali kiriş", "asik": "aşık", "capraz": "çapraz", "doseme": "döşeme", "temel": "temel"}
    return " · ".join(f"{c} {ad[t]}" for t, c in sayac.items())


if __name__ == "__main__":
    S = tablo()
    print("eleman:", len(S))
    f = Suzgec(S)
    for k in KATEGORI:
        print(KATEGORI[k][0], dict((v, N) for v, (n, N) in f.sayim(k).items()))
    f = Suzgec(S, {"kat": {"Kat 2"}, "kesit": {"HE340A", "IPE400"}})
    print("Kat 2 · HE340A/IPE400 →", len(f.eslesen()), ozet(f.eslesen()))
    print("  kesit sayımı:", dict(f.sayim("kesit")))
    print("  kat sayımı:", dict(f.sayim("kat")))
    f = Suzgec(S, {"kat": {"Kat 1", "Kat 2", "Kat 3"}, "yer": {"Kolon › köşe"}})
    print("Kat 1–3 · köşe kolon →", len(f.eslesen()), dict(f.sayim("kat")))
    f = Suzgec(S, {"kat": {"Kat 2"}, "kesit": {"HE340A", "IPE400"}}, ek=[("uzunluk > 5", lambda a: (a["uzunluk"] or 0) > 5.0)])
    print("+ uzunluk > 5 →", len(f.eslesen()), ozet(f.eslesen()))
    f = Suzgec(S, {"kat": {"Kat 1", "Kat 2", "Kat 3"}, "yer": {"Kiriş › dış"}})
    print("dış kiriş 1–3 →", len(f.eslesen()), dict(f.sayim("yer")))
