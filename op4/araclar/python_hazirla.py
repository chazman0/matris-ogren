# -*- coding: utf-8 -*-
"""op4 için gömülü Python hazırlar: resmi Windows gömülebilir (embeddable) CPython + numpy/sympy + hesap motoru.

Çıktı düzeni (--paket DIZIN, op4.exe'nin yanında):
  python/   python3XX.dll, python3XX.zip (standart kitaplık, .pyc), python3XX._pth, *.pyd, vcruntime140*.dll,
            Lib/site-packages/ (numpy, sympy, mpmath; testler ve derleme dosyaları budanmış, .pyc önceden derlenmiş)
  motor/    hesap motoru: docs/ altındaki motor kopyaları (web_kopru.py köprüsü dahil) + __pycache__/*.pyc

Neden önceden derleme: kurulum klasörü (Program Files) kullanıcı için salt okunurdur; Python orada .pyc yazamaz ve her
açılışta kaynakları yeniden derler (sympy için saniyeler). Burada derlenen .pyc'ler "unchecked-hash" kipindedir: kaynak
zaman damgasına bakılmaz (kurulumun dosya tarihlerini değiştirmesi önbelleği bozmaz).

Python sürümü: varsayılan olarak betiği çalıştıran yorumlayıcının sürümü (CI'da actions/setup-python 3.13 x64) —
gömülü dağıtım aynı sürümden indirilir; böylece pip'in seçtiği tekerlekler (cp313) ve .pyc sihirli sayısı uyar.

Kullanım:
  python op4/araclar/python_hazirla.py --paket paket [--onbellek op4/.onbellek] [--surum 3.13.9] [--zip yerel.zip]
  python op4/araclar/python_hazirla.py --paket /tmp/p --platform manylinux_2_28_x86_64 --zip-yok   (Linux'ta deneme)
"""
from __future__ import annotations

import argparse
import compileall
import hashlib
import json
import os
import pathlib
import platform
import py_compile
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

DEPO = pathlib.Path(__file__).resolve().parents[2]
# testler.yml'deki sürümlerle aynı (motor testleri bu sürümlerle geçiyor).
GEREKSINIMLER = ["numpy==2.5.3", "sympy==1.14.0"]
# docs/ altındaki motor kopyaları (web_yap.py ile kaynaklardan üretilir; CI aynılığı denetler).
MOTOR = ["web_kopru.py", "matris_ogren.py", "sonlu_eleman.py", "yapi.py", "yapi_serbest.py", "yapi_veri.py", "temel.py",
         "tasarim.py", "rapor.py", "tablolar.py", "alan.py"]
BUDANAN_KLASORLER = {"tests", "testing_utils", "__pycache__"}
BUDANAN_EKLER = {".pyi", ".c", ".h", ".pxd", ".pyx", ".f", ".f90", ".a", ".lib"}


def boyut(yol: pathlib.Path) -> int:
    if yol.is_file():
        return yol.stat().st_size
    return sum(p.stat().st_size for p in yol.rglob("*") if p.is_file())


def mb(n: int) -> str:
    return f"{n / 1048576:.1f} MB"


def indir(url: str, hedef: pathlib.Path) -> None:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    for deneme in range(1, 4):
        try:
            gecici = hedef.with_suffix(hedef.suffix + ".indiriliyor")
            with urllib.request.urlopen(url, timeout=120) as y, open(gecici, "wb") as f:
                shutil.copyfileobj(y, f)
            gecici.replace(hedef)
            return
        except OSError as e:  # noqa: PERF203
            print(f"  indirme denemesi {deneme} başarısız: {e}")
            time.sleep(3 * deneme)
    raise SystemExit(f"İndirilemedi: {url}")


def sha256(yol: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def budama(site: pathlib.Path) -> int:
    """Çalışma anında gerekmeyen dosyaları siler; silinen bayt sayısını döndürür."""
    silinen = 0
    for p in sorted(site.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and p.name in BUDANAN_KLASORLER:
            silinen += boyut(p)
            shutil.rmtree(p)
    for p in list(site.rglob("*")):
        if p.is_file() and p.suffix.lower() in BUDANAN_EKLER:
            silinen += p.stat().st_size
            p.unlink()
    for ad in ("bin", "share"):  # pip --target'ın konsol betikleri (f2py.exe, isympy.exe) ve el kitapları
        p = site / ad
        if p.exists():
            silinen += boyut(p)
            shutil.rmtree(p)
    for ad in ("numpy/_core/include", "numpy/_core/lib", "numpy/f2py", "numpy/_pyinstaller", "numpy/typing/tests",
               "sympy/testing/tests", "sympy/utilities/_compilation"):
        p = site / ad
        if p.exists():
            silinen += boyut(p)
            shutil.rmtree(p)
    return silinen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paket", required=True, help="op4.exe'nin bulunduğu (bulunacağı) paket klasörü")
    ap.add_argument("--onbellek", default=str(DEPO / "op4" / ".onbellek"), help="indirme önbelleği")
    ap.add_argument("--surum", default=platform.python_version(), help="gömülü Python sürümü (ör. 3.13.9)")
    ap.add_argument("--zip", help="önceden indirilmiş python-X.Y.Z-embed-amd64.zip")
    ap.add_argument("--zip-yok", action="store_true", help="gömülü Python'u indirme (yalnız paketler + motor; deneme)")
    ap.add_argument("--platform", default="win_amd64", help="pip tekerlek platformu (deneme için)")
    args = ap.parse_args()

    t0 = time.time()
    paket = pathlib.Path(args.paket).resolve()
    onbellek = pathlib.Path(args.onbellek).resolve()
    surum = args.surum
    xy = ".".join(surum.split(".")[:2])
    kisa = xy.replace(".", "")
    if xy != f"{sys.version_info[0]}.{sys.version_info[1]}":
        raise SystemExit(f"Betik Python {xy} ile çalıştırılmalı (.pyc ve tekerlek uyumu); şu an {sys.version.split()[0]}.")
    py = paket / "python"
    motor = paket / "motor"
    if py.exists():
        shutil.rmtree(py)
    if motor.exists():
        shutil.rmtree(motor)
    py.mkdir(parents=True)
    motor.mkdir(parents=True)
    rapor: dict = {"python": surum, "paketler": GEREKSINIMLER}

    # 1) Gömülü CPython.
    if not args.zip_yok:
        zipyol = pathlib.Path(args.zip) if args.zip else onbellek / f"python-{surum}-embed-amd64.zip"
        if not zipyol.exists():
            url = f"https://www.python.org/ftp/python/{surum}/python-{surum}-embed-amd64.zip"
            print(f"İndiriliyor: {url}")
            indir(url, zipyol)
        rapor["zip_sha256"] = sha256(zipyol)
        rapor["zip_bayt"] = zipyol.stat().st_size
        print(f"Gömülü Python: {zipyol.name} ({mb(zipyol.stat().st_size)}, sha256 {rapor['zip_sha256']})")
        with zipfile.ZipFile(zipyol) as z:
            z.extractall(py)
        pth = py / f"python{kisa}._pth"
        if not pth.exists():
            raise SystemExit(f"{pth.name} yok — beklenmeyen gömülü dağıtım.")
        # sys.path: ._pth'nin klasörüne göreli. "import site" yok: kullanıcı site-packages'ı ve .pth işlenmez (yalıtım).
        pth.write_text(f"python{kisa}.zip\n.\nLib\\site-packages\n..\\motor\n", encoding="utf-8")

    # 2) numpy + sympy (+ mpmath) — ikili tekerlekler, hedef platform için.
    site = py / "Lib" / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    t = time.time()
    komut = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-warn-script-location",
             "--no-compile", "--target", str(site), "--only-binary=:all:", "--platform", args.platform,
             "--python-version", xy, "--implementation", "cp", "--cache-dir", str(onbellek / "pip"), *GEREKSINIMLER]
    print("pip:", " ".join(komut[3:]))
    subprocess.run(komut, check=True)
    once = boyut(site)
    silinen = budama(site)
    print(f"site-packages: {mb(once)} → budama {mb(silinen)} → {mb(boyut(site))} ({time.time() - t:.1f} s)")
    rapor["site_packages_budama_once_bayt"] = once

    # 3) Hesap motoru.
    for ad in MOTOR:
        kaynak = DEPO / "docs" / ad
        if not kaynak.exists():
            raise SystemExit(f"Motor dosyası yok: {kaynak}")
        shutil.copy2(kaynak, motor / ad)
    print(f"motor: {len(MOTOR)} dosya ({mb(boyut(motor))})")

    # 4) Önceden derleme (unchecked-hash .pyc).
    t = time.time()
    kip = py_compile.PycInvalidationMode.UNCHECKED_HASH
    tamam = compileall.compile_dir(str(site), quiet=1, workers=0, invalidation_mode=kip)
    tamam &= compileall.compile_dir(str(motor), quiet=1, workers=0, invalidation_mode=kip)
    if not tamam:
        raise SystemExit("compileall başarısız.")
    print(f".pyc derlemesi: {time.time() - t:.1f} s")

    rapor["python_bayt"] = boyut(py)
    rapor["motor_bayt"] = boyut(motor)
    rapor["sure_s"] = round(time.time() - t0, 1)
    (py / "op4_python.json").write_text(json.dumps(rapor, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"BOYUT: python/ {mb(rapor['python_bayt'])}, motor/ {mb(rapor['motor_bayt'])}; süre {rapor['sure_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
