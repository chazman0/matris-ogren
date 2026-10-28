# -*- coding: utf-8 -*-
"""Tarayıcı testleri için yerel sunucu (testler/test_bina_tarayici.py bunu alt süreç olarak başlatır).

- ``docs/`` klasörünü durağan olarak sunar (önbelleksiz);
- ``/motor.worker.js`` yerine küçük bir ara worker verir: Pyodide indirmek yerine istekleri ``POST /__kopru`` ile bu sürece
  gönderir; süreç onları CPython'da ``docs/web_kopru.calistir`` ile çözer (``POST /__surum`` → ``web_kopru.surum_json``).
  Motor modülleri proje kökünden (güncel kaynak) yüklenir; ``docs/`` içindeki kopyalar yalnız kökte olmayanlar için kullanılır.

Kullanım: ``python3 -I testler/tarayici_sunucu.py <proje_kökü> <port>`` (port 0: boş bir port seçilir). Hazır olunca standart
çıktıya tek satır yazar: ``HAZIR http://127.0.0.1:<port>/``.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

KOK = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
DOCS = os.path.join(KOK, "docs")
for yol in (DOCS, KOK):          # kök önce: güncel motor kaynağı
    if yol not in sys.path:
        sys.path.insert(0, yol)

import web_kopru  # noqa: E402

KILIT = threading.Lock()         # motor modül düzeyi durum taşır: istekler sırayla

ARA_WORKER = r'''"use strict";
async function gonder(yol, govde) { const r = await fetch(yol, { method: "POST", body: govde }); return r.text(); }
self.onmessage = async function (e) {
  const m = e.data || {};
  if (m.tur === "baslat") {
    try { const s = JSON.parse(await gonder("/__surum", "")); s.pyodide = "cpython-test"; self.postMessage({ tur: "hazir", surum: s }); }
    catch (err) { self.postMessage({ tur: "hata", mesaj: "Test köprüsü: " + err }); }
    return;
  }
  if (m.tur === "istek") {
    let yanit;
    try { yanit = JSON.parse(await gonder("/__kopru", JSON.stringify(m.istek || {}))); }
    catch (err) { yanit = { hata: "Motor hatası: " + err, hata_turu: "ic" }; }
    self.postMessage({ tur: "yanit", id: m.id, yanit: yanit });
  }
};'''


class Isleyici(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DOCS, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _yaz(self, govde: bytes, tur: str):
        self.send_response(200)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def do_GET(self):
        if self.path.split("?")[0] == "/motor.worker.js":
            return self._yaz(ARA_WORKER.encode("utf-8"), "text/javascript; charset=utf-8")
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        govde = self.rfile.read(n).decode("utf-8")
        with KILIT:
            try:
                cikti = web_kopru.surum_json() if self.path == "/__surum" else web_kopru.calistir(govde)
            except Exception:
                cikti = json.dumps({"hata": "Test sunucusu: " + traceback.format_exc()[-800:], "hata_turu": "ic"})
        self._yaz(cikti.encode("utf-8"), "application/json; charset=utf-8")


def main():
    sunucu = ThreadingHTTPServer(("127.0.0.1", PORT), Isleyici)
    print(f"HAZIR http://127.0.0.1:{sunucu.server_address[1]}/", flush=True)
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
