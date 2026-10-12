"""docs/web_kopru.py "ders_calistir" işlemi: ders örneklerinin kodunu çalıştırıp normal işlem yanıtı biçiminde döndürür."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_ders_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, kod):
    return json.loads(kopru.calistir(json.dumps({"islem": "ders_calistir", "girdi": {"kod": kod}})))


def test_tek_sonuc(kopru):
    y = iste(kopru, "mo.determinant('1 2; 3 4')")
    assert y["hata"] is None
    assert y["bloklar"], "anlatım blokları gelmeli"
    assert y["sonuc_latex"]
    assert y["sonuc_metin"] == "-2"
    assert y["zincir"] is True
    assert any(b["tur"] in ("math", "md") for b in y["bloklar"])


def test_onceki_satirlar_calisir(kopru):
    y = iste(kopru, "A = '2 0; 0 3'\nmo.transpoz(A)")
    assert y["hata"] is None
    assert y["sonuc_metin"] == "2 0; 0 3"


def test_liste_sonuc(kopru):
    y = iste(kopru, "[mo.determinant('1 2; 3 4'), mo.transpoz('1 2; 3 4')]")
    assert y["hata"] is None
    basliklar = [b["icerik"] for b in y["bloklar"] if b["tur"] == "md" and b["icerik"].startswith("####")]
    assert len(basliklar) == 2
    assert basliklar[0].startswith("#### 1.") and basliklar[1].startswith("#### 2.")
    assert y["sonuc_metin"] == "1 3; 2 4"  # son sonuç öne çıkar


def test_sade_sympy_degeri(kopru):
    y = iste(kopru, "sp.Matrix([[1, 2], [3, 4]]) * 2")
    assert y["hata"] is None
    assert y["ad"] == ""
    assert y["bloklar"][0]["tur"] == "math"
    assert "matrix" in y["sonuc_latex"]
    assert y["sonuc_metin"] == "2 4; 6 8"


def test_sade_sayi(kopru):
    y = iste(kopru, "sp.Rational(1, 3) + sp.Rational(1, 6)")
    assert y["hata"] is None
    assert y["sonuc_metin"] == "1/2"


def test_sozdizimi_hatasi(kopru):
    y = iste(kopru, "mo.determinant(")
    assert y["hata"]
    assert y["hata_turu"] == "girdi"
    assert "SyntaxError" in y["hata"]
    assert "iz" not in y


def test_calisma_hatasi(kopru):
    y = iste(kopru, "tanimsiz_ad + 1")
    assert y["hata_turu"] == "girdi"
    assert "NameError" in y["hata"]


def test_motor_hatasi_olduğu_gibi(kopru):
    y = iste(kopru, "mo.determinant('1 2 3; 4 5 6')")  # kare olmayan matris
    assert y["hata"]
    assert y["hata_turu"] == "girdi"
    assert "Örnek kodu çalışmadı" not in y["hata"]


def test_cok_uzun(kopru):
    y = iste(kopru, "1 + 1  # " + "x" * (kopru.KOD_EN_FAZLA + 10))
    assert y["hata_turu"] == "girdi"
    assert "uzun" in y["hata"]


def test_bos_kod(kopru):
    assert iste(kopru, "   ")["hata_turu"] == "girdi"
    y = json.loads(kopru.calistir(json.dumps({"islem": "ders_calistir", "girdi": {}})))
    assert y["hata_turu"] == "girdi"


def test_son_satir_ifade_degil(kopru):
    y = iste(kopru, "x = 3")
    assert y["hata_turu"] == "girdi"


def test_diger_islemler_bozulmadi(kopru):
    y = json.loads(kopru.calistir(json.dumps({"islem": "determinant", "girdi": {"A": "1 2; 3 4"}})))
    assert y["hata"] is None and y["sonuc_metin"] == "-2"
