# -*- coding: utf-8 -*-
"""op4 şablon dökümü (MIMARI §13.4; F1 iş 1.5, kabul D6). Sahibi: D (dosya-cozum).

Hesap motorunun 9 bina şablonunu (docs/web_kopru.py ``bina_sablonlar`` + ``bina_sablon``) op4/veri/sablonlar/ altına
yazar; op4 şablonları motor hazır olmadan, bu dosyalardan açar (Dosya › Yeni › Şablondan, Başlangıç paneli).

  <ad>.json   bina JSON'u (``bina_sablon`` yanıtının "bina" alanı; UTF-8, girinti 1, anahtar sırası motorunki)
  dizin.json  {"bicim": 1, "kaynak", "sablonlar": [{ad, baslik, aciklama, sistem, kat, aks, dosya}]}

Kullanım (depo kökünden; ``-I``: betik klasörü ve ortam değişkenleri içe aktarma yoluna girmez):
  python3 -I op4/araclar/sablon_dok.py                     döküm (op4/veri/sablonlar/)
  python3 -I op4/araclar/sablon_dok.py --denetle           döküm güncel mi? (fark varsa çıkış 1; ctest dosya_sablon)
  python3 -I op4/araclar/sablon_dok.py --cikti <klasör>    başka klasöre
  python3 -I op4/araclar/sablon_dok.py --yanit-fikstur <zip> <ad>...
                                                           bina_coz yanıt fikstürleri (op4 sonuç çözümü sınaması:
                                                           <ad>.bina.json + <ad>.yanit.json, ayrıca hata.yanit.json)
Çıkış kodları: 0 tamam, 1 döküm güncel değil / hata, 3 motor (numpy, sympy) bu Python'da yok.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

DEPO = Path(__file__).resolve().parents[2]
VARSAYILAN_CIKTI = DEPO / "op4" / "veri" / "sablonlar"
KAYNAK = "docs/web_kopru.py bina_sablonlar + bina_sablon (op4/araclar/sablon_dok.py)"


def _kopru():
    for yol in (str(DEPO / "docs"), str(DEPO)):
        if yol not in sys.path:
            sys.path.insert(0, yol)
    try:
        import web_kopru  # noqa: PLC0415 — depo yolu yukarıda eklendi
    except ImportError as e:  # numpy / sympy yok
        print(f"sablon_dok: hesap motoru içe aktarılamadı ({e}); numpy ve sympy gerekli.", file=sys.stderr)
        sys.exit(3)
    return web_kopru


def _calistir(wk, islem: str, girdi: dict) -> dict:
    yanit = json.loads(wk.calistir(json.dumps({"islem": islem, "girdi": girdi}, ensure_ascii=False)))
    if yanit.get("hata"):
        raise SystemExit(f"sablon_dok: {islem} hata döndürdü: {yanit['hata']}")
    return yanit


def dokum_icerigi(wk) -> dict[str, str]:
    """Dosya adı → metin (UTF-8). Belirlenimci: aynı motor → aynı baytlar."""
    liste = _calistir(wk, "bina_sablonlar", {})["sablonlar"]
    dosyalar: dict[str, str] = {}
    dizin = []
    for s in liste:
        ad = str(s["ad"])
        bina = _calistir(wk, "bina_sablon", {"ad": ad})["bina"]
        dosyalar[f"{ad}.json"] = json.dumps(bina, ensure_ascii=False, indent=1) + "\n"
        dizin.append({"ad": ad, "baslik": s.get("baslik", ""), "aciklama": s.get("aciklama", ""),
                      "sistem": s.get("sistem", ""), "kat": s.get("kat", 0), "aks": s.get("aks", ""),
                      "dosya": f"{ad}.json"})
    dosyalar["dizin.json"] = json.dumps({"bicim": 1, "kaynak": KAYNAK, "sablonlar": dizin}, ensure_ascii=False,
                                        indent=1) + "\n"
    return dosyalar


def dok(cikti: Path, wk) -> int:
    cikti.mkdir(parents=True, exist_ok=True)
    icerik = dokum_icerigi(wk)
    for ad, metin in icerik.items():
        (cikti / ad).write_text(metin, encoding="utf-8", newline="\n")
    for eski in cikti.glob("*.json"):
        if eski.name not in icerik:
            eski.unlink()
    print(f"sablon_dok: {len(icerik) - 1} şablon + dizin.json → {cikti}")
    return 0


def denetle(cikti: Path, wk) -> int:
    icerik = dokum_icerigi(wk)
    farklar = []
    for ad, metin in icerik.items():
        yol = cikti / ad
        if not yol.is_file():
            farklar.append(f"eksik: {ad}")
        elif yol.read_text(encoding="utf-8") != metin:
            farklar.append(f"farklı: {ad}")
    fazla = sorted(p.name for p in cikti.glob("*.json") if p.name not in icerik) if cikti.is_dir() else []
    farklar += [f"fazla: {ad}" for ad in fazla]
    if farklar:
        print("sablon_dok: döküm güncel değil (python3 -I op4/araclar/sablon_dok.py ile yenileyin):\n  " +
              "\n  ".join(farklar), file=sys.stderr)
        return 1
    print(f"sablon_dok: döküm güncel ({len(icerik) - 1} şablon)")
    return 0


def yanit_fikstur(zip_yolu: Path, adlar: list[str], wk) -> int:
    """bina_coz (anlat: false) yanıtları: op4 C++ sonuç çözümü gerçek köprü çıktısına karşı sınanır."""
    zip_yolu.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_yolu, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for ad in adlar:
            bina = _calistir(wk, "bina_sablon", {"ad": ad})["bina"]
            yanit = wk.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": bina, "anlat": False}},
                                           ensure_ascii=False))
            z.writestr(zipfile.ZipInfo(f"{ad}.bina.json", (2026, 1, 1, 0, 0, 0)),
                       json.dumps(bina, ensure_ascii=False, indent=1) + "\n", compress_type=zipfile.ZIP_DEFLATED)
            z.writestr(zipfile.ZipInfo(f"{ad}.yanit.json", (2026, 1, 1, 0, 0, 0)), yanit,
                       compress_type=zipfile.ZIP_DEFLATED)
            print(f"sablon_dok: {ad}: {len(yanit)} bayt")
        hata = wk.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": {"tur": "bina", "surum": 3}}}))
        z.writestr(zipfile.ZipInfo("hata.yanit.json", (2026, 1, 1, 0, 0, 0)), hata, compress_type=zipfile.ZIP_DEFLATED)
    return 0


def main(argv: list[str] | None = None) -> int:
    # -I ortam değişkenlerini (PYTHONUTF8) yok sayar; Windows'ta boruya yazılan çıktı cp1252 olur ve "ş" ile çöker.
    for akis in (sys.stdout, sys.stderr):
        if hasattr(akis, "reconfigure"):
            akis.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="op4 şablon dökümü (op4/veri/sablonlar/)")
    p.add_argument("--cikti", type=Path, default=VARSAYILAN_CIKTI)
    p.add_argument("--denetle", action="store_true", help="döküm güncel mi (yazmaz)")
    p.add_argument("--yanit-fikstur", type=Path, metavar="ZIP", help="bina_coz yanıt fikstürleri")
    p.add_argument("adlar", nargs="*", help="--yanit-fikstur için şablon adları")
    a = p.parse_args(argv)
    wk = _kopru()
    if a.yanit_fikstur:
        return yanit_fikstur(a.yanit_fikstur, a.adlar or ["betonarme-tek-aciklik", "celik-1kat-depo", "celik-cbf-3kat"], wk)
    return denetle(a.cikti, wk) if a.denetle else dok(a.cikti, wk)


if __name__ == "__main__":
    sys.exit(main())
