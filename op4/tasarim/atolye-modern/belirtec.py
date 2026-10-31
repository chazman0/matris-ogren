#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atölye · Modern — TEK belirteç modülü: renk, vurgu paletleri, anlamsal renkler, D/C ölçeği, yarıçap, aralık,
yazı ölçeği ve modül yükseklikleri. Bütün çizim kodu yalnız buradaki adları kullanır; sabit renk yazılmaz.

Palet değişimi tek satırdır:
    VARSAYILAN_PALET = "kobalt"        # "kobalt" | "petrol" | "grafit"
Üreteç üç seçeneği yan yana göstermek için palet_uygula(ad) ile C sözlüğünü yerinde günceller.
"""

VARSAYILAN_PALET = "kobalt"   # ← palet değişimi: tek satır

# ----------------------------------------------------------------------------
# Nötr yüzeyler (üç palette ortak) — katmanlı beyaz/griler, 1 px kenarlar
# ----------------------------------------------------------------------------
NOTR = dict(
    zemin="#F3F4F6",        # krom zemini: başlık, şerit sekme satırı, ray, pencere şeridi, rıhtım sekmeleri, durum çubuğu
    zemin2="#E9ECEF",       # gömme iz: segmentli denetim yuvası, kaydırıcı izi, kapalı anahtar
    yuzey="#FFFFFF",        # paneller, şerit gövdesi, kartlar, açılır pencereler
    yuzey2="#F8F9FA",       # panel/bölüm başlığı, tablo başlığı, Ayarlar sol gezinti
    sayfa="#F5F6F8",        # Ayarlar sayfa zemini (kartların arkası)
    alan="#F3F4F6",         # dolgulu giriş alanı (kenarsız); odakta beyaza döner
    alan_kenar="#E3E6EA",   # dolgulu alanın 1 px iç kenarı
    hover="#F0F2F4",        # satır/düğme üzerinde
    basili="#E7EAEE",       # nötr basılı
    cizgi="#E1E4E8",        # panel kenarı, güçlü ayraç
    cizgi2="#ECEEF1",       # ince ayraç, satır çizgisi, girinti kılavuzu
    kenar="#CDD2D8",        # ikincil düğme, onay kutusu, kaydırıcı kenarı
    metin="#14181B",        # birincil metin (Antrasit)
    metin2="#4A515A",       # ikincil metin, alan etiketi            (beyazda 8,0:1)
    metin3="#646B75",       # açıklama, grup adı, yer tutucu         (beyazda 5,4:1 · zeminde 4,9:1)
    metin4="#A0A6AE",       # yalnız devre dışı / kapalı simge (metin için kullanılmaz)
    simge="#353B43",        # şerit ve panel simgeleri
    simge2="#59606A",       # ikincil simge
    golge="#0F172A",        # gölge rengi (saydamlıkla)
    karartma="#0F172A",     # kipli pencere arkası (%38)
    beyaz="#FFFFFF",
)

# ----------------------------------------------------------------------------
# Vurgu paletleri (bronz/kahve–altın YOK). Her biri aynı rolleri doldurur.
#   vurgu       birincil düğme, etkin sekme çizgisi, açık anahtar, onay kutusu, basılı araç simgesi, bağlantı
#   vurgu_koyu  üzerinde/basılı birincil, vurgu zemininde metin
#   vurgu_ton   basılı araç zemini, etkin gezinti satırı;  vurgu_ton2: aynı öğenin kenarı
#   secim       modelde seçim konturu, seçili ağaç satırı simgesi, seçim rozeti, başlangıç tutamacı
#   secim_ton   seçili satır zemini;  secim_ton2: seçili satır kenarı
#   secim_dolgu modelde seçili elemanın açık dolgusu (gölgeleme öncesi taban)
#   hover_model modelde üzerinde konturu (seçimden açık ve ince)
#   odak        odak halkası (3 px, %28 saydam)
# ----------------------------------------------------------------------------
PALETLER = {
    "kobalt": dict(
        ad="Kobalt mavisi", kisa="A",
        vurgu="#2563EB", vurgu_koyu="#1D4ED8", vurgu_metin="#1D4ED8",
        vurgu_ton="#EEF3FE", vurgu_ton2="#CFDDFC",
        secim="#2563EB", secim_ton="#EAF1FE", secim_ton2="#C9DAFC", secim_dolgu="#C9DBFB",
        hover_model="#5B8FF2", odak="#2563EB",
    ),
    "petrol": dict(
        ad="Petrol yeşili", kisa="B",
        vurgu="#0F766E", vurgu_koyu="#115E59", vurgu_metin="#0F6B64",
        vurgu_ton="#E8F4F2", vurgu_ton2="#BFE0DB",
        secim="#0F766E", secim_ton="#E6F3F1", secim_ton2="#BCDDD8", secim_dolgu="#BFE3DD",
        hover_model="#3E9C93", odak="#0F766E",
    ),
    "grafit": dict(
        ad="Grafit (tek renk)", kisa="C",
        vurgu="#262B31", vurgu_koyu="#111418", vurgu_metin="#262B31",
        vurgu_ton="#EBEDF0", vurgu_ton2="#D3D8DE",
        secim="#2F6FDB", secim_ton="#ECF2FD", secim_ton2="#C9DBF8", secim_dolgu="#CCDDF8",
        hover_model="#6E9BE6", odak="#2F6FDB",
    ),
}

# ----------------------------------------------------------------------------
# Anlamsal renkler (vurgudan bağımsız, renk körlüğüne dayanıklı; metin olarak beyazda ≥ 4,5:1)
# ----------------------------------------------------------------------------
ANLAM = dict(
    ok="#1E7B4C", ok_ton="#E8F5EE",
    uyari="#A15C07", uyari_ton="#FEF3DC", uyari_dolgu="#E9A23B",
    hata="#C0362C", hata_ton="#FCEBEA", hata_kenar="#F2C4C0",
    bilgi="#2E6AB3",
    eksen_x="#C0362C", eksen_y="#1E7B4C", eksen_z="#2E6AB3",
)

# D/C ölçeği (5 eşik; kullanıcı düzenler). Komşu sınıflar döteranopi/protanopide ΔE ≥ 27/35 (CIELAB, Machado 2009).
DC_RENK = ["#2E6AB3", "#2BA37B", "#F3D84C", "#DD6A1C", "#A61B2E"]
DC_ESIK = [0.50, 0.70, 0.90, 1.00]
DC_AD = ["≤ 0,50", "0,50–0,70", "0,70–0,90", "0,90–1,00", "> 1,00"]

# Model (3B görünüm) nötr nesne renkleri ve arka plan
MODEL = dict(
    vp_ust="#FBFCFD", vp_alt="#E4E8EC",     # dikey gradyan
    vp_isik="#FFFFFF",                       # model arkasında yumuşak ışık (ortam)
    kolon="#CBD0D7", kiris="#D3D7DD", tali="#D9DDE2", asik="#D9DDE2", capraz="#C4C9D0",
    doseme="#E3E5E8", temel="#D6D8DB",
    kenar="#454B53", kenar_ince="#5A616A", kenar_doseme="#8E939A",
    izgara="#B7BCC4", izgara_ana="#9AA0A8", aks="#7E858F",
)

# ----------------------------------------------------------------------------
# Yarıçap · aralık · gölge
# ----------------------------------------------------------------------------
R = dict(
    kucuk=4,     # onay kutusu, kısayol rozeti, eşik kutusu
    orta=6,      # KART, GİRİŞ, DÜĞME, ÇİP, segment, satır vurgusu  (ana yarıçap)
    buyuk=8,     # açılır pencere, mini araç çubuğu, görünüm pili
    pencere=10,  # kipli pencere (Ayarlar)
    hap=999,     # anahtar, sayaç rozeti
)
A = dict(a1=4, a2=8, a3=12, a4=16, a5=24, a6=32)   # 8 px ızgara, 4 px yarım adım

GOLGE = dict(   # (bulanıklık yarıçapı, dy, saydamlık)
    panel=(6, 0, 0.06),          # panel → görünüm kenarında çok yumuşak geçiş
    kabarik=(2, 1, 0.10),        # segmentli denetimde seçili hap
    yuzen=(8, 2, 0.10),          # görünüm üstündeki pil/düğme grupları
    acilir=(14, 6, 0.14),        # açılır pencere, mini araç çubuğu, ipucu
    kipli=(28, 12, 0.24),        # Ayarlar penceresi
)

# ----------------------------------------------------------------------------
# Yazı ölçeği — Inter değişken (opsz = boyut, 14–32'ye kırpılır). (boyut px @1×, ağırlık)
# ----------------------------------------------------------------------------
Y = dict(
    sayfa=(20, 600),        # Ayarlar sayfa başlığı
    pencere=(15, 600),      # kipli pencere başlığı
    baslik=(13, 600),       # panel başlığı, kart başlığı, nesne adı, "op4"
    govde=(12, 400),        # alan değeri, ağaç satırı, komut satırı
    govde_orta=(12, 500),   # düğme, sekme
    govde_kalin=(12, 600),  # etkin sekme, seçili satır
    etiket=(11, 500),       # şerit düğme adı, durum çubuğu, çip, görünüm pili
    etiket_ince=(11, 400),  # açıklama satırları, ipucu
    kucuk=(10, 500),        # şerit grup adı, kısayol rozeti, lejant
    rozet=(9, 600),         # sayaç rozeti
    bolum=(9, 600),         # BÜYÜK HARF bölüm etiketi (ÇİZ / SEÇ), harf aralığı +0,6 px
)

# ----------------------------------------------------------------------------
# Modül yükseklikleri/genişlikleri — iki yoğunluk. "rahat" ≥ 1600×900, "siki" daha küçük ekranda otomatik.
# ----------------------------------------------------------------------------
OLCU = {
    "rahat": dict(
        baslik=32, sekme=32, serit=88,                # üst krom 152
        ray=40, agac=272, ozel=320, pencere_seridi=32,
        gsekme=32, rihtim_sekme=32, rihtim=48, komut=32, durum=28,
        panel_baslik=40, nesne=48, panel_alt=48, segment=28, arama=28,
        satir_agac=24, satir_ozel=24, alan_h=20, bolum=28,
        buyuk_dugme=64, kucuk_satir=20, ray_dugme=32,
    ),
    "siki": dict(
        baslik=28, sekme=28, serit=76,                # üst krom 132
        ray=36, agac=232, ozel=288, pencere_seridi=28,
        gsekme=28, rihtim_sekme=28, rihtim=40, komut=28, durum=26,
        panel_baslik=36, nesne=48, panel_alt=44, segment=24, arama=24,
        satir_agac=22, satir_ozel=22, alan_h=20, bolum=24,
        buyuk_dugme=56, kucuk_satir=18, ray_dugme=28,
    ),
}

# ----------------------------------------------------------------------------
# Etkin renk sözlüğü (çizim kodu yalnız bunu okur)
# ----------------------------------------------------------------------------
C = {}


def palet_uygula(ad=None):
    """C sözlüğünü yerinde kurar: nötr + anlamsal + model + seçilen vurgu paleti."""
    ad = ad or VARSAYILAN_PALET
    C.clear()
    C.update(NOTR)
    C.update(ANLAM)
    C.update(MODEL)
    C.update(PALETLER[ad])
    C["palet"] = ad
    return C


palet_uygula()


# ----------------------------------------------------------------------------
# Renk yardımcıları
# ----------------------------------------------------------------------------
def hex2rgb(h):
    if isinstance(h, tuple):
        return tuple(h[:3])
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(h, a):
    return hex2rgb(h) + (int(round(a * 255)),)


def karisim(a, b, t):
    """a ile b renklerini t oranında karıştır (t=0 → a)."""
    a, b = hex2rgb(a), hex2rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def parlaklik(h):
    r, g, b = hex2rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def kontrast(a, b):
    la, lb = parlaklik(a), parlaklik(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def ustundeki_metin(zemin):
    """Dolgu üstündeki metin rengi: beyaz ya da Antrasit, hangisi daha yüksek kontrastsa."""
    return NOTR["beyaz"] if kontrast(NOTR["beyaz"], zemin) >= kontrast(NOTR["metin"], zemin) else NOTR["metin"]
