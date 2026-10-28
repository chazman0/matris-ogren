# -*- coding: utf-8 -*-
"""docs/bina_cizim.js (aks tabanlı çizim, Dilim 4f 2. aşama) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/bina_cizim.test.js`` (saf mantık; node'un yerleşik test koşucusu).
- Kablolama: index.html'de bina.js'ten SONRA yüklenir (MatrisBina hazır olunca kurulur); servis çalışanı kabuğunda ve
  stil dosyasında yer alır.
- Sözleşme: serbest koordinatla düğüm üretmez (çizim kipleri yakalama sonucunun REF'ini yazar; üreteç / kopya sonuçları
  aksaBaglaHepsi'nden geçer); bütün model değişiklikleri MatrisBina.binaAyarla ile tek geri al yığınından geçer;
  araç kutusunun aks / çizim / düzenleme / değiştirme komutlarını bağlar ve bina.js'teki "sonraki aşama" listesindeki
  her komut burada karşılanır.
node yoksa node gerektiren testler atlanır.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MODUL = PROJE / "docs" / "bina_cizim.js"
KAYNAK = MODUL.read_text(encoding="utf-8")
BINA = (PROJE / "docs" / "bina.js").read_text(encoding="utf-8")
JS_TEST = PROJE / "testler" / "js" / "bina_cizim.test.js"
NODE = shutil.which("node")

node_gerekli = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, zaman=120):
    return subprocess.run([NODE, *args], capture_output=True, text=True, timeout=zaman, cwd=PROJE)


@node_gerekli
def test_sozdizimi():
    r = _node("--check", str(MODUL))
    assert r.returncode == 0, r.stderr


@node_gerekli
def test_node_birim_testleri():
    r = _node("--test", str(JS_TEST), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


def test_index_servis_calisani_ve_stil():
    html = (PROJE / "docs" / "index.html").read_text(encoding="utf-8")
    sira = [m.group(1) for m in re.finditer(r'<script src="([^"]+)"', html)]
    assert "bina_cizim.js" in sira
    assert sira.index("aks_sistemi.js") < sira.index("bina.js") < sira.index("bina_cizim.js")
    sw = (PROJE / "docs" / "sw.js").read_text(encoding="utf-8")
    assert '"./bina_cizim.js"' in sw
    css = (PROJE / "docs" / "style.css").read_text(encoding="utf-8")
    for sinif in (".b3-cubuk", ".b3-panel", ".b3-mafsal", ".b3-yc-c", ".bc-onizleme", ".bn-duzlem", ".bc-uretec"):
        assert sinif in css, sinif


@node_gerekli
def test_araclar_bagli_ve_sonraki_asama_karsilaniyor():
    cikti = _node("-e", "process.stdout.write(JSON.stringify(require('./docs/arac_kutusu.js').KATALOG.map(k => k.id)))").stdout
    katalog = set(json.loads(cikti))
    bagla = KAYNAK[KAYNAK.index("MB.komutBagla({"):]
    bagla = bagla[:bagla.index("\n    });")]
    bagli = set(re.findall(r'(?:^|[\s{,])"?([a-z][a-z0-9-]*)"?\s*:\s*(?:secenekli|kipK|\{|aks|makas|besik|kren|dugum|function)', bagla, re.M))
    sonraki = set(re.findall(r'"([a-z0-9-]+)"', re.search(r"const SONRAKI = \[(.*?)\];", BINA, re.S).group(1)))
    # bina.js'in 2. aşamaya bıraktığı her komut (katalogda olanlar) burada bağlanır
    eksik = sorted(k for k in sonraki & katalog if k not in bagli and k not in ("aks-yapisik", "yakalama", "aks-balon", "aks-olcu"))
    assert not eksik, f"bina_cizim.js'te bağlanmayan komut: {eksik}"
    for k in ("aks-sihirbaz", "aks-ekle", "aks-sil", "aks-tasi", "aks-sistemi", "aks-gorunurluk", "cubuk-ciz", "hizli-kolon", "hizli-kiris",
              "hizli-capraz", "hizli-panel", "egik-cubuk", "makas", "besik-cerceve", "asik", "kren-yolu", "mesnet", "yuk-ata",
              "tasi", "dondur", "ayna", "dogrusal-dizi", "ozellik-ata", "mafsal", "yalniz-cekme", "bol", "kesisimde-bol",
              "duzlemle-bol", "birlestir", "dugum-birlestir", "kesit-degistir", "aci"):
        assert k in bagli, k


def test_serbest_koordinat_yok_ve_tek_geri_al():
    # düğümler yalnız yakalama sonucunun REF'i ya da aksa bağlanmış işlem sonucu; serbest {X, Y, Z} düğümü yazılmaz
    assert not re.search(r"dugumler\.push\(\s*\{[^}]*\bX\s*:", KAYNAK)
    assert "aksaBaglaHepsi(" in KAYNAK and "serbestleriBagla(" in KAYNAK
    assert "MB.binaAyarla(" in KAYNAK
    assert "localStorage" not in KAYNAK, "model durumu tarayıcı deposuna yazılmaz (bina.js taslağı tek kaynak)"
    # MatrisBina hazır olunca kurulur
    assert 'addEventListener("matris-bina-hazir"' in KAYNAK
    assert "matris-bina-hazir" in BINA


def test_bina_js_surum3_kablolamasi():
    for ad in ("s3Var", "aksKatModu", "duzlemSec", "duzlemGec", "zAkslari", "refKoordinat", "geometri", "motorS3", "firca", "ayarla"):
        assert re.search(r"(^|[\s,{])" + ad + r"\s*:", BINA), ad
    # surum 3 modelini çözemeyen motor için öğretici hata; genel model çözümü
    assert "S3_MOTOR_YOK" in BINA and 'veri.model !== "genel"' in BINA
    # aks–kat şablonları eskisi gibi: aks–kat kipleri aksKatModu'nda
    assert "eskiMi" in BINA
