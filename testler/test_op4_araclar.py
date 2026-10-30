# -*- coding: utf-8 -*-
"""op4 CI araçları ve iş akışı sözleşmesi (op4/MIMARI.md §18.1, §20).

* op4/araclar/gunluk_png_yaz.py ↔ gunluk_png_coz.py: günlük protokolü gidiş-dönüşü (zaman damgalı satırlar, ::group::
  katlaması, günlük aracının JSON kaydı), sha256 ve boyut denetimi, kesik blok, eski (özetsiz) biçim.
* .github/workflows/op4.yml: tetikleyiciler, sabit Windows imajı, engelleyici pencere testi, etikette yayın işi,
  işleme özetiyle sabitlenmiş eylemler.
* Sürüm tek kaynaktan: op4/CMakeLists.txt OP4_TABAN_SURUM = op4.iss varsayılanı.
* kimlik_uret.py --sihirbaz: Inno Setup'ın önerdiği boyutlarda 24 bit BMP'ler (Pillow varsa).
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import struct
import zlib
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
ARACLAR = KOK / "op4" / "araclar"


def _modul(ad: str):
    spec = importlib.util.spec_from_file_location(f"op4_{ad}", ARACLAR / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


yaz = _modul("gunluk_png_yaz")
coz = _modul("gunluk_png_coz")


def _png(gen: int = 7, yuk: int = 5) -> bytes:
    """Pillow'suz küçük RGB PNG."""
    def parca(tur: bytes, veri: bytes) -> bytes:
        return struct.pack(">I", len(veri)) + tur + veri + struct.pack(">I", zlib.crc32(tur + veri) & 0xFFFFFFFF)
    ham = b"".join(b"\x00" + bytes(c for x in range(gen) for c in (x * 30 % 256, y * 40 % 256, 128))
                   for y in range(yuk))
    return (b"\x89PNG\r\n\x1a\n" + parca(b"IHDR", struct.pack(">IIBBBBB", gen, yuk, 8, 2, 0, 0, 0))
            + parca(b"IDAT", zlib.compress(ham)) + parca(b"IEND", b""))


def _ci_gunlugu(govde: str) -> str:
    """GitHub iş günlüğü biçimi: BOM, zaman damgası, ::group:: → ##[group], CRLF."""
    satirlar = []
    for i, s in enumerate(govde.splitlines()):
        s = s.replace("::group::", "##[group]").replace("::endgroup::", "##[endgroup]")
        satirlar.append(f"2026-10-30T13:30:{i % 60:02d}.{1234567 + i}Z {s}")
    return "﻿" + "\r\n".join(satirlar) + "\r\n"


def test_png_boyutu():
    assert yaz.png_boyutu(_png(7, 5)) == (7, 5)
    assert yaz.png_boyutu(b"degil") == (0, 0)


def test_gidis_donus_ham_gunluk_ve_json_kaydi(tmp_path):
    a, b = _png(7, 5), _png(3, 9)
    govde = ("Run python op4/araclar/gunluk_png_yaz.py sahne=sahne.png\n" + yaz.blok("sahne", a + b"x", a)
             + "OP4OLCUM senaryo=ekran gen=7 yuk=5\n" + yaz.blok("acilis", b, b))
    assert "::group::OP4-PNG sahne" in govde and f"sha256={hashlib.sha256(a).hexdigest()}" in govde
    assert all(len(s) <= 100 for s in govde.splitlines() if re.fullmatch(r"[A-Za-z0-9+/=]+", s))
    gunluk = _ci_gunlugu(govde)
    # 1) ham günlük
    (tmp_path / "ham.log").write_text(gunluk, encoding="utf-8")
    assert coz.main([str(tmp_path / "ham.log"), str(tmp_path / "c1"), "--olcum"]) == 0
    assert (tmp_path / "c1" / "sahne.png").read_bytes() == a
    assert (tmp_path / "c1" / "acilis.png").read_bytes() == b
    # 2) günlük aracının JSON kaydı, iç içe metin olarak
    kayit = [{"type": "text", "text": json.dumps({"job_id": 1, "logs_content": gunluk, "message": "ok"})}]
    (tmp_path / "kayit.json").write_text(json.dumps(kayit), encoding="utf-8")
    bloklar, olcumler = coz.coz(coz.gunluk_metni((tmp_path / "kayit.json").read_text(encoding="utf-8")), tmp_path / "c2")
    assert [x["durum"] for x in bloklar] == ["doğrulandı", "doğrulandı"]
    assert [x["gen"] for x in bloklar] == ["7", "3"]
    assert olcumler == ["OP4OLCUM senaryo=ekran gen=7 yuk=5"]


def test_bozuk_ve_kesik_bloklar(tmp_path):
    a = _png()
    govde = yaz.blok("sahne", a, a)
    satirlar = govde.splitlines()
    i = satirlar.index(coz.BASLA) + 1
    satirlar[i] = ("B" if satirlar[i][0] != "B" else "C") + satirlar[i][1:]
    (tmp_path / "bozuk.log").write_text(_ci_gunlugu("\n".join(satirlar)), encoding="utf-8")
    assert coz.main([str(tmp_path / "bozuk.log"), str(tmp_path / "c")]) == 2
    kesik = govde.split(coz.BITIR)[0]
    (tmp_path / "kesik.log").write_text(_ci_gunlugu(kesik), encoding="utf-8")
    bloklar, _ = coz.coz(coz.gunluk_metni(_ci_gunlugu(kesik)), tmp_path / "c")
    assert bloklar[0]["durum"].startswith("kesik")
    (tmp_path / "bos.log").write_text("hiçbir şey\n", encoding="utf-8")
    assert coz.main([str(tmp_path / "bos.log"), str(tmp_path / "c")]) == 1


def test_eski_ozetsiz_bicim_ve_betik_yankisi(tmp_path):
    """Deneme günlüğü biçimi (sha256 yok) ve iş akışı betiğinin günlüğe yansıyan satırları."""
    a = _png()
    b64 = base64.b64encode(a).decode()
    govde = "\n".join([
        'echo "-----OP4-PNG-BASLA-----"',  # betik yankısı: işaret değildir
        f"OP4-PNG ad=onizleme bayt={len(a)} gunluk_bayt={len(a)}",
        coz.BASLA, b64, coz.BITIR,
    ])
    bloklar, _ = coz.coz(coz.gunluk_metni(_ci_gunlugu(govde)), tmp_path)
    assert len(bloklar) == 1 and bloklar[0]["durum"] == "özetsiz (doğrulanamadı)"
    assert (tmp_path / "onizleme.png").read_bytes() == a


def test_yaz_sinir_ve_eksik_dosya(tmp_path, capsys):
    (tmp_path / "a.png").write_bytes(_png())
    assert yaz.main([f"a={tmp_path / 'a.png'}", "--indirgeme-yok"]) == 0
    assert "OP4-PNG ad=a " in capsys.readouterr().out
    assert yaz.main([f"b={tmp_path / 'yok.png'}"]) == 2
    assert yaz.main([f"a={tmp_path / 'a.png'}", "--indirgeme-yok", "--sinir-kb", "0"]) == 2


def _is_akisi() -> dict:
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load((KOK / ".github" / "workflows" / "op4.yml").read_text(encoding="utf-8"))


def test_op4_is_akisi_sozlesmesi():
    d = _is_akisi()
    on = d.get("on", d.get(True))
    assert {"main", "claude/**"} <= set(on["push"]["branches"])
    assert on["push"]["tags"] == ["op4-v*"]
    assert "pull_request" in on and "workflow_dispatch" in on
    for yol in ("op4/**", "docs/*.js", "docs/*.py", "*.py", ".github/workflows/op4.yml"):
        assert yol in on["push"]["paths"] and yol in on["pull_request"]["paths"]
    win = d["jobs"]["windows"]
    assert win["runs-on"] == "windows-2025"
    adimlar = win["steps"]
    assert not [a["name"] for a in adimlar if "continue-on-error" in a], "engelleyici olmayan adım var"
    pencere = [a for a in adimlar if "--test-pencere" in a.get("run", "")]
    assert pencere and "if" not in pencere[0]
    assert any("--hata-katmani" in a.get("run", "") for a in adimlar)
    assert any("license.txt" in a.get("run", "") for a in adimlar)
    assert any("gunluk_png_yaz.py" in a.get("run", "") for a in adimlar)
    yay = d["jobs"]["yayinla"]
    assert yay["needs"] == "windows" and "refs/tags/op4-v" in yay["if"]
    assert yay["permissions"] == {"contents": "write"} and d["permissions"] == {"contents": "read"}
    assert "op4-setup-$OP4_SURUM.exe" in yay["steps"][-1]["run"]
    for is_ in d["jobs"].values():
        for a in is_["steps"]:
            if "uses" in a:
                assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", a["uses"]), a["uses"]


def test_surum_tek_kaynak():
    cmake = (KOK / "op4" / "CMakeLists.txt").read_text(encoding="utf-8")
    m = re.search(r'^set\(OP4_TABAN_SURUM "(\d+\.\d+\.\d+)"\)', cmake, re.M)
    assert m, "op4/CMakeLists.txt: OP4_TABAN_SURUM X.Y.Z bulunamadı (CI bu satırı okur)"
    iss = (KOK / "op4" / "kurulum" / "op4.iss").read_text(encoding="utf-8-sig")
    assert f'#define Surum "{m.group(1)}"' in iss
    assert "OutputBaseFilename=op4-setup-{#Surum}" in iss


def test_sihirbaz_gorselleri(tmp_path):
    pil = pytest.importorskip("PIL.Image")
    kimlik = _modul("kimlik_uret")
    yazilan = {p.name: p for p in kimlik.sihirbaz_uret(tmp_path)}
    for tur, boylar in (("buyuk", kimlik.SIHIRBAZ_BUYUK), ("kucuk", kimlik.SIHIRBAZ_KUCUK)):
        for olcek, boyut in boylar.items():
            with pil.open(yazilan[f"sihirbaz-{tur}-{olcek}.bmp"]) as im:
                assert im.format == "BMP" and im.mode == "RGB" and im.size == boyut
    assert "sihirbaz-onizleme.png" in yazilan
    iss = (KOK / "op4" / "kurulum" / "op4.iss").read_text(encoding="utf-8-sig")
    for ad in yazilan:
        if ad.endswith(".bmp"):
            assert "{#Sihirbaz}\\" + ad in iss, ad
