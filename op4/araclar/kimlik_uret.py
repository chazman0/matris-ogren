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

Kullanım:  python3 op4/araclar/kimlik_uret.py                       (op4.ico; Pillow gerekir)
           python3 op4/araclar/kimlik_uret.py --sihirbaz <klasör>   (sihirbaz görselleri)
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


def main() -> None:
    ap = argparse.ArgumentParser(description="op4 simgesi ve kurulum sihirbazı görselleri (Opus Fortis kimliğinden)")
    ap.add_argument("--sihirbaz", type=pathlib.Path, metavar="KLASÖR",
                    help="kurulum sihirbazı BMP'lerini bu klasöre yaz (op4.ico üretilmez)")
    a = ap.parse_args()
    if a.sihirbaz:
        for yol in sihirbaz_uret(a.sihirbaz):
            with Image.open(yol) as im:
                print(yol.name, f"{im.width}x{im.height}", yol.stat().st_size, "bayt")
        return
    hedef = simge_uret()
    print(hedef.name, hedef.stat().st_size, "bayt")


if __name__ == "__main__":
    main()
