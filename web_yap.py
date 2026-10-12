# -*- coding: utf-8 -*-
"""docs\\ içindeki web uygulamasını (PWA) derler.

Yaptıkları:
  1. matris_ogren.py motorunu docs\\ altına kopyalar (uygulama bu dosyayı Pyodide içinde çalıştırır).
  2. Matris_Ogren.ipynb defterinin markdown hücrelerini docs\\dersler.json olarak çıkarır (Dersler sekmesi).
  3. İkon PNG'lerini icon.svg / icon-maskable.svg'den üretir (pymupdf varsa; yoksa mevcut PNG'ler kalır).
  4. docs\\ dosyalarının içeriğinden bir sürüm damgası hesaplar, sw.js içindeki SURUM satırına ve surum.json'a yazar
     (damga değişince servis çalışanı eski önbelleği atar; uygulama güncellenir).

Çalıştırma (proje klasöründen, yalnız standart kütüphane gerekir):
  python web_yap.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
DOCS = KOK / "docs"
IKON = DOCS / "icons"


def motor_kopyala() -> int:
    kaynak = KOK / "matris_ogren.py"
    hedef = DOCS / "matris_ogren.py"
    shutil.copyfile(kaynak, hedef)
    return hedef.stat().st_size


def se_kopyala() -> str:
    """Sonlu eleman motoru (varsa) docs\\ altına kopyalanır; uygulama bunu Pyodide'a ek modül olarak yükler."""
    kaynak = KOK / "sonlu_eleman.py"
    if not kaynak.exists():
        return "yok (atlandı)"
    shutil.copyfile(kaynak, DOCS / "sonlu_eleman.py")
    return f"{(DOCS / 'sonlu_eleman.py').stat().st_size:,} bayt"


def ders_derle_yukle():
    """ders_derle.py'yi dosya yoluyla yükler (python -I altında da çalışır); yoksa None."""
    yol = KOK / "ders_derle.py"
    if not yol.exists():
        return None
    ozellik = importlib.util.spec_from_file_location("ders_derle", yol)
    modul = importlib.util.module_from_spec(ozellik)
    sys.modules["ders_derle"] = modul  # dataclass/tip çözümlemesi için
    ozellik.loader.exec_module(modul)
    return modul


def zengin_dersler_yaz() -> int:
    """dersler/*.md → docs/dersler.json (zengin ders biçimi). Ders yoksa ya da derleme hatası varsa 0 döner."""
    try:
        modul = ders_derle_yukle()
        if modul is None:
            return 0
        dersler = modul.derle()
    except Exception as e:  # DersHatasi dahil: eski defter çıkarımına düş, hatayı göster
        print(f"⚠️ ders_derle: {type(e).__name__}: {e}")
        return 0
    if not dersler:
        return 0
    modul.json_yaz(dersler)
    return len(dersler)


def dersler_cikar() -> int:
    """Defterin markdown hücreleri → dersler.json: [{"no", "baslik", "md"}]."""
    defter = KOK / "Matris_Ogren.ipynb"
    if not defter.exists():
        print("⚠️ Matris_Ogren.ipynb yok; dersler.json değiştirilmedi.")
        return 0
    nb = json.loads(defter.read_text(encoding="utf-8"))
    dersler = []
    for hucre in nb.get("cells", []):
        if hucre.get("cell_type") != "markdown":
            continue
        kaynak = hucre.get("source", "")
        md = "".join(kaynak) if isinstance(kaynak, list) else kaynak
        md = md.strip()
        if not md:
            continue
        m = re.search(r"^#+\s*(.+?)\s*$", md, re.M)
        baslik = m.group(1).strip() if m else f"Bölüm {len(dersler)}"
        # Defterin giriş hücresi ile Colab'a özgü "Ayarlar" ve "Serbest çalışma alanı" bölümleri uygulamaya alınmaz.
        if re.match(r"^(🧮|10\)\s*Ayarlar|11\)\s*Serbest)", baslik):
            continue
        dersler.append({"no": len(dersler), "baslik": baslik, "md": md})
    (DOCS / "dersler.json").write_text(json.dumps(dersler, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(dersler)


def ikonlar() -> str:
    try:
        import fitz  # pymupdf
    except ImportError:
        return "pymupdf yok; PNG ikonlar yeniden üretilmedi"
    isler = [
        ("icon.svg", "icon-192.png", 192, True),
        ("icon.svg", "icon-512.png", 512, True),
        ("icon.svg", "apple-touch-icon.png", 180, False),
        ("icon-maskable.svg", "icon-512-maskable.png", 512, False),
    ]
    for svg, png, boyut, saydam in isler:
        doc = fitz.open(stream=(IKON / svg).read_bytes(), filetype="svg")
        sayfa = doc[0]
        olcek = boyut / sayfa.rect.width
        pix = sayfa.get_pixmap(matrix=fitz.Matrix(olcek, olcek), alpha=saydam)
        pix.save(str(IKON / png))
        doc.close()
    return f"{len(isler)} PNG ikon üretildi"


def surum_damgala() -> str:
    h = hashlib.sha256()
    for yol in sorted(DOCS.rglob("*")):
        if yol.is_dir() or yol.name in ("sw.js", "surum.json"):
            continue
        h.update(yol.relative_to(DOCS).as_posix().encode("utf-8"))
        h.update(yol.read_bytes())
    damga = h.hexdigest()[:10]
    sw = DOCS / "sw.js"
    metin = sw.read_text(encoding="utf-8")
    yeni, n = re.subn(r'const SURUM = "[^"]*";', f'const SURUM = "{damga}";', metin, count=1)
    if n != 1:
        raise SystemExit("sw.js içinde 'const SURUM = \"...\";' satırı bulunamadı")
    sw.write_text(yeni, encoding="utf-8")
    bilgi = {"surum": damga, "tarih": dt.datetime.now().astimezone().isoformat(timespec="minutes")}
    (DOCS / "surum.json").write_text(json.dumps(bilgi, ensure_ascii=False), encoding="utf-8")
    return damga


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not DOCS.exists():
        raise SystemExit(f"docs klasörü yok: {DOCS}")
    print(f"motor kopyalandı: {motor_kopyala():,} bayt")
    zengin = zengin_dersler_yaz()
    if zengin:
        print(f"dersler.json: {zengin} zengin ders (dersler/*.md)")
    else:
        print(f"dersler.json: {dersler_cikar()} bölüm (defter)")
    print(f"sonlu_eleman.py: {se_kopyala()}")
    print(f"ikonlar: {ikonlar()}")
    print(f"sürüm damgası: {surum_damgala()}")
    print("✅ docs hazır")


if __name__ == "__main__":
    main()
