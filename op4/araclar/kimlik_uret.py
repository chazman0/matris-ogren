# -*- coding: utf-8 -*-
"""Opus Fortis kimlik dosyalarından op4 uygulama simgesini ve kurulum sihirbazı görsellerini üretir.

1) Uygulama simgesi (varsayılan): op4/kimlik/op4.ico
   Kaynak: op4/kimlik/opus-fortis-simge-renkli.png (kahve kemer + krem kilit taşı, saydam zemin, 1200 × 1397).
   Simge kareye ortalanır, kenar boşluğu kırpılır; 16 … 256 piksellik katmanlar yüksek kaliteli küçültmeyle yazılır.
   Küçük boyutlarda (≤ 24 px) kemer çizgisi kalın kalsın diye kırpma daha sıkıdır. Çıktı depoya işlenir.

2) Kurulum sihirbazı görselleri (--sihirbaz KLASÖR; MIMARI §18.1): Inno Setup'ın önerdiği yedi DPI ölçeğinde
   (100 … 250 %) 24 bit BMP'ler. Derleme sırasında (CI) üretilir, depoya işlenmez; op4.iss /DSihirbaz=KLASÖR ile alır.
   * sihirbaz-buyuk-<ölçek>.bmp (100 %'de 164 × 314): karşılama ve bitiş sayfalarının sol paneli. Antrasit zemin,
     ortada renkli kemer simgesi (opus-fortis-simge-renkli.png), altında altın çizgi ve krem tek satır yazı logosu
     (opus-fortis-yazi-koyu-zemin.png).
   * sihirbaz-kucuk-<ölçek>.bmp (100 %'de 55 × 55): iç sayfaların sağ üst köşesi. Beyaz zeminde renkli kemer simgesi.
   * sihirbaz-onizleme.png: hepsinin yan yana önizlemesi (CI günlüğüne basılır).
   Kimlik dosyaları değiştirilmez; yalnız ölçeklenip zemine yerleştirilir. Renkler op4/kimlik/README.md paletinden.

3) Gömülü yazı tipleri (--yazi; MIMARI §25 "sistem yazı tipi kullanılmaz"): op4/kimlik/fontlar/ yazı tiplerinden
   arayüzün (ARAYUZ_YAZI = YAZI_ADAYLARI[...]: TEK satır; şimdilik Inter yer tutucu) + sembol yedeği ("Simgeler")
   ve açılış ekranının (Inter 300 opsz 32, Cormorant Garamond) kullandığı statik örnekler fontTools
   instancer ile kesilir, Latin + Türkçe (U+0020–017F) ve gereken simge / noktalama alt kümesine indirilir, stb biçiminde
   sıkıştırılıp base85 ile op4/kaynak/arayuz/yazi_verisi.cpp içine gömülür (ImGui ve DirectWrite aynı veriyi kullanır).
   Çıktı depoya işlenir; fontTools gerekir.

4) Açılış ekranı kontur verisi (--kontur): op4/kimlik/acilis/kontur.json → op4/kaynak/arayuz/acilis_kontur.h
   (constexpr diziler; açılış ekranı Direct2D çizimi, MIMARI §25). Çıktı depoya işlenir.

5) Arayüz belirteçleri (--tema; MIMARI §5.9, §25.1): op4/tasarim/atolye-modern/belirtec.py (TEK belirteç modülü: nötr
   yüzeyler, üç vurgu paleti, anlamsal renkler, D/C ölçeği, model renkleri, yarıçap, aralık, gölge, yazı ölçeği, iki
   yoğunluğun modül ölçüleri) → op4/kaynak/arayuz/tema_belirtec.h (constexpr tablolar). C++ tarafında elle renk değeri
   yazılmaz; tema.h / tema.cpp yalnız bu tabloyu okur. Çıktı depoya işlenir.

Kullanım:  python3 op4/araclar/kimlik_uret.py                       (op4.ico; Pillow gerekir)
           python3 op4/araclar/kimlik_uret.py --sihirbaz <klasör>   (sihirbaz görselleri)
           python3 op4/araclar/kimlik_uret.py --yazi                (gömülü yazı tipleri; fontTools gerekir)
           python3 op4/araclar/kimlik_uret.py --kontur              (açılış ekranı kontur başlığı)
           python3 op4/araclar/kimlik_uret.py --tema                (arayüz belirteç başlığı)
"""
from __future__ import annotations

import argparse
import pathlib

from PIL import Image, ImageDraw

KIMLIK = pathlib.Path(__file__).resolve().parent.parent / "kimlik"
KAYNAK = KIMLIK / "opus-fortis-simge-renkli.png"
YAZI_KOYU = KIMLIK / "opus-fortis-yazi-koyu-zemin.png"
BOYLAR = [16, 20, 24, 32, 40, 48, 64, 128, 256]

# Palet (op4/kimlik/README.md)
ANTRASIT = (0x14, 0x18, 0x1B)
ALTIN = (0xB0, 0x89, 0x50)
BEYAZ = (0xFF, 0xFF, 0xFF)

# Inno Setup 6'nın önerdiği boyutlar: ölçek (%) → (genişlik, yükseklik)
SIHIRBAZ_BUYUK = {100: (164, 314), 125: (192, 386), 150: (246, 459), 175: (273, 556), 200: (328, 604),
                  225: (355, 700), 250: (410, 797)}
SIHIRBAZ_KUCUK = {100: (55, 55), 125: (64, 68), 150: (83, 80), 175: (92, 97), 200: (110, 106), 225: (119, 123),
                  250: (138, 140)}


def kare(im: Image.Image, bosluk: float) -> Image.Image:
    kutu = im.getbbox() or (0, 0, im.width, im.height)
    parca = im.crop(kutu)
    kenar = int(max(parca.width, parca.height) * (1.0 + 2.0 * bosluk))
    tuval = Image.new("RGBA", (kenar, kenar), (0, 0, 0, 0))
    tuval.alpha_composite(parca, ((kenar - parca.width) // 2, (kenar - parca.height) // 2))
    return tuval


def simge_uret() -> pathlib.Path:
    im = Image.open(KAYNAK).convert("RGBA")
    katmanlar = []
    for b in BOYLAR:
        k = kare(im, 0.02 if b <= 24 else 0.06)
        katmanlar.append(k.resize((b, b), Image.LANCZOS))
    hedef = KIMLIK / "op4.ico"
    katmanlar[-1].save(hedef, sizes=[(b, b) for b in BOYLAR], append_images=katmanlar[:-1])
    return hedef


def _sigdir(im: Image.Image, gen: float, yuk: float) -> Image.Image:
    """Saydam kenarları kırpar, en-boy oranını koruyarak gen × yuk kutusuna sığdırır."""
    parca = im.crop(im.getbbox() or (0, 0, im.width, im.height))
    k = min(gen / parca.width, yuk / parca.height)
    return parca.resize((max(1, round(parca.width * k)), max(1, round(parca.height * k))), Image.LANCZOS)


def sihirbaz_buyuk(gen: int, yuk: int, simge: Image.Image, yazi: Image.Image) -> Image.Image:
    tuval = Image.new("RGB", (gen, yuk), ANTRASIT)
    # Hafif düşey ton: üstte antrasit, altta bir ton açık (bant hissi; açılış ekranıyla uyumlu).
    ciz = ImageDraw.Draw(tuval)
    for y in range(yuk):
        t = y / max(1, yuk - 1)
        ciz.line([(0, y), (gen, y)], fill=tuple(round(c + (c2 - c) * t * 0.6) for c, c2 in zip(ANTRASIT, (0x26, 0x2B, 0x2F))))
    s = _sigdir(simge, gen * 0.56, yuk * 0.38)
    ust = round(yuk * 0.21)
    tuval.paste(s, ((gen - s.width) // 2, ust), s)
    cizgi_y = ust + s.height + round(yuk * 0.075)
    kalinlik = max(1, round(gen / 164))
    yari = round(gen * 0.20)
    ciz.rectangle([gen // 2 - yari, cizgi_y, gen // 2 + yari, cizgi_y + kalinlik - 1], fill=ALTIN)
    y = _sigdir(yazi, gen * 0.80, yuk * 0.08)
    tuval.paste(y, ((gen - y.width) // 2, cizgi_y + kalinlik + round(yuk * 0.045)), y)
    # Alt kenarda ince altın bant (açılış ekranındaki ilerleme çubuğunun rengi).
    ciz.rectangle([0, yuk - max(2, round(yuk / 157)), gen, yuk], fill=ALTIN)
    return tuval


def sihirbaz_kucuk(gen: int, yuk: int, simge: Image.Image) -> Image.Image:
    tuval = Image.new("RGB", (gen, yuk), BEYAZ)
    s = _sigdir(simge, gen * 0.86, yuk * 0.86)
    tuval.paste(s, ((gen - s.width) // 2, (yuk - s.height) // 2), s)
    return tuval


def sihirbaz_uret(klasor: pathlib.Path) -> list[pathlib.Path]:
    klasor.mkdir(parents=True, exist_ok=True)
    simge = Image.open(KAYNAK).convert("RGBA")
    yazi = Image.open(YAZI_KOYU).convert("RGBA")
    yazilan = []
    buyukler, kucukler = [], []
    for olcek, (g, y) in SIHIRBAZ_BUYUK.items():
        im = sihirbaz_buyuk(g, y, simge, yazi)
        yol = klasor / f"sihirbaz-buyuk-{olcek}.bmp"
        im.save(yol, format="BMP")
        yazilan.append(yol)
        buyukler.append(im)
    for olcek, (g, y) in SIHIRBAZ_KUCUK.items():
        im = sihirbaz_kucuk(g, y, simge)
        yol = klasor / f"sihirbaz-kucuk-{olcek}.bmp"
        im.save(yol, format="BMP")
        yazilan.append(yol)
        kucukler.append(im)
    # Önizleme: büyükler yan yana, küçükler altta (gri zeminde, aralarında boşluk).
    bosluk = 12
    gen = sum(im.width for im in buyukler) + bosluk * (len(buyukler) + 1)
    yuk = max(im.height for im in buyukler) + max(im.height for im in kucukler) + bosluk * 3
    onizleme = Image.new("RGB", (gen, yuk), (0xC8, 0xC8, 0xC8))
    x = bosluk
    for im in buyukler:
        onizleme.paste(im, (x, bosluk))
        x += im.width + bosluk
    x, ust = bosluk, max(im.height for im in buyukler) + 2 * bosluk
    for im in kucukler:
        onizleme.paste(im, (x, ust))
        x += im.width + bosluk
    yol = klasor / "sihirbaz-onizleme.png"
    onizleme.save(yol, optimize=True)
    yazilan.append(yol)
    return yazilan


# ---------------------------------------------------------------------------------------------------- gömülü yazı tipleri
KAYNAK_ARAYUZ = pathlib.Path(__file__).resolve().parent.parent / "kaynak" / "arayuz"
FONTLAR = KIMLIK / "fontlar"
# (C++ adı, dosya, eksenler, açıklama). Inter opsz 14 arayüz boyutları (11–15 px) içindir; 32 açılıştaki 92 DIP "op4" için.
# ---- ARAYÜZ YAZI TİPİ: TEK YER (aile belirteci + dosya listesi) ---------------------------------------------------------
# Arayüz yazısı değişimi yalnız bu bloktur: aile adı + ağırlık → (kimlik/fontlar dosyası, değişken eksen değerleri; statik
# dosyada {}). Sonra "python3 op4/araclar/kimlik_uret.py --yazi". C++ tarafı rol adlarını ("Arayuz400" …) kullanır, aile
# adını bilmez (yazi.h). Inter yer tutucudur (kullanıcı yeni yazı tipini seçiyor, 31.10.2026).
# Aday aileler: (görünen ad, kimlik/fontlar dosyası, ağırlık dışındaki değişken eksenler). Statik aile için dosya yerine
# {ağırlık: dosya} sözlüğü verilir. Önerilen: Noto Sans SemiCondensed (wdth 87,5; tanı notu, kullanıcı onayı bekleniyor;
# dosyanın kimlik/fontlar/'a eklenmesi gerekir).
YAZI_ADAYLARI = {
    "inter": ("Inter", "inter-Inter[opsz,wght].ttf", {"opsz": 14}),
    "noto_dar": ("Noto Sans SemiCondensed", "notosans-NotoSans[wdth,wght].ttf", {"wdth": 87.5}),
    "fira": ("Fira Sans", {400: "firasans-FiraSans-Regular.ttf", 500: "firasans-FiraSans-Medium.ttf",
                           600: "firasans-FiraSans-SemiBold.ttf", 700: "firasans-FiraSans-SemiBold.ttf"}, {}),
}
ARAYUZ_YAZI = YAZI_ADAYLARI["inter"]   # ← arayüz yazı tipi değişimi: TEK satır (Inter yer tutucu)
ARAYUZ_YAZI_AGIRLIKLARI = (400, 450, 500, 600, 700)
ARAYUZ_YAZI_AILESI = ARAYUZ_YAZI[0]


def _arayuz_dosyasi(agirlik):
    ad, dosya, eksen = ARAYUZ_YAZI
    if isinstance(dosya, dict):  # statik aile: en yakın ağırlığın dosyası
        yakin = min(dosya, key=lambda w: abs(w - agirlik))
        return dosya[yakin], {}
    return dosya, {**eksen, "wght": agirlik}


ARAYUZ_YAZI_DOSYALARI = {w: _arayuz_dosyasi(w) for w in ARAYUZ_YAZI_AGIRLIKLARI}
# Sembol yedeği (MergeMode ile her arayüz yazısına birleştirilir): seçilen ailede olmayan ≈ ≤ ≥ ← → ↔ ↺ ▾ ⇄ … Inter'den.
SIMGE_KOD_NOKTALARI = [0x2248, 0x2260, 0x2264, 0x2265, 0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x21C4, 0x21BA, 0x21BB,
                       0x25BE, 0x25B4, 0x25B8, 0x25C2, 0x2022, 0x22EF, 0x2026, 0x00D7, 0x00B1, 0x2212, 0x221E, 0x2206,
                       0x0394, 0x03A3, 0x03BB, 0x039B, 0x2713, 0x2717, 0x2318, 0x21E7, 0x2303, 0x23CE]
# Açılış ekranı (marka; MIMARI §25 "değişmez"): arayüz yazısından bağımsızdır.
ACILIS_YAZILARI = [
    ("kAcilisInce", "inter-Inter[opsz,wght].ttf", {"wght": 300, "opsz": 32}, "Açılış 'op4' (Inter Light 300, opsz 32)"),
    ("kCormorant500", "cormorantgaramond-CormorantGaramond[wght].ttf", {"wght": 500}, "Cormorant Garamond Medium: açılış alt başlığı"),
    ("kCormorant600", "cormorantgaramond-CormorantGaramond[wght].ttf", {"wght": 600}, "Cormorant Garamond SemiBold: proje adı"),
]
YAZI_ORNEKLERI = ([(f"kArayuz{agirlik}", dosya, eksen, f"Arayüz {ARAYUZ_YAZI_AILESI} {agirlik}")
                   for agirlik, (dosya, eksen) in ARAYUZ_YAZI_DOSYALARI.items()]
                  + [("kSimgeler", "inter-Inter[opsz,wght].ttf", {"wght": 450, "opsz": 14}, "Sembol yedeği (Inter alt kümesi)")]
                  + ACILIS_YAZILARI)
YAZI_KOD_NOKTALARI = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) +
                      [0x2009, 0x200A, 0x202F, 0x2039, 0x203A, 0x039B, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2030,
                       0x2032, 0x2033, 0x2070, 0x2074, 0x2075, 0x2076, 0x2077, 0x2078, 0x2079, 0x2080, 0x2081, 0x2082,
                       0x2083, 0x20AC, 0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x2206, 0x2212, 0x2215, 0x221A, 0x221E,
                       0x2248, 0x2260, 0x2264, 0x2265, 0x0394, 0x03A3, 0x03A6, 0x03B1, 0x03B2, 0x03B3, 0x03B4, 0x03B5,
                       0x03B8, 0x03BB, 0x03BC, 0x03C0, 0x03C1, 0x03C3, 0x03C4, 0x03C6, 0x03C8, 0x03C9])


def _stb_sikistir(veri: bytes) -> bytes:
    """ImGui'nin stb_decompress biçiminde açgözlü LZ sıkıştırma (imgui_draw.cpp stb_decompress_token ile birebir)."""
    n = len(veri)
    cikti = bytearray(b"\x57\xbc\x00\x00\x00\x00\x00\x00")
    cikti += n.to_bytes(4, "big") + (1 << 18).to_bytes(4, "big")
    zincir: dict[bytes, list[int]] = {}
    yazi = bytearray()

    def yazi_bosalt():
        i = 0
        while i < len(yazi):
            parca = yazi[i:i + 65536]
            L = len(parca)
            if L <= 32:
                cikti.append(0x20 + L - 1)
            elif L <= 2048:
                v = L - 1 + 0x0800
                cikti.extend((v >> 8, v & 0xFF))
            else:
                cikti.extend((0x07, (L - 1) >> 8, (L - 1) & 0xFF))
            cikti.extend(parca)
            i += L
        yazi.clear()

    def eslesme(d: int, L: int):
        if d <= 256 and L <= 128:
            cikti.extend((0x80 + L - 1, d - 1))
        elif d <= 16384 and L <= 256:
            v = d - 1 + 0x4000
            cikti.extend((v >> 8, v & 0xFF, L - 1))
        elif d <= 0x80000 and L <= 256:
            v = d - 1 + 0x180000
            cikti.extend((v >> 16, (v >> 8) & 0xFF, v & 0xFF, L - 1))
        elif d <= 0x80000:
            v = d - 1 + 0x100000
            cikti.extend((v >> 16, (v >> 8) & 0xFF, v & 0xFF, (L - 1) >> 8, (L - 1) & 0xFF))
        else:
            v = d - 1
            cikti.extend((0x04, v >> 16, (v >> 8) & 0xFF, v & 0xFF, (L - 1) >> 8, (L - 1) & 0xFF))

    i = 0
    while i < n:
        en_L, en_d = 0, 0
        if i + 4 <= n:
            anahtar = veri[i:i + 4]
            adaylar = zincir.get(anahtar)
            if adaylar:
                for j in reversed(adaylar[-48:]):
                    d = i - j
                    if d > 0x7FFFF:
                        break
                    L = 4
                    while i + L < n and L < 65536 and veri[j + L] == veri[i + L]:
                        L += 1
                    if L > en_L:
                        en_L, en_d = L, d
                        if L >= 258:
                            break
        if en_L >= 5 or (en_L == 4 and en_d <= 256):
            yazi_bosalt()
            eslesme(en_d, en_L)
            for k in range(i, min(i + en_L, n - 3)):
                zincir.setdefault(veri[k:k + 4], []).append(k)
            i += en_L
        else:
            if i + 4 <= n:
                zincir.setdefault(veri[i:i + 4], []).append(i)
            yazi.append(veri[i])
            i += 1
    yazi_bosalt()
    s1, s2 = 1, 0
    for b in veri:
        s1 = (s1 + b) % 65521
        s2 = (s2 + s1) % 65521
    cikti += bytes((0x05, 0xFA)) + ((s2 << 16) | s1).to_bytes(4, "big")
    return bytes(cikti)


def _base85(veri: bytes) -> str:
    """ImGui Encode85 eşleniği: 4 bayt (küçük uçlu) → 5 karakter, '\\' atlanır."""
    veri = veri + b"\x00" * (-len(veri) % 4)
    o = []
    for i in range(0, len(veri), 4):
        v = int.from_bytes(veri[i:i + 4], "little")
        for _ in range(5):
            c = v % 85 + 35
            o.append(chr(c + 1 if c >= 92 else c))
            v //= 85
    return "".join(o)


def yazi_uret() -> pathlib.Path:
    import io
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    satirlar = ["// op4 — gömülü yazı tipleri. ÜRETİLMİŞ DOSYA: python3 op4/araclar/kimlik_uret.py --yazi",
                "// Kaynak: op4/kimlik/fontlar/ (Inter, Cormorant Garamond; SIL Open Font License 1.1 — lisans metinleri",
                "// kimlik/fontlar/*-OFL.txt). Statik örnekler, Latin + Türkçe alt kümesi, stb sıkıştırma + base85.",
                f"// Arayüz yazı ailesi: {ARAYUZ_YAZI_AILESI} (kimlik_uret.py ARAYUZ_YAZI_AILESI / ARAYUZ_YAZI_DOSYALARI).",
                '#include "arayuz/yazi.h"', "", "namespace op4 {", "namespace {", ""]
    kayitlar = []
    for ad, dosya, eksen, aciklama in YAZI_ORNEKLERI:
        f = TTFont(FONTLAR / dosya)
        ornek = instancer.instantiateVariableFont(f, eksen) if "fvar" in f and eksen else f
        sec = subset.Options()
        sec.layout_features = []
        sec.hinting = False
        sec.notdef_outline = True
        sec.name_IDs = [1, 2, 4, 6, 16, 17]
        sec.drop_tables += ["GSUB", "GPOS", "GDEF", "STAT", "DSIG", "MVAR", "HVAR"]
        alt = subset.Subsetter(sec)
        alt.populate(unicodes=SIMGE_KOD_NOKTALARI if ad == "kSimgeler" else YAZI_KOD_NOKTALARI)
        alt.subset(ornek)
        b = io.BytesIO()
        ornek.save(b)
        ham = b.getvalue()
        sik = _stb_sikistir(ham)
        b85 = _base85(sik)
        satirlar.append(f"// {aciklama}: {len(ham)} bayt TTF, {len(sik)} bayt sıkıştırılmış")
        satirlar.append(f"const char* const {ad}[] = {{")
        for i in range(0, len(b85), 16000):
            parca = b85[i:i + 16000]
            # "?" kaçışlanır (\?): "??x" üçlü karakter dizisi uyarısı (-Wtrigraphs) çıkmasın.
            satirlar.append("    \"" + "\"\n    \"".join(parca[k:k + 116].replace("?", "\\?") for k in range(0, len(parca), 116)) + "\",")
        satirlar.append("    nullptr};")
        satirlar.append("")
        kayitlar.append((ad, len(ham)))
        print(f"{ad}: {len(ham)} → {len(sik)} bayt")
    satirlar += ["}  // namespace", "", "const GomuluYazi* GomuluYazilar(size_t& sayi) {",
                 "    static const GomuluYazi y[] = {"]
    for (ad, dosya, eksen, aciklama), (_, boy) in zip(YAZI_ORNEKLERI, kayitlar):
        satirlar.append(f'        {{"{ad[1:]}", {ad}, {boy}u}},')
    satirlar += ["    };", "    sayi = sizeof(y) / sizeof(y[0]);", "    return y;", "}", "",
                 f'const char* ArayuzYaziAilesi() {{ return "{ARAYUZ_YAZI_AILESI}"; }}', "", "}  // namespace op4", ""]
    hedef = KAYNAK_ARAYUZ / "yazi_verisi.cpp"
    hedef.write_text("\n".join(satirlar), encoding="utf-8")
    return hedef


def kontur_uret() -> pathlib.Path:
    import json

    def fl(x):
        t = f"{float(x):g}"
        return (t if ("." in t or "e" in t) else t + ".0") + "f"

    k = json.loads((KIMLIK / "acilis" / "kontur.json").read_text(encoding="utf-8"))
    s = ["// op4 — açılış ekranı \"Kemer Çizgisi\" kalem yolları. ÜRETİLMİŞ DOSYA: python3 op4/araclar/kimlik_uret.py --kontur",
         "// Kaynak: op4/kimlik/acilis/kontur.json (simge PNG koordinatları, 1200 × 1397). Açılış çizimi (acilis.cpp) bunları",
         "// aciklama.md \"Yerleşim\" ölçeğiyle ekrana çevirir.",
         "#pragma once", "", "#include <cstddef>", "", "namespace op4::kontur {", "",
         "struct Nokta {", "    float x, y;", "};", "struct Kalem {", "    const char* ad;", "    const Nokta* p;",
         "    const float* g;", "    size_t n;", "};", "struct Yol {", "    const char* ad;", "    const Nokta* p;", "    size_t n;", "};", ""]
    def nokta_dizisi(ad, pts):
        s.append(f"inline constexpr Nokta {ad}[] = {{")
        satir = "    "
        for x, y in pts:
            parca = f"{{{fl(x)}, {fl(y)}}}, "
            if len(satir) + len(parca) > 118:
                s.append(satir.rstrip())
                satir = "    "
            satir += parca
        s.append(satir.rstrip())
        s.append("};")
    def sayi_dizisi(ad, v):
        s.append(f"inline constexpr float {ad}[] = {{")
        satir = "    "
        for x in v:
            parca = f"{fl(x)}, "
            if len(satir) + len(parca) > 118:
                s.append(satir.rstrip())
                satir = "    "
            satir += parca
        s.append(satir.rstrip())
        s.append("};")
    kalemler = []
    for ad, v in k["kalemler"].items():
        nokta_dizisi(f"k_{ad}_p", v["p"])
        sayi_dizisi(f"k_{ad}_g", v["g"])
        kalemler.append(ad)
    hayaletler = []
    for ad, pts in k["hayalet"].items():
        nokta_dizisi(f"h_{ad}", pts)
        hayaletler.append(ad)
    s.append("")
    s.append("inline constexpr Kalem KALEMLER[] = {")
    for ad in kalemler:
        s.append(f'    {{"{ad}", k_{ad}_p, k_{ad}_g, sizeof(k_{ad}_p) / sizeof(Nokta)}},')
    s.append("};")
    s.append("inline constexpr Yol HAYALETLER[] = {")
    for ad in hayaletler:
        s.append(f'    {{"{ad}", h_{ad}, sizeof(h_{ad}) / sizeof(Nokta)}},')
    s.append("};")
    o = k["olcu"]
    s += ["", "// Ölçüler (simge PNG pikseli)",
          f"inline constexpr float PNG_GEN = {fl(o['png'][0])}, PNG_YUK = {fl(o['png'][1])};",
          f"inline constexpr float KUTU_X0 = {fl(o['bbox'][0])}, KUTU_Y0 = {fl(o['bbox'][1])}, KUTU_X1 = {fl(o['bbox'][2])}, "
          f"KUTU_Y1 = {fl(o['bbox'][3])};",
          f"inline constexpr float CX = {fl(o['cx'])}, UZENGI_Y = {fl(o['uzengi_y'])}, TABAN_Y = {fl(o['taban_y'])};",
          f"inline constexpr float DIS_R = {fl(o['dis_r'])}, IC_R = {fl(o['ic_r'])};", "", "}  // namespace op4::kontur", ""]
    hedef = KAYNAK_ARAYUZ / "acilis_kontur.h"
    hedef.write_text("\n".join(s), encoding="utf-8")
    return hedef


BELIRTEC = KIMLIK.parent / "tasarim" / "atolye-modern" / "belirtec.py"


def _belirtec_yukle():
    import importlib.util
    tanim = importlib.util.spec_from_file_location("op4_belirtec", BELIRTEC)
    m = importlib.util.module_from_spec(tanim)
    tanim.loader.exec_module(m)
    return m


def tema_metni() -> str:
    """belirtec.py → tema_belirtec.h metni (deterministik; sınama güncelliği bununla denetler)."""
    b = _belirtec_yukle()

    def hx(h):
        return "0x" + h.lstrip("#").upper()

    def fl(x):
        t = f"{float(x):g}"
        return (t if ("." in t or "e" in t) else t + ".0") + "f"

    def sar(bas, ogeler, son):
        """Uzun ilklendirici satırlarını 120 sütunda böler."""
        satir = bas
        for i, oge in enumerate(ogeler):
            parca = oge + (", " if i + 1 < len(ogeler) else "")
            if len(satir) + len(parca.rstrip()) > 118:
                s.append(satir.rstrip())
                satir = "    "
            satir += parca
        s.append(satir + son)

    def renk_yapisi(ad, sozluk, aciklama):
        alanlar = [k for k, v in sozluk.items() if isinstance(v, str) and v.startswith("#")]
        s.append(f"// {aciklama}")
        s.append(f"struct {ad} {{")
        for i in range(0, len(alanlar), 8):
            s.append("    uint32_t " + ", ".join(alanlar[i:i + 8]) + ";")
        s.append("};")
        return alanlar

    def deger(sozluk, alanlar):
        return [hx(sozluk[k]) for k in alanlar]

    s = ["// op4 — arayüz belirteçleri. ÜRETİLMİŞ DOSYA: python3 op4/araclar/kimlik_uret.py --tema",
         "// Kaynak: op4/tasarim/atolye-modern/belirtec.py (Atölye · Modern, MIMARI §25.1). Elle düzenlenmez; renkler",
         "// 0xRRGGBB, ölçüler 1× mantıksal pikseldir. Kullanım: tema.h / tema.cpp (tema::RenkleriKur, tema::OlculeriKur).",
         "#pragma once", "", "#include <cstdint>", "", "namespace op4::tema::belirtec {", ""]
    notr = renk_yapisi("Notr", b.NOTR, "Nötr yüzeyler (üç palette ortak)")
    sar("inline constexpr Notr NOTR = {", deger(b.NOTR, notr), "};")
    s.append("")
    ilk = next(iter(b.PALETLER.values()))
    palet = renk_yapisi("PaletRenk", ilk, "Vurgu paleti (bronz / kahve–altın yok); rol tanımları belirtec.py başında")
    s.append("struct Palet {")
    s.append("    const char* kimlik;  // ayar değeri (\"kobalt\" | \"petrol\" | \"grafit\")")
    s.append("    const char* ad;      // görünen ad (Türkçe; Tr() ile çevrilir)")
    s.append("    PaletRenk r;")
    s.append("};")
    s.append(f"inline constexpr int PALET_SAYISI = {len(b.PALETLER)};")
    s.append("inline constexpr Palet PALETLER[PALET_SAYISI] = {")
    for kimlik, p in b.PALETLER.items():
        sar(f'    {{"{kimlik}", "{p["ad"]}", {{', deger(p, palet), "}},")
    s.append("};")
    s.append(f"inline constexpr int VARSAYILAN_PALET = {list(b.PALETLER).index(b.VARSAYILAN_PALET)};  // {b.VARSAYILAN_PALET}")
    s.append("")
    anlam = renk_yapisi("Anlam", b.ANLAM, "Anlamsal renkler (vurgudan bağımsız)")
    sar("inline constexpr Anlam ANLAM = {", deger(b.ANLAM, anlam), "};")
    s.append("")
    model = renk_yapisi("Model", b.MODEL, "Model (3B görünüm) nötr nesne renkleri ve arka plan")
    sar("inline constexpr Model MODEL = {", deger(b.MODEL, model), "};")
    s.append("")
    s.append("// D/C ölçeği (5 eşik)")
    s.append("inline constexpr uint32_t DC_RENK[5] = {" + ", ".join(hx(h) for h in b.DC_RENK) + "};")
    s.append("inline constexpr float DC_ESIK[4] = {" + ", ".join(fl(x) for x in b.DC_ESIK) + "};")
    s.append("")

    def sayi_yapisi(ad, sozluk, aciklama, tur="float"):
        s.append(f"// {aciklama}")
        s.append(f"struct {ad} {{")
        anahtar = list(sozluk)
        for i in range(0, len(anahtar), 8):
            s.append(f"    {tur} " + ", ".join(anahtar[i:i + 8]) + ";")
        s.append("};")
        return anahtar

    r = sayi_yapisi("Yaricap", b.R, "Yarıçaplar (px)")
    s.append("inline constexpr Yaricap R = {" + ", ".join(fl(b.R[k]) for k in r) + "};")
    a = sayi_yapisi("Aralik", b.A, "Aralık (8 px ızgara, 4 px yarım adım)")
    s.append("inline constexpr Aralik A = {" + ", ".join(fl(b.A[k]) for k in a) + "};")
    s.append("struct Golge {")
    s.append("    float bulaniklik, dy, saydamlik;")
    s.append("};")
    g = list(b.GOLGE)
    s.append("// Gölgeler (bulanıklık yarıçapı, dy, saydamlık)")
    s.append("struct Golgeler {")
    s.append("    Golge " + ", ".join(g) + ";")
    s.append("};")
    sar("inline constexpr Golgeler GOLGE = {", ["{" + ", ".join(fl(x) for x in b.GOLGE[k]) + "}" for k in g], "};")
    s.append("struct YaziRolu {")
    s.append("    float boy;")
    s.append("    int agirlik;  // 400 · 500 · 600")
    s.append("};")
    y = list(b.Y)
    s.append("// Yazı ölçeği (Inter; boyut px @1×, ağırlık)")
    s.append("struct YaziOlcegi {")
    for i in range(0, len(y), 6):
        s.append("    YaziRolu " + ", ".join(y[i:i + 6]) + ";")
    s.append("};")
    sar("inline constexpr YaziOlcegi Y = {", [f"{{{fl(b.Y[k][0])}, {b.Y[k][1]}}}" for k in y], "};")
    s.append("")
    o = sayi_yapisi("Olcu", b.OLCU["rahat"], "Modül ölçüleri; \"rahat\" ≥ 1600×900, \"siki\" daha küçük ekranda")
    for yogunluk in ("rahat", "siki"):
        sar(f"inline constexpr Olcu OLCU_{yogunluk.upper()} = {{", [fl(b.OLCU[yogunluk][k]) for k in o], "};")
    s += ["", "}  // namespace op4::tema::belirtec", ""]
    return "\n".join(s)


def tema_uret() -> pathlib.Path:
    hedef = KAYNAK_ARAYUZ / "tema_belirtec.h"
    hedef.write_text(tema_metni(), encoding="utf-8")
    return hedef


def main() -> None:
    ap = argparse.ArgumentParser(description="op4 simgesi ve kurulum sihirbazı görselleri (Opus Fortis kimliğinden)")
    ap.add_argument("--sihirbaz", type=pathlib.Path, metavar="KLASÖR",
                    help="kurulum sihirbazı BMP'lerini bu klasöre yaz (op4.ico üretilmez)")
    ap.add_argument("--yazi", action="store_true", help="gömülü yazı tiplerini üret (kaynak/arayuz/yazi_verisi.cpp)")
    ap.add_argument("--kontur", action="store_true", help="açılış kontur başlığını üret (kaynak/arayuz/acilis_kontur.h)")
    ap.add_argument("--tema", action="store_true", help="arayüz belirteç başlığını üret (kaynak/arayuz/tema_belirtec.h)")
    a = ap.parse_args()
    if a.yazi or a.kontur or a.tema:
        if a.tema:
            print(tema_uret())
        if a.yazi:
            print(yazi_uret())
        if a.kontur:
            print(kontur_uret())
        return
    if a.sihirbaz:
        for yol in sihirbaz_uret(a.sihirbaz):
            with Image.open(yol) as im:
                print(yol.name, f"{im.width}x{im.height}", yol.stat().st_size, "bayt")
        return
    hedef = simge_uret()
    print(hedef.name, hedef.stat().st_size, "bayt")


if __name__ == "__main__":
    main()
