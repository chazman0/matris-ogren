# -*- coding: utf-8 -*-
"""Opus Fortis kimlik dosyalarından op4 uygulama simgesini (op4/kimlik/op4.ico) üretir.

Kaynak: op4/kimlik/opus-fortis-simge-renkli.png (kahve kemer + krem kilit taşı, saydam zemin, 1200 × 1397).
Simge kareye ortalanır, kenar boşluğu kırpılır; 16 … 256 piksellik katmanlar yüksek kaliteli küçültmeyle yazılır.
Küçük boyutlarda (≤ 24 px) kemer çizgisi kalın kalsın diye kırpma daha sıkıdır.

Kullanım:  python3 op4/araclar/kimlik_uret.py   (Pillow gerekir; çıktı depoya işlenir, derleme sırasında çalışmaz)
"""
from __future__ import annotations

import pathlib

from PIL import Image

KIMLIK = pathlib.Path(__file__).resolve().parent.parent / "kimlik"
KAYNAK = KIMLIK / "opus-fortis-simge-renkli.png"
BOYLAR = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def kare(im: Image.Image, bosluk: float) -> Image.Image:
    kutu = im.getbbox() or (0, 0, im.width, im.height)
    parca = im.crop(kutu)
    kenar = int(max(parca.width, parca.height) * (1.0 + 2.0 * bosluk))
    tuval = Image.new("RGBA", (kenar, kenar), (0, 0, 0, 0))
    tuval.alpha_composite(parca, ((kenar - parca.width) // 2, (kenar - parca.height) // 2))
    return tuval


def main() -> None:
    im = Image.open(KAYNAK).convert("RGBA")
    katmanlar = []
    for b in BOYLAR:
        k = kare(im, 0.02 if b <= 24 else 0.06)
        katmanlar.append(k.resize((b, b), Image.LANCZOS))
    hedef = KIMLIK / "op4.ico"
    katmanlar[-1].save(hedef, sizes=[(b, b) for b in BOYLAR], append_images=katmanlar[:-1])
    print(hedef.name, hedef.stat().st_size, "bayt")


if __name__ == "__main__":
    main()
