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


def test_yaz_en_genislik_gunluk_kopyasi(tmp_path, capsys):
    """--en-genislik: geniş görüntünün günlük kopyası küçültülür (asıl boyut gen/yuk, kopya gunluk_gen/gunluk_yuk)."""
    pil = pytest.importorskip("PIL.Image")
    im = pil.new("RGB", (1920, 1080), (243, 244, 246))
    im.paste((37, 99, 235), (100, 100, 900, 600))
    im.save(tmp_path / "b.png")
    (tmp_path / "k.png").write_bytes(_png(7, 5))
    assert yaz.main([f"b={tmp_path / 'b.png'}", f"k={tmp_path / 'k.png'}", "--en-genislik", "960"]) == 0
    cikti = capsys.readouterr().out
    assert "OP4-PNG ad=b " in cikti and "gen=1920 yuk=1080 gunluk_gen=960 gunluk_yuk=540" in cikti
    assert "gen=7 yuk=5\n" in cikti  # dar görüntü küçültülmez, ek alan yok
    bloklar, _ = coz.coz(coz.gunluk_metni(_ci_gunlugu(cikti)), tmp_path / "c")
    assert [x["durum"] for x in bloklar] == ["doğrulandı", "doğrulandı"]
    assert yaz.png_boyutu((tmp_path / "c" / "b.png").read_bytes()) == (960, 540)


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


# ---------------------------------------------------------------------------------------------- F1 iş 1.1 / 1.2 (A)
def test_cmake_on_ayarlari():
    """MIMARI §19, kabul A2: CMakePresets.json'da dört ön ayar; ASan ön ayarı UBSan'ı da açar; uyarılar hata."""
    d = json.loads((KOK / "op4" / "CMakePresets.json").read_text(encoding="utf-8"))
    yap = {p["name"]: p for p in d["configurePresets"]}
    for ad in ("win-surum", "win-hata", "linux-cekirdek", "linux-cekirdek-asan"):
        assert ad in yap and not yap[ad].get("hidden"), ad
        assert ad in {p["name"] for p in d["buildPresets"]} and ad in {p["name"] for p in d["testPresets"]}, ad
    assert yap["linux-cekirdek-asan"]["cacheVariables"]["OP4_ASAN"] == "ON"
    assert yap["win-surum"]["architecture"]["value"] == "x64" and "generator" not in yap["win-surum"]
    assert yap["temel"]["cacheVariables"]["OP4_UYARI_HATA"] == "ON"
    derleyici = (KOK / "op4" / "cmake" / "Derleyici.cmake").read_text(encoding="utf-8")
    assert 'option(OP4_UYARI_HATA "Uyarılar hata sayılır (/WX, -Werror)" ON)' in derleyici
    assert "-fsanitize=address,undefined" in derleyici and "/WX" in derleyici


def test_golgelendiriciler_tek_kaynak():
    """MIMARI D12, kabul A4: HLSL tek dosyada; grafik.cpp'nin istediği giriş noktaları orada (FXC kendiliğinden bulur)."""
    hlsl = (KOK / "op4" / "golgelendiriciler" / "op4.hlsl").read_text(encoding="utf-8")
    girisler = set(re.findall(r"[ \t\r\n]((?:vs|ps)_[A-Za-z0-9_]+)[ \t]*\(", hlsl))
    grafik = (KOK / "op4" / "kaynak" / "grafik.cpp").read_text(encoding="utf-8")
    istenen = set(re.findall(r'Derle\("((?:vs|ps)_[a-z_0-9]+)"', grafik))
    assert istenen and istenen <= girisler, istenen - girisler
    baslik = (KOK / "op4" / "kaynak" / "golgelendirici.h").read_text(encoding="utf-8")
    assert "golgelendirici_kaynak.inc" in baslik and "cbuffer" not in baslik
    cmake = (KOK / "op4" / "cmake" / "Golgelendiriciler.cmake").read_text(encoding="utf-8")
    assert "/T ${_tur}_5_1" in cmake and "op4_golgelendiriciler" in (KOK / "op4" / "CMakeLists.txt").read_text(encoding="utf-8")


def test_motor_paketleme_ve_karmalar():
    """MIMARI §8.5, §2.2.8; kabul A11: op4_sunucu + op4_protokol pakete girer; tekerlekler sabit sürüm + SHA256."""
    hazirla = _modul("python_hazirla")
    for ad in hazirla.OP4_MOTOR:
        assert (KOK / "op4" / "motor" / ad).is_file(), ad
    assert {"op4_sunucu.py", "op4_protokol.py"} <= set(hazirla.OP4_MOTOR)
    satirlar = hazirla.KARMALI_GEREKSINIMLER.read_text(encoding="utf-8")
    paketler = dict(re.findall(r"^([a-z0-9_-]+)==([0-9.]+)", satirlar, re.M))
    assert paketler == {"numpy": "2.5.3", "sympy": "1.14.0", "mpmath": "1.3.0"}
    karmalar = re.findall(r"--hash=sha256:([0-9a-f]+)", satirlar)
    assert len(karmalar) >= 4 and all(len(k) == 64 for k in karmalar)
    for s in hazirla.GEREKSINIMLER:
        ad, surum = s.split("==")
        assert paketler[ad] == surum, s
    iss = (KOK / "op4" / "kurulum" / "op4.iss").read_text(encoding="utf-8-sig")
    assert '[InstallDelete]' in iss and 'Name: "{app}\\python"' in iss and 'Name: "{app}\\motor"' in iss


def test_op4_is_akisi_motor_ve_linux_matrisi():
    """Kabul A1–A3, A6, A10, A11: Linux işi 3.13 + 3.14 matrisi ve ASan ön ayarı; Windows işi Python 3.14, op4motor.exe,
    gömülü gölgelendirici denetimi, kurulu programla --test-motor ve --oz-sinama."""
    d = _is_akisi()
    lin = d["jobs"]["cekirdek-linux"]
    assert lin["strategy"]["matrix"]["python"] == ["3.13", "3.14"]
    assert lin["env"]["OP4_MOTOR_SINAMA_ZORUNLU"] == "1"
    lin_run = "\n".join(a.get("run", "") for a in lin["steps"])
    for parca in ("--preset linux-cekirdek-asan", "ctest --preset linux-cekirdek-asan", "node --test op4/testler/js",
                  "pytest op4/testler/python", "numpy==2.5.3", "OP4OLCUM"):
        assert parca in lin_run, parca
    win = d["jobs"]["windows"]
    py = [a for a in win["steps"] if a.get("uses", "").startswith("actions/setup-python")]
    assert py and py[0]["with"]["python-version"] == "3.14"
    win_run = "\n".join(a.get("run", "") for a in win["steps"])
    for parca in ("--preset win-surum", "op4motor.exe --denetle", "motor/op4_sunucu.py", "--test-motor",
                  "gömülü bayt kodu (FXC, SM 5.1", "--oz-sinama", "OP4_MOTOR_SINAMA_ZORUNLU",
                  "OP4_GOLGELENDIRICI=calisma_ani", "OP4OLCUM senaryo=golgelendirici"):
        assert parca in win_run or parca in str(win), parca
    # Kabul A4 ölçüm kipi: CI'nın kapattığı gömülü yol golgelendirici_bayt.cpp'de; günlük satırı CI'nın aradığıyla aynı.
    bayt = (KOK / "op4" / "kaynak" / "grafik" / "golgelendirici_bayt.cpp").read_text(encoding="utf-8")
    assert 'L"OP4_GOLGELENDIRICI"' in bayt and 'L"calisma_ani"' in bayt and "gömülü bayt kodu kapalı" in bayt
    assert "gömülü bayt kodu (FXC, SM 5.1" in bayt


def test_op4_is_akisi_ekran_goruntuleri():
    """C'nin ekran sınamaları (MIMARI §25, §25.1): 1920×1080 boş / örnek / katı / Ayarlar sayfaları, 1366×768 örnek ve
    Büyük yazı boyutu, açılış kareleri (--olcek 2, açık ve koyu); hepsi günlüğe küçültülmüş kopyayla basılır. Eski 640×360
    ekran sınaması 1280×720'ye çıktı; pencere testinin kayma ölçümleri iş akışında da eşiklenir."""
    d = _is_akisi()
    win = d["jobs"]["windows"]
    win_run = "\n".join(a.get("run", "") for a in win["steps"])
    for parca in ("ekran-bos-1920.png --boyut 1920x1080", "ekran-ornek-1920.png --boyut 1920x1080 --senaryo ornek",
                  "--senaryo ornek-kati", "--senaryo ayarlar", "--senaryo ayarlar-program", "--senaryo ayarlar-dil",
                  "ekran-ornek-1366.png --boyut 1366x768", "ekran-buyuk-1366.png --boyut 1366x768 --senaryo ornek-buyuk",
                  "--test-acilis acilis.png --olcek 2", "acilis-koyu-", "--en-genislik", "model_yuzde",
                  "kaydirma_kayma_px", "yakinlasma_kayma_px", "lisanslar/FreeType-FTL.txt"):
        assert parca in win_run, parca
    assert "640x360" not in win_run
    # Değişken adları C'nin ekran sınamasındakilerle aynı (test_ekran.cpp EkranOrtami::Degisken).
    ekran = (KOK / "op4" / "kaynak" / "test_ekran.cpp").read_text(encoding="utf-8")
    for ad in ("ornek-kati", "ornek-buyuk", "ayarlar-program", "ayarlar-dil"):
        assert f'"{ad}"' in ekran, ad
    assert 'rfind("ayarlar", 0)' in ekran


def test_arayuz_yazi_ailesi_tek_kaynak():
    """Arayüz yazı tipi (MIMARI §25.1, kullanıcı kararı 31.10.2026): kimlik_uret.py ARAYUZ_YAZI = belirtec.py YAZI_AILESI =
    gömülü veri (yazi_verisi.cpp) = tema_belirtec.h; kullanılan bütün yazı tipi dosyaları ve OFL metinleri depoda."""
    pytest.importorskip("PIL.Image")
    kimlik = _modul("kimlik_uret")
    b = kimlik._belirtec_yukle()
    assert kimlik.ARAYUZ_YAZI_AILESI == b.YAZI_AILESI
    veri = (KOK / "op4" / "kaynak" / "arayuz" / "yazi_verisi.cpp").read_text(encoding="utf-8")
    assert f'ArayuzYaziAilesi() {{ return "{b.YAZI_AILESI}"; }}' in veri
    assert kimlik.tema_metni() == (KOK / "op4" / "kaynak" / "arayuz" / "tema_belirtec.h").read_text(encoding="utf-8")
    fontlar = KOK / "op4" / "kimlik" / "fontlar"
    for _, dosya, _, _ in kimlik.YAZI_ORNEKLERI:
        assert (fontlar / dosya).is_file(), dosya
        assert (fontlar / (dosya.split("-")[0] + "-OFL.txt")).is_file(), dosya
    assert set(b.YAZI_BOYUTU) == {"kucuk", "orta", "buyuk"} and b.YAZI_BOYUTU["orta"] == 1.0
