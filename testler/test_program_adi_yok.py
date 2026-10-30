# -*- coding: utf-8 -*-
"""Bekçi testi: depoda başka yazılım ürünlerinin adı geçmez.

Kullanıcı kuralı: uygulamanın hiçbir yerinde (dersler, arayüz metinleri, belgeler, kod yorumları, testler,
dosya adları) başka programların adı geçmez. Yerine "ticari yapı analiz programları", "yaygın yapı analiz
programları", "sonlu eleman programları" gibi genel ifadeler kullanılır. Programlama dili, kütüphane ve standart
adları (Python, NumPy, SymPy, Pyodide, KaTeX, IFC, DXF, AISC 360, Eurocode, TS, TBDY...) serbesttir.

Tarama `git ls-files` ile izlenen metin dosyalarında yapılır (op4'ün C++, HLSL, CMake, kaynak, bildirim ve kurulum
dosyaları dahil). Yasak adlar bu dosyada parçalı yazılır (ör. "SAP" + "2000"); böylece test kendi listesini yakalamaz.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
UZANTILAR = {".py", ".js", ".md", ".html", ".css", ".json", ".yml", ".yaml", ".txt", ".ipynb", ".cmd", ".webmanifest",
             # op4 (yerel Windows programı): C++ ve HLSL kaynakları, CMake, kurulum betikleri, kaynak / bildirim dosyaları
             ".cpp", ".h", ".hpp", ".hlsl", ".cmake", ".iss", ".nsi", ".rc", ".in", ".manifest", ".ini", ".ps1", ".sh"}

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
    return [p for p in yollar if p.is_file() and (p.suffix.lower() in UZANTILAR or _uzantisiz_taranir(p))]


# op4/ ve .github/ altında uzantısı listede olmayan metin dosyaları da (.gitignore, CMakePresets vb.) taranır;
# görüntü ve ikili dosyalar UTF-8 çözülemediği için zaten atlanır, bunlar baştan ayıklanır.
TAM_TARANAN = {"op4", ".github"}
IKILI = {".png", ".ico", ".bmp", ".jpg", ".jpeg", ".gif", ".webp", ".exe", ".dll", ".zip", ".pyc", ".ttf", ".otf"}


def _uzantisiz_taranir(yol: Path) -> bool:
    goreli = yol.relative_to(KOK).parts
    return bool(goreli) and goreli[0] in TAM_TARANAN and yol.suffix.lower() not in IKILI


def test_yasak_liste_kendini_yakalamaz():
    metin = Path(__file__).read_text(encoding="utf-8")
    assert not YASAK.search(_ISTISNA.sub("", metin))
    # liste gerçekten çalışır
    for ornek in ("SAP" + "2000", "Sap " + "2000", "ETA" + "BS", "Open" + "SeesPy", "Ex" + "cel", "C" + "SI", "SA" + "FE ile döşeme"):
        assert YASAK.search(_ISTISNA.sub("", ornek)), ornek
    for serbest in ("env(safe-area-inset-top)", "Roboto", "robots", "Python", "NumPy", "AISC 360", "DXF", "IFC",
                    '"sa' 'fe-buffer": "~5.1.1"', "node_modules/json-stringify-sa" "fe"):
        assert not YASAK.search(_ISTISNA.sub("", serbest)), serbest


def test_op4_ve_is_akislari_taraniyor():
    """op4'ün C++, HLSL, CMake, kurulum ve bildirim dosyaları ile iş akışları taramaya girer."""
    for ek in (".cpp", ".h", ".hpp", ".hlsl", ".cmake", ".iss", ".nsi", ".rc", ".in", ".manifest", ".ini", ".ps1", ".sh"):
        assert ek in UZANTILAR, ek
    taranan = {p.relative_to(KOK).as_posix() for p in _izlenen_dosyalar()}
    for yol in ("op4/kaynak/ana.cpp", "op4/kaynak/grafik.h", "op4/kurulum/op4.iss", "op4/kaynak/op4.rc.in",
                "op4/kaynak/op4.manifest", "op4/araclar/mingw.cmake", "op4/.gitignore", ".github/workflows/op4.yml"):
        if (KOK / yol).is_file():
            assert yol in taranan, yol
    assert not any(y.endswith((".png", ".ico")) for y in taranan)


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
