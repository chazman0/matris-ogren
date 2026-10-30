# -*- coding: utf-8 -*-
"""Rapor ve tablolar — kalan işler turu (K-1, K-10, K-15, K-26, K-30, K-34, K-35, K-36, K-44).

Bu modülün testleri iki gruptadır:

- Modül düzeyindeki testler rapor.py / tablolar.py'nin kendi tarafını sınar ve tek başına (motor paketi olmadan) geçer: sentetik
  çözüm dilimleri (yaylar, yay_ozet, yaylı mesnet kaydı), aks–kat motorunun elastik temel yayları, genelleştirilmiş (docs/model_ops.js)
  aks–kat şablonlarında kalıp ve duvar tabloları.
- ``TestMotorSonrasi`` sınıfının testleri motor paketinin sözleşme tarafına dayanır (C11 genel modelde mütemadi/radye, C12 yay_ozet,
  C13/C14 yaylı ve diyafram bağlı mesnet, C18 motor adresi, C20 basit kesit sınıfı, C21 kolon özeti, K-44 kat ağırlıkları). Bunlar
  paketler birleştirilmeden önce KALIR; birleştirmeden sonra geçmelidir. Tek başına çalıştırma:
  ``python3 -m pytest testler/test_rapor_tablolar_kalan.py -q -k "not MotorSonrasi"``.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import rapor
import tablolar as tb
import yapi
import yapi_serbest as YS

PROJE = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
C18 = {"kolon": "kolon", "kiris": "kiriş", "capraz": "çapraz", "makas-ust": "makas üst başlık", "makas-alt": "makas alt başlık",
       "makas-dikme": "makas dikmesi", "makas-diyagonal": "makas diyagonali", "asik": "aşık", "kren": "kren kirişi", "bag": "bağ",
       "diger": "diğer"}
_GENELLESTIR = ('const M=require(process.argv[1]);let v="";process.stdin.on("data",d=>v+=d);'
                'process.stdin.on("end",()=>{process.stdout.write(JSON.stringify(M.genellestir(JSON.parse(v)).model))});')


def metin(html: str) -> str:
    html = re.sub(r"</t[dh]>", " | ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).replace("&nbsp;", " ")


def bolum(html: str, no: int) -> str:
    i = html.index(f'id="b{no}"')
    j = html.index('id="b', i + 5) if no < 14 else html.index('id="ek', i)
    return html[i:j]


def korunum_satirlari(html: str) -> dict:
    """§10.1 'Korunum denetimi' tablosu → {durum: satır metni}."""
    i = html.index("Korunum denetimi")
    tablo = html[i:html.index("</table>", i)]
    return {metin(s).split(" | ")[0].strip(): s for s in re.findall(r"<tr>(.*?)</tr>", tablo)[1:]}


def genellestir(ad: str) -> dict:
    """docs/model_ops.js ModelOps.genellestir(şablon) → genel (surum 3) bina."""
    if NODE is None:
        pytest.skip("node kurulu değil")
    r = subprocess.run([NODE, "-e", _GENELLESTIR, str(PROJE / "docs" / "model_ops.js")], input=json.dumps(yapi.bina_sablon(ad)),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    assert g["surum"] == 3 and g["cubuklar"] and not g.get("kolonlar")
    return g


def coz(bina) -> dict:
    return yapi.bina_coz(copy.deepcopy(bina), goster="yok", anlat=False).veri


@pytest.fixture(scope="module")
def tek():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    return b, coz(b)


@pytest.fixture(scope="module")
def cbf():
    b = yapi.bina_sablon("celik-cbf-3kat")
    return b, coz(b)


# ---------------------------------------------------------------------------- K-26 / C18: Türkçe tür adları
def test_tur_adi_sozlesme_c18():
    assert rapor.TUR_ADI == C18 and tb.TUR_ADI == C18
    assert rapor._CUBUK_TURU is rapor.TUR_ADI                     # rapor tür okunuşu aynı sözlük
    assert tb._cubuk_adresi(13, "kiris") == "Ç13 (kiriş)" and tb._cubuk_adresi(4, "makas-ust") == "Ç4 (makas üst başlık)"
    assert tb._cubuk_adresi(7, None) == "Ç7"


def test_tur_adi_motorla_ayni():
    if not hasattr(YS, "TUR_ADI"):
        pytest.skip("yapi_serbest.TUR_ADI yok (motor paketi C18 öncesi)")
    assert YS.TUR_ADI == tb.TUR_ADI == rapor.TUR_ADI


def test_genel_tablolarda_adres_turkce():
    b = yapi.bina_sablon("celik-cbf-3kat")
    T = tb.bina_tablolari(b)
    adresler = [r["degerler"]["adres"] for ad in ("eleman_yukleri", "metraj_celik") for r in tb.tablo(T, ad)["satirlar"]]
    assert adresler and not [a for a in adresler if "(kiris)" in a or "(capraz)" in a]
    assert any(a.endswith("(kiriş)") for a in adresler) and any(a.endswith("(çapraz)") for a in adresler)


def test_rapor_eleman_basligi_ve_ek_b_turkce(cbf):
    """§12.3 eleman başlıkları ("Ç41 (çapraz) — çapraz 41, …") ve Ek B Tür sütunu ham tür kimliği (capraz, asik, makas-ust …)
    yazmaz; aks–kat motorunda da Ek B "kiriş"."""
    b, v = cbf
    h = rapor.statik_rapor(b, v)
    basliklar = re.findall(r"<h4>(Ç\d+ \([^)]*\) — [^,]*),", bolum(h, 12))
    assert any(x.endswith(" — çapraz " + x.split("Ç")[1].split(" ")[0]) for x in basliklar), basliklar[:5]
    assert basliklar and not [x for x in basliklar if re.search(r"— (capraz|asik|kiris|makas-|diger|bag|kren) ", x)], basliklar
    ekb = metin(h[h.index('id="ekB"'):])
    assert "| çapraz |" in ekb and "| kiriş |" in ekb and "| capraz |" not in ekb and "| kiris |" not in ekb
    assert rapor._ELEMAN_TURU["temel-kirisi"] == "temel kirişi" and rapor._ELEMAN_TURU["makas-ust"] == "makas üst başlık"


# ---------------------------------------------------------------------------- C12: tepki toplamı (yay kuvvetleri, yay_ozet)
def test_tepki_toplami_yaylar_ve_yay_ozet():
    """Σ tepki + Σ yazılmış yay (motor → bina: Fx→FX, Fz→−FY, Fy→FZ, Mx→MX, Mz→−MY, My→MZ) + yay_ozet."""
    kisa = {"tepkiler": [{"dugum": 1, "FX": 1.0, "FY": 2.0, "FZ": 3.0, "MX": 0.1, "MY": 0.2, "MZ": 0.3}],
            "yaylar": [{"dugum": 2, "bilesen": "Fx", "k": 1e4, "kuvvet": 10.0, "tur": "yay-mesnet"},
                       {"dugum": 2, "bilesen": "Fz", "k": 1e4, "kuvvet": 20.0, "tur": "yay-mesnet"},
                       {"dugum": 2, "bilesen": "Fy", "k": 5e3, "kuvvet": 30.0, "tur": "yay-mesnet"},
                       {"dugum": 3, "bilesen": "Mx", "k": 1e3, "kuvvet": 1.0},
                       {"dugum": 3, "bilesen": "Mz", "k": 1e3, "kuvvet": 2.0},
                       {"dugum": 3, "bilesen": "My", "k": 1e3, "kuvvet": 3.0, "tur": "diyafram-mesnet"}],
            "yay_ozet": {"FX": 0.5, "FY": -0.5, "FZ": 100.0, "MX": 0.0, "MY": 0.0, "MZ": 0.0}}
    S = rapor._Rapor.tepki_toplami(kisa)
    assert S == pytest.approx({"FX": 1 + 10 + 0.5, "FY": 2 - 20 - 0.5, "FZ": 3 + 30 + 100, "MX": 0.1 + 1, "MY": 0.2 - 2, "MZ": 0.3 + 3})
    assert rapor._Rapor.tepki_toplami({"tepkiler": kisa["tepkiler"]}) == pytest.approx(
        {"FX": 1.0, "FY": 2.0, "FZ": 3.0, "MX": 0.1, "MY": 0.2, "MZ": 0.3})       # yaysız kayıt: yalnız tepkiler (eski davranış)
    kayit, oz = rapor._tepki_kayitlari(kisa)
    tip = {k["dugum"]: k["tip"] for k in kayit}
    assert tip == {1: "mesnet", 2: "yaylı mesnet", 3: "mesnet (diyafram bağıyla)"} and oz["FZ"] == 100.0
    assert rapor._yay_metni({"kz": 5000.0, "krx": 250.0}) == "k_z = 5 000 kN/m; k_rx = 250 kN·m/rad"
    assert rapor._yay_metni({"kx": 3.2e10}) == "k_x = 3.2e+10 kN/m"


def test_elastik_temel_yaylari_korunumu_saglar():
    """Aks–kat tekil 'elastik' mesnet: düşey yük yazılan zemin yaylarına gider; §10.1 korunum ✔ (eskiden Σ R_Z = 0 → ✘), düğüm
    tablosunda 'elastik mesnet (zemin yayı)' satırları ve rijitlikleri; Mesnet Tepkileri tablosunun Σ satırı ΣG."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["temeller"]["mesnet"] = "elastik"
    v = coz(b)
    h = rapor.statik_rapor(b, v)
    sat = korunum_satirlari(h)
    assert set(sat) >= {"G", "Q"} and all("✔" in s and "✘" not in s for s in sat.values()), {a: metin(s) for a, s in sat.items()}
    i = h.index("Durum G (sabit yük)")
    t = h[i:h.index("</table>", i)]
    assert "elastik mesnet (zemin yayı)" in t and "k_z = " in metin(t)
    G = v["yukler"]["toplam"]["G"]
    assert metin(t[t.index("<tfoot>"):]).startswith(f"Σ | | | | 0 | 0 | {rapor._f(G, 3)} |")
    T = tb.bina_tablolari(b, v)
    mt = tb.tablo(T, "mesnet_tepkileri")
    oz = next(r["degerler"] for r in mt["satirlar"] if r.get("ozet") and r["degerler"]["durum"] == "G")
    assert oz["FZ"] == pytest.approx(G, rel=1e-6)
    assert {r["degerler"]["tip"] for r in mt["satirlar"] if not r.get("ozet")} == {"elastik mesnet (zemin yayı)"}
    assert "yay" in {s["ad"] for s in mt["sutunlar"]} and "k_z = " in mt["satirlar"][0]["degerler"]["yay"]


def test_yaysiz_modelde_yay_sutunu_yok(tek):
    """Yay yoksa Mesnet Tepkileri tablosu eskisi gibidir (boş 'Yay rijitliği' sütunu eklenmez)."""
    b, v = tek
    mt = tb.tablo(tb.bina_tablolari(b, v), "mesnet_tepkileri")
    assert [s["ad"] for s in mt["sutunlar"]] == ["durum", "dugum", "adres", "tip", "FX", "FY", "FZ", "MX", "MY", "MZ"]
    assert not [r for r in mt["satirlar"] if "yay" in r["degerler"]]


def _yayli_veri(v):
    """Sentetik dilim: ilk mesnet düğümü yaylı mesnet (kz = 5000; yay kuvveti G durumunda), ikincisi diyafram bağlı mesnet."""
    v = copy.deepcopy(v)
    d1, d2 = (t["dugum"] for t in v["durumlar"]["G"]["tepkiler"][:2])
    for k in list(v["durumlar"].values()) + list((v.get("sonuclar") or {}).values()):
        tep = k["tepkiler"]
        t1 = next(t for t in tep if t["dugum"] == d1)
        fz = t1["FZ"]
        t1["FZ"] = 0.0
        k["yaylar"] = list(k.get("yaylar") or []) + [
            {"dugum": d1, "sd": "v", "bilesen": "Fy", "k": 5000.0, "kuvvet": fz, "tur": "yay-mesnet"},
            {"dugum": d2, "sd": "u", "bilesen": "Fx", "k": 3.2e10, "kuvvet": 0.0, "tur": "diyafram-mesnet"}]
    v["akis"]["mesnetler"] = [{"dugum": d1, "adres": "A1/k0", "tip": "yay", "yay": {"kz": 5000.0}, "N_G": 12.5, "N_Q": 3.0, "MX": 0.0,
                               "MY": 0.0},
                              {"dugum": d2, "adres": "A2/k0", "tip": "ozel", "N_G": 7.0, "N_Q": 1.0, "MX": 0.0, "MY": 0.0}]
    return v, d1, d2


def test_yayli_ve_diyafram_mesnet_rapor(tek):
    """K-10 / K-15 (rapor): yaylı mesnet 'yaylı mesnet' ve rijitlikleriyle, diyafram bağlı mesnet 'mesnet (diyafram bağıyla)'; Σ satırı
    = tepki toplamı (yay kuvveti dahil), korunum ✔."""
    b, v0 = tek
    v, d1, d2 = _yayli_veri(v0)
    h = rapor.statik_rapor(b, v)
    assert all("✔" in s for s in korunum_satirlari(h).values())
    i = h.index("Durum G (sabit yük)")
    t = metin(h[i:h.index("</table>", i)])
    assert "| yaylı mesnet | k_z = 5 000 kN/m |" in t and "| mesnet (diyafram bağıyla) | k_x = 3.2e+10 kN/m |" in t
    b13 = metin(bolum(h, 13))
    assert "Açık mesnet tepkileri" in b13 and "| yaylı mesnet | k_z = 5 000 kN/m | 12.5 |" in b13
    assert "| mesnet (diyafram bağıyla) | ux/uy/rz ceza rijitliğiyle |" in b13 and "Diyafram bağı:" in b13


def test_yayli_ve_diyafram_mesnet_tablolar(tek):
    """K-10 / K-15 (tablolar): Mesnet Tepkileri satır türü ve yay rijitliği; Σ satırı yay kuvvetini içerir."""
    b, v0 = tek
    v, d1, d2 = _yayli_veri(v0)
    T = tb.bina_tablolari(b, v, kati=True)
    mt = tb.tablo(T, "mesnet_tepkileri")
    sat = {r["degerler"]["dugum"]: r["degerler"] for r in mt["satirlar"] if r["degerler"]["durum"] == "G" and not r.get("ozet")}
    assert sat[d1]["tip"] == "yaylı mesnet" and sat[d1]["yay"] == "k_z = 5 000 kN/m"
    assert sat[d2]["tip"] == "mesnet (diyafram bağıyla)" and "k_x = 3.2e+10 kN/m" in sat[d2]["yay"]
    oz = next(r["degerler"] for r in mt["satirlar"] if r.get("ozet") and r["degerler"]["durum"] == "G")
    assert oz["FZ"] == pytest.approx(v["yukler"]["toplam"]["G"], rel=1e-6)
    assert "Yaylı mesnet" in mt["aciklama"] and "diyafram bağıyla" in mt["aciklama"]


def test_mesnetler_tablosu_yay_rijitlikleri():
    """Açık mesnetin k_x … k_rz değerleri Mesnetler tablosunda düzenlenebilir (bina eksenleri, kN/m / kN·m/rad)."""
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "z": "±0.00"}, "ux": True, "uy": True, "rx": True, "ry": True, "rz": True,
                       "kz": 25000.0}]
    T = tb.bina_tablolari(b, kati=True)
    m = tb.tablo(T, "mesnetler")
    sut = {s["ad"]: s for s in m["sutunlar"]}
    assert all(sut[a]["duzenlenebilir"] for a in ("kx", "ky", "kz", "krx", "kry", "krz")) and sut["kz"]["birim"] == "kN/m"
    assert sut["krx"]["birim"] == "kN·m/rad" and sut["kz"]["baslik"] == "k_z"
    r = next(r for r in m["satirlar"] if r["degerler"]["adres"] == "serbest")
    assert r["degerler"]["tip"] == "yaylı mesnet" and r["degerler"]["kz"] == 25000.0 and r["degerler"]["uz"] is False
    yeni = tb.degisiklikleri_uygula(b, [{"yol": r["yol"]["kz"], "deger": 30000.0}, {"yol": r["yol"]["krx"], "deger": 500.0}])
    assert yeni["mesnetler"][0]["kz"] == 30000.0 and yeni["mesnetler"][0]["krx"] == 500.0
    # aks–kat modelinde yaylı mesnet yoksa sütun yok (eski tablo)
    T1 = tb.bina_tablolari(yapi.bina_sablon("betonarme-2kat-3x2"), kati=True)
    assert "kz" not in {s["ad"] for s in tb.tablo(T1, "mesnetler")["sutunlar"]}


# ---------------------------------------------------------------------------- K-1 (rapor tarafı): §13 eski çözüm, açık mesnet, korunum
def test_temel_ayari_cozumun_normalize_kaydindan(tek):
    """Mütemadi/radye boyutları önce veri.bina.temeller'den (çözülen normalize değer), yoksa modelden."""
    b, v = tek
    b = copy.deepcopy(b)
    v = copy.deepcopy(v)
    b["temeller"] = {"tip": "radye", "zemin": {"q_em": 150, "k0": 15000}, "radye": {"h": 0.6, "tasma": 1.0, "ag": "otomatik"}}
    v["bina"]["temeller"] = {"tip": "radye", "radye": {"h": 0.6, "tasma": 1.0, "ag": 0.75, "kiris": None}}
    v["temel"] = {"tip": "radye", "p_maks": 40.0, "q_em": 150.0, "DC_zemin": 0.27}
    v["akis"]["mesnetler"] = [{"dugum": 77, "adres": "C3/±0.00", "tip": "mafsal", "N_G": 4.5, "N_Q": 1.0, "MX": 0.0, "MY": 0.0}]
    b13 = bolum(rapor.statik_rapor(b, v), 13)
    m = metin(b13)
    assert "Radye temel boyutları" in b13 and "| Izgara aralığı a | 0.75 m |" in m       # 'otomatik' yerine çözülen 0.75 m
    assert "13.1 Temel analizi sonuçları" in b13 and rapor.ESKI_TEMEL_NOTU not in b13
    assert "Açık mesnet tepkileri" in b13 and "C3/±0.00" in b13                       # mütemadi/radye dalında açık mesnetler


def test_korunum_temel_oz_agirligi():
    """Mütemadi temelde korunum tablolarında 'temel öz ağırlığı' satırı / sütunu (temel.py W); tekil temelde sütun yok."""
    b = yapi.bina_sablon("betonarme-3kat-surekli-temel")
    v = coz(b)
    W = v["akis"]["korunum"]["G"]["temel_oz"]
    assert W > 0
    i = (h := rapor.statik_rapor(b, v)).index("Yük akışı korunumu")
    assert f"| temel öz ağırlığı | {rapor._f(W, 3)} |" in metin(h[i:h.index("</table>", i)])
    kor = tb.tablo(tb.bina_tablolari(b, v), "korunum")
    assert "temel_oz" in {s["ad"] for s in kor["sutunlar"]}
    assert next(r["degerler"]["temel_oz"] for r in kor["satirlar"] if r["degerler"]["durum"] == "G") == pytest.approx(W)
    b1 = yapi.bina_sablon("betonarme-tek-aciklik")
    kor1 = tb.tablo(tb.bina_tablolari(b1, coz(b1)), "korunum")
    assert "temel_oz" not in {s["ad"] for s in kor1["sutunlar"]}
    # §13: mütemadi / radyede tekil temelin mesnet modeli (ankastre …) yazılmaz
    assert "| Mesnet modeli (üst yapı analizi) | temel ağı (Winkler zemin yayları; sabit mesnet yok) |" in metin(bolum(h, 13))
    # §10.1: temel ağı düğümlerinin (yatayda tutulu) tepki satırları ayrı türle; yanıta yazılmayan zemin yayları tek satırda (Σ)
    v2 = copy.deepcopy(v)
    ag = {d["no"] for d in v2["temel"]["dugumler"]}
    tep = v2["durumlar"]["G"]["tepkiler"]
    v2["durumlar"]["G"]["yay_ozet"] = {"FX": 0.0, "FY": 0.0, "FZ": v2["yukler"]["toplam"]["G"] - sum(t["FZ"] for t in tep), "MX": 0.0,
                                       "MY": 0.0, "MZ": 0.0}
    h2 = rapor.statik_rapor(b, v2)
    i = h2.index("Durum G (sabit yük)")
    t = metin(h2[i:h2.index("</table>", i)])
    assert any(x["dugum"] in ag for x in tep) and "| temel ağı (yatay tutulu) | – |" in t and "| temel ağı (Σ) | zemin yayları (Winkler) |" in t
    assert "✔" in korunum_satirlari(h2)["G"]


# ---------------------------------------------------------------------------- K-34 (rapor tarafı): basit kesit sınıfı satırı
def test_basit_kesit_sinifi_satiri(monkeypatch, cbf):
    """tasarim.kesit_sinifi basit kesit adını çözdüğünde (C20) §5: '<kesit> — <ad>: basınçta …, eğilmede …' ve parça oranları."""
    b, v = cbf
    r = rapor._Rapor(b, v, {})
    if r.ts is None:
        pytest.skip("tasarim.py yok")

    def sahte(profil, Fy):
        if not str(profil).startswith("BORU"):
            raise ValueError("I profili değil")
        return {"tur": "kesit_sinifi", "profil": profil, "basinc": "narin olmayan", "egilme": "kompakt", "kaynak": "ÇYTHYE Tablo 5.1A",
                "parcalar": [{"ad": "D/t", "oran": 26.71, "lambda_r_basinc": 80.0, "basinc": "narin olmayan", "lambda_p": 50.9,
                              "lambda_r": 225.5, "egilme": "kompakt"}]}
    eski = rapor._Rapor.kesit_sinifi
    monkeypatch.setattr(rapor._Rapor, "kesit_sinifi",
                        lambda self, p, Fy: sahte(p, Fy) if str(p).startswith("BORU") else eski(self, p, Fy))
    b5 = metin(bolum(rapor.statik_rapor(b, v), 5))
    assert "CAPRAZ-V — BORU 168.3x6.3: basınçta narin olmayan, eğilmede kompakt" in b5
    assert "| CAPRAZ-V | BORU 168.3x6.3 | D/t | 26.71 |" in b5


# ---------------------------------------------------------------------------- K-35: genel metraj döşeme kalıbı (köşe örtüşmesi)
def test_panel_net_alani_dikdortgen_ve_ucgen():
    P = [[0, 0, 3], [5, 0, 3], [5, 4, 3], [0, 4, 3]]
    p = {"P": P, "alan": 20.0, "normal": [0, 0, 1], "geo": {"disbukey": True}, "kenarlar": [{"L": 5}, {"L": 4}, {"L": 5}, {"L": 4}]}
    d = [0.125, 0.15, 0.125, 0.10]
    assert tb._panel_net_alani(p, d) == pytest.approx((5 - 0.15 - 0.10) * (4 - 0.125 - 0.125), abs=1e-12)
    assert tb._panel_net_alani(p, [0, 0, 0, 0]) == 20.0
    p["P"] = list(reversed(P))                                          # saat yönünde köşe sırası
    assert tb._panel_net_alani(p, [0.125, 0.10, 0.125, 0.15]) == pytest.approx(4.75 * 3.75, abs=1e-12)
    # dik üçgen (3-4-5), her kenarda 0,1 m: iç üçgen benzer, iç yarıçap r = 1 → ölçek (r − d)/r = 0,9
    U = {"P": [[0, 0, 0], [4, 0, 0], [0, 3, 0]], "alan": 6.0, "normal": [0, 0, 1], "geo": {"disbukey": True},
         "kenarlar": [{"L": 4}, {"L": 5}, {"L": 3}]}
    assert tb._panel_net_alani(U, [0.1, 0.1, 0.1]) == pytest.approx(6.0 * 0.9 ** 2, rel=1e-12)
    # eğik (çatı) dikdörtgen: düzlem içinde aynı kural
    E = {"P": [[0, 0, 0], [4, 0, 0], [4, 3, 3], [0, 3, 3]], "alan": 4 * 18 ** 0.5, "normal": [0, -0.7071067811865476, 0.7071067811865476],
         "geo": {"disbukey": True}, "kenarlar": [{"L": 4}, {"L": 18 ** 0.5}, {"L": 4}, {"L": 18 ** 0.5}]}
    assert tb._panel_net_alani(E, [0.1, 0.2, 0.1, 0.2]) == pytest.approx((4 - 0.4) * (18 ** 0.5 - 0.2), rel=1e-12)


@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "betonarme-tek-aciklik", "betonarme-3kat-3x3", "betonarme-4kat-4x3"])
def test_genel_kalip_aks_kat_ile_ayni(ad):
    """Genelleştirilmiş şablonun Kalıp toplamı surum 1 ile aynı (kiriş yarı genişlikleri köşede iki kez düşülmez)."""
    def kalip(T):
        return {r["degerler"]["kalem"]: r["degerler"]["miktar"] for r in tb.tablo(T, "metraj_ozet")["satirlar"]}["Kalıp"]

    def doseme(T):
        return sum(r["degerler"]["kalip"] for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Döşeme")
    T1, T3 = tb.bina_tablolari(yapi.bina_sablon(ad)), tb.bina_tablolari(genellestir(ad))
    assert kalip(T3) == pytest.approx(kalip(T1), abs=1e-6) and doseme(T3) == pytest.approx(doseme(T1), abs=1e-6)


# ---------------------------------------------------------------------------- K-36: genel Duvar Yükleri her duvarlı olabilir çubuk
def test_genel_duvar_tablosu_butun_kirisler():
    g = genellestir("betonarme-2kat-3x2")
    T, T1 = tb.bina_tablolari(g, kati=True), tb.bina_tablolari(yapi.bina_sablon("betonarme-2kat-3x2"), kati=True)
    d, d1 = tb.tablo(T, "duvar_yukleri"), tb.tablo(T1, "duvar_yukleri")
    assert len(d["satirlar"]) == len(d1["satirlar"]) == 14
    assert d["toplam"] == pytest.approx(d1["toplam"])                  # toplamlar yalnız duvarlı satırlardan
    bos = [r for r in d["satirlar"] if r["degerler"]["duvar"] is None]
    assert len(bos) == 2 and all(r["degerler"]["toplam"] == 0.0 and r["degerler"]["adres"].endswith("(kiriş)") for r in bos)
    r = bos[0]
    assert r["yol"]["duvar"][0] == "cubuklar" and r["yol"]["h_duvar"][2] == "duvar_h"
    yeni = tb.degisiklikleri_uygula(g, [{"yol": r["yol"]["duvar"], "deger": "tugla19"}, {"yol": r["yol"]["h_duvar"], "deger": 1.2}])
    cb = next(c for c in YS._oku(copy.deepcopy(yeni)).cubuklar if c["no"] == r["degerler"]["kiris"])
    assert cb["duvar"] == "tugla19" and cb["duvar_h"] == 1.2
    d2 = tb.tablo(tb.bina_tablolari(yeni, kati=True), "duvar_yukleri")
    assert len(d2["satirlar"]) == 14 and d2["toplam"]["toplam"] > d["toplam"]["toplam"]
    # kolon duvar listesinde değil; elle duvar verilmiş başka tür (ör. çapraz) yine listelenir
    assert not [x for x in d["satirlar"] if "(kolon)" in x["degerler"]["adres"]]


# ============================================================================ birleştirmeden sonra (motor paketi)
def _genel_temel(ad):
    g = genellestir(ad)
    assert g["temeller"]["tip"] in ("surekli", "radye")
    return g


@pytest.fixture(scope="module")
def temel_cozumleri():
    """{ad: (bina, veri)}: aks–kat ve genelleştirilmiş mütemadi / radye şablonları."""
    sonuc = {}
    for ad in ("betonarme-3kat-surekli-temel", "betonarme-4kat-radye"):
        b = yapi.bina_sablon(ad)
        sonuc[ad] = (b, coz(b))
        g = _genel_temel(ad)
        sonuc[ad + "-genel"] = (g, coz(g))
    return sonuc


class TestMotorSonrasi:
    """Motor paketinin sözleşme tarafı gerekir (C11–C14, C18, C20, C21, K-44); birleştirmeden önce kalır."""

    @pytest.mark.parametrize("ad,hat,dugum,beton", [("betonarme-3kat-surekli-temel", 6, 135, 43.56),
                                                    ("betonarme-4kat-radye", 1, 195, 117.60)])
    def test_genel_mutemadi_radye_rapor_ve_tablolar(self, temel_cozumleri, ad, hat, dugum, beton):
        """K-1 / C11: genel modelde §13 temel analizi ve tasarımı; temeller, temel düğümleri, metraj (W/25 = aks–kat), çözümlü ve
        çözümsüz; §10.1 korunum G/Q ✔ (iki modelde de, C12 yay_ozet)."""
        for anahtar in (ad, ad + "-genel"):
            b, v = temel_cozumleri[anahtar]
            assert (v.get("model") == "genel") == anahtar.endswith("-genel")
            h = rapor.statik_rapor(b, v)
            b13 = bolum(h, 13)
            assert "13.1 Temel analizi sonuçları" in b13 and "13.2 Temel tasarım kontrolleri" in b13
            assert "yapılmadı" not in b13 and rapor.ESKI_TEMEL_NOTU not in b13
            sat = korunum_satirlari(h)
            assert "✔" in sat["G"] and "✔" in sat["Q"], (anahtar, metin(sat["G"]), metin(sat["Q"]))
            assert "Winkler zemin yayları; sabit mesnet yok" in b13
            ekb = metin(h[h.index('id="ekB"'):])
            assert ("| temel kirişi |" if hat > 1 else "| radye şeridi |") in ekb and "| temel-kirisi |" not in ekb
            i = h.index("Durum G (sabit yük)")
            assert "| temel ağı (Σ) | zemin yayları (Winkler) |" in metin(h[i:h.index("</table>", i)])
            for T in (tb.bina_tablolari(b, v, kati=True), tb.bina_tablolari(b, kati=True)):
                tem = tb.tablo(T, "temeller")["satirlar"]
                assert len(tem) == hat and (hat > 1 or tem[0]["degerler"].get("ad") == "Radye plağı")
                V = sum(r["degerler"]["beton"] for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Temel")
                assert V == pytest.approx(beton, abs=0.01), anahtar
            T = tb.bina_tablolari(b, v, kati=True)
            assert len(tb.tablo(T, "temel_dugumleri")["satirlar"]) == dugum
            W = v["temel"]["model"]["W_temel"]
            assert V == pytest.approx(W / 25.0, rel=1e-3)

    def test_genel_eski_cozum_notu(self, temel_cozumleri):
        """Model radye ama çözüm tekil (temel tipi sonradan değişti): genel modelde de 'yeniden çözün' notu."""
        b, v = temel_cozumleri["betonarme-4kat-radye-genel"]
        v = copy.deepcopy(v)
        v["temel"] = None
        assert rapor.ESKI_TEMEL_NOTU in bolum(rapor.statik_rapor(b, v), 13)

    def test_yayli_mesnet_kopru(self):
        """K-10 / C13 köprü: yaylı açık mesnet çözülür; tablolar ve rapor 'yaylı mesnet' + rijitlik, korunum ✔."""
        import importlib.util
        ozellik = importlib.util.spec_from_file_location("web_kopru_kalan", PROJE / "docs" / "web_kopru.py")
        kopru = importlib.util.module_from_spec(ozellik)
        ozellik.loader.exec_module(kopru)

        def iste(islem, girdi):
            return json.loads(kopru.calistir(json.dumps({"islem": islem, "girdi": girdi}, ensure_ascii=False)))
        b = yapi.bina_sablon("celik-cbf-3kat")
        b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "z": "±0.00"}, "ux": True, "uy": True, "rx": True, "ry": True, "rz": True,
                           "kz": 25000.0}]
        c = iste("bina_coz", {"bina": b})
        assert c["hata"] is None, c["hata"]
        k = c["veri"]["cozum_kimligi"]
        m = next(x for x in c["veri"]["akis"]["mesnetler"] if x.get("tip") == "yay")
        assert m["yay"] == {"kz": 25000.0}
        T = iste("bina_tablolar", {"cozum_kimligi": k})["tablolar"]
        mt = tb.tablo(T, "mesnet_tepkileri")
        r = next(x["degerler"] for x in mt["satirlar"] if x["degerler"]["dugum"] == m["dugum"] and x["degerler"]["durum"] == "G")
        assert r["tip"] == "yaylı mesnet" and r["yay"] == "k_z = 25 000 kN/m"
        h = iste("bina_rapor", {"cozum_kimligi": k})["html"]
        assert all("✔" in s for a, s in korunum_satirlari(h).items() if a in ("G", "Q"))
        assert "| yaylı mesnet | k_z = 25 000 kN/m |" in metin(bolum(h, 13))

    def test_diyafram_bagli_mesnet(self):
        """K-15 / C14: rijit diyaframlı seviyedeki ux mesnedi 'mesnet (diyafram bağıyla)'; EX+ korunumu ✔."""
        b = yapi.bina_sablon("betonarme-2kat-3x2")
        b["deprem"]["etkin"] = True
        b["yuk_durumlari"]["E"]["acik"] = True
        b["surum"] = 3
        b["mesnetler"] = [{"dugum": {"aks": ["C", "2"], "kat": 1}, "ux": True}]
        v = coz(b)
        h = rapor.statik_rapor(b, v)
        assert "✔" in korunum_satirlari(h)["EX+"]
        assert "mesnet (diyafram bağıyla)" in metin(bolum(h, 13))
        mt = tb.tablo(tb.bina_tablolari(b, v), "mesnet_tepkileri")
        assert any(r["degerler"]["tip"] == "mesnet (diyafram bağıyla)" for r in mt["satirlar"])

    def test_motor_adresi_turkce(self):
        """K-26 / C18: genel çözümün adresleri 'Ç{no} ({TUR_ADI[tur]})'; rapor ve tablolar ham tür yazmaz."""
        b = yapi.bina_sablon("celik-cbf-3kat")
        v = coz(b)
        h = rapor.statik_rapor(b, v)
        assert "(kiris)" not in h and "(capraz)" not in h and "(kiriş)" in h
        T = tb.bina_tablolari(b, v)
        assert "(kiris)" not in json.dumps(T, ensure_ascii=False)

    def test_basit_kesit_sinifi_sanayi_ve_cbf(self):
        """K-34 / C20: tasarim.kesit_sinifi basit adı çözer; §5'te sınıf satırı."""
        for ad in ("celik-sanayi-4hol", "celik-cbf-3kat"):
            b = yapi.bina_sablon(ad)
            b5 = metin(bolum(rapor.statik_rapor(b, coz(b)), 5))
            assert "BORU 168.3x6.3: basınçta narin olmayan, eğilmede kompakt" in b5, ad

    def test_genel_kolon_ozeti_yon(self):
        """K-30 / C21: genelleştirilmiş 2 katlı binada §11.3 Yön sütunu aks–kat ile aynı; N_min aks–kat kuralıyla."""
        def kolonlar(h):
            b11 = bolum(h, 11)
            i = b11.index("11.3 Kolonlar")
            t = b11[i:b11.index("</table>", i)]
            return [metin(s).split(" | ") for s in re.findall(r"<tr>(.*?)</tr>", t)[1:]]
        b1 = yapi.bina_sablon("betonarme-2kat-3x2")
        g = genellestir("betonarme-2kat-3x2")
        k1, k3 = kolonlar(rapor.statik_rapor(b1, coz(b1))), kolonlar(rapor.statik_rapor(g, coz(g)))
        assert len(k1) == len(k3) and sorted(r[2] for r in k1) == sorted(r[2] for r in k3) and all(r[2] for r in k3)
        assert sorted(float(r[4]) for r in k3) == pytest.approx(sorted(float(r[4]) for r in k1), rel=0.01)

    def test_kat_agirliklari_aks_kat_kurali(self):
        """K-44: genelleştirilmiş 2 katlı binanın kat ağırlıkları (her kolonun ağırlığı üst seviyesine) surum 1 ile aynı."""
        b1 = yapi.bina_sablon("betonarme-2kat-3x2")
        g = genellestir("betonarme-2kat-3x2")
        v1, v3 = coz(b1), coz(g)

        def katlar(v):
            return [(k["kat"], round(k["G"], 1), round(k["Q"], 1)) for k in v["yukler"]["katlar"]]
        assert katlar(v3) == katlar(v1)
        for v, b in ((v1, b1), (v3, g)):
            t = [(r["degerler"]["kat"], round(r["degerler"]["G"], 1)) for r in tb.tablo(tb.bina_tablolari(b, v), "kat_agirliklari")["satirlar"]]
            assert t == [(k, G_) for k, G_, _ in katlar(v1)]
