"""Sınama motoru: op4_sunucu ve C++ motor istemcisi sınamalarında docs/web_kopru.py'nin yerine geçer (yalnız standart
kitaplık; numpy / sympy gerekmez). Gerçek motorla aynı arayüz: surum_json(), calistir(istek_json) -> JSON metni.

İşlemler (girdi alanları):
  yanki     {…}            → {"hata": null, "islem", "girdi", "ayarlar"} (gidiş-dönüş, Türkçe / kaçışlı metin);
            "bina_yanki" aynısıdır (bina_ önekli istek: istemcinin sd_siniri eklemesi sınanır)
  uyu       {"s": 1.0}     → kesilebilir bekleme (iptal sınaması: KeyboardInterrupt dışarı çıkar)
  kilitlen  {"s": 30}      → iptale yanıt vermeyen hesap (uzun yerel çağrı benzetimi: KeyboardInterrupt yutulur)
  cok       {"kod": 7}     → süreç hemen çöker (os._exit)
  buyuk     {"mb": 50}     → ≈ mb MiB'lik yanıt
  yazdir    {}             → print / stderr / fd 1–2'ye ham yazım (protokol bozulmamalı)
  ortam     {}             → BLAS ortam değişkenleri, pid
  hata      {}             → {"hata": "...", "hata_turu": "girdi"}
Ortam: OP4_SAHTE_MOTOR_ICE_AKTARMA_HATASI=1 → içe aktarma hatası (hazir basarili=false sınaması).
"""
from __future__ import annotations

import json
import os
import sys
import time

if os.environ.get("OP4_SAHTE_MOTOR_ICE_AKTARMA_HATASI") == "1":
    raise ImportError("sahte motor: istenen içe aktarma hatası (sınama)")

SURUM = "sahte-1"


def surum_json() -> str:
    return json.dumps({"motor": SURUM, "python": sys.version.split()[0]})


def _yanit(**alanlar) -> str:
    return json.dumps({"hata": None, **alanlar}, ensure_ascii=False)


def calistir(istek_json: str) -> str:
    try:
        istek = json.loads(istek_json)
    except ValueError as e:
        return json.dumps({"hata": f"istek JSON değil: {e}", "hata_turu": "girdi"}, ensure_ascii=False)
    islem = istek.get("islem")
    g = istek.get("girdi") or {}
    if islem in ("yanki", "bina_yanki"):
        return _yanit(islem=islem, girdi=g, ayarlar=istek.get("ayarlar") or {})
    if islem == "uyu":
        s = float(g.get("s", 1.0))
        time.sleep(s)
        return _yanit(uyudu=s)
    if islem == "kilitlen":
        bitis = time.monotonic() + float(g.get("s", 30.0))
        kesme = 0
        while time.monotonic() < bitis:
            try:
                time.sleep(0.02)
            except KeyboardInterrupt:
                kesme += 1
        return _yanit(kesme=kesme)
    if islem == "cok":
        os._exit(int(g.get("kod", 7)))
    if islem == "buyuk":
        n = int(float(g.get("mb", 50)) * 1024 * 1024)
        return '{"hata": null, "boyut": %d, "veri": "%s"}' % (n, "ş" * (n // 2))
    if islem == "yazdir":
        print("print: stdout'a yazı (protokolü bozmamalı)", flush=True)
        print("print: stderr'e yazı", file=sys.stderr, flush=True)
        os.write(1, b"\x00\x00\x00\x10fd1 ham bayt\n")
        os.write(2, b"fd2 ham bayt\n")
        return _yanit(yazdi=True)
    if islem == "ortam":
        return _yanit(pid=os.getpid(), blas={k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
                                                                          "MKL_NUM_THREADS")})
    if islem == "hata":
        return json.dumps({"hata": "sahte girdi hatası", "hata_turu": "girdi"}, ensure_ascii=False)
    return json.dumps({"hata": f"Bilinmeyen işlem: {islem!r}", "hata_turu": "girdi"}, ensure_ascii=False)
