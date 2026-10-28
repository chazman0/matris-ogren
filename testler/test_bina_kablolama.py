# -*- coding: utf-8 -*-
"""Bina sayfası kablolaması (docs/bina.js, Dilim 4f 1. aşama) için durağan sözleşme denetimleri.

bina.js DOM'a bağlı olduğundan davranışı tarayıcı koşumlarıyla sınanır; burada sonraki aşamaların dayandığı yüzey kilitlenir:
- ``window.MatrisBina`` iç API'si (adlar: bina, binaAyarla, veri, cozumKimligi, coz, yenile, secim, seciliAyarla, gorunum,
  gorunumAyarla, sahne, izdusum + kancalar) tanımlı;
- araç kutusu kataloğundaki (docs/arac_kutusu.js) her komut kimliği bina.js'te bağlı ya da "sonraki aşama" listesinde;
- masaüstü menüsünün (masaustu/README.md) her komutu bina.js'te işleniyor (köprünün yerleşik işledikleri hariç);
- köprü işlemleri (bina_rapor, bina_tablolar, bina_alan) ve modüller (MatrisIFC, MatrisTablo, MatrisIsi, MatrisBilgi, MatrisDosya) kullanılıyor;
- uzun basma tek kaynak (MatrisBilgi.bagla uzunBasma: false, Cizim3B.jestler uzunBas → bağlam menüsü).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
BINA = (PROJE / "docs" / "bina.js").read_text(encoding="utf-8")
NODE = shutil.which("node")

API = ["hazir", "bina", "binaAyarla", "veri", "cozumEski", "cozumKimligi", "coz", "yenile", "secim", "seciliAyarla", "gorunum",
       "gorunumAyarla", "sahne", "izdusum", "kip", "kipAyarla", "kipKaydet", "katmanKaydet", "katmanTazele", "komutBagla",
       "baglamKancasi", "hedefBul", "dinle", "kaplamaAc", "kaplamaKapat", "raporAc", "tablolarAc", "isiAc", "ifcAc", "ifcUret",
       "projeNesnesi", "projeYukle", "projeKaydet"]
# köprünün kendisinin işlediği (masaustu_kopru.js yerleşik davranışı) komutlar
YERLESIK = {"sayfa", "ayarlar", "yazdir"}


def _api_govdesi() -> str:
    m = re.search(r"window\.MatrisBina = Object\.freeze\(\{(.*?)\n  \}\);", BINA, re.S)
    assert m, "window.MatrisBina tanımı bulunamadı"
    return m.group(1)


def test_matrisbina_api_adlari():
    govde = _api_govdesi()
    eksik = [a for a in API if not re.search(r"(^|[\s,{])" + a + r"\s*:", govde)]
    assert not eksik, f"MatrisBina'da eksik: {eksik}"


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_arac_katalogu_bina_js_de_bagli():
    cikti = subprocess.run([NODE, "-e", "process.stdout.write(JSON.stringify(require('./docs/arac_kutusu.js').KATALOG.map(k => k.id)))"],
                           cwd=PROJE, capture_output=True, text=True, check=True).stdout
    idler = json.loads(cikti)
    assert len(idler) > 60
    komutlar = BINA[BINA.index("function aracKomutlari()"):BINA.index("function aracKur()")]
    sonraki = re.search(r"const SONRAKI = \[(.*?)\];", BINA, re.S).group(1)
    olcum = re.search(r"const OLCUM_KIP = \{(.*?)\};", BINA, re.S).group(1)
    eksik = []
    for i in idler:
        anahtar = re.compile(r'(^|[\s{,])("' + re.escape(i) + r'"|' + re.escape(i) + r")\s*:", re.M)
        if not (anahtar.search(komutlar) or ('"' + i + '"') in sonraki or ('"' + i + '"') in olcum):
            eksik.append(i)
    assert not eksik, f"araç kutusu komutu bina.js'te bağlı değil: {eksik}"
    # 2. aşamaya bırakılanlar etkin değil ve ipucunda nedeni yazıyor
    assert "SONRAKI_ASAMA" in komutlar and "etkin: false" in komutlar


def test_kisayollar_tek_kaynak():
    # F tam ekran (mevcut davranış), Shift+F sığdır; araç kutusu varsa eski harf kısayolları bina.js'te işlenmez
    assert re.search(r'sigdir:\s*\{\s*kisayol:\s*"Shift\+F"', BINA)
    assert re.search(r'"tam-ekran":\s*\{\s*kisayol:\s*"F"', BINA)
    assert "if (aracYon) {" in BINA and "kisayollar: true" in BINA


def test_masaustu_komutlari_isleniyor():
    readme = (PROJE / "masaustu" / "README.md").read_text(encoding="utf-8")
    bolum = readme[readme.index("### Komutlar"):]
    bolum = bolum[:bolum.index("\n### ", 10)] if "\n### " in bolum[10:] else bolum
    komutlar = set(re.findall(r"^\| `([a-z0-9-]+)` \|", bolum, re.M)) - {"komut"}
    assert len(komutlar) > 60
    harita = re.search(r"const MASAUSTU_ARAC = \{(.*?)\};", BINA, re.S).group(1)
    islev = BINA[BINA.index("function masaustuKomut(d)"):BINA.index("function raporHazirOlunca(fn)")]
    eksik = sorted(k for k in komutlar - YERLESIK
                   if not (re.search(r'case "' + re.escape(k) + r'"', islev) or re.search(r'(^|[\s,{])"?' + re.escape(k) + r'"?\s*:', harita)))
    assert not eksik, f"masaüstü komutu işlenmiyor: {eksik}"
    assert 'addEventListener("masaustu-dosya-acildi"' in BINA and "projeKaynagi(" in BINA and "F.degisti(true)" in BINA


def test_cikti_kopru_islemleri_ve_moduller():
    for islem in ("bina_rapor", "bina_tablolar", "bina_alan"):
        assert f'islem: "{islem}"' in BINA, islem
    for cagri in ("uretAyrintili(", 'modul("MatrisTablo")', 'modul("MatrisIsi")', ".bagla(ref.svg", "pdfYazdir(", 'kaydet(projeDosyaAdi()'):
        assert cagri in BINA, cagri
    # proje dosyası biçimi
    assert 'tur: "matris-proje"' in BINA and "arac_yerlesimi:" in BINA and "gorunum: gorunum()" in BINA


def test_uzun_basma_tek_kaynak():
    assert "uzunBasma: false" in BINA
    assert "uzunBas: function (p, e) { uzunBasmaMenusu(p, e); }" in BINA


def test_tek_geri_al_yigini():
    govde = BINA[BINA.index("function binaAyarla(yeni, sec)"):BINA.index("function modelDegisti(etiket)")]
    assert "gecmis.geri.push" in govde and "gecmis.ileri = []" in govde and "GECMIS_EN_FAZLA" in govde
    # tablo düzenlemesi aynı yığından geçer
    assert re.search(r"duzenle: function \(yeni, degisiklikler, bilgi\) \{\s*const geri = .*?\n\s*binaAyarla\(yeni, \{ geriAl: true", BINA, re.S)
