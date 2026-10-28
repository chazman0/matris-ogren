# -*- coding: utf-8 -*-
"""Masaüstü sürümü (masaustu/) testleri.

- Sözdizimi ve saf JS birim testleri (testler/js/masaustu.test.js: hazirla yardımcıları, worker'ın yerel Pyodide adresi,
  ön yükleme yüzeyi, menü, ana süreç yardımcıları, protokol sunucusu). node yoksa atlanır.
- package.json / package-lock.json / iş akışı (YAML) alanları; git'e girmemesi gerekenler; ana süreç güvenlik ayarları;
  belgelerdeki komut sözleşmesi.
- hazirla.js çıktı yapısı (ağ yoksa atlanır; indirilenler masaustu/.onbellek/ önbelleğinden yeniden kullanılır).
- Tarayıcıda (Playwright + Chromium; yoksa atlanır): window.MatrisDosya web yolu, sahte window.masaustu ile masaüstü
  köprüsü, hazırlanan uygulamanın CDN'ye hiç gitmeden motoru yükleyip bir bina şablonunu çözmesi.
"""
from __future__ import annotations

import functools
import glob
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MASAUSTU = PROJE / "masaustu"
DOCS = PROJE / "docs"
NODE = shutil.which("node")
nodeli = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, zaman=180, cwd=PROJE):
    return subprocess.run([NODE, *args], capture_output=True, text=True, timeout=zaman, cwd=cwd)


def _paket() -> dict:
    return json.loads((MASAUSTU / "package.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------- sözdizimi, birim
@nodeli
@pytest.mark.parametrize("dosya", ["masaustu/main.js", "masaustu/preload.js", "masaustu/hazirla.js", "masaustu/lib/menu.js",
                                   "masaustu/lib/sunucu.js", "masaustu/lib/yardimci.js", "docs/masaustu_kopru.js",
                                   "docs/motor.worker.js", "testler/js/masaustu.test.js"])
def test_sozdizimi(dosya):
    r = _node("--check", str(PROJE / dosya))
    assert r.returncode == 0, r.stderr


@nodeli
def test_node_birim_testleri():
    r = _node("--test", str(PROJE / "testler" / "js" / "masaustu.test.js"), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


# ---------------------------------------------------------------------------------------------- paket ve kilit
def test_package_json_alanlari():
    p = _paket()
    assert p["name"] == "matris-ogren" and p["productName"] == "Matris Öğren"
    assert p["main"] == "main.js" and p["private"] is True
    assert re.fullmatch(r"\d+\.\d+\.\d+", p["version"])
    gelistirme = p["devDependencies"]
    assert re.fullmatch(r"45\.\d+\.\d+", gelistirme["electron"]), "çatı 45.x tam sürüm olmalı"
    assert re.fullmatch(r"26\.\d+\.\d+", gelistirme["electron-builder"]), "paketleyici 26.x tam sürüm olmalı"
    assert not p.get("dependencies"), "çalışma zamanı bağımlılığı yok (uygulama kendi içinde tam)"
    for betik in ("start", "hazirla", "dist", "denetle"):
        assert betik in p["scripts"], betik
    assert "hazirla.js" in p["scripts"]["hazirla"] and "--publish never" in p["scripts"]["dist"]

    b = p["build"]
    assert b["appId"] == "com.matrisogren.app" and b["productName"] == "Matris Öğren"
    assert b["publish"] is None
    assert set(b["files"]) >= {"main.js", "preload.js", "lib/**/*", "uygulama/**/*"}
    assert all("node_modules" not in f and "dist" not in f for f in b["files"])
    assert [f["ext"] for f in b["fileAssociations"]] == ["matris"]
    hedefler = lambda pl: {t["target"] for t in b[pl]["target"]}  # noqa: E731
    assert hedefler("win") == {"nsis", "portable"}
    assert hedefler("mac") == {"dmg"}
    assert hedefler("linux") == {"AppImage", "deb"}
    assert b["nsis"]["oneClick"] is False and b["nsis"]["installerLanguages"] == ["tr_TR"]
    assert b["mac"]["identity"] == "-"
    for ad in ("artifactName",):
        assert re.fullmatch(r"[A-Za-z0-9${}._-]+", b[ad]), "paket dosya adları ASCII"
    assert re.fullmatch(r"[A-Za-z0-9]+", b["executableName"])


def test_kilit_dosyasi_package_json_ile_uyumlu():
    p = _paket()
    k = json.loads((MASAUSTU / "package-lock.json").read_text(encoding="utf-8"))
    assert k["lockfileVersion"] >= 2
    kok = k["packages"][""]
    assert kok["devDependencies"] == p["devDependencies"]
    for ad, surum in p["devDependencies"].items():
        assert k["packages"][f"node_modules/{ad}"]["version"] == surum, ad
    kaynaklar = {v["resolved"].split("/")[2] for v in k["packages"].values() if v.get("resolved")}
    assert kaynaklar == {"registry.npmjs.org"}, kaynaklar
    assert all(v.get("integrity", "").startswith("sha512-") for ad, v in k["packages"].items() if ad and v.get("resolved"))


# ---------------------------------------------------------------------------------------------- iş akışı
def test_is_akisi():
    yaml = pytest.importorskip("yaml")
    metin = (PROJE / ".github" / "workflows" / "masaustu.yml").read_text(encoding="utf-8")
    w = yaml.safe_load(metin)
    tetik = w.get("on", w.get(True))
    assert "workflow_dispatch" in tetik
    assert tetik["push"]["tags"] == ["v*"] and "branches" not in tetik["push"]
    assert w["permissions"] == {"contents": "read"}

    paketle = w["jobs"]["paketle"]
    matris = paketle["strategy"]["matrix"]["include"]
    assert {m["os"]: m["platform"] for m in matris} == {"windows-latest": "win", "macos-latest": "mac", "ubuntu-latest": "linux"}
    assert "permissions" not in paketle
    adimlar = paketle["steps"]
    calistir = "\n".join(a.get("run", "") for a in adimlar)
    kullan = [a["uses"] for a in adimlar if "uses" in a]
    dugum = next(a for a in adimlar if a.get("uses", "").startswith("actions/setup-node@"))
    assert str(dugum["with"]["node-version"]) == "22"
    assert "npm ci" in calistir and "npm run hazirla" in calistir
    assert re.search(r"electron-builder --\$\{\{ matrix\.platform \}\} --publish never", calistir)
    assert any(u.startswith("actions/upload-artifact@") for u in kullan)
    # etiketten sürüm: ${{ }} doğrudan kabuğa yazılmaz, ortam değişkeniyle geçer
    surum = next(a for a in adimlar if "npm version" in a.get("run", ""))
    assert "github.ref_name" in surum["env"]["ETIKET"] and "${{" not in surum["run"]

    yayin = w["jobs"]["yayinla"]
    assert yayin["needs"] == "paketle" and "refs/tags/v" in yayin["if"]
    assert yayin["permissions"] == {"contents": "write"}
    yayin_kullan = [a["uses"] for a in yayin["steps"] if "uses" in a]
    assert any(u.startswith("softprops/action-gh-release@") for u in yayin_kullan)
    # bütün eylemler 40 haneli işleme özetiyle sabit
    for u in kullan + yayin_kullan:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u), u


def test_testler_is_akisi():
    """.github/workflows/testler.yml: her itme ve çekme isteğinde docs eşleşmesi, ders denetimi, pytest ve node testleri."""
    yaml = pytest.importorskip("yaml")
    w = yaml.safe_load((PROJE / ".github" / "workflows" / "testler.yml").read_text(encoding="utf-8"))
    tetik = w.get("on", w.get(True))
    assert "push" in tetik and "pull_request" in tetik
    assert w["permissions"] == {"contents": "read"}
    (is_,) = w["jobs"].values()
    assert is_["runs-on"] == "ubuntu-latest" and "permissions" not in is_
    adimlar = is_["steps"]
    kullan = [a["uses"] for a in adimlar if "uses" in a]
    for u in kullan:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u), u
    py = next(a for a in adimlar if a.get("uses", "").startswith("actions/setup-python@"))
    assert str(py["with"]["python-version"]) == "3.13"
    dugum = next(a for a in adimlar if a.get("uses", "").startswith("actions/setup-node@"))
    assert str(dugum["with"]["node-version"]) == "22"
    calistir = [a.get("run", "") for a in adimlar]
    metin = "\n".join(calistir)
    for paket in ("numpy", "sympy", "pytest", "PyYAML"):
        assert paket in metin, paket
    sira = ["python3 web_yap.py", "git diff --exit-code -- docs/ ':!docs/sw.js' ':!docs/surum.json'", "python3 ders_derle.py --denetle",
            "python3 -m pytest testler", "node --test testler/js/*.test.js"]
    yer = [metin.index(k) for k in sira]
    assert yer == sorted(yer), "adım sırası: docs eşleşmesi → ders denetimi → pytest → node"


# ---------------------------------------------------------------------------------------------- git, güvenlik, belgeler
def test_uretilen_dosyalar_gitte_yok():
    satirlar = (PROJE / ".gitignore").read_text(encoding="utf-8").splitlines()
    for d in ("masaustu/node_modules/", "masaustu/uygulama/", "masaustu/dist/", "masaustu/.onbellek/", "masaustu/build/"):
        assert d in satirlar, d
    try:
        izlenen = subprocess.run(["git", "ls-files", "masaustu"], cwd=PROJE, capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git ls-files çalışmadı")
    kotu = [y for y in izlenen if re.match(r"masaustu/(node_modules|uygulama|dist|\.onbellek|build)/", y)
            or y.endswith((".whl", ".wasm", ".zip", ".exe", ".dmg", ".AppImage", ".deb"))]
    assert not kotu, kotu
    for y in izlenen:
        assert (PROJE / y).stat().st_size < 512 * 1024, y


def test_ana_surec_guvenlik_ve_ozellikler():
    m = (MASAUSTU / "main.js").read_text(encoding="utf-8")
    for desen in (r"contextIsolation:\s*true", r"sandbox:\s*true", r"nodeIntegration:\s*false", r"webSecurity:\s*true",
                  r"standard:\s*true", r"secure:\s*true", r"supportFetchAPI:\s*true", r"corsEnabled:\s*true",
                  r"requestSingleInstanceLock\(\)", r"\"second-instance\"", r"\"open-file\"", r"setWindowOpenHandler",
                  r"\"will-navigate\"", r"shell\.openExternal", r"printToPDF", r"Menu\.setApplicationMenu", r"setPermissionRequestHandler",
                  r"\"render-process-gone\"", r"app\.setPath\(\"userData\""):
        assert re.search(desen, m), desen
    assert "nodeIntegration: true" not in m and "contextIsolation: false" not in m
    # kullanıcıya görünen metinlerde çatı adı yok (yalnız modül adı ve tarayıcı kimliği temizliği)
    for dosya in ("main.js", "preload.js", "lib/menu.js", "lib/yardimci.js", "lib/sunucu.js"):
        metin = (MASAUSTU / dosya).read_text(encoding="utf-8")
        for dizgi in re.findall(r"\"((?:[^\"\\\n]|\\.)*)\"", metin):
            assert "electron" not in dizgi.lower() or dizgi == "electron", (dosya, dizgi)
    k = (DOCS / "masaustu_kopru.js").read_text(encoding="utf-8")
    assert "electron" not in k.lower()


@nodeli
def test_belgeler_komut_sozlesmesini_kapsar():
    r = _node("-e", "process.stdout.write(JSON.stringify(require('./lib/menu').komutListesi('linux')))", cwd=MASAUSTU)
    assert r.returncode == 0, r.stderr
    komutlar = {k["komut"] for k in json.loads(r.stdout)}
    belge = (MASAUSTU / "README.md").read_text(encoding="utf-8")
    eksik = sorted(k for k in komutlar if f"| `{k}` |" not in belge)
    assert not eksik, "README'de olmayan komutlar: " + ", ".join(eksik)
    for ad in ("masaustu-komut", "masaustu-dosya-acildi", "MatrisDosya.kaydet", "projeKaynagi", "bekleyenDosya", "e.preventDefault()"):
        assert ad in belge, ad
    ana = (PROJE / "README.md").read_text(encoding="utf-8")
    assert "## Masaüstü sürümü" in ana and "masaustu/README.md" in ana


def test_web_sayfasi_kopruyu_yukler():
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    betikler = re.findall(r'<script src="([^"]+)"', html)
    assert "masaustu_kopru.js" in betikler
    assert betikler.index("masaustu_kopru.js") < betikler.index("app.js"), "köprü app.js'ten önce (servis çalışanı kaydı)"
    assert '"./masaustu_kopru.js"' in (DOCS / "sw.js").read_text(encoding="utf-8")
    w = (DOCS / "motor.worker.js").read_text(encoding="utf-8")
    assert "self.MATRIS_PYODIDE_URL" in w and 'searchParams.get("pyodide")' in w
    assert 'const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_SURUM + "/full/";' in w


def test_kullanim_kopru_islemlerini_kapsar():
    """KULLANIM.md 3.9.5 tablosu köprünün (docs/web_kopru.py BINA_ISLEMLER) bütün bina işlemlerini anlatır; README ve Yardım
    sayfası Bina sayfasını ve kısayolları anlatır (uygulama ile web/masaüstü belgeleri aynı yüzeyi kapsar)."""
    kopru = (DOCS / "web_kopru.py").read_text(encoding="utf-8")
    m = re.search(r"^BINA_ISLEMLER = \{(.*?)\}", kopru, re.M | re.S)
    assert m, "BINA_ISLEMLER bulunamadı"
    islemler = set(re.findall(r'"(bina_[a-z_]+)"', m.group(1)))
    assert len(islemler) >= 12
    kullanim = (PROJE / "KULLANIM.md").read_text(encoding="utf-8")
    bolum = kullanim[kullanim.index("### 3.9.5"):kullanim.index("### 3.10")]
    eksik = sorted(i for i in islemler if f"`{i}`" not in bolum)
    assert not eksik, f"KULLANIM.md 3.9.5'te anlatılmayan köprü işlemleri: {eksik}"
    assert "`bina_eleman_bilgi`" in bolum and "### 3.12 Klavye kısayolları" in kullanim
    ana = (PROJE / "README.md").read_text(encoding="utf-8")
    assert "## Bina sayfası (yapı analizi)" in ana and "TASARIM.md" in ana and "node --test testler/js/*.test.js" in ana
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    for kimlik in ('id="yardim-bina"', 'id="yardim-kisayollar"', 'id="yardim-masaustu"', "github.com/chazman0/matris-ogren/releases"):
        assert kimlik in html, kimlik
    assert "kisayolTablosu" in (DOCS / "app.js").read_text(encoding="utf-8")


@nodeli
def test_surum_damgasi_uretilmis_dosyalari_saymaz(tmp_path, monkeypatch):
    """web_yap.py sürüm damgası git'e girmeyen üretilmiş dosyaları (docs/__pycache__/*.pyc, işletim sistemi artıkları) saymaz;
    masaustu/hazirla.js dosya listesiyle aynı kural. Böylece aynı kaynaktan her makinede aynı SURUM çıkar."""
    import importlib.util
    ozellik = importlib.util.spec_from_file_location("web_yap_deneme", PROJE / "web_yap.py")
    wy = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(wy)
    k = tmp_path / "docs"
    for y in ("a.js", "alt/b.py", "icons/i.svg", "__pycache__/b.cpython-313.pyc", "alt/__pycache__/c.cpython-313.pyc", "alt/d.pyc",
              "Thumbs.db", ".DS_Store", "alt/desktop.ini", "sw.js", "surum.json"):
        (k / y).parent.mkdir(parents=True, exist_ok=True)
        (k / y).write_text("x", encoding="utf-8")
    monkeypatch.setattr(wy, "DOCS", k)
    damga = [p.relative_to(k).as_posix() for p in wy.damga_dosyalari()]
    assert damga == ["a.js", "alt/b.py", "icons/i.svg"]
    r = _node("-e", f"process.stdout.write(JSON.stringify(require('./hazirla.js').dosyaListesi({json.dumps(str(k))})))", cwd=MASAUSTU)
    assert r.returncode == 0, r.stderr
    assert [y for y in json.loads(r.stdout) if y not in ("sw.js", "surum.json")] == damga
    # önbellek klasörü değişince damga değişmez
    (k / "sw.js").write_text('const SURUM = "x";\n', encoding="utf-8")
    once = wy.surum_damgala()
    (k / "__pycache__" / "yeni.cpython-313.pyc").write_bytes(b"\x00\x01")
    assert wy.surum_damgala() == once
    (k / "a.js").write_text("y", encoding="utf-8")
    assert wy.surum_damgala() != once


# ---------------------------------------------------------------------------------------------- hazirla.js çıktısı
@pytest.fixture(scope="module")
def hazir_uygulama(tmp_path_factory):
    if NODE is None:
        pytest.skip("node kurulu değil")
    cikti = tmp_path_factory.mktemp("masaustu") / "uygulama"
    r = _node(str(MASAUSTU / "hazirla.js"), "--cikti", str(cikti), zaman=900, cwd=MASAUSTU)
    if r.returncode == 3:
        pytest.skip("ağ yok: hazirla.js indirme yapamadı\n" + r.stderr[-500:])
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    return cikti


def test_hazirla_cikti_yapisi(hazir_uygulama):
    c = hazir_uygulama
    bilgi = json.loads((c / "masaustu.json").read_text(encoding="utf-8"))
    worker = (DOCS / "motor.worker.js").read_text(encoding="utf-8")
    surum = re.search(r'PYODIDE_SURUM = "([^"]+)"', worker).group(1)
    assert bilgi["pyodide"]["surum"] == surum and bilgi["pyodide"]["adres"] == "./pyodide/"
    assert bilgi["uygulama"] == _paket()["version"]

    # docs eksiksiz kopyalanır; yalnız CDN adresleri yerelleşen sayfalar ve worker değişir
    degisen = {"index.html", "galeri.html", "motor.worker.js"}
    for kaynak in sorted(DOCS.rglob("*")):
        if not kaynak.is_file() or "__pycache__" in kaynak.parts or kaynak.suffix == ".pyc":
            continue
        g = kaynak.relative_to(DOCS).as_posix()
        hedef = c / g
        assert hedef.is_file(), "kopyalanmadı: " + g
        if g not in degisen:
            assert hedef.read_bytes() == kaynak.read_bytes(), g
    assert bilgi["docs_dosyalari"] == sum(1 for k in DOCS.rglob("*") if k.is_file() and "__pycache__" not in k.parts and k.suffix != ".pyc")

    # Pyodide çekirdeği + motorun paketleri (bağımlılıklarıyla), SHA-256 kilit dosyasıyla aynı
    py = c / "pyodide"
    for ad in ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"):
        assert (py / ad).is_file() and (py / ad).stat().st_size > 0, ad
    assert (py / "pyodide.asm.wasm").read_bytes()[:4] == b"\0asm"
    kilit = json.loads((py / "pyodide-lock.json").read_text(encoding="utf-8"))["packages"]
    adlar = {p["ad"] for p in bilgi["pyodide"]["paketler"]}
    assert {"numpy", "sympy", "mpmath"} <= adlar
    for p in bilgi["pyodide"]["paketler"]:
        veri = (py / p["dosya"]).read_bytes()
        assert hashlib.sha256(veri).hexdigest() == kilit[p["ad"]]["sha256"], p["ad"]
    assert not [d for d in py.iterdir() if d.suffix == ".whl" and d.name not in {p["dosya"] for p in bilgi["pyodide"]["paketler"]}]

    # sayfalar dış kaynak kullanmaz; kütüphaneler yerel
    for sayfa in ("index.html", "galeri.html"):
        html = (c / sayfa).read_text(encoding="utf-8")
        assert "cdn.jsdelivr.net" not in html, sayfa
        assert not re.findall(r'(?:src|href)="((?:https?:)?//[^"]+)"', html), sayfa
        for yol in re.findall(r'(?:src|href)="(kutuphane/[^"]+)"', html):
            assert (c / yol).is_file(), yol
    assert any(y.endswith("katex.min.css") for y in bilgi["kutuphaneler"])
    assert any(y.endswith(".woff2") for y in bilgi["kutuphaneler"])
    for y in bilgi["kutuphaneler"]:
        assert (c / "kutuphane" / y).is_file(), y

    kopya = (c / "motor.worker.js").read_text(encoding="utf-8")
    assert '"use strict";\nself.MATRIS_PYODIDE_URL = "./pyodide/";' in kopya
    eklenen = re.findall(r"^self\.MATRIS_PYODIDE_URL = .*\n", kopya, flags=re.M)
    assert len(eklenen) == 1 and kopya.replace(eklenen[0], "", 1) == worker   # tek satır eklenmiş, gerisi aynı


# ---------------------------------------------------------------------------------------------- tarayıcı testleri
def _chromium_adaylari() -> list[str]:
    """Hazır Chromium yolları (öncelik sırasıyla): MATRIS_CHROMIUM ortam değişkeni, /opt/pw-browsers/chromium bağlantısı ve
    tarayıcı paketlerinin klasörleri (eski düzende chrome-linux, yenisinde chrome-linux64)."""
    adaylar = [os.environ.get("MATRIS_CHROMIUM") or "", "/opt/pw-browsers/chromium"]
    adaylar += sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), reverse=True)
    gorulen, sonuc = set(), []
    for y in adaylar:
        if y and y not in gorulen and os.path.isfile(y) and os.access(y, os.X_OK):
            gorulen.add(y)
            sonuc.append(y)
    return sonuc


@pytest.fixture(scope="module")
def tarayici():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        b, hata = None, None
        try:
            b = p.chromium.launch()
        except Exception as e:
            hata = e
            for yol in _chromium_adaylari():
                try:
                    b = p.chromium.launch(executable_path=yol)
                    break
                except Exception as e2:  # pragma: no cover
                    hata = e2
        if b is None:
            pytest.skip("Chromium yok" if not _chromium_adaylari() else f"Chromium açılamadı: {hata}")
        yield b
        b.close()


TEST_KOK = "https://matris.test/"   # güvenli bağlam (servis çalışanı API'si var); istekleri route karşılar
TEST_SAYFASI = """<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Köprü</title></head><body>
<nav class="alt-nav"><button type="button" data-sayfa="bina" onclick="window.__nav = 'bina'">Bina</button></nav>
<input id="girdi"><button id="ayarlar-ac" onclick="window.__ayar = true">⚙</button>
<script src="masaustu_kopru.js"></script></body></html>"""


def _kopru_sayfasi(baglam):
    kopru = (DOCS / "masaustu_kopru.js").read_text(encoding="utf-8")

    def yanitla(route):
        url = route.request.url
        if url == TEST_KOK:
            route.fulfill(status=200, content_type="text/html; charset=utf-8", body=TEST_SAYFASI)
        elif url == TEST_KOK + "masaustu_kopru.js":
            route.fulfill(status=200, content_type="text/javascript; charset=utf-8", body=kopru)
        else:
            route.fulfill(status=404, body="")

    baglam.route(TEST_KOK + "**", yanitla)
    sayfa = baglam.new_page()
    return sayfa


def test_matrisdosya_web_yolu(tarayici, tmp_path):
    baglam = tarayici.new_context(accept_downloads=True)
    try:
        sayfa = _kopru_sayfasi(baglam)
        sayfa.goto(TEST_KOK)
        assert sayfa.evaluate("() => MatrisDosya.masaustu") is False
        assert sayfa.evaluate("() => Object.isFrozen(MatrisDosya) && !document.documentElement.classList.contains('masaustu')")

        with sayfa.expect_download() as d:
            sonuc = sayfa.evaluate("() => MatrisDosya.kaydet('model', 'ISO-10303-21;', 'ifc')")
        assert sonuc == {"ad": "model.ifc"} and d.value.suggested_filename == "model.ifc"
        assert Path(d.value.path()).read_text(encoding="utf-8") == "ISO-10303-21;"
        with sayfa.expect_download() as d:
            sayfa.evaluate("() => MatrisDosya.kaydet('Rapor: 1/2', '<h1>R</h1>', 'text/html')")
        assert d.value.suggested_filename == "Rapor_ 1_2.html"
        with sayfa.expect_download() as d:
            sayfa.evaluate("() => MatrisDosya.kaydet('resim.png', new Uint8Array([137, 80, 78, 71]))")
        assert d.value.suggested_filename == "resim.png" and Path(d.value.path()).read_bytes() == bytes([137, 80, 78, 71])
        with sayfa.expect_download() as d:
            sayfa.evaluate("() => MatrisDosya.kaydet('tablo', new Blob(['\\ufeffa;b\\n1;2']), '.csv')")
        assert d.value.suggested_filename == "tablo.csv" and Path(d.value.path()).read_bytes() == "﻿a;b\n1;2".encode("utf-8")

        proje = tmp_path / "proje.matris"
        proje.write_text('﻿{"surum": 3}', encoding="utf-8")
        with sayfa.expect_file_chooser() as fc:
            sayfa.evaluate("() => { window.__ac = MatrisDosya.ac(); }")
        assert fc.value.element.get_attribute("accept") == ".matris,.json"
        fc.value.set_files(str(proje))
        assert sayfa.evaluate("() => window.__ac") == {"ad": "proje.matris", "icerik": '{"surum": 3}'}
        with sayfa.expect_file_chooser() as fc:
            sayfa.evaluate("() => { window.__ac = MatrisDosya.ac(['ifc', 'csv'], {ikili: true}).then(r => ({ad: r.ad, n: r.icerik.length, ilk: r.icerik[0]})); }")
        assert fc.value.element.get_attribute("accept") == ".ifc,.csv"
        fc.value.set_files(str(proje))
        assert sayfa.evaluate("() => window.__ac") == {"ad": "proje.matris", "n": len(proje.read_bytes()), "ilk": 0xEF}
        assert sayfa.evaluate("() => document.querySelectorAll('input[type=file]').length") == 0

        sayfa.evaluate("() => { window.print = () => {}; }")
        with sayfa.expect_popup() as acilan:
            assert sayfa.evaluate("() => MatrisDosya.pdfYazdir('<html><body><h1>Statik rapor</h1></body></html>', 'rapor.html')") == {"ad": "rapor"}
        acilan.value.wait_for_load_state()
        assert "Statik rapor" in acilan.value.content()
        acilan.value.close()
        # açılır pencere engellenince görünmez çerçeve
        sayfa.evaluate("() => { window.open = () => null; return MatrisDosya.pdfYazdir('<p>çerçeve</p>', 'r'); }")
        assert sayfa.evaluate("() => { const f = document.querySelector('iframe'); return f && f.srcdoc; }") == "<p>çerçeve</p>"

        # web'de durum işlevleri zararsız; tür çözümü
        assert sayfa.evaluate("() => { MatrisDosya.degisti(true); MatrisDosya.yeni(); MatrisDosya.projeKaynagi(() => ({})); return MatrisDosya.bekleyenDosya(); }") is None
        assert sayfa.evaluate("() => [MatrisDosya.turCoz('text/csv').uzanti, MatrisDosya.turCoz('', 'a.IFC').uzanti, MatrisDosya.turCoz('.xyz').uzanti]") == ["csv", "ifc", "xyz"]
    finally:
        baglam.close()


SAHTE_MASAUSTU = """
window.__cagri = [];
window.__dinleyici = {};
const kayit = (ad, sonuc) => function () { window.__cagri.push([ad].concat(Array.from(arguments).map(a => (a instanceof Uint8Array ? {ikili: Array.from(a)} : a)))); return sonuc; };
window.masaustu = Object.freeze({
  surum: "1.0.0", platform: "linux",
  kaydet: (s) => { window.__cagri.push(["kaydet", Object.assign({}, s, {icerik: s.icerik instanceof Uint8Array ? {ikili: Array.from(s.icerik)} : s.icerik})]); return Promise.resolve({ad: s.ad, yol: "/k/" + s.ad}); },
  ac: (s) => { window.__cagri.push(["ac", s]); return Promise.resolve({ad: "t.csv", yol: "/k/t.csv", icerik: "a;b"}); },
  projeKaydet: (s) => { window.__cagri.push(["projeKaydet", s]); return Promise.resolve({ad: s.ad, yol: "/k/" + s.ad}); },
  projeAc: () => { window.__cagri.push(["projeAc"]); return Promise.resolve({ad: "p.matris", yol: "/k/p.matris", icerik: "{}"}); },
  pdfYazdir: (s) => { window.__cagri.push(["pdfYazdir", s]); return Promise.resolve({ad: s.ad, yol: "/k/" + s.ad}); },
  klasordeGoster: kayit("klasordeGoster"), degisti: kayit("degisti"), yeni: kayit("yeni"), otomatikKayit: kayit("otomatikKayit"),
  hazir: kayit("hazir"), tamEkran: kayit("tamEkran"), yeniPencere: kayit("yeniPencere"), harici: kayit("harici"),
  komutDinle: (fn) => { window.__dinleyici.komut = fn; return () => {}; },
  dosyaDinle: (fn) => { window.__dinleyici.dosya = fn; return () => {}; },
});
"""


def test_masaustu_koprusu_sahte_yuzeyle(tarayici):
    baglam = tarayici.new_context()
    try:
        baglam.add_init_script(SAHTE_MASAUSTU)
        sayfa = _kopru_sayfasi(baglam)
        sayfa.clock.install()
        sayfa.goto(TEST_KOK)
        sayfa.clock.run_for(100)
        assert sayfa.evaluate("() => MatrisDosya.masaustu && document.documentElement.classList.contains('masaustu')")
        assert sayfa.evaluate("() => window.__cagri.filter(c => c[0] === 'hazir').length") == 1
        assert "servis çalışanı" in sayfa.evaluate("() => navigator.serviceWorker.register('sw.js').then(() => 'kaydedildi', e => e.message)")

        sayfa.evaluate("() => { window.__cagri.length = 0; }")
        sayfa.evaluate("""async () => {
          await MatrisDosya.kaydet('proje', '{"a":1}', 'matris');
          await MatrisDosya.kaydet('proje.matris', '{}', 'matris', {farkli: true});
          await MatrisDosya.kaydet('model', 'ISO', 'ifc', {baslik: 'IFC'});
          await MatrisDosya.kaydet('r.png', new Blob([new Uint8Array([1, 2])]));
          await MatrisDosya.ac(['matris', 'json']);
          await MatrisDosya.ac(['csv', 'tsv'], {ikili: true});
          await MatrisDosya.pdfYazdir('<h1>R</h1>', 'statik_rapor.html');
          MatrisDosya.klasordeGoster('/k/x.ifc');
        }""")
        cagri = sayfa.evaluate("() => window.__cagri")
        assert cagri[0] == ["projeKaydet", {"ad": "proje.matris", "icerik": '{"a":1}', "farkli": False}]
        assert cagri[1] == ["projeKaydet", {"ad": "proje.matris", "icerik": "{}", "farkli": True}]
        assert cagri[2] == ["kaydet", {"ad": "model.ifc", "icerik": "ISO", "baslik": "IFC", "filtreler": [{"ad": "IFC yapı modeli", "uzantilar": ["ifc"]}]}]
        assert cagri[3][1]["ad"] == "r.png" and cagri[3][1]["icerik"] == {"ikili": [1, 2]}
        assert cagri[4] == ["projeAc"]
        assert cagri[5] == ["ac", {"ikili": True, "baslik": "", "filtreler": [{"ad": "CSV tablosu, TSV tablosu", "uzantilar": ["csv", "tsv"]}]}]
        assert cagri[6] == ["pdfYazdir", {"html": "<h1>R</h1>", "ad": "statik_rapor.pdf"}]
        assert cagri[7] == ["klasordeGoster", "/k/x.ifc"]

        # menü komutları → masaustu-komut; işlenmeyenlerde yerleşik davranış
        sayfa.evaluate("""() => { window.__komut = []; window.addEventListener('masaustu-komut', e => {
            window.__komut.push(e.detail); if (e.detail.komut === 'coz') e.preventDefault(); }); }""")
        sayfa.evaluate("() => { __dinleyici.komut({komut: 'coz'}); __dinleyici.komut({komut: 'sayfa', sayfa: 'bina'}); __dinleyici.komut({komut: 'ayarlar'}); __dinleyici.komut({yanlis: 1}); }")
        assert sayfa.evaluate("() => window.__komut") == [{"komut": "coz"}, {"komut": "sayfa", "sayfa": "bina"}, {"komut": "ayarlar"}]
        assert sayfa.evaluate("() => [window.__nav, window.__ayar]") == ["bina", True]
        sayfa.click("#girdi")
        sayfa.keyboard.type("abc")
        sayfa.evaluate("() => __dinleyici.komut({komut: 'geri-al'})")
        assert sayfa.input_value("#girdi") == ""
        sayfa.evaluate("() => __dinleyici.komut({komut: 'yinele'})")
        assert sayfa.input_value("#girdi") == "abc"

        # açılan dosyalar → masaustu-dosya-acildi; işlenmeyen bekletilir
        sayfa.evaluate("() => __dinleyici.dosya({ad: 'a.matris', yol: '/k/a.matris', icerik: '{}'})")
        assert sayfa.evaluate("() => MatrisDosya.bekleyenDosya()") == {"ad": "a.matris", "yol": "/k/a.matris", "icerik": "{}"}
        assert sayfa.evaluate("() => MatrisDosya.bekleyenDosya()") is None
        sayfa.evaluate("() => { window.__dosya = []; window.addEventListener('masaustu-dosya-acildi', e => { window.__dosya.push(e.detail.ad); e.preventDefault(); }); __dinleyici.dosya({ad: 'b.matris', icerik: '{}', kurtarma: true}); __dinleyici.dosya({ad: 'bozuk'}); }")
        assert sayfa.evaluate("() => [window.__dosya, MatrisDosya.bekleyenDosya()]") == [["b.matris"], None]

        # kirli bayrağı ve otomatik kayıt (yalnız kirliyken, ~20 sn sonra)
        sayfa.evaluate("() => { window.__cagri.length = 0; MatrisDosya.projeKaynagi(() => ({ad: 'p.matris', icerik: '{\"kirli\":1}'})); MatrisDosya.degisti(); }")
        sayfa.clock.run_for(19000)
        assert sayfa.evaluate("() => window.__cagri") == [["degisti", True]]
        sayfa.clock.run_for(2000)
        assert sayfa.evaluate("() => window.__cagri") == [["degisti", True], ["otomatikKayit", '{"kirli":1}', "p.matris"]]
        sayfa.evaluate("() => { MatrisDosya.degisti(true); MatrisDosya.degisti(false); }")
        sayfa.clock.run_for(25000)
        assert sayfa.evaluate("() => window.__cagri.filter(c => c[0] === 'otomatikKayit').length") == 1
        assert sayfa.evaluate("() => [MatrisDosya.kirliMi(), (MatrisDosya.yeni(), window.__cagri.slice(-1)[0])]") == [False, ["yeni"]]
        # işlenmeyen kaydet / farklı kaydet: proje kaynağıyla köprü kaydeder
        sayfa.evaluate("() => { window.__cagri.length = 0; __dinleyici.komut({komut: 'kaydet', kapatmak: true}); __dinleyici.komut({komut: 'farkli-kaydet'}); }")
        sayfa.clock.run_for(10)
        assert sayfa.evaluate("() => window.__cagri.filter(c => c[0] === 'projeKaydet')") == [
            ["projeKaydet", {"ad": "p.matris", "icerik": '{"kirli":1}', "farkli": False}],
            ["projeKaydet", {"ad": "p.matris", "icerik": '{"kirli":1}', "farkli": True}]]
    finally:
        baglam.close()


class _SessizIsleyici(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401
        pass


def test_hazirlanan_uygulama_cevrimdisi_motoru_yukler(hazir_uygulama, tarayici):
    sunucu = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_SessizIsleyici, directory=str(hazir_uygulama)))
    is_parcacigi = threading.Thread(target=sunucu.serve_forever, daemon=True)
    is_parcacigi.start()
    kok = f"http://127.0.0.1:{sunucu.server_address[1]}/"
    baglam = tarayici.new_context(service_workers="block")
    dis, istekler = [], []
    try:
        def engelle(route):
            dis.append(route.request.url)
            route.abort()

        baglam.route(lambda u: not u.startswith(kok), engelle)
        sayfa = baglam.new_page()
        sayfa.on("request", lambda r: istekler.append(r.url))
        sayfa.goto(kok + "index.html")
        sayfa.wait_for_function("() => /^Hazır|hatası/.test((document.getElementById('durum') || {}).textContent || '')", timeout=240000)
        assert "Hazır" in sayfa.text_content("#durum"), sayfa.text_content("#yukleme-metin")
        sonuc = sayfa.evaluate("""async () => {
          const b = await MatrisApp.motorIstegi({islem: "bina_sablon", girdi: {ad: "betonarme-2kat-3x2"}});
          if (b.hata) return {hata: b.hata};
          const c = await MatrisApp.motorIstegi({islem: "bina_coz", girdi: {bina: b.bina}});
          return {hata: c.hata, sd: c.veri && c.veri.ozet && c.veri.ozet.sd_sayisi, katex: !!window.katex, marked: !!window.marked};
        }""")
        assert sonuc["hata"] is None and sonuc["sd"] > 0, sonuc
        assert sonuc["katex"] and sonuc["marked"]
        assert not dis, "dış istek yapıldı: " + ", ".join(dis[:5])
        yerel = {u.rsplit("/", 1)[-1] for u in istekler if "/pyodide/" in u}
        assert {"pyodide.mjs", "pyodide.asm.wasm", "python_stdlib.zip"} <= yerel, yerel
        assert any(a.startswith("numpy-") for a in yerel) and any(a.startswith("sympy-") for a in yerel)
    finally:
        baglam.close()
        sunucu.shutdown()
        sunucu.server_close()


def test_yardim_kisayol_tablosu_soguk_acilista_dolar(tarayici):
    """Adres #yardim iken açılan sayfada (yeniden yükleme, yer imi) Yardım'ın kısayol tablosu dolar. app.js ertelenmiş betiklerin
    ilkidir ve sayfayı hemen gösterir; arac_kutusu.js (MatrisArac) ondan sonra çalışır. Tablo "araç kutusu modülü yüklenmedi"
    yazısında kalmamalı (yalnız modül gerçekten yoksa o yazı çıkar)."""
    import mimetypes

    def yanitla(route):
        url = route.request.url
        if not url.startswith(TEST_KOK):
            return route.abort()                       # dış kaynaklar (CDN) yok: tablo onlara bağlı değil
        dosya = DOCS / (url[len(TEST_KOK):].split("#")[0].split("?")[0] or "index.html")
        if dosya.is_file() and DOCS.resolve() in dosya.resolve().parents:
            tur = mimetypes.guess_type(dosya.name)[0] or "application/octet-stream"
            return route.fulfill(status=200, content_type=tur, body=dosya.read_bytes())
        return route.fulfill(status=404, body="")

    baglam = tarayici.new_context(service_workers="block")
    try:
        baglam.route("**/*", yanitla)
        sayfa = baglam.new_page()
        hatalar = []
        sayfa.on("pageerror", lambda e: hatalar.append(str(e)))
        sayfa.goto(TEST_KOK + "index.html#yardim")
        sayfa.wait_for_load_state("load")
        durum = sayfa.evaluate("""() => { const t = document.getElementById('yardim-kisayollar');
          return {aktif: document.querySelector('.sayfa.aktif').id, kaynak: t.dataset.kaynak || null,
                  satir: t.querySelectorAll('tbody tr').length, metin: t.textContent}; }""")
        assert durum["aktif"] == "sayfa-yardim", durum
        assert durum["kaynak"] == "katalog" and durum["satir"] >= 30, durum
        for tus in ("Shift+F10", "PgUp", "Ctrl+Enter", "?"):
            assert tus in durum["metin"], tus
        assert not hatalar, hatalar
    finally:
        baglam.close()
