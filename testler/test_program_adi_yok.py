# -*- coding: utf-8 -*-
"""Bekçi testi: depoda başka yazılım ürünlerinin adı geçmez.

Kullanıcı kuralı: uygulamanın hiçbir yerinde (dersler, arayüz metinleri, belgeler, kod yorumları, testler,
dosya adları) başka programların adı geçmez. Yerine "ticari yapı analiz programları", "yaygın yapı analiz
programları", "sonlu eleman programları" gibi genel ifadeler kullanılır. Programlama dili, kütüphane ve standart
adları (Python, NumPy, SymPy, Pyodide, KaTeX, IFC, DXF, AISC 360, Eurocode, TS, TBDY...) serbesttir.

Tarama `git ls-files` ile izlenen metin dosyalarında yapılır. Yasak adlar bu dosyada parçalı yazılır
(ör. "SAP" + "2000"); böylece test kendi listesini yakalamaz.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
UZANTILAR = {".py", ".js", ".md", ".html", ".css", ".json", ".yml", ".yaml", ".txt", ".ipynb", ".cmd", ".webmanifest"}

# Yasak ürün adları (büyük/küçük harf duyarsız). Parçalı yazım bilinçlidir.
_YASAK = [
    r"\bsap\s?" + "2000",
    "et" + "abs",
    r"\bsa" + r"fe\b",
    r"\bc" + r"si\b",
    "an" + "sys",
    "aba" + "qus",
    "open" + "sees",
    "ex" + "cel",
    "auto" + "cad",
    "re" + "vit",
    "tek" + "la",
    r"\bro" + r"bot\b",
    "ide" + "cad",
    "pro" + "bina",
    "sta4" + "cad",
    "mat" + "lab",
    "math" + "cad",
    r"\bmi" + r"das\b",
    "st" + "aad",
]
YASAK = re.compile("|".join(f"(?:{d})" for d in _YASAK), re.IGNORECASE)

# Yanlış pozitifler: CSS'teki güvenli alan değişkenleri (ör. env(safe-area-inset-top)) ve masaüstü paket kilit
# dosyasındaki npm paket adları (sa""fe-buffer, json-stringify-sa""fe: İngilizce "güvenli" sözcüğü).
_ISTISNA = re.compile(r"sa" r"fe-area-inset|env\(sa" r"fe-|\bsa" r"fe-buffer\b|stringify-sa" r"fe\b", re.IGNORECASE)


def _izlenen_dosyalar() -> list[Path]:
    try:
        cikti = subprocess.run(["git", "ls-files", "-z"], cwd=KOK, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git ls-files çalışmadı (git deposu değil)")
    yollar = [KOK / p for p in cikti.decode("utf-8").split("\0") if p]
    return [p for p in yollar if p.suffix.lower() in UZANTILAR and p.is_file()]


def test_yasak_liste_kendini_yakalamaz():
    metin = Path(__file__).read_text(encoding="utf-8")
    assert not YASAK.search(_ISTISNA.sub("", metin))
    # liste gerçekten çalışır
    for ornek in ("SAP" + "2000", "Sap " + "2000", "ETA" + "BS", "Open" + "SeesPy", "Ex" + "cel", "C" + "SI", "SA" + "FE ile döşeme"):
        assert YASAK.search(_ISTISNA.sub("", ornek)), ornek
    for serbest in ("env(safe-area-inset-top)", "Roboto", "robots", "Python", "NumPy", "AISC 360", "DXF", "IFC",
                    '"sa' 'fe-buffer": "~5.1.1"', "node_modules/json-stringify-sa" "fe"):
        assert not YASAK.search(_ISTISNA.sub("", serbest)), serbest


def test_dosya_adlarinda_program_adi_yok():
    yollar = subprocess.run(["git", "ls-files"], cwd=KOK, capture_output=True, text=True).stdout.splitlines()
    kotu = [y for y in yollar if YASAK.search(y)]
    assert not kotu, "Dosya adında başka program adı: " + ", ".join(kotu)


def test_metinlerde_program_adi_yok():
    kendisi = Path(__file__).resolve()
    bulunan = []
    for yol in _izlenen_dosyalar():
        if yol.resolve() == kendisi:
            continue
        try:
            metin = yol.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for no, satir in enumerate(metin.splitlines(), 1):
            m = YASAK.search(_ISTISNA.sub("", satir))
            if m:
                bulunan.append(f"{yol.relative_to(KOK).as_posix()}:{no}: {m.group(0)!r}")
    assert not bulunan, "Başka program adı geçen satırlar:\n" + "\n".join(bulunan)
