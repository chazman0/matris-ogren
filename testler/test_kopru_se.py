"""docs/web_kopru.py sonlu eleman işlemleri: "se_coz", "se_ornekler", "se_ornek"."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

import sonlu_eleman as se

PROJE = Path(__file__).resolve().parent.parent
ADLAR = list(se.ORNEK_MODELLER)


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_se_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, islem, girdi=None, ayarlar=None):
    istek = {"islem": islem, "girdi": girdi or {}}
    if ayarlar is not None:
        istek["ayarlar"] = ayarlar
    return json.loads(kopru.calistir(json.dumps(istek)))


def test_ornekler_listesi(kopru):
    y = iste(kopru, "se_ornekler")
    assert y["hata"] is None
    assert [o["ad"] for o in y["ornekler"]] == ADLAR
    assert len(ADLAR) == 10
    for o in y["ornekler"]:
        assert o["baslik"] and o["tip"] and "aciklama" in o


def test_ornek_model(kopru):
    y = iste(kopru, "se_ornek", {"ad": "kafes-iki-cubuk"})
    assert y["hata"] is None
    assert y["model"]["tip"] == "kafes"
    assert len(y["model"]["dugumler"]) == 3
    assert y["model"]["mesnetler"][0]["ux"] is True


def test_bilinmeyen_ornek(kopru):
    y = iste(kopru, "se_ornek", {"ad": "yok-boyle-bir-sey"})
    assert y["hata_turu"] == "girdi"
    assert "Örnek model yok" in y["hata"]


@pytest.mark.parametrize("ad", ADLAR)
def test_her_ornek_cozulur(kopru, ad):
    model = iste(kopru, "se_ornek", {"ad": ad})["model"]
    y = iste(kopru, "se_coz", {"model": model})
    assert y["hata"] is None, y.get("hata")
    # matris işlemleriyle aynı yanıt biçimi
    assert y["bloklar"] and y["sonuc_latex"] and y["sonuc_metin"] and y["zincir"] is False
    assert {b["tur"] for b in y["bloklar"]} <= {"md", "math", "kod", "sema"}
    assert any(b["tur"] == "sema" and b["icerik"]["kareler"] for b in y["bloklar"])
    v = y["veri"]
    assert v["tip"] == model["tip"]
    assert len(v["dugumler"]) == len(model["dugumler"])
    assert len(v["elemanlar"]) == len(model["elemanlar"])
    assert len(v["u"]) == v["sd_sayisi"]
    for e in v["elemanlar"]:
        d = e["diyagram"]
        assert len(d["x"]) == len(d["N"]) == len(d["V"]) == len(d["M"]) >= 2
    assert v["tepkiler"]
    assert set(v["denge"]) >= {"Fx", "Fy", "M"}
    assert all(abs(x) < 1e-6 for x in v["denge"].values())


def test_json_metni_olarak_model(kopru):
    metin = json.dumps(se.ornek_model("kiris-konsol"))
    y = iste(kopru, "se_coz", {"model": metin})
    assert y["hata"] is None
    assert y["veri"]["tip"] == "kiris"


def test_yanit_katı_json(kopru):
    """Yanıt NaN/Infinity içermemeli (tarayıcıda JSON.parse çalışmalı)."""
    ham = kopru.calistir(json.dumps({"islem": "se_coz", "girdi": {"model": se.ornek_model("cerceve-portal")}}))
    json.loads(ham, parse_constant=lambda c: pytest.fail(f"geçersiz JSON sabiti: {c}"))


def test_sayisal_mod(kopru):
    y = iste(kopru, "se_coz", {"model": se.ornek_model("kafes-pratt-kopru")})
    assert y["veri"]["mod"] == "sayisal"
    assert y["veri"]["sd_sayisi"] == 16


def test_bos_model(kopru):
    for girdi in ({}, {"model": ""}, {"model": "   "}):
        y = iste(kopru, "se_coz", girdi)
        assert y["hata_turu"] == "girdi"
        assert "boş" in y["hata"]


def test_bozuk_json(kopru):
    y = iste(kopru, "se_coz", {"model": "{bozuk"})
    assert y["hata_turu"] == "girdi"
    assert "JSON" in y["hata"]


def test_cok_uzun_model(kopru):
    y = iste(kopru, "se_coz", {"model": " " * (kopru.SE_MODEL_EN_FAZLA + 5)})
    assert y["hata_turu"] == "girdi"


def test_model_hatasi_ogretici(kopru):
    model = se.ornek_model("kafes-iki-cubuk")
    model["mesnetler"] = []
    y = iste(kopru, "se_coz", {"model": model})
    assert y["hata"] and y["hata_turu"] == "girdi"
    assert "iz" not in y


def test_sema_kapali(kopru):
    y = iste(kopru, "se_coz", {"model": se.ornek_model("kafes-iki-cubuk")}, ayarlar={"sema": False})
    assert y["hata"] is None
    assert y["veri"]["elemanlar"]


def test_matris_islemleri_bozulmadi(kopru):
    y = iste(kopru, "determinant", {"A": "1 2; 3 4"})
    assert y["hata"] is None and y["sonuc_metin"] == "-2"
