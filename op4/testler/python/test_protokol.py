"""op4 hesap motoru tel protokolü — Python kodlayıcısı sınamaları (sözleşme S12).

Ortak vektörler op4/testler/ortak/motor_protokol.json; aynı vektörleri C++ (op4/testler/cekirdek/sozlesme_protokol.cpp)
de sınar. Çalıştırma: python3 -m pytest op4/testler/python -q -p no:cacheprovider
"""
from __future__ import annotations

import io
import json
import pathlib
import struct
import sys

import pytest

OP4 = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(OP4 / "motor"))

import op4_protokol as p  # noqa: E402

VEKTORLER = json.loads((OP4 / "testler" / "ortak" / "motor_protokol.json").read_text(encoding="utf-8"))


def _uret(v: dict) -> bytes:
    g, t = v["girdi"], v["tur"]
    if t == "istek":
        return p.istek_iletisi(g["id"], g["islem"], g["istek_json"])
    if t == "iptal":
        return p.iptal_iletisi(g["id"])
    if t == "kapat":
        return p.kapat_iletisi()
    if t == "hazir":
        return p.hazir_iletisi(g["rol"], g["basarili"], g["pid"], g["python"], g["sure_ms"], g["surum_json"], g["hata"])
    if t == "durum":
        return p.durum_iletisi(g["metin"], g["oran"])
    if t == "ilerleme":
        return p.ilerleme_iletisi(g["id"], g["metin"], g["oran"])
    if t == "gunluk":
        return p.gunluk_iletisi(g["duzey"], g["metin"])
    if t == "yanit":
        return p.yanit_iletisi(g["id"], g["sure_ms"], g["calistir_metni"])
    raise AssertionError(t)


@pytest.mark.parametrize("v", VEKTORLER["vektorler"], ids=lambda v: v["ad"])
def test_vektor_kodlama_ve_cozum(v):
    govde = _uret(v)
    assert govde.decode("utf-8") == v["govde"]
    c = p.ileti_coz(govde)
    g = v["girdi"]
    assert c["tur"] == v["tur"]
    if v["tur"] == "istek":
        assert (c["id"], c["islem"], c["istek_metni"]) == (g["id"], g["islem"], g["istek_json"])
    elif v["tur"] == "yanit":
        assert (c["id"], c["yanit_metni"]) == (g["id"], g["calistir_metni"])
    else:
        json.loads(govde)  # diğer iletiler geçerli JSON


def test_hata_yaniti():
    assert p.hata_yaniti(p.IPTAL_YANITI_METNI, "iptal") == VEKTORLER["hata_yaniti_iptal"]
    assert json.loads(p.hata_yaniti('a"b', "girdi")) == {"hata": 'a"b', "hata_turu": "girdi"}


def test_cerceve_akis_ve_eof():
    akis = io.BytesIO()
    p.cerceve_yaz(akis, p.kapat_iletisi())
    p.cerceve_yaz(akis, p.iptal_iletisi(3))
    akis.seek(0)
    assert p.cerceve_oku(akis) == b'{"tur":"kapat"}'
    assert p.ileti_coz(p.cerceve_oku(akis)) == {"tur": "iptal", "id": 3}
    assert p.cerceve_oku(akis) is None  # temiz EOF


@pytest.mark.parametrize("bayt", [struct.pack("<I", 0) + b"x", struct.pack("<I", p.EN_BUYUK_CERCEVE + 1), b"\x05\x00",
                                  struct.pack("<I", 10) + b"kisa"])
def test_bozuk_cerceve(bayt):
    with pytest.raises(p.ProtokolHatasi):
        p.cerceve_oku(io.BytesIO(bayt))


def test_bos_govde_yazilmaz():
    with pytest.raises(p.ProtokolHatasi):
        p.cerceve(b"")


def test_yuvarlama_c_ile_ayni():
    # oran: yarım sıfırdan uzağa (C llround); sure_ms: "%.1f".
    assert p.durum_iletisi("x", 2.5).endswith(b'"oran":3}')
    assert p.durum_iletisi("x", -2.5).endswith(b'"oran":-3}')
    assert b'"sure_ms":0.1,' in p.yanit_iletisi(1, 0.05000001, "{}")


def test_buyuk_yanit_dilimlenir():
    buyuk = json.dumps({"hata": None, "veri": {"x": "a" * 1_000_000, "yanit": '"yanit":}'}})
    c = p.ileti_coz(p.yanit_iletisi(7, 1.0, buyuk))
    assert c["yanit_metni"] == buyuk
