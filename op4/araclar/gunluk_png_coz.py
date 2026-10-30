# -*- coding: utf-8 -*-
"""CI iş günlüğündeki OP4-PNG bloklarını PNG dosyalarına çözer ve sha256 özetini denetler (MIMARI §20.2, §20.3).

Girdi şunlardan biri olabilir:
  * ham iş günlüğü (her satırın başında `2026-10-30T13:08:00.1234567Z ` zaman damgası olabilir),
  * GitHub günlük aracının kaydettiği JSON yanıtı: metin `logs_content` alanındadır; alan iç içe JSON metni
    (ör. [{"type": "text", "text": "{...\"logs_content\": ...}"}]) içinde de olabilir.

Bloklar `gunluk_png_yaz.py` biçimindedir. `OP4-PNG ad=… gunluk_bayt=… sha256=…` satırı varsa çözülen baytların
boyutu ve özeti onunla karşılaştırılır; uyuşmazlık (kesik ya da bozulmuş günlük) hata sayılır. Günlükteki
`OP4OLCUM` satırları da listelenir (`--olcum`).

Kullanım:  python3 op4/araclar/gunluk_png_coz.py <günlük ya da kayıt.json> <çıktı klasörü> [--olcum]
Çıkış kodu: 0 her blok doğrulandı; 1 hiç blok yok; 2 en az bir blok bozuk ya da özeti tutmuyor.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import pathlib
import re
import sys

BASLA = "-----OP4-PNG-BASLA-----"
BITIR = "-----OP4-PNG-BITIR-----"
ZAMAN = re.compile(r"^\ufeff?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?")
BASLIK = re.compile(r"OP4-PNG ad=(\S+)(.*)$")
ALAN = re.compile(r"(\w+)=(\S+)")
GUVENLI_AD = re.compile(r"[^0-9A-Za-z_.-]")


def _metinleri_topla(deger, cikti: list[str]) -> None:
    """JSON ağacında `logs_content` alanlarını (iç içe JSON metinleri dahil) toplar."""
    if isinstance(deger, dict):
        for k, v in deger.items():
            if k == "logs_content" and isinstance(v, str):
                cikti.append(v)
            else:
                _metinleri_topla(v, cikti)
    elif isinstance(deger, list):
        for v in deger:
            _metinleri_topla(v, cikti)
    elif isinstance(deger, str):
        s = deger.lstrip()
        if s[:1] in "{[" and "logs_content" in s:
            try:
                _metinleri_topla(json.loads(s), cikti)
            except ValueError:
                pass


def gunluk_metni(ham: str) -> str:
    s = ham.lstrip("\ufeff").lstrip()
    if s[:1] in "{[":
        try:
            agac = json.loads(s)
        except ValueError:
            return ham
        parcalar: list[str] = []
        _metinleri_topla(agac, parcalar)
        if parcalar:
            return "\n".join(parcalar)
    return ham


def satirlar(metin: str):
    for satir in metin.splitlines():
        yield ZAMAN.sub("", satir).rstrip("\r").strip()


def coz(metin: str, klasor: pathlib.Path) -> tuple[list[dict], list[str]]:
    """Blokları çözer; (bloklar, olcum satırları) döndürür. Her blok: ad, yol, bayt, sha256, durum."""
    klasor.mkdir(parents=True, exist_ok=True)
    bloklar: list[dict] = []
    olcumler: list[str] = []
    baslik: dict = {}
    parca: list[str] | None = None
    adlar: dict[str, int] = {}
    for satir in satirlar(metin):
        if parca is None:
            if satir.startswith("OP4OLCUM "):
                olcumler.append(satir)
            m = BASLIK.match(satir)
            if m:
                baslik = {"ad": m.group(1), **dict(ALAN.findall(m.group(2)))}
            elif satir == BASLA:
                parca = []
            continue
        if satir == BITIR:
            bloklar.append(_blok_yaz(baslik, parca, klasor, adlar))
            baslik, parca = {}, None
        elif satir == BASLA:  # kapanmamış önceki blok
            bloklar.append({"ad": baslik.get("ad", "png"), "durum": "kesik (BİTİR yok)"})
            parca = []
        elif satir.startswith(("##[", "::")):
            continue
        else:
            parca.append(satir)
    if parca is not None:
        bloklar.append({"ad": baslik.get("ad", "png"), "durum": "kesik (BİTİR yok)"})
    return bloklar, olcumler


def _blok_yaz(baslik: dict, parca: list[str], klasor: pathlib.Path, adlar: dict[str, int]) -> dict:
    ad = GUVENLI_AD.sub("_", baslik.get("ad", "png")) or "png"
    adlar[ad] = adlar.get(ad, 0) + 1
    dosya_adi = ad if adlar[ad] == 1 else f"{ad}-{adlar[ad]}"
    sonuc = {"ad": dosya_adi}
    try:
        veri = base64.b64decode("".join(parca), validate=True)
    except (binascii.Error, ValueError) as e:
        sonuc["durum"] = f"base64 çözülemedi ({e})"
        return sonuc
    ozet = hashlib.sha256(veri).hexdigest()
    sonuc.update(bayt=len(veri), sha256=ozet)
    beklenen = baslik.get("sha256")
    beklenen_bayt = baslik.get("gunluk_bayt")
    if beklenen and beklenen.lower() != ozet:
        sonuc["durum"] = f"sha256 tutmuyor (beklenen {beklenen[:16]}…, çözülen {ozet[:16]}…)"
    elif beklenen_bayt and beklenen_bayt.isdigit() and int(beklenen_bayt) != len(veri):
        sonuc["durum"] = f"boyut tutmuyor (beklenen {beklenen_bayt}, çözülen {len(veri)})"
    elif not veri.startswith(b"\x89PNG\r\n\x1a\n"):
        sonuc["durum"] = "PNG imzası yok"
    else:
        sonuc["durum"] = "doğrulandı" if beklenen else "özetsiz (doğrulanamadı)"
    yol = klasor / f"{dosya_adi}.png"
    yol.write_bytes(veri)
    sonuc["yol"] = str(yol)
    for k in ("gen", "yuk"):
        if k in baslik:
            sonuc[k] = baslik[k]
    return sonuc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("girdi", type=pathlib.Path, help="ham günlük ya da günlük aracının kaydettiği JSON")
    ap.add_argument("cikti", type=pathlib.Path, help="PNG'lerin yazılacağı klasör")
    ap.add_argument("--olcum", action="store_true", help="OP4OLCUM satırlarını da yaz")
    a = ap.parse_args(argv)
    metin = gunluk_metni(a.girdi.read_text(encoding="utf-8", errors="replace"))
    bloklar, olcumler = coz(metin, a.cikti)
    for b in bloklar:
        boyut = f"{b['gen']}x{b['yuk']} " if "gen" in b else ""
        print(f"{b['ad']}: {boyut}{b.get('bayt', '?')} bayt, {b['durum']}" + (f" → {b['yol']}" if "yol" in b else ""))
    if a.olcum:
        for s in olcumler:
            print(s)
    if not bloklar:
        print("Günlükte OP4-PNG bloğu yok.", file=sys.stderr)
        return 1
    return 0 if all(b["durum"] in ("doğrulandı", "özetsiz (doğrulanamadı)") for b in bloklar) else 2


if __name__ == "__main__":
    sys.exit(main())
