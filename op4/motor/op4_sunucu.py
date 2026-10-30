"""op4 hesap motoru SUNUCUSU (MIMARI §8.1, §8.2, §8.4; F1 iş 1.2, kabul A7).

op4.exe hesap motorunu ayrı süreçte çalıştırır. Bu modül o sürecin sunucu döngüsüdür:

  op4motor.exe --istek <tutamaç> --yanit <tutamaç> --rol ana|yardimci [--gunluk <dosya>] [--blas <n>]
      (Windows; op4motor.exe aynı bağımsız değişkenleri `-X utf8 -B -m op4_sunucu` ile Py_Main'e iletir)
  python3 -X utf8 -B -m op4_sunucu --istek <fd> --yanit <fd> --rol ana    (Linux sınaması; PYTHONPATH = op4/motor:docs)

Tel protokolü op4_protokol.py'dedir (bağlayıcı tanım: op4/kaynak/cekirdek/motor_protokol.h). Bu döngünün kuralları:

1. Protokol stdout / stderr'den GEÇMEZ: miras alınan iki boru tutamacı kullanılır. sys.stdout, sys.stderr ve fd 1–2 günlük
   dosyasına yönlendirilir; motordaki print çağrıları ve yerel kitaplıkların stderr yazıları protokolü bozmaz.
2. BLAS iş parçacığı sayısı numpy içe aktarılmadan önce ayarlanır (ana: çekirdek − 1, yardımcı: 1; --blas önceliklidir).
3. Okuyucu iş parçacığı istek borusunu dinler: "istek" kuyruğa girer; "iptal" kuyruktaki isteği hemen yanıtlar, çalışan
   isteği `_thread.interrupt_main()` ile keser; "kapat" ve borunun kapanması (op4.exe öldü) düzgün çıkıştır (kod 0).
4. Ana iş parçacığı istekleri geliş sırasıyla, tek tek `web_kopru.calistir()` ile işler (Y2) ve her id'ye TAM BİR yanıt
   verir (Y1): başarı, hata ya da {"hata":"İşlem iptal edildi.","hata_turu":"iptal"}.
5. SIGINT işleyicisi KeyboardInterrupt'ı YALNIZ iptal edilen istek çalışırken yükseltir (MIMARI §8.4'teki
   `signal.default_int_handler`'ın korumalı biçimi): istek bittikten sonra gelen geç kesme yok sayılır, böylece bir sonraki
   istek ya da yanıt yazımı yanlışlıkla kesilmez. `interrupt_main` bayt kodu sınırında etkilidir; ana iş parçacığı
   beklemedeyse (time.sleep, dosya) uyansın diye ayrıca gerçek SIGINT verilir (Windows: raise_signal → Python'un SIGINT
   olayı; POSIX: ana iş parçacığına pthread_kill). Süren uzun yerel çağrı (LAPACK) bitince kesilir; 5 s içinde yanıt
   gelmezse istemci süreci sonlandırır.
6. Açılışta "durum" iletileri (oran 0–100), web_kopru içe aktarılınca BİR "hazir" iletisi. İçe aktarma başarısızsa
   hazir basarili=false + hata, çıkış kodu 4. Bozuk çerçeve: çıkış kodu 3. Kullanım hatası: 2.

Yalnız standart kitaplık (+ web_kopru'nun kendi bağımlılıkları). Python 3.10+.
"""
from __future__ import annotations

import _thread
import argparse
import collections
import faulthandler
import json
import os
import platform
import signal
import sys
import threading
import time
import traceback

try:
    import op4_protokol as p
except ImportError:  # pragma: no cover — paket içinden içe aktarma
    from . import op4_protokol as p  # type: ignore[no-redef]

BASLANGIC = time.perf_counter()
KAPANIS_BEKLEME_S = 3.0   # kapat / boru kapandıktan sonra ana iş parçacığı bitmezse süreç zorla sonlanır
BLAS_DEGISKENLERI = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


def _simdi() -> str:
    return time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"


def _akis_ac(deger: str, yazma: bool):
    """Komut satırındaki tutamaç (Windows HANDLE onluk) ya da fd (POSIX) → ikili akış."""
    try:
        n = int(deger, 0)
    except ValueError:
        raise SystemExit(f"op4_sunucu: geçersiz tutamaç: {deger!r}") from None
    if os.name == "nt":
        import msvcrt
        fd = msvcrt.open_osfhandle(n, (os.O_WRONLY if yazma else os.O_RDONLY) | getattr(os, "O_BINARY", 0))
    else:
        fd = n
    return open(fd, "wb" if yazma else "rb", closefd=True)


def _gunluge_yonlendir(yol: str | None):
    """sys.stdout / sys.stderr ve fd 1–2 → günlük dosyası (yoksa boşa). Dönüş: günlük akışı."""
    if yol:
        try:
            akis = open(yol, "a", encoding="utf-8", errors="replace", buffering=1)
        except OSError:
            akis = open(os.devnull, "w", encoding="utf-8")
    else:
        akis = open(os.devnull, "w", encoding="utf-8")
    for eski in (sys.stdout, sys.stderr):
        try:
            if eski is not None:
                eski.flush()
        except (OSError, ValueError):
            pass
    try:
        os.dup2(akis.fileno(), 1)
        os.dup2(akis.fileno(), 2)
    except OSError:
        pass
    sys.stdout = sys.stderr = akis
    try:
        faulthandler.enable(file=akis)   # yerel çökmede (erişim ihlali) Python yığını günlüğe
    except (OSError, ValueError, RuntimeError):
        pass
    return akis


def _blas_ayarla(rol: str, blas: int | None) -> int:
    """numpy'den ÖNCE: OpenBLAS / OpenMP / MKL iş parçacığı sayısı (MIMARI D30)."""
    if blas and blas > 0:
        n = blas
        for ad in BLAS_DEGISKENLERI:
            os.environ[ad] = str(n)
    else:
        n = max(1, (os.cpu_count() or 2) - 1) if rol == "ana" else 1
        for ad in BLAS_DEGISKENLERI:
            os.environ.setdefault(ad, str(n))
    return int(os.environ.get("OPENBLAS_NUM_THREADS", n) or n)


class Sunucu:
    def __init__(self, istek_akisi, yanit_akisi, rol: str, gunluk):
        self.rol = rol
        self._istek = istek_akisi
        self._yanit = yanit_akisi
        self._gunluk = gunluk
        self._yaz_kilidi = threading.Lock()
        self._kilit = threading.Lock()
        self._kosul = threading.Condition(self._kilit)
        self._kuyruk: collections.deque = collections.deque()   # (id, islem, istek_metni)
        self._calisan = None        # çalışan isteğin id'si
        self._iptal_id = None       # çalışan istek için iptal istendi
        self._kesilebilir = False   # ana iş parçacığı calistir() içinde (yalnız ana iş parçacığı yazar)
        self._kapaniyor = False
        self._cikis_kodu = 0
        self.calistir = None        # web_kopru.calistir (içe aktarılınca)
        self.islenen = 0
        self._ana = threading.main_thread().ident

    # ------------------------------------------------------------------------------------------------------- günlük
    def yaz(self, metin: str) -> None:
        try:
            self._gunluk.write(f"[{_simdi()} op4_sunucu {self.rol}] {metin}\n")
            self._gunluk.flush()
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------------------------------------------------- yazım
    def gonder(self, govde: bytes) -> bool:
        with self._yaz_kilidi:
            try:
                p.cerceve_yaz(self._yanit, govde)
                return True
            except (OSError, ValueError) as e:   # op4.exe yanıt borusunu kapattı (öldü)
                self.yaz(f"yanıt borusuna yazılamadı: {e}")
        self.bitir(0, "yanıt borusu kapandı")
        return False

    def durum(self, metin: str, oran: float) -> None:
        self.yaz(f"durum %{oran:.0f}: {metin}")
        self.gonder(p.durum_iletisi(metin, oran))

    def gunluk_iletisi(self, duzey: str, metin: str) -> None:
        self.yaz(f"{duzey}: {metin}")
        self.gonder(p.gunluk_iletisi(duzey, metin))

    # ------------------------------------------------------------------------------------------------------- kesme
    def sigint(self, signum, frame) -> None:  # noqa: ARG002 — signal işleyici imzası
        """Ana iş parçacığında çalışır. Yalnız iptal edilen istek calistir() içindeyken KeyboardInterrupt yükseltir."""
        if self._kesilebilir and self._iptal_id is not None and self._iptal_id == self._calisan:
            self._kesilebilir = False
            raise KeyboardInterrupt

    def _kes(self) -> None:
        """Ana iş parçacığını keser: bayt kodu sınırında (interrupt_main) ve beklemedeyse uyandırarak (gerçek SIGINT)."""
        _thread.interrupt_main()
        try:
            if os.name == "nt":
                signal.raise_signal(signal.SIGINT)   # C işleyicisi: bayrak + Python'un SIGINT olayı (time.sleep uyanır)
            elif self._ana is not None:
                signal.pthread_kill(self._ana, signal.SIGINT)
        except (OSError, ValueError, AttributeError):
            pass

    def iptal(self, id_: int) -> None:
        with self._kilit:
            for i, is_ in enumerate(self._kuyruk):
                if is_[0] == id_:
                    del self._kuyruk[i]
                    break
            else:
                if self._calisan == id_:
                    self._iptal_id = id_
                    self.yaz(f"istek {id_}: çalışırken iptal (interrupt_main)")
                    self._kes()
                else:
                    self.yaz(f"istek {id_}: iptal edilecek istek yok (bitmiş ya da bilinmiyor; yok sayıldı)")
                return
        self.yaz(f"istek {id_}: kuyruktayken iptal")
        self.gonder(p.yanit_iletisi(id_, 0.0, p.hata_yaniti(p.IPTAL_YANITI_METNI, "iptal")))

    def bitir(self, kod: int, neden: str) -> None:
        """Düzgün kapanış (kapat, boru kapandı) ya da protokol hatası: ana döngü kuyruğu boşaltmadan çıkar."""
        with self._kilit:
            if self._kapaniyor:
                return
            self._kapaniyor = True
            self._cikis_kodu = kod
            calisan = self._calisan
            if calisan is not None:
                self._iptal_id = calisan
            self._kosul.notify_all()
        self.yaz(f"kapanış (kod {kod}): {neden}")
        if calisan is not None:
            self._kes()
        # Ana iş parçacığı uzun bir yerel çağrıdaysa (LAPACK) beklemeden çık.
        zamanlayici = threading.Timer(KAPANIS_BEKLEME_S, self._zorla_cik)
        zamanlayici.daemon = True
        zamanlayici.start()

    def _zorla_cik(self) -> None:
        self.yaz(f"ana iş parçacığı {KAPANIS_BEKLEME_S:.0f} s içinde bitmedi; süreç sonlandırılıyor")
        self._cik(self._cikis_kodu)

    def _cik(self, kod: int) -> None:
        try:
            self._gunluk.flush()
        except (OSError, ValueError):
            pass
        os._exit(kod)

    # ------------------------------------------------------------------------------------------------------- okuyucu
    def okuyucu(self) -> None:
        try:
            while True:
                govde = p.cerceve_oku(self._istek)
                if govde is None:
                    self.bitir(0, "istek borusu kapandı (op4 kapandı)")   # Y4
                    return
                ileti = p.ileti_coz(govde)
                tur = ileti.get("tur")
                if tur == "istek":
                    id_ = int(ileti["id"])
                    if not 1 <= id_ <= p.EN_BUYUK_ID:
                        raise p.ProtokolHatasi(f"istek id'si aralık dışı: {id_}")
                    metin = ileti.get("istek_metni")
                    if metin is None:   # alan sırası bağlayıcı değilmiş gibi yazılmış ileti: yine de kabul et
                        metin = json.dumps(ileti.get("istek") or {}, ensure_ascii=False)
                    with self._kilit:
                        self._kuyruk.append((id_, str(ileti.get("islem", "")), metin))
                        self._kosul.notify()
                elif tur == "iptal":
                    self.iptal(int(ileti["id"]))
                elif tur == "kapat":
                    self.bitir(0, "kapat iletisi")
                    return
                else:   # ileriye uyum: bilinmeyen tür hata değildir
                    self.gunluk_iletisi("uyari", f"bilinmeyen ileti türü yok sayıldı: {tur!r}")
        except (p.ProtokolHatasi, KeyError, ValueError, TypeError) as e:
            self.yaz(f"PROTOKOL HATASI: {e}")
            self.bitir(p.CIKIS_PROTOKOL, f"protokol hatası: {e}")
        except OSError as e:
            self.bitir(0, f"istek borusu okunamadı: {e}")

    # ------------------------------------------------------------------------------------------------------- ana döngü
    def dongu(self) -> int:
        while True:
            with self._kilit:
                while not self._kuyruk and not self._kapaniyor:
                    self._kosul.wait()
                if self._kapaniyor:
                    break
                id_, islem, metin = self._kuyruk.popleft()
                self._calisan, self._iptal_id = id_, None
            t0 = time.perf_counter()
            try:
                self._kesilebilir = True
                if self._iptal_id == id_:     # iptal, kesilebilir olmadan hemen önce geldiyse
                    raise KeyboardInterrupt
                yanit = self.calistir(metin)
                self._kesilebilir = False
            except KeyboardInterrupt:
                self._kesilebilir = False
                yanit = p.hata_yaniti(p.IPTAL_YANITI_METNI, "iptal")
            except (Exception, SystemExit) as e:  # noqa: BLE001 — web_kopru kendi hatalarını yakalar; bu son güvence
                self._kesilebilir = False
                yanit = json.dumps({"hata": f"{type(e).__name__}: {e}", "hata_turu": "ic",
                                    "iz": traceback.format_exc()[-1500:]}, ensure_ascii=False)
            sure_ms = (time.perf_counter() - t0) * 1000.0
            if not isinstance(yanit, str) or not yanit.startswith("{"):
                yanit = p.hata_yaniti(f"web_kopru.calistir beklenmeyen yanıt türü: {type(yanit).__name__}", "ic")
            with self._kilit:
                self._calisan = self._iptal_id = None
                kapaniyor = self._kapaniyor
            self.islenen += 1
            self.yaz(f"istek {id_} {islem}: {len(metin)} B → {len(yanit)} B, {sure_ms:.1f} ms")
            if not self.gonder(p.yanit_iletisi(id_, sure_ms, yanit)) or kapaniyor:
                break
        return self._cikis_kodu


def _surum(web_kopru) -> str:
    try:
        surum = json.loads(web_kopru.surum_json())
        if not isinstance(surum, dict):
            surum = {"motor": str(surum)}
    except Exception as e:  # noqa: BLE001
        surum = {"hata": f"surum_json: {e}"}
    numpy = sys.modules.get("numpy")
    if numpy is not None:
        surum.setdefault("numpy", getattr(numpy, "__version__", "?"))
    surum.setdefault("python", platform.python_version())
    surum["protokol"] = 1
    return json.dumps(surum, ensure_ascii=False, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="op4_sunucu", description="op4 hesap motoru sunucusu (tel protokolü, MIMARI §8.2)")
    ap.add_argument("--istek", required=True, help="istek borusu: Windows HANDLE (onluk) ya da POSIX fd")
    ap.add_argument("--yanit", required=True, help="yanıt borusu: Windows HANDLE (onluk) ya da POSIX fd")
    ap.add_argument("--rol", choices=("ana", "yardimci"), default="ana")
    ap.add_argument("--gunluk", help="stdout / stderr ve sunucu günlüğü (eklenir)")
    ap.add_argument("--blas", type=int, help="BLAS iş parçacığı sayısı (varsayılan: ana çekirdek − 1, yardımcı 1)")
    args = ap.parse_args(argv)

    gunluk = _gunluge_yonlendir(args.gunluk)
    istek = _akis_ac(args.istek, yazma=False)
    yanit = _akis_ac(args.yanit, yazma=True)
    s = Sunucu(istek, yanit, args.rol, gunluk)
    signal.signal(signal.SIGINT, s.sigint)
    blas = _blas_ayarla(args.rol, args.blas)
    s.yaz(f"başladı: pid {os.getpid()}, Python {platform.python_version()} ({sys.executable}), BLAS {blas} iş parçacığı, "
          f"sys.path[0:3] = {sys.path[0:3]}")
    threading.Thread(target=s.okuyucu, name="op4-istek-okuyucu", daemon=True).start()

    s.durum("Python başlatıldı", 5)
    try:
        s.durum("numpy yükleniyor", 15)
        try:
            import numpy  # noqa: F401 — BLAS ayarından sonra; web_kopru da içe aktarır
        except ImportError:
            pass   # web_kopru numpy'siz işlemlerde de çalışır; eksikse kendi hatasını verir
        s.durum("sympy yükleniyor", 35)
        try:
            import sympy  # noqa: F401
        except ImportError:
            pass
        s.durum("Hesap motoru yükleniyor (web_kopru)", 60)
        import web_kopru
        s.calistir = web_kopru.calistir
        surum = _surum(web_kopru)
    except BaseException as e:  # noqa: BLE001 — eksik paket, sözdizimi, yerel kitaplık hatası …
        hata = f"web_kopru içe aktarılamadı: {type(e).__name__}: {e}\n" + traceback.format_exc()[-1500:]
        s.yaz(hata)
        s.gonder(p.hazir_iletisi(args.rol, False, os.getpid(), platform.python_version(),
                                 (time.perf_counter() - BASLANGIC) * 1000.0, "{}", hata))
        s._cik(p.CIKIS_BASLATMA)
        return p.CIKIS_BASLATMA
    sure = (time.perf_counter() - BASLANGIC) * 1000.0
    s.durum("Hesap motoru hazır", 100)
    s.gonder(p.hazir_iletisi(args.rol, True, os.getpid(), platform.python_version(), sure, surum, ""))
    s.yaz(f"hazır ({sure:.1f} ms): {surum}")
    kod = s.dongu()
    s.yaz(f"çıkış: {s.islenen} istek işlendi, kod {kod}")
    try:
        yanit.close()
    except OSError:
        pass
    s._cik(kod)
    return kod


if __name__ == "__main__":
    sys.exit(main())
