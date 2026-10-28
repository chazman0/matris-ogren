# -*- coding: utf-8 -*-
"""Colab defteri (Matris_Ogren.ipynb) matris modülüyle eşleşik mi?

Defter ``defter_yap.py`` ile üretilir ve kurulum hücresine ``matris_ogren.py``'yi zlib + base64 olarak gömer. Modül değişip
defter yeniden üretilmezse Colab'daki öğrenci eski modülü çalıştırır; bu test bunu yakalar. Düzeltme:
``uv run --no-project --python 3.13 --with nbformat python3 defter_yap.py`` (ya da ``pip install nbformat`` ile).
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import zlib
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
DEFTER = KOK / "Matris_Ogren.ipynb"
MODUL = KOK / "matris_ogren.py"
YENIDEN = "Defteri yeniden üretin: uv run --no-project --python 3.13 --with nbformat python3 defter_yap.py"


def _kurulum_hucresi() -> str:
    if not DEFTER.exists():
        pytest.skip("Matris_Ogren.ipynb yok")
    nb = json.loads(DEFTER.read_text(encoding="utf-8"))
    for h in nb.get("cells", []):
        kaynak = h.get("source", "")
        metin = "".join(kaynak) if isinstance(kaynak, list) else kaynak
        if h.get("cell_type") == "code" and "_SHA256 = " in metin:
            return metin
    pytest.fail("Defterde kurulum hücresi (_SHA256 satırı) bulunamadı.")


def test_defterdeki_ozet_modulle_ayni():
    hucre = _kurulum_hucresi()
    m = re.search(r'^_SHA256 = "([0-9a-f]{64})"$', hucre, re.M)
    assert m, "kurulum hücresinde _SHA256 satırı yok"
    gercek = hashlib.sha256(MODUL.read_bytes()).hexdigest()
    assert m.group(1) == gercek, (f"Defterdeki gömülü modül eski (_SHA256 {m.group(1)[:12]}…, matris_ogren.py {gercek[:12]}…). "
                                  + YENIDEN)


def test_gomulu_paket_modulun_kendisi():
    """Bildirilen özet yetmez: gömülü paket açılınca matris_ogren.py'nin baytları çıkmalı, sürüm etiketi de aynı olmalı."""
    hucre = _kurulum_hucresi()
    paket = re.search(r"^_PAKET = \(\n(.*?)\n\)$", hucre, re.M | re.S)
    assert paket, "kurulum hücresinde _PAKET bloğu yok"
    b64 = "".join(re.findall(r'"([A-Za-z0-9+/=]+)"', paket.group(1)))
    kaynak = zlib.decompress(base64.b64decode(b64))
    assert kaynak == MODUL.read_bytes(), "gömülü paket matris_ogren.py ile aynı değil. " + YENIDEN
    surum = re.search(r'^__version__\s*=\s*"([^"]+)"', kaynak.decode("utf-8"), re.M).group(1)
    assert f'_SURUM = "{surum}"' in hucre
