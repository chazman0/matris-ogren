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


# ---- surum 3 sonuç ekranı, masaüstü komutları ve CSP sözleşmeleri

def _s3var_kaynagi() -> str:
    bas = BINA.index("const S3_LISTELER = [")
    son = BINA.index("\n  }\n", BINA.index("function s3Var(b) {")) + 4
    return BINA[bas:son]


# C1 doğruluk tablosu (motor paketiyle ortak); taban model: betonarme-2kat-3x2 şablonu
C1_TABLOSU = [
    ("taban", {}, False),
    ("mesnet", {"mesnetler": [{"dugum": {"aks": ["B", "2"], "z": "+3.00"}, "ux": True, "uy": True, "uz": True}]}, True),
    ("dugum", {"dugumler": [{"no": 100001, "X": 0, "Y": 0, "Z": 3}]}, True),
    ("uretec", {"uretecler": [{"no": 1, "tur": "makas", "parametreler": {}}]}, True),
    ("aks-kat dugum yuku", {"ek_yukler": [{"tur": "dugum", "aks": ["B", "2"], "kat": 1, "durum": "G", "FZ": -10}]}, False),
    ("ref dugum yuku", {"ek_yukler": [{"tur": "dugum", "dugum": {"aks": ["B", "2"], "z": "+3.00"}, "durum": "G", "FZ": -10}]}, True),
    ("cubuk yuku", {"ek_yukler": [{"tur": "cubuk", "cubuk": 1, "durum": "G", "q": -1}]}, True),
    ("surum 3", {"surum": 3}, True),
    ("bos listeler", {"cubuklar": [], "mesnetler": []}, False),
]


def test_s3var_c1_anahtarlari():
    kaynak = _s3var_kaynagi()
    for anahtar in ("cubuklar", "paneller", "dugumler", "mesnetler", "uretecler", "surum", "ek_yukler", "dugum", "cubuk", "panel"):
        assert f'"{anahtar}"' in kaynak or f".{anahtar}" in kaynak, anahtar
    # iç API modeli de alır (tarayıcı testi ve sağ tık menüsü için)
    assert re.search(r"s3Var: function \(b\) \{ return s3Var\(b\); \}", _api_govdesi())


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_s3var_c1_dogruluk_tablosu():
    import yapi
    taban = yapi.bina_sablon("betonarme-2kat-3x2")
    assert int(taban.get("surum", 1)) < 3
    girdiler = [dict(taban, **ek) for _ad, ek, _b in C1_TABLOSU]
    betik = ("let B = null;\n" + _s3var_kaynagi() + "\nlet v = ''; process.stdin.on('data', d => v += d);"
             "process.stdin.on('end', () => process.stdout.write(JSON.stringify(JSON.parse(v).map(b => s3Var(b)))));")
    r = subprocess.run([NODE, "-e", betik], input=json.dumps(girdiler), cwd=PROJE, capture_output=True, text=True, check=True)
    sonuc = json.loads(r.stdout)
    assert {ad: s for (ad, _e, _b), s in zip(C1_TABLOSU, sonuc)} == {ad: b for ad, _e, b in C1_TABLOSU}


def test_s3_yonlendirme_zehirlemiyor():
    govde = BINA[BINA.index("function coz("):BINA.index("function coz(") + 6000]
    assert "S3_YONLENDIRME" in govde
    # eski motor genel modeli aks–kat çözdüyse hata gösterilir; sonraki genel model çözümleri engellenmez
    assert "MOTOR_S3 = false" not in BINA


def test_aks_kat_sinirlari_genel_modelde_yok():
    govde = BINA[BINA.index("function dogrula()"):BINA.index("function dogrula()") + 3000]
    i = govde.index("if (!s3Var()) {")
    assert govde.index("En çok 12×12 aks") > i and govde.index("En çok 12 kat") > i


def test_masaustu_sayfa_komutlari():
    islev = BINA[BINA.index("function masaustuKomut(d)"):BINA.index("function raporHazirOlunca(fn)")]
    for k in ("yazdir", "csv", "kisayollar"):
        assert f'case "{k}"' in islev, k
    assert "tumunuCsv(" in BINA and 'ayirici: ";"' in BINA
    assert "function kisayolPenceresi()" in BINA


def test_satir_ici_olay_ozniteligi_yok():
    """Masaüstü CSP'si (script-src 'self') satır içi olay özniteliklerini (onclick=, onsubmit=…) çalıştırmaz: HTML dizgilerinde yok."""
    oznitelik = re.compile(r"""\son[a-z]+=\\?["']""")
    etiket = re.compile(r"""<[a-zA-Z][^<>]*\son[a-z]+\s*=""")
    bulunan = []
    for yol in sorted((PROJE / "docs").glob("*.js")) + sorted((PROJE / "docs").glob("*.html")):
        metin = yol.read_text(encoding="utf-8")
        for r in (oznitelik, etiket):
            bulunan += [f"{yol.name}:{metin.count(chr(10), 0, m.start()) + 1}" for m in r.finditer(metin)]
    assert not bulunan, f"satır içi olay özniteliği: {bulunan}"


def test_devre_disi_komut_nedeni():
    komutlar = BINA[BINA.index("function aracKomutlari()"):BINA.index("function aracKur()")]
    assert "neden:" in komutlar and "Önce modeli çözün (Çöz ▶)." in BINA
    # reddedilen komut sayfada bildirilir (araç kutusu "reddedildi" olayı)
    assert '"reddedildi"' in BINA
