"""op4 Faz 1 paket sözleşmeleri bekçisi (op4/MIMARI.md §24).

* Dosya sahipliği: §24.3'teki ```sahiplik bloğu depodaki her op4 dosyasını (ve listelenen kök dosyaları) bir pakete bağlar;
  ilk eşleşen satır geçerlidir. Sahipsiz dosya ya da tanımsız paket kodu sınamayı düşürür.
* Sözleşme (S) dosyaları silinemez: joker içermeyen her S satırı var olan bir dosyayı göstermelidir.
* Komut kataloğu: op4/veri/komutlar.json'daki her komutun sahibi A–D'den biridir; id ve kısayollar tekildir.
* Ortak kod tabloları: op4/veri/sahne_kodlari.json ile op4/js/op4_ops.js KODLAR aynı (node varsa).
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
MIMARI = KOK / "op4" / "MIMARI.md"
PAKETLER = {"A", "B", "C", "D", "S", "-"}
KOK_DOSYALARI = (".github/workflows/op4.yml", "docs/web_kopru.py", "testler/test_op4_sozlesme.py", "testler/test_op4_araclar.py")


def _kurallar() -> list[tuple[str, str, re.Pattern]]:
    metin = MIMARI.read_text(encoding="utf-8")
    m = re.search(r"```sahiplik\n(.*?)```", metin, re.S)
    assert m, "MIMARI.md §24.3: ```sahiplik bloğu yok"
    kurallar = []
    for satir in m.group(1).splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        desen, paket = satir.split()
        assert paket in PAKETLER, f"tanımsız paket kodu: {satir}"
        rx = re.escape(desen).replace(r"\*\*", "\0").replace(r"\*", "[^/]*").replace("\0", ".*")
        kurallar.append((desen, paket, re.compile(rx + r"\Z")))
    return kurallar


def _dosyalar() -> list[str]:
    if shutil.which("git"):
        r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "op4"], cwd=KOK,
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return sorted({s for s in r.stdout.splitlines() if (KOK / s).is_file()})
    return sorted(str(p.relative_to(KOK)).replace("\\", "/") for p in (KOK / "op4").rglob("*")
                  if p.is_file() and ".onbellek" not in p.parts)


def _sahip(kurallar, yol: str):
    for desen, paket, rx in kurallar:
        if rx.match(yol):
            return desen, paket
    return None


def test_her_op4_dosyasinin_sahibi_var():
    kurallar = _kurallar()
    sahipsiz = [y for y in _dosyalar() + list(KOK_DOSYALARI) if _sahip(kurallar, y) is None]
    assert not sahipsiz, "MIMARI §24.3 sahiplik tablosunda karşılığı olmayan dosyalar: " + ", ".join(sahipsiz)


def test_sozlesme_dosyalari_yerinde():
    eksik = [d for d, p, _ in _kurallar() if p == "S" and "*" not in d and not (KOK / d).is_file()]
    assert not eksik, "sözleşme dosyası silinmiş ya da taşınmış: " + ", ".join(eksik)


def test_ornek_sahiplikler():
    k = _kurallar()
    beklenen = {
        "op4/kaynak/cekirdek/model_cekirdegi.h": "S",
        "op4/kaynak/cekirdek/motor_istemci.cpp": "A",
        "op4/kaynak/cekirdek/oznitelik.cpp": "B",
        "op4/kaynak/cekirdek/secme.cpp": "C",
        "op4/kaynak/cekirdek/proje_dosyasi.cpp": "D",
        "op4/kaynak/cekirdek_js/gecici_cekirdek.cpp": "B",
        "op4/kaynak/uygulama.cpp": "C",
        "op4/kaynak/motor_modulu.cpp": "A",
        "op4/kaynak/dosya/dosya_modulu.cpp": "D",
        "op4/veri/komutlar.json": "C",
        "op4/veri/sablonlar/betonarme-3kat-3x3.json": "D",
        "op4/testler/cekirdek/secme_bvh.cpp": "C",
        "op4/kimlik/opus-fortis-simge-renkli.png": "-",
        ".github/workflows/op4.yml": "A",
    }
    for yol, paket in beklenen.items():
        assert _sahip(k, yol)[1] == paket, yol


def test_komut_katalogu():
    d = json.loads((KOK / "op4" / "veri" / "komutlar.json").read_text(encoding="utf-8"))
    ids, kisayollar = set(), set()
    for k in d["komutlar"]:
        assert k["sahip"] in {"A", "B", "C", "D"}, k["id"]
        assert re.fullmatch(r"[a-z0-9_]+\.[a-z0-9_]+", k["id"]), k["id"]
        assert k["id"] not in ids, k["id"]
        ids.add(k["id"])
        if k.get("kisayol"):
            assert k["kisayol"] not in kisayollar, k["kisayol"]
            kisayollar.add(k["kisayol"])
        if k.get("serit"):
            assert k["serit"]["sekme"] in d["sekmeler"], k["id"]
    assert len(ids) >= 30


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
def test_js_kodlari_sahne_kodlariyla_ayni():
    betik = ("const o=require(process.argv[1]);process.stdout.write(JSON.stringify(o.KODLAR))")
    r = subprocess.run(["node", "-e", betik, str(KOK / "op4" / "js" / "op4_ops.js")], capture_output=True, text=True,
                       check=True)
    js = json.loads(r.stdout)
    veri = json.loads((KOK / "op4" / "veri" / "sahne_kodlari.json").read_text(encoding="utf-8"))
    for tablo, deger in js.items():
        assert veri[tablo] == deger, tablo
