"""docs/web_kopru.py op4 eklemeleri (op4/MIMARI.md §8.6, F1 iş 1.2, kabul A9) — yalnız eklemeli; web davranışı değişmez.

* bina_coz ``anlat:false`` (girdi ya da ayarlar): ``bloklar: []``, ``veri`` anlatımlı çözümle aynı (sayılar bağıl ≤ 1e-9).
* bina_kimlik: ``{bina}`` → ``{cozum_kimligi, onbellekte}``; bina_coz ``veri.cozum_kimligi`` ile aynı (aks–kat ve genel model).
* KeyboardInterrupt (op4 motor sunucusunun iptali) → ``{"hata": "İşlem iptal edildi.", "hata_turu": "iptal"}``.
* ``ayarlar.sd_siniri``: istek süresince yapi / yapi_serbest SD sınırı ve temel en küçük ağ aralığı; sonra geri yüklenir;
  sınır iletileri "bellek ve süre sınırı" der; geçersiz değer öğretici "girdi" hatası.
* MemoryError → öğretici "ic" hatası.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

import temel
import yapi
import yapi_serbest

PROJE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_op4_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, islem, girdi=None, ayarlar=None):
    istek = {"islem": islem, "girdi": girdi or {}}
    if ayarlar is not None:
        istek["ayarlar"] = ayarlar
    return json.loads(kopru.calistir(json.dumps(istek)))


SURE_ALANLARI = {"cozum_sure_ms", "sure_ms"}   # duvar süresi (ölçüm): karşılaştırılmaz


def _yakin(a, b, yol="veri"):
    """Sayılar bağıl 1e-9 içinde, diğer her şey birebir (MIMARI §2.2.6); süre ölçüm alanları hariç."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str):
        assert a == b, yol
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12), (yol, a, b)
    elif isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), yol
        for k in a:
            if k not in SURE_ALANLARI:
                _yakin(a[k], b[k], f"{yol}.{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), yol
        for i, (x, y) in enumerate(zip(a, b)):
            _yakin(x, y, f"{yol}[{i}]")
    else:
        assert a == b, yol


@pytest.fixture(scope="module")
def iki_kat():
    return yapi.bina_sablon("betonarme-2kat-3x2")


def test_anlatimsiz_cozum_ayni_veri_bos_bloklar(kopru, iki_kat):
    tam = iste(kopru, "bina_coz", {"bina": iki_kat})
    assert tam["hata"] is None and tam["bloklar"], "varsayılan (web) davranışı anlatımlıdır"
    for girdi, ayarlar in (({"bina": iki_kat, "anlat": False}, None), ({"bina": iki_kat}, {"anlat": False})):
        kisa = iste(kopru, "bina_coz", girdi, ayarlar)
        assert kisa["hata"] is None
        assert kisa["bloklar"] == []
        assert kisa["sonuc_metin"] == tam["sonuc_metin"]
        _yakin(kisa["veri"], tam["veri"])
    # girdi.anlat ayarlar.anlat'tan önce gelir
    y = iste(kopru, "bina_coz", {"bina": iki_kat, "anlat": True}, {"anlat": False})
    assert y["bloklar"]


def test_bina_kimlik(kopru, iki_kat):
    kopru._BINA_ONBELLEK.clear()
    k = iste(kopru, "bina_kimlik", {"bina": iki_kat})
    assert k["hata"] is None and k["cozum_kimligi"].startswith("bina-") and k["onbellekte"] is False
    cozum = iste(kopru, "bina_coz", {"bina": json.dumps(iki_kat)}, {"anlat": False})
    assert cozum["veri"]["cozum_kimligi"] == k["cozum_kimligi"]
    k2 = iste(kopru, "bina_kimlik", {"bina": json.dumps(iki_kat)})
    assert k2["cozum_kimligi"] == k["cozum_kimligi"] and k2["onbellekte"] is True
    # Genel (surum 3) model şablonu da aynı kuralla.
    genel = next((ad for ad in yapi.BINA_SABLONLARI if yapi._serbest_mi(yapi.bina_sablon(ad))), None)
    if genel:
        b = yapi.bina_sablon(genel)
        assert iste(kopru, "bina_kimlik", {"bina": b})["cozum_kimligi"] == yapi.cozum_kimligi(b)
    # Başka model → başka kimlik.
    assert iste(kopru, "bina_kimlik", {"bina": yapi.bina_sablon("betonarme-3kat-3x3")})["cozum_kimligi"] != k["cozum_kimligi"]
    h = iste(kopru, "bina_kimlik", {})
    assert h["hata_turu"] == "girdi" and "boş" in h["hata"]
    h = iste(kopru, "bina_kimlik", {"bina": "{bozuk"})
    assert h["hata_turu"] == "girdi" and "JSON" in h["hata"]
    assert "bina_kimlik" not in kopru.BINA_ISLEMLER and "bina_kimlik" in kopru.OP4_ISLEMLER


def test_iptal_keyboardinterrupt(kopru, monkeypatch, iki_kat):
    def kesik(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(kopru, "_bina_islem", kesik)
    y = iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": 6000})
    assert y == {"hata": "İşlem iptal edildi.", "hata_turu": "iptal"}
    # iptal sınırları geri yükler
    assert yapi.EN_FAZLA_SD == 1500 and yapi_serbest.EN_FAZLA_SD == 2000 and temel.EN_KUCUK_AG == 0.10
    monkeypatch.setattr(kopru, "_calistir", kesik)
    assert iste(kopru, "determinant", {"A": "1 2; 3 4"})["hata_turu"] == "iptal"


def test_bellek_hatasi_ogretici(kopru, monkeypatch):
    def tasma(*a, **k):
        raise MemoryError
    monkeypatch.setattr(kopru, "_bina_islem", tasma)
    y = iste(kopru, "bina_coz", {"bina": {}})
    assert y["hata_turu"] == "ic" and "bellek" in y["hata"]


def test_sd_siniri_istek_suresince(kopru, monkeypatch, iki_kat):
    gorulen = {}
    gercek = yapi.bina_coz

    def izle(*a, **k):
        gorulen.update(yapi=yapi.EN_FAZLA_SD, serbest=yapi_serbest.EN_FAZLA_SD, ag=temel.EN_KUCUK_AG)
        return gercek(*a, **k)
    monkeypatch.setattr(yapi, "bina_coz", izle)
    y = iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": 6000, "anlat": False})
    assert y["hata"] is None
    assert gorulen == {"yapi": 6000, "serbest": 6000, "ag": 0.05}
    assert yapi.EN_FAZLA_SD == 1500 and yapi_serbest.EN_FAZLA_SD == 2000 and temel.EN_KUCUK_AG == 0.10
    # aralığa çekilir; küçük sınırda ağ alt sınırı değişmez
    iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": 10 ** 9, "anlat": False})
    assert gorulen["yapi"] == 200_000 and gorulen["ag"] == 0.02
    iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": 1000, "anlat": False})
    assert gorulen == {"yapi": 1000, "serbest": 1000, "ag": 0.10}
    # verilmezse web sınırları
    iste(kopru, "bina_coz", {"bina": iki_kat}, {"anlat": False})
    assert gorulen == {"yapi": 1500, "serbest": 2000, "ag": 0.10}
    assert yapi.EN_FAZLA_SD == 1500


def test_sd_siniri_iletisi_ve_gecersiz_deger(kopru, iki_kat):
    web = iste(kopru, "bina_coz", {"bina": iki_kat}, {"anlat": False})
    assert web["hata"] is None
    sd = web["veri"]["ozet"]["sd_sayisi"]
    assert sd > 100
    y = iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": 100})
    assert y["hata_turu"] == "girdi"
    assert "bellek ve süre sınırı nedeniyle en fazla 100" in y["hata"] and "tarayıcı" not in y["hata"]
    assert yapi.EN_FAZLA_SD == 1500
    for kotu in ("çok", [1], {"a": 1}):
        h = iste(kopru, "bina_coz", {"bina": iki_kat}, {"sd_siniri": kotu})
        assert h["hata_turu"] == "girdi" and "sd_siniri" in h["hata"], h
        assert iste(kopru, "bina_kimlik", {"bina": iki_kat}, {"sd_siniri": kotu})["hata_turu"] == "girdi"
    # bina dışı işlemler bilinmeyen ayarı yok sayar
    d = iste(kopru, "determinant", {"A": "2 1; 1 3"}, {"sd_siniri": 6000})
    assert d["hata"] is None and d["sonuc_metin"] == "5"
    assert kopru._sinir_iletileri("x; tarayıcıda çözüm için en fazla 1500. y") == "x; bellek ve süre sınırı nedeniyle en fazla 1500. y"
