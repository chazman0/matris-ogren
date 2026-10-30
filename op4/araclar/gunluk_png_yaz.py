# -*- coding: utf-8 -*-
"""CI'da PNG görüntülerini iş günlüğüne base64 olarak yazar (MIMARI §20.3 günlük protokolü).

Yapıtlar (artifact) ve ham günlük adresi bazı ortamlardan indirilemez; görüntüler bu yüzden günlüğün içinde taşınır ve
`gunluk_png_coz.py` ile geri çözülür. Her görüntü bir `::group::` bloğuna katlanır:

    ::group::OP4-PNG sahne
    OP4-PNG ad=sahne bayt=48211 gunluk_bayt=17012 sha256=<hex> gen=640 yuk=360
    -----OP4-PNG-BASLA-----
    <base64, satır başına 100 karakter>
    -----OP4-PNG-BITIR-----
    ::endgroup::

`bayt` asıl PNG'nin, `gunluk_bayt` ve `sha256` günlüğe yazılan kopyanın boyutu ve özetidir. Kopya, Pillow varsa 256
renge indirgenir (≈ 3 kat küçük); Pillow yoksa asıl dosya olduğu gibi yazılır.

Kullanım:  python op4/araclar/gunluk_png_yaz.py ad=dosya.png [ad2=dosya2.png ...] [--indirgeme-yok] [--sinir-kb 300]
Çıkış kodu: 0 her görüntü yazıldı; 2 dosya yok ya da sınırı aşıyor (yine de diğerleri yazılır).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import pathlib
import struct
import sys

BASLA = "-----OP4-PNG-BASLA-----"
BITIR = "-----OP4-PNG-BITIR-----"
SATIR = 100


def png_boyutu(veri: bytes) -> tuple[int, int]:
    """PNG IHDR'den genişlik ve yükseklik (Pillow gerekmez)."""
    if veri[:8] != b"\x89PNG\r\n\x1a\n" or veri[12:16] != b"IHDR":
        return 0, 0
    return struct.unpack(">II", veri[16:24])


def indirge(veri: bytes) -> bytes:
    try:
        from PIL import Image
    except ImportError:
        return veri
    try:
        im = Image.open(io.BytesIO(veri)).convert("RGB").quantize(256)
        cikti = io.BytesIO()
        im.save(cikti, format="PNG", optimize=True)
        kucuk = cikti.getvalue()
    except Exception:  # bozuk / okunamayan dosya: olduğu gibi yaz
        return veri
    return kucuk if len(kucuk) < len(veri) else veri


def blok(ad: str, asil: bytes, gunluk: bytes) -> str:
    gen, yuk = png_boyutu(asil)
    b64 = base64.b64encode(gunluk).decode("ascii")
    satirlar = [
        f"::group::OP4-PNG {ad}",
        f"OP4-PNG ad={ad} bayt={len(asil)} gunluk_bayt={len(gunluk)} sha256={hashlib.sha256(gunluk).hexdigest()} "
        f"gen={gen} yuk={yuk}",
        BASLA,
        *(b64[i:i + SATIR] for i in range(0, len(b64), SATIR)),
        BITIR,
        "::endgroup::",
    ]
    return "\n".join(satirlar) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("goruntuler", nargs="+", metavar="ad=dosya.png")
    ap.add_argument("--indirgeme-yok", action="store_true", help="256 renge indirgeme yapma")
    ap.add_argument("--sinir-kb", type=int, default=300, help="günlük kopyası için üst sınır (KB; MIMARI §20.3)")
    a = ap.parse_args(argv)
    kod = 0
    for oge in a.goruntuler:
        ad, _, yol = oge.partition("=")
        if not yol:
            ad, yol = pathlib.Path(oge).stem, oge
        dosya = pathlib.Path(yol)
        if not dosya.is_file():
            print(f"OP4-PNG ad={ad} HATA: {yol} yok", flush=True)
            kod = 2
            continue
        asil = dosya.read_bytes()
        gunluk = asil if a.indirgeme_yok else indirge(asil)
        if len(gunluk) > a.sinir_kb * 1024:
            print(f"OP4-PNG ad={ad} HATA: günlük kopyası {len(gunluk)} bayt, sınır {a.sinir_kb} KB", flush=True)
            kod = 2
            continue
        sys.stdout.write(blok(ad, asil, gunluk))
        sys.stdout.flush()
    return kod


if __name__ == "__main__":
    sys.exit(main())
