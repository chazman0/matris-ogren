# -*- coding: utf-8 -*-
"""op4 kimlik dosyalarının YER TUTUCU sürümlerini üretir (Opus Fortis logosu henüz gelmedi).

Üretilenler (op4/kimlik/):
  opus_fortis_logo_placeholder.png   açılış ekranındaki logo yuvası (saydam zemin, 880 x 280)
  op4_simge_placeholder.ico          uygulama / kurulum simgesi (16 … 256 px)
  op4_simge_placeholder.png          aynı simgenin 256 px PNG'si (belgeler için)

Gerçek logo geldiğinde bu betik çalıştırılmaz: kimlik/README.md'deki adlarla (logo.png, op4.ico) dosyalar eklenir; program
ve kurulum önce gerçek dosyaları, yoksa yer tutucuları kullanır.

Kullanım:  python3 op4/araclar/yer_tutucu_kimlik.py   (Pillow gerekir)
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

KIMLIK = pathlib.Path(__file__).resolve().parent.parent / "kimlik"
LACIVERT = (24, 40, 64, 255)
ALTIN = (201, 162, 39, 255)
GRI = (120, 128, 140, 255)

ADAYLAR = {
    "kalin": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/segoeuib.ttf"],
    "yari": ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "C:/Windows/Fonts/seguisb.ttf"],
    "normal": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "C:/Windows/Fonts/segoeui.ttf"],
}


def yazi_tipi(tur: str, boy: int):
    for yol in ADAYLAR[tur]:
        if pathlib.Path(yol).exists():
            return ImageFont.truetype(yol, boy)
    return ImageFont.load_default(boy)


def amblem(boy: int) -> Image.Image:
    """Yuvarlatılmış lacivert kare içinde altın çizgili 'OF' monogramı (yer tutucu)."""
    olcek = 4  # yumuşak kenar için büyük çiz, küçült
    b = boy * olcek
    im = Image.new("RGBA", (b, b), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, b - 1, b - 1], radius=int(b * 0.18), fill=LACIVERT)
    d.rounded_rectangle([int(b * 0.07), int(b * 0.07), b - 1 - int(b * 0.07), b - 1 - int(b * 0.07)],
                        radius=int(b * 0.13), outline=ALTIN, width=max(2, int(b * 0.025)))
    f = yazi_tipi("kalin", int(b * 0.46))
    metin = "OF"
    x0, y0, x1, y1 = d.textbbox((0, 0), metin, font=f)
    d.text(((b - (x1 - x0)) / 2 - x0, (b - (y1 - y0)) / 2 - y0), metin, font=f, fill=(255, 255, 255, 255))
    return im.resize((boy, boy), Image.LANCZOS)


def logo() -> Image.Image:
    g, y = 880, 280
    olcek = 2
    im = Image.new("RGBA", (g * olcek, y * olcek), (0, 0, 0, 0))
    am = amblem(200 * olcek)
    im.alpha_composite(am, (20 * olcek, 40 * olcek))
    d = ImageDraw.Draw(im)
    f1 = yazi_tipi("kalin", 84 * olcek)
    f2 = yazi_tipi("normal", 30 * olcek)
    f3 = yazi_tipi("yari", 20 * olcek)
    d.text((250 * olcek, 52 * olcek), "OPUS FORTIS", font=f1, fill=LACIVERT)
    d.line([(254 * olcek, 168 * olcek), (840 * olcek, 168 * olcek)], fill=ALTIN, width=4 * olcek)
    d.text((254 * olcek, 182 * olcek), "Mühendislik · Yapı Yazılımları", font=f2, fill=GRI)
    # Yer tutucu olduğu açıkça görünsün.
    d.text((254 * olcek, 232 * olcek), "YER TUTUCU — gerçek logo: kimlik/logo.png", font=f3,
           fill=(190, 60, 60, 255))
    return im.resize((g, y), Image.LANCZOS)


def simge(boy: int) -> Image.Image:
    olcek = 4
    b = boy * olcek
    im = Image.new("RGBA", (b, b), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, b - 1, b - 1], radius=int(b * 0.2), fill=LACIVERT)
    d.rectangle([int(b * 0.12), int(b * 0.78), int(b * 0.88), int(b * 0.83)], fill=ALTIN)
    f = yazi_tipi("kalin", int(b * (0.42 if boy >= 32 else 0.5)))
    metin = "op4"
    x0, y0, x1, y1 = d.textbbox((0, 0), metin, font=f)
    d.text(((b - (x1 - x0)) / 2 - x0, (b * 0.9 - (y1 - y0)) / 2 - y0), metin, font=f, fill=(255, 255, 255, 255))
    return im.resize((boy, boy), Image.LANCZOS)


def main() -> None:
    KIMLIK.mkdir(parents=True, exist_ok=True)
    logo().save(KIMLIK / "opus_fortis_logo_placeholder.png", optimize=True)
    buyuk = simge(256)
    buyuk.save(KIMLIK / "op4_simge_placeholder.png", optimize=True)
    boylar = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    ana = simge(256)
    ana.save(KIMLIK / "op4_simge_placeholder.ico", sizes=[(s, s) for s in boylar],
             append_images=[simge(s) for s in boylar if s != 256])
    for ad in ("opus_fortis_logo_placeholder.png", "op4_simge_placeholder.ico", "op4_simge_placeholder.png"):
        print(ad, (KIMLIK / ad).stat().st_size, "bayt")


if __name__ == "__main__":
    main()
