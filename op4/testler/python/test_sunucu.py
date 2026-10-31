"""op4 hesap motoru sunucusu (op4/motor/op4_sunucu.py) — süreç düzeyinde sınamalar (MIMARI §8.1, §8.4; kabul A7).

Sunucu gerçek bir alt süreç olarak `python -X utf8 -B -m op4_sunucu --istek <fd> --yanit <fd>` ile başlatılır; iki boru
üstünden tel protokolüyle (op4_protokol.py) konuşulur. Motor olarak çoğu sınamada sahte_motor/web_kopru.py (yalnız standart
kitaplık) kullanılır; gerçek docs/web_kopru.py sınamaları numpy + sympy varsa çalışır (OP4_MOTOR_SINAMA_ZORUNLU=1 iken
eksiklik sınamayı düşürür — CI).

Denetlenenler: hazir / durum iletileri, Y1 (her id'ye tam bir yanıt), Y2 (sıra), kuyruktaki ve çalışan isteğin iptali
(interrupt_main), geç iptalin yok sayılması, iptale yanıt vermeyen hesap, print / fd 1–2 yazılarının protokolü bozmaması ve
günlüğe gitmesi, 50 MB yanıt, kapat ve boru kapanması (Y4, kod 0), çökme, bozuk çerçeve (kod 3), içe aktarma hatası
(hazir basarili=false, kod 4), kullanım hatası (kod 2), BLAS iş parçacığı ayarı.
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import queue
import struct
import subprocess
import sys
import threading
import time

import pytest

OP4 = pathlib.Path(__file__).resolve().parents[2]
DEPO = OP4.parent
MOTOR = OP4 / "motor"
SAHTE = pathlib.Path(__file__).resolve().parent / "sahte_motor"
sys.path.insert(0, str(MOTOR))

import op4_protokol as p  # noqa: E402

BLAS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


def _gercek_motor_var() -> bool:
    try:
        import numpy  # noqa: F401
        import sympy  # noqa: F401
    except ImportError:
        return False
    return (DEPO / "docs" / "web_kopru.py").is_file()


gercek_motor = pytest.mark.skipif(not _gercek_motor_var() and os.environ.get("OP4_MOTOR_SINAMA_ZORUNLU") != "1",
                                  reason="numpy / sympy yok (gerçek web_kopru sınaması)")


class Sunucu:
    """Alt süreçte op4_sunucu + iki boru; gelen iletiler arka planda okunup kuyruğa konur."""

    def __init__(self, yollar=(SAHTE,), rol="ana", gunluk=None, blas=None, ortam=None, ek=()):
        istek_r, istek_w = os.pipe()
        yanit_r, yanit_w = os.pipe()
        env = {k: v for k, v in os.environ.items() if k not in BLAS and k != "PYTHONPATH"}
        env.update(PYTHONPATH=os.pathsep.join([str(MOTOR), *map(str, yollar)]), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        env.update(ortam or {})
        if os.name == "nt":
            import msvcrt
            h_istek, h_yanit = msvcrt.get_osfhandle(istek_r), msvcrt.get_osfhandle(yanit_w)
            os.set_handle_inheritable(h_istek, True)
            os.set_handle_inheritable(h_yanit, True)
            arg_istek, arg_yanit = str(h_istek), str(h_yanit)
            si = subprocess.STARTUPINFO()
            si.lpAttributeList = {"handle_list": [h_istek, h_yanit]}
            ek_kw = {"startupinfo": si, "close_fds": True}
        else:
            arg_istek, arg_yanit = str(istek_r), str(yanit_w)
            ek_kw = {"pass_fds": (istek_r, yanit_w)}
        komut = [sys.executable, "-X", "utf8", "-B", "-m", "op4_sunucu", "--istek", arg_istek, "--yanit", arg_yanit,
                 "--rol", rol, *(["--gunluk", str(gunluk)] if gunluk else []), *(["--blas", str(blas)] if blas else []),
                 *ek]
        self.surec = subprocess.Popen(komut, env=env, cwd=str(OP4), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, **ek_kw)
        os.close(istek_r)
        os.close(yanit_w)
        self.yazici = os.fdopen(istek_w, "wb")
        self.okuyucu = os.fdopen(yanit_r, "rb")
        self.gelen: queue.Queue = queue.Queue()
        self.ham: list[bytes] = []
        threading.Thread(target=self._oku, daemon=True).start()

    def _oku(self):
        try:
            while True:
                g = p.cerceve_oku(self.okuyucu)
                if g is None:
                    break
                self.ham.append(g)
                self.gelen.put(p.ileti_coz(g))
        except Exception as e:  # noqa: BLE001
            self.gelen.put({"tur": "_okuma_hatasi", "hata": repr(e)})
        self.gelen.put({"tur": "_eof"})

    # -- gönderim
    def yaz(self, govde: bytes):
        p.cerceve_yaz(self.yazici, govde)

    def istek(self, id_, islem, girdi=None, ayarlar=None):
        metin = json.dumps({"islem": islem, "girdi": girdi or {}, "ayarlar": ayarlar or {}}, ensure_ascii=False)
        self.yaz(p.istek_iletisi(id_, islem, metin))

    def iptal(self, id_):
        self.yaz(p.iptal_iletisi(id_))

    def kapat(self):
        self.yaz(p.kapat_iletisi())

    # -- alım
    def al(self, zaman=10.0, tur=None):
        bitis = time.monotonic() + zaman
        while True:
            kalan = bitis - time.monotonic()
            if kalan <= 0:
                raise TimeoutError(f"{zaman} s içinde ileti gelmedi (beklenen tür {tur})")
            i = self.gelen.get(timeout=kalan)
            if tur is None or i["tur"] == tur or i["tur"] in ("_eof", "_okuma_hatasi"):
                if tur is not None and i["tur"] != tur:
                    raise AssertionError(f"{tur} beklenirken {i}; stderr: {self.stderr()}")
                return i

    def yanit(self, zaman=10.0):
        i = self.al(zaman, "yanit")
        i["yanit"] = json.loads(i["yanit_metni"])
        return i

    def hazir(self, zaman=60.0):
        durumlar = []
        while True:
            i = self.al(zaman)
            if i["tur"] == "durum":
                durumlar.append(i)
                continue
            assert i["tur"] == "hazir", (i, self.stderr())
            i["durumlar"] = durumlar
            return i

    def bos_mu(self, sure=0.3) -> bool:
        try:
            i = self.gelen.get(timeout=sure)
        except queue.Empty:
            return True
        self.gelen.put(i)
        return False

    def bekle(self, zaman=10.0) -> int:
        return self.surec.wait(timeout=zaman)

    def stderr(self) -> str:
        return "(süreç çalışıyor)" if self.surec.poll() is None else self.surec.stderr.read().decode("utf-8", "replace")

    def kapat_zorla(self):
        for akis in (self.yazici,):
            try:
                akis.close()
            except OSError:
                pass
        if self.surec.poll() is None:
            self.surec.kill()
        self.surec.wait(timeout=10)
        self.surec.stdout.close()
        self.surec.stderr.close()


@pytest.fixture
def sunucu(request):
    nesneler = []

    def kur(**kw):
        s = Sunucu(**kw)
        nesneler.append(s)
        return s
    yield kur
    for s in nesneler:
        s.kapat_zorla()


def test_hazir_ve_durum_iletileri(sunucu):
    s = sunucu()
    h = s.hazir()
    assert h["rol"] == "ana" and h["basarili"] is True and h["hata"] == ""
    assert h["pid"] == s.surec.pid and h["python"] == platform.python_version() and h["sure_ms"] > 0
    assert h["surum"]["motor"] == "sahte-1" and h["surum"]["protokol"] == 1
    oranlar = [d["oran"] for d in h["durumlar"]]
    assert oranlar == sorted(oranlar) and oranlar[-1] == 100 and len(oranlar) >= 3
    # hazir bayt düzeyinde ortak kodlayıcının biçiminde (alan sırası bağlayıcı)
    ham = next(g for g in s.ham if g.startswith(b'{"tur":"hazir"'))
    assert ham.startswith(b'{"tur":"hazir","rol":"ana","basarili":true,"pid":') and ham.endswith(b',"hata":""}')


def test_istekler_sirayla_tek_yanit(sunucu):
    s = sunucu()
    s.hazir()
    metin = 'Ş"ğ\\ı\n\t — çözüm'
    for i in range(1, 8):
        s.istek(i, "yanki", {"n": i, "metin": metin}, {"anlat": False})
    for i in range(1, 8):
        y = s.yanit()
        assert y["id"] == i and y["yanit"]["hata"] is None
        assert y["yanit"]["girdi"] == {"n": i, "metin": metin} and y["yanit"]["ayarlar"] == {"anlat": False}
        assert y["sure_ms"] >= 0
    assert s.bos_mu()


def test_kuyruktaki_istegin_iptali_hemen(sunucu):
    s = sunucu()
    s.hazir()
    s.istek(1, "uyu", {"s": 1.5})
    s.istek(2, "yanki", {"a": 1})
    s.istek(3, "yanki", {"a": 2})
    t0 = time.monotonic()
    s.iptal(2)
    y = s.yanit()
    assert y["id"] == 2 and y["yanit"] == {"hata": "İşlem iptal edildi.", "hata_turu": "iptal"}
    assert time.monotonic() - t0 < 1.0, "kuyruktaki iptal hemen yanıtlanmalı"
    assert s.yanit()["id"] == 1
    y3 = s.yanit()
    assert y3["id"] == 3 and y3["yanit"]["girdi"] == {"a": 2}
    assert s.bos_mu()


def test_calisan_istegin_iptali_interrupt_main(sunucu):
    s = sunucu()
    s.hazir()
    s.istek(1, "uyu", {"s": 30})
    time.sleep(0.4)
    t0 = time.monotonic()
    s.iptal(1)
    y = s.yanit(zaman=5)
    assert y["id"] == 1 and y["yanit"]["hata_turu"] == "iptal"
    assert time.monotonic() - t0 < 2.0
    # sunucu sağlam: sonraki istekler olağan
    s.istek(2, "uyu", {"s": 0.3})
    s.istek(3, "yanki", {"x": "y"})
    assert s.yanit()["yanit"] == {"hata": None, "uyudu": 0.3}
    assert s.yanit()["id"] == 3


def test_gec_ve_bilinmeyen_iptal_yok_sayilir(sunucu):
    s = sunucu()
    s.hazir()
    s.istek(1, "yanki", {})
    assert s.yanit()["id"] == 1
    s.iptal(1)       # bitmiş
    s.iptal(999)     # hiç gelmemiş
    s.istek(2, "uyu", {"s": 0.4})
    y = s.yanit()
    assert y["id"] == 2 and y["yanit"]["hata"] is None, "geç iptal sonraki isteği kesmemeli"
    assert s.bos_mu(0.5)


def test_iptal_yarisi_her_ide_tek_yanit(sunucu):
    """İptal, istek bitişiyle yarışabilir: her durumda her id'ye tam bir yanıt (Y1)."""
    s = sunucu()
    s.hazir()
    n = 40
    for i in range(1, n + 1):
        s.istek(i, "uyu", {"s": 0.01 * (i % 3)})
        if i % 2 == 0:
            s.iptal(i)
        if i % 5 == 0:
            s.iptal(i - 1)
    gelen = [s.yanit()["id"] for _ in range(n)]
    assert sorted(gelen) == list(range(1, n + 1))
    assert s.bos_mu(0.5)


def test_iptale_yanit_vermeyen_hesap(sunucu):
    """KeyboardInterrupt'ı yutan hesap (uzun yerel çağrı benzetimi) bitene dek yanıt gelmez; istemci 5 s sonra sonlandırır."""
    s = sunucu()
    s.hazir()
    s.istek(1, "kilitlen", {"s": 1.5})
    time.sleep(0.2)
    s.iptal(1)
    assert s.bos_mu(0.8)
    y = s.yanit(zaman=5)
    assert y["id"] == 1 and y["yanit"]["kesme"] >= 1
    s.istek(2, "yanki", {})
    assert s.yanit()["id"] == 2


def test_print_ve_ham_yazi_protokolu_bozmaz(sunucu, tmp_path):
    gunluk = tmp_path / "motor-ana.log"
    s = sunucu(gunluk=gunluk)
    s.hazir()
    s.istek(1, "yazdir")
    s.istek(2, "yanki", {"sonra": True})
    assert s.yanit()["yanit"] == {"hata": None, "yazdi": True}
    assert s.yanit()["yanit"]["girdi"] == {"sonra": True}
    s.kapat()
    assert s.bekle() == 0
    metin = gunluk.read_text(encoding="utf-8", errors="replace")
    for parca in ("print: stdout'a yazı", "print: stderr'e yazı", "fd1 ham bayt", "fd2 ham bayt", "hazır", "istek 1 yazdir"):
        assert parca in metin, parca
    assert s.surec.stdout.read() == b"" and s.surec.stderr.read() == b""


def test_buyuk_yanit_50_mb(sunucu):
    s = sunucu()
    s.hazir()
    t0 = time.monotonic()
    s.istek(1, "buyuk", {"mb": 50})
    i = s.al(60, "yanit")
    sure = time.monotonic() - t0
    assert i["id"] == 1
    assert len(i["yanit_metni"].encode("utf-8")) >= 50 * 1024 * 1024
    y = json.loads(i["yanit_metni"])
    assert y["hata"] is None and len(y["veri"]) == y["boyut"] // 2
    print(f"OP4OLCUM senaryo=sunucu_buyuk_yanit mb=50 sure_ms={sure * 1000:.0f}")
    s.istek(2, "yanki", {})
    assert s.yanit()["id"] == 2


def test_kapat_kuyrugu_bosaltmadan_cikar(sunucu):
    s = sunucu()
    s.hazir()
    s.istek(1, "uyu", {"s": 30})
    s.istek(2, "yanki", {})
    time.sleep(0.3)
    t0 = time.monotonic()
    s.kapat()
    assert s.bekle(5) == 0
    assert time.monotonic() - t0 < 4.0
    kalan = []
    while True:
        i = s.gelen.get(timeout=5)
        if i["tur"] == "_eof":
            break
        kalan.append(i)
    assert all(i.get("id") != 2 for i in kalan), "kapat kuyruğu işlememeli"


def test_istek_borusu_kapaninca_cikar(sunucu):
    s = sunucu()
    s.hazir()
    s.yazici.close()
    assert s.bekle(5) == 0
    assert s.al(5)["tur"] == "_eof"


def test_cokme_eof_ve_cikis_kodu(sunucu):
    s = sunucu()
    s.hazir()
    s.istek(1, "cok", {"kod": 7})
    assert s.al(5)["tur"] == "_eof"
    assert s.bekle(5) == 7


@pytest.mark.parametrize("govde", [b"\x00\x00\x00\x00", struct.pack("<I", p.EN_BUYUK_CERCEVE + 1)])
def test_bozuk_cerceve_kod_3(sunucu, govde):
    s = sunucu()
    s.hazir()
    s.yazici.write(govde)
    s.yazici.flush()
    assert s.bekle(5) == p.CIKIS_PROTOKOL


@pytest.mark.parametrize("ileti", [b"bu json degil", b'{"tur":"istek","id":0,"islem":"x","istek":{}}', b'{"tur":"iptal"}'])
def test_bozuk_ileti_kod_3(sunucu, ileti):
    s = sunucu()
    s.hazir()
    s.yaz(ileti)
    assert s.bekle(5) == p.CIKIS_PROTOKOL


def test_bilinmeyen_ileti_turu_ve_esnek_alan_sirasi(sunucu):
    s = sunucu()
    s.hazir()
    s.yaz(b'{"tur":"gelecekte","x":1}')
    g = s.al(5, "gunluk")
    assert g["duzey"] == "uyari" and "gelecekte" in g["metin"]
    s.yaz(json.dumps({"tur": "istek", "istek": {"islem": "yanki", "girdi": {"k": 1}}, "islem": "yanki", "id": 5}).encode())
    y = s.yanit()
    assert y["id"] == 5 and y["yanit"]["girdi"] == {"k": 1}


def test_ice_aktarma_hatasi_hazir_basarisiz_kod_4(sunucu):
    s = sunucu(ortam={"OP4_SAHTE_MOTOR_ICE_AKTARMA_HATASI": "1"})
    h = s.hazir()
    assert h["basarili"] is False and "içe aktarılamadı" in h["hata"] and "ImportError" in h["hata"]
    assert s.bekle(5) == p.CIKIS_BASLATMA


def test_kullanim_hatasi_kod_2():
    r = subprocess.run([sys.executable, "-m", "op4_sunucu", "--rol", "ana"], cwd=str(MOTOR), capture_output=True,
                       timeout=30)
    assert r.returncode == p.CIKIS_KULLANIM


@pytest.mark.parametrize("rol,blas,beklenen", [("yardimci", None, "1"), ("ana", 3, "3"),
                                                ("ana", None, str(max(1, (os.cpu_count() or 2) - 1)))])
def test_blas_is_parcacigi(sunucu, rol, blas, beklenen):
    s = sunucu(rol=rol, blas=blas)
    assert s.hazir()["rol"] == rol
    s.istek(1, "ortam")
    y = s.yanit()["yanit"]
    assert y["pid"] == s.surec.pid
    assert set(y["blas"].values()) == {beklenen}


# --------------------------------------------------------------------------------------------- gerçek motor (web_kopru)
@gercek_motor
def test_gercek_motor(sunucu):
    s = sunucu(yollar=(DEPO / "docs",), rol="ana")
    h = s.hazir(zaman=120)
    assert h["basarili"] is True, h
    assert {"motor", "python", "sympy", "numpy"} <= set(h["surum"])
    print(f"OP4OLCUM senaryo=sunucu_gercek hazir_ms={h['sure_ms']:.1f}")
    s.istek(1, "determinant", {"A": "2 1; 1 3"})
    assert s.yanit()["yanit"]["sonuc_metin"] == "5"
    s.istek(2, "bina_sablonlar")
    sablonlar = [x["ad"] for x in s.yanit()["yanit"]["sablonlar"]]
    assert len(sablonlar) >= 9
    s.istek(3, "bina_sablon", {"ad": "betonarme-tek-aciklik"})
    bina = s.yanit()["yanit"]["bina"]
    s.istek(4, "bina_kimlik", {"bina": bina})
    kimlik = s.yanit()["yanit"]["cozum_kimligi"]
    s.istek(5, "bina_coz", {"bina": bina}, {"anlat": False, "sd_siniri": 6000})
    c = s.yanit(zaman=120)["yanit"]
    assert c["hata"] is None and c["bloklar"] == [] and c["veri"]["cozum_kimligi"] == kimlik
    # büyük çözümün iptali (KeyboardInterrupt hesap ortasında)
    s.istek(6, "bina_sablon", {"ad": "celik-sanayi-4hol"})
    buyuk = s.yanit()["yanit"]["bina"]
    s.istek(7, "bina_coz", {"bina": buyuk}, {"anlat": True})
    time.sleep(1.0)
    t0 = time.monotonic()
    s.iptal(7)
    y = s.yanit(zaman=30)
    sure = time.monotonic() - t0
    assert y["id"] == 7 and y["yanit"]["hata_turu"] == "iptal", y["yanit"].get("hata")
    print(f"OP4OLCUM senaryo=sunucu_iptal iptal_ms={sure * 1000:.0f}")
    assert sure < 5.0
    s.istek(8, "determinant", {"A": "4"})
    assert s.yanit()["yanit"]["sonuc_metin"] == "4"
    s.kapat()
    assert s.bekle(10) == 0
