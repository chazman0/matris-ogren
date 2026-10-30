"""op4 hesap motoru TEL PROTOKOLÜ — Python kodlayıcısı / çözücüsü (MIMARI §8.2; "F1 paket sözleşmeleri" §S12).

Bağlayıcı tanım op4/kaynak/cekirdek/motor_protokol.h başlık yorumundadır; bu modül onun Python karşılığıdır ve aynı
baytları üretir (ortak sınama vektörleri: op4/testler/ortak/motor_protokol.json). Sunucu döngüsü (op4_sunucu.py; A paketi)
bu modülü kullanır. Yalnız standart kitaplık; Python 3.10+.

Çerçeve: 4 bayt küçük-endian uzunluk N (1 ≤ N ≤ 512 MiB) + N bayt UTF-8 JSON nesnesi.
İletilerde alan sırası ve boşluksuz yazım bağlayıcıdır; `istek` ve `yanit` alanları SON alandır ve olduğu gibi (yeniden
kodlanmadan) taşınır. Sayı yazımı: sure_ms "%.1f", oran tamsayı (yarım sıfırdan uzağa yuvarlanır, C llround gibi).
"""
from __future__ import annotations

import json
import math
import struct
from typing import BinaryIO, Optional

EN_BUYUK_CERCEVE = 512 * 1024 * 1024
EN_BUYUK_ID = (1 << 53) - 1

# Sunucu çıkış kodları (motor_protokol.h).
CIKIS_DUZGUN = 0
CIKIS_KULLANIM = 2
CIKIS_PROTOKOL = 3
CIKIS_BASLATMA = 4

IPTAL_YANITI_METNI = "İşlem iptal edildi."


class ProtokolHatasi(Exception):
    """Bozuk çerçeve ya da ileti (sunucu CIKIS_PROTOKOL ile çıkar)."""


# ---------------------------------------------------------------------------------------------------------------- çerçeve
def cerceve(govde: bytes) -> bytes:
    if not govde or len(govde) > EN_BUYUK_CERCEVE:
        raise ProtokolHatasi(f"çerçeve uzunluğu geçersiz: {len(govde)}")
    return struct.pack("<I", len(govde)) + govde


def cerceve_yaz(akis: BinaryIO, govde: bytes) -> None:
    akis.write(cerceve(govde))
    akis.flush()


def _tam_oku(akis: BinaryIO, n: int) -> bytes:
    parcalar = []
    kalan = n
    while kalan:
        b = akis.read(kalan)
        if not b:
            break
        parcalar.append(b)
        kalan -= len(b)
    return b"".join(parcalar)


def cerceve_oku(akis: BinaryIO) -> Optional[bytes]:
    """Bir çerçeve okur. Çerçeve sınırında akış biterse None (karşı uç kapandı); yarım çerçeve ProtokolHatasi."""
    bas = _tam_oku(akis, 4)
    if not bas:
        return None
    if len(bas) < 4:
        raise ProtokolHatasi("yarım çerçeve başlığı")
    (n,) = struct.unpack("<I", bas)
    if n == 0 or n > EN_BUYUK_CERCEVE:
        raise ProtokolHatasi(f"çerçeve uzunluğu geçersiz: {n}")
    govde = _tam_oku(akis, n)
    if len(govde) < n:
        raise ProtokolHatasi(f"yarım çerçeve: {len(govde)}/{n} bayt")
    return govde


# ---------------------------------------------------------------------------------------------------------------- yazım
def json_kacis(s: str) -> str:
    """JSON dize kaçışı, tırnaksız (json.dumps(ensure_ascii=False) ile aynı)."""
    return json.dumps(s, ensure_ascii=False)[1:-1]


def _ondalik1(v: float) -> str:
    if v is None or not math.isfinite(v):
        v = 0.0
    return "%.1f" % v


def _tam(oran: float) -> str:
    if oran is None or not math.isfinite(oran):
        oran = 0.0
    return str(int(math.floor(oran + 0.5)) if oran >= 0 else -int(math.floor(-oran + 0.5)))


def _b(s: str) -> bytes:
    return s.encode("utf-8")


def istek_iletisi(id_: int, islem: str, istek_json: str) -> bytes:
    return _b('{"tur":"istek","id":%d,"islem":"%s","istek":' % (id_, json_kacis(islem)) + istek_json + "}")


def iptal_iletisi(id_: int) -> bytes:
    return _b('{"tur":"iptal","id":%d}' % id_)


def kapat_iletisi() -> bytes:
    return b'{"tur":"kapat"}'


def hazir_iletisi(rol: str, basarili: bool, pid: int, python: str, sure_ms: float, surum_json: str,
                  hata: str = "") -> bytes:
    return _b('{"tur":"hazir","rol":"%s","basarili":%s,"pid":%d,"python":"%s","sure_ms":%s,"surum":%s,"hata":"%s"}' % (
        json_kacis(rol), "true" if basarili else "false", pid, json_kacis(python), _ondalik1(sure_ms),
        surum_json or "{}", json_kacis(hata)))


def durum_iletisi(metin: str, oran: float) -> bytes:
    return _b('{"tur":"durum","metin":"%s","oran":%s}' % (json_kacis(metin), _tam(oran)))


def ilerleme_iletisi(id_: int, metin: str, oran: float) -> bytes:
    return _b('{"tur":"ilerleme","id":%d,"metin":"%s","oran":%s}' % (id_, json_kacis(metin), _tam(oran)))


def gunluk_iletisi(duzey: str, metin: str) -> bytes:
    return _b('{"tur":"gunluk","duzey":"%s","metin":"%s"}' % (json_kacis(duzey), json_kacis(metin)))


def yanit_iletisi(id_: int, sure_ms: float, calistir_metni: str) -> bytes:
    return _b('{"tur":"yanit","id":%d,"sure_ms":%s,"yanit":' % (id_, _ondalik1(sure_ms)) + calistir_metni + "}")


def hata_yaniti(ileti: str, hata_turu: str) -> str:
    return '{"hata":"%s","hata_turu":"%s"}' % (json_kacis(ileti), json_kacis(hata_turu))


# ---------------------------------------------------------------------------------------------------------------- çözüm
_ISTEK_ONEKI = '{"tur":"istek","id":'
_YANIT_ONEKI = '{"tur":"yanit","id":'


def ileti_coz(govde: bytes) -> dict:
    """Bir ileti gövdesini çözer.

    istek → {"tur": "istek", "id", "islem", "istek_metni"} (istek nesnesi ayrıştırılmadan dilimlenir)
    yanit → {"tur": "yanit", "id", "sure_ms", "yanit_metni"}
    diğerleri → json.loads sonucu (bilinmeyen tür hata değildir).
    """
    try:
        metin = govde.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ProtokolHatasi(f"ileti UTF-8 değil: {e}") from None
    if metin.startswith(_ISTEK_ONEKI):
        kalan = metin[len(_ISTEK_ONEKI):]
        v = kalan.find(',"islem":"')
        if v < 0 or not kalan.endswith("}"):
            raise ProtokolHatasi("istek iletisi biçimi bozuk")
        id_ = int(kalan[:v])
        kalan = kalan[v + len(',"islem":'):]
        # islem bir JSON dizesidir: kaçışlı tırnakları atlayarak sonunu bul.
        i, kac = 1, False
        while i < len(kalan):
            c = kalan[i]
            if kac:
                kac = False
            elif c == "\\":
                kac = True
            elif c == '"':
                break
            i += 1
        islem = json.loads(kalan[:i + 1])
        kalan = kalan[i + 1:]
        if not kalan.startswith(',"istek":'):
            raise ProtokolHatasi("istek iletisinde 'istek' alanı yok")
        return {"tur": "istek", "id": id_, "islem": islem, "istek_metni": kalan[len(',"istek":'):-1]}
    if metin.startswith(_YANIT_ONEKI):
        kalan = metin[len(_YANIT_ONEKI):]
        v1 = kalan.find(',"sure_ms":')
        v2 = kalan.find(',"yanit":')
        if v1 < 0 or v2 < v1 or not kalan.endswith("}"):
            raise ProtokolHatasi("yanit iletisi biçimi bozuk")
        return {"tur": "yanit", "id": int(kalan[:v1]), "sure_ms": float(kalan[v1 + len(',"sure_ms":'):v2]),
                "yanit_metni": kalan[v2 + len(',"yanit":'):-1]}
    try:
        d = json.loads(metin)
    except ValueError as e:
        raise ProtokolHatasi(f"ileti JSON değil: {e}") from None
    if not isinstance(d, dict):
        raise ProtokolHatasi("ileti JSON nesnesi değil")
    return d
