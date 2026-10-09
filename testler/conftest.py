# -*- coding: utf-8 -*-
"""pytest ortak ayarları.

- Üst klasörü (matris_ogren.py'nin bulunduğu proje klasörü) sys.path'e ekler.
- Her testten önce anlatımı susturur (goster="yok"); test bitince eski ayarları geri yükler,
  böylece her test bağımsızdır.

Çalıştırma (proje klasöründen):
  uv run --python 3.13 --with sympy --with numpy --with pytest python -m pytest testler -q
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
if str(PROJE) not in sys.path:
    sys.path.insert(0, str(PROJE))

import matris_ogren as mo  # noqa: E402


@pytest.fixture(autouse=True)
def sessiz_ayarlar():
    """Anlatım basılmaz; test sonunda ayarlar (ondalik, basamak, python, kural, goster...) geri alınır."""
    eski = dataclasses.asdict(mo.ayarlar)
    mo.ayarla(goster="yok")
    try:
        yield mo.ayarlar
    finally:
        for anahtar, deger in eski.items():
            setattr(mo.ayarlar, anahtar, deger)
