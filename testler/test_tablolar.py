# -*- coding: utf-8 -*-
"""tablolar.py (tablo editörü ve metraj, tasarım belgesi §15) ve docs/tablo_editoru.js testleri.

- Şema: her şablon için çözümsüz (Model + Yükler + Metraj) ve çözümlü (+ Analiz, Deprem, Tasarım, Temel) tablolar; sütun/satır
  tutarlılığı, katı JSON (NaN yok), düzenlenebilir hücrelerde gerçek bina JSON yolu.
- Yollar: gösterilen değer yoluna geri yazılınca model aynı kalır; düzenleme motor okumasına yansır.
- Metraj: el hesabıyla (kolon b·h·(H − t), kiriş b·(h − t)·L_net, döşeme alan·t, tekil temel B·L·h; çelik g·L, bağlantı payı,
  boya yüzeyi; mütemadi/radye), donatı tasarımdan ya da açıkça "yaklaşık" orandan.
- Aks sistemi (§19): Akslar (X/Y/Z) ve Aks Sistemleri tabloları, düğüm aks adresi, REF koordinatları (Z aksı, döndürülmüş ve silindirik
  sistem, bölme düğümü), yeniden adlandırmanın bağlı başvuruları güncellemesi.
- Köprü "bina_tablolar": önbellekteki çözüm (kimlik eşleşmesi), düzenlenmiş binada çözümsüz tablolar.
- JS: node --check, node --test (saf mantık), Python ↔ JS eşdeğerliği (değişiklik uygulama ve hücre biçimi).
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

import tablolar as tb
import yapi
import yapi_serbest as YS
import yapi_veri as yv

PROJE = Path(__file__).resolve().parent.parent
JS = PROJE / "docs" / "tablo_editoru.js"
JS_TEST = PROJE / "testler" / "js" / "tablo_editoru.test.js"
NODE = shutil.which("node")
SABLONLAR = list(yapi.BINA_SABLONLARI)
TURLER = {"sayi", "metin", "secim", "bool"}


@pytest.fixture(scope="module")
def cozumler():
    """Şablon adı → (bina, veri) (modül başına bir kez çözülür)."""
    sonuc = {}
    for ad in SABLONLAR:
        b = yapi.bina_sablon(ad)
        sonuc[ad] = (b, yapi.bina_coz(copy.deepcopy(b), goster="yok", anlat=False).veri)
    return sonuc


def _katı_json(nesne):
    def reddet(x):
        raise ValueError(f"katı JSON değil: {x}")
    return json.loads(json.dumps(nesne, ensure_ascii=False, allow_nan=False), parse_constant=reddet)


def _sema_dogrula(tablolar):
    adlar = [t["ad"] for t in tablolar]
    assert len(adlar) == len(set(adlar)), adlar
    sira = [tb.GRUPLAR.index(t["grup"]) for t in tablolar]
    assert sira == sorted(sira), "tablolar grup sırasında olmalı"
    for t in tablolar:
        assert set(t) >= {"ad", "baslik", "grup", "sutunlar", "satirlar", "aciklama", "kaynak"}, t["ad"]
        sutun = {s["ad"]: s for s in t["sutunlar"]}
        assert len(sutun) == len(t["sutunlar"]), t["ad"]
        for s in t["sutunlar"]:
            assert s["tur"] in TURLER and isinstance(s["duzenlenebilir"], bool) and "baslik" in s and "birim" in s, (t["ad"], s)
            if s["tur"] == "secim":
                assert isinstance(s.get("secenekler"), list), (t["ad"], s["ad"])
        for r in t["satirlar"]:
            assert set(r["degerler"]) <= set(sutun), (t["ad"], set(r["degerler"]) - set(sutun))
            for a, yol in (r.get("yol") or {}).items():
                assert sutun[a]["duzenlenebilir"], f"{t['ad']}.{a}: yol var ama sütun düzenlenemez"
                assert isinstance(yol, list) and yol, (t["ad"], a, yol)
            for a in r.get("hucre") or {}:
                assert a in sutun, (t["ad"], a)
            for a, bag in (r.get("bag") or {}).items():
                assert bag["islem"] in ("aks_ad", "sistem_ad") and a in (r.get("yol") or {}), (t["ad"], a, bag)
        for a in t.get("toplam") or {}:
            assert a in sutun, (t["ad"], a)
    _katı_json(tablolar)


# ---------------------------------------------------------------------------- şema ve gruplar
@pytest.mark.parametrize("ad", SABLONLAR)
def test_cozumsuz_tablolar(ad):
    b = yapi.bina_sablon(ad)
    once = json.dumps(b, sort_keys=True)
    T = tb.bina_tablolari(b, kati=True)
    assert json.dumps(b, sort_keys=True) == once, "bina_tablolari girdiyi değiştirmemeli"
    _sema_dogrula(T)
    gruplar = {t["grup"] for t in T}
    assert {"Model", "Yükler", "Metraj"} <= gruplar and not gruplar & {"Analiz", "Tasarım"}
    adlar = {t["ad"] for t in T}
    assert {"genel", "katlar", "akslar", "aks_sistemleri", "dugumler", "cubuklar", "kesitler", "malzemeler", "dosemeler", "mesnetler",
            "temeller", "yuk_durumlari", "doseme_yukleri", "duvar_yukleri", "kar_ruzgar", "ek_yukler", "eleman_yukleri", "kat_agirliklari",
            "kombinasyonlar", "temel_parametreleri", "metraj_ozet", "metraj_betonarme", "metraj_varsayimlari"} <= adlar
    # JSON metni de kabul edilir
    assert [t["ad"] for t in tb.bina_tablolari(json.dumps(b))] == [t["ad"] for t in T]


@pytest.mark.parametrize("ad", SABLONLAR)
def test_cozumlu_tablolar(ad, cozumler):
    b, v = cozumler[ad]
    T = tb.bina_tablolari(b, v, kati=True)
    _sema_dogrula(T)
    adlar = {t["ad"] for t in T}
    assert {"dugum_yer_degistirmeleri", "mesnet_tepkileri", "eleman_kuvvetleri_zarf", "kolon_yukleri", "korunum", "temel_basinclari"} <= adlar
    assert any(t["grup"] == "Tasarım" for t in T)
    # mesnet tepkisi Σ satırları durumun düşey toplamını dengeler (G)
    tep = tb.tablo(T, "mesnet_tepkileri")
    sigma_G = next(r for r in tep["satirlar"] if r.get("ozet") and r["degerler"]["durum"] == "G")
    assert sigma_G["degerler"]["FZ"] == pytest.approx(v["yukler"]["toplam"]["G"], rel=1e-6)
    # tasarım tablolarında D/C sütunu vurgulu ve değerler çözümle aynı
    tas = [t for t in T if t["grup"] == "Tasarım"]
    for t in tas:
        assert next(s for s in t["sutunlar"] if s["ad"] == "dc").get("vurgu") == "dc"
    dc = {(e["tur"], e["no"]): e["dc"] for e in v["tasarim"]["elemanlar"]}
    for t in tas:
        for r in t["satirlar"]:
            tur = r["degerler"].get("tur") or ("kiris" if "kiris" in t["ad"] else "kolon")
            if (tur, r["degerler"]["no"]) in dc:
                assert r["degerler"]["dc"] == pytest.approx(dc[(tur, r["degerler"]["no"])])
    if v.get("deprem"):
        assert {"deprem_parametreleri", "kat_kuvvetleri", "oteleme", "theta", "burulma"} <= adlar


def test_deprem_onizleme_cozumsuz():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    T = tb.bina_tablolari(b, kati=True)
    dp = tb.tablo(T, "deprem_parametreleri")
    hesap = [r for r in dp["satirlar"] if r["degerler"]["tur"].startswith("hesap")]
    assert hesap and all("önizleme" in r["degerler"]["tur"] for r in hesap)
    assert tb.tablo(T, "kat_kuvvetleri")["satirlar"]


# ---------------------------------------------------------------------------- yollar
def _duzenlenebilir_hucreler(T):
    for t in T:
        for i, r in enumerate(t["satirlar"]):
            for a, yol in (r.get("yol") or {}).items():
                yield t, i, r, a, yol


def _genel_okuma_ayni(b0, b1):
    """Genel (surum 3) model: geri yazım öncesi/sonrası yapi_serbest okuması aynı (katlar, akslar, çubuklar, paneller, temeller…)."""
    S0, S1 = YS._oku(copy.deepcopy(b0)), YS._oku(copy.deepcopy(b1))
    assert [(k["no"], k["ad"], k["kot"]) for k in S1.katlar] == [(k["no"], k["ad"], pytest.approx(k["kot"])) for k in S0.katlar]
    for yon in ("x", "y", "z"):
        assert [(a["ad"], a["konum"]) for a in S1.akslar[yon]] == [(a["ad"], pytest.approx(a["konum"])) for a in S0.akslar[yon]]
    cub = lambda S: [(c["no"], c["i"], c["j"], c["tur"], c["kesit"], c["aci"], c["yalniz_cekme"], c["duvar"]) for c in S.cubuklar]  # noqa: E731
    assert cub(S1) == cub(S0)
    pan = lambda S: [(p["no"], p["tur"], p["kalinlik"], p["g_ek"], p["q"], p["kullanim"], p["kar"], p["dagitim"]) for p in S.paneller]  # noqa: E731
    assert pan(S1) == pan(S0)
    tem = lambda S: {n: (m["tip"], m.get("B"), m.get("L")) for n, m in S.mesnetler.items()}  # noqa: E731
    assert tem(S1) == tem(S0)
    assert {k: v for k, v in S0.temeller.items() if k != "ozel"} == {k: v for k, v in S1.temeller.items() if k != "ozel"}
    assert {a: (k["tip"], k.get("profil"), k["A"]) for a, k in S0.kesitler.items()} == \
        {a: (k["tip"], k.get("profil"), k["A"]) for a, k in S1.kesitler.items()}
    assert S0.deprem == S1.deprem and S0.kombinasyon_kumesi == S1.kombinasyon_kumesi and S0.analiz == S1.analiz


@pytest.mark.parametrize("ad", SABLONLAR)          # aks–kat (yapi._bina_oku) ve genel model (yapi_serbest._oku)
def test_yollar_cozulur_ve_geri_yazim_modeli_degistirmez(ad, cozumler):
    b, v = cozumler[ad]
    T = tb.bina_tablolari(b, v, kati=True)
    degisiklik, sayi = [], 0
    for t, i, r, a, yol in _duzenlenebilir_hucreler(T):
        sayi += 1
        tb.yol_ata(copy.deepcopy(b), yol, r["degerler"].get(a))     # yol yazılabilir (eksik isteğe bağlı sözlükler oluşur)
        try:
            tb.yol_al(b, yol)
        except KeyError:                                   # yalnız isteğe bağlı ayar sözlükleri / oluşturulacak eleman eksik olabilir
            tek = yol[0] if tb._coklu_yol(yol) else yol
            assert tek[0] in ("metraj", "analiz", "yuk_durumlari", "deprem", "temeller") or any(
                isinstance(p, dict) and p.get("_olustur") for p in tek), (t["ad"], a, yol)
        deger = r["degerler"].get(a)
        if deger is not None and not r.get("bag"):
            degisiklik.append({"yol": yol, "deger": deger})
    assert sayi > 20
    yeni = tb.degisiklikleri_uygula(b, degisiklik)
    if yapi._serbest_mi(b):            # genel model: kendi okuyucusuyla karşılaştırılır
        _genel_okuma_ayni(b, yeni)
        return
    B0, B1 = yapi._bina_oku(copy.deepcopy(b)), yapi._bina_oku(yeni)
    assert [(k["no"], k["ad"], k["kot"]) for k in B1.katlar] == [(k["no"], k["ad"], pytest.approx(k["kot"])) for k in B0.katlar]
    for yon in ("x", "y"):        # tablo kayan nokta gürültüsünü atar (9.600000000000001 → 9.6): yaklaşık eşit
        assert [(a["ad"], a["konum"]) for a in B1.akslar[yon]] == [(a["ad"], pytest.approx(a["konum"])) for a in B0.akslar[yon]]
    assert [(k["no"], k["kesit"], k["yon"]) for k in B0.kolonlar] == [(k["no"], k["kesit"], k["yon"]) for k in B1.kolonlar]
    assert [(d["no"], d["h"], d["q"], d["g_ek"]) for d in B0.dosemeler] == [(d["no"], d["h"], d["q"], d["g_ek"]) for d in B1.dosemeler]
    def etkin_temel(B):     # geri yazım özel temel kaydı oluşturabilir; etkin boyutlar aynı kalmalı
        return {(c["ix"], c["iy"]): tuple((B.temeller["ozel"].get((c["ix"], c["iy"])) or B.temeller["varsayilan"])[k] for k in ("B", "L"))
                for c in B.kolonlar if c["kat"] == 1}
    assert etkin_temel(B0) == etkin_temel(B1)
    assert {k: v for k, v in B0.temeller.items() if k != "ozel"} == {k: v for k, v in B1.temeller.items() if k != "ozel"}
    assert B0.deprem == B1.deprem and B0.kombinasyon_kumesi == B1.kombinasyon_kumesi and B0.analiz == B1.analiz


def test_duzenleme_motor_okumasina_yansir():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    T = tb.bina_tablolari(b, kati=True)
    kat = tb.tablo(T, "katlar")["satirlar"][2]
    kesit = next(r for r in tb.tablo(T, "kesitler")["satirlar"] if r["degerler"]["ad"] == "K25x50")
    kol = tb.tablo(T, "cubuklar")["satirlar"][0]
    dos = tb.tablo(T, "dosemeler")["satirlar"][0]
    tem = tb.tablo(T, "temeller")["satirlar"][0]
    gen = {r["degerler"]["parametre"]: r for r in tb.tablo(T, "genel")["satirlar"]}
    met = {r["degerler"]["parametre"]: r for r in tb.tablo(T, "metraj_varsayimlari")["satirlar"]}
    yeni = tb.degisiklikleri_uygula(b, [
        {"yol": kat["yol"]["kot"], "deger": 6.5},
        {"yol": kesit["yol"]["h"], "deger": 0.6},
        {"yol": kol["yol"]["kesit"], "deger": "K25x50"},
        {"yol": dos["yol"]["kullanim"], "deger": "ofis"},
        {"yol": tem["yol"]["B"], "deger": 2.2},
        {"yol": gen["Kombinasyon kümesi"]["yol"]["deger"], "deger": "cythye_gkt"},
        {"yol": met["Çelik bağlantı payı"]["yol"]["deger"], "deger": 0.15},
    ])
    assert b["katlar"][2]["kot"] == 6.0, "girdi değişmemeli"
    B = yapi._bina_oku(yeni)
    assert B.kat[2]["kot"] == 6.5 and B.kat[2]["h"] == pytest.approx(3.5)
    assert B.kesitler["K25x50"]["h"] == 0.6
    assert B.kolon_no[kol["degerler"]["no"]]["kesit"] == "K25x50"
    assert B.doseme_no[dos["degerler"]["no"]]["kullanim"] == "ofis"
    aks = tem["degerler"]["aks"]
    ix, iy = B.ax[aks[0]], B.ay[aks[1:]]
    assert B.temeller["ozel"][(ix, iy)]["B"] == 2.2
    assert B.kombinasyon_kumesi == "cythye_gkt"
    T2 = tb.bina_tablolari(yeni, kati=True)
    assert tb.tablo(T2, "katlar")["satirlar"][2]["degerler"]["h"] == pytest.approx(3.5)
    assert next(r for r in tb.tablo(T2, "kesitler")["satirlar"] if r["degerler"]["ad"] == "K25x50")["degerler"]["A"] == pytest.approx(0.25 * 0.6 * 1e4)
    assert next(r for r in tb.tablo(T2, "metraj_varsayimlari")["satirlar"] if r["degerler"]["parametre"] == "Çelik bağlantı payı")["degerler"]["deger"] == 0.15


def test_yol_islevleri():
    b = {"l": [{"no": 1, "x": 1}, {"no": 2}], "d": {}}
    assert tb.yol_al(b, ["l", {"no": 1}, "x"]) == 1
    assert tb.yol_al(b, ["l", -1, "x"]) is None
    with pytest.raises(KeyError):
        tb.yol_al(b, ["l", {"no": 3}, "x"])
    tb.yol_ata(b, ["l", {"no": 3, "_olustur": True}, "x"], 5)
    assert b["l"][-1] == {"no": 3, "x": 5}
    tb.yol_ata(b, ["d", "a", "b"], 2)
    assert b["d"] == {"a": {"b": 2}}
    tb.yol_ata(b, [["l", 0, "x"], ["d", "a", "b"]], 9)
    assert b["l"][0]["x"] == 9 and b["d"]["a"]["b"] == 9
    with pytest.raises(KeyError):
        tb.yol_ata(b, ["l", {"no": 1}], 1)
    with pytest.raises(KeyError):
        tb.yol_ata(b, ["l", 5, "x"], 1)


# ---------------------------------------------------------------------------- metraj
def test_metraj_betonarme_el_hesabi():
    b = yapi.bina_sablon("betonarme-2kat-3x2")   # 40×40 kolon, 25×50 kiriş, 14 cm döşeme, 3 m kat, A–B–C (0, 5, 9), 1–2 (0, 4)
    T = tb.bina_tablolari(b, kati=True)
    m = tb.tablo(T, "metraj_betonarme")
    kol = [r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Kolon"]
    assert len(kol) == 12
    for k in kol:
        assert k["beton"] == pytest.approx(0.4 * 0.4 * (3.0 - 0.14))
        assert k["kalip"] == pytest.approx(4 * 0.4 * (3.0 - 0.14))
        assert k["donati_kaynak"].startswith("yaklaşık")
        assert k["donati"] == pytest.approx(k["beton"] * tb.DONATI_ORANLARI["kolon"])
    kir = {r["degerler"]["adres"]: r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Kiriş"}
    k = next(v for a, v in kir.items() if a.startswith("K-A1→B1/k1"))
    assert k["uzunluk"] == pytest.approx(5.0 - 0.2 - 0.2)                     # L_net = aks boyu − kolon yarı genişlikleri
    assert k["beton"] == pytest.approx(0.25 * (0.5 - 0.14) * 4.6)
    assert k["kalip"] == pytest.approx((0.25 + 2 * 0.36) * 4.6)
    dos = [r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Döşeme"]
    assert sum(d["beton"] for d in dos) == pytest.approx(2 * (9 * 4) * 0.14)
    tem = [r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Temel"]
    assert len(tem) == 6
    assert sum(t["beton"] for t in tem) == pytest.approx(4 * 1.6 * 1.6 * 0.6 + 2 * 2.0 * 2.0 * 0.6)   # B1, B2 özel 2,0 × 2,0
    assert m["toplam"]["beton"] == pytest.approx(sum(r["degerler"]["beton"] for r in m["satirlar"]))
    oz = {(r["degerler"]["kalem"], r["degerler"]["malzeme"]): r["degerler"] for r in tb.tablo(T, "metraj_ozet")["satirlar"]}
    assert oz[("Beton (toplam)", "C30/37")]["miktar"] == pytest.approx(m["toplam"]["beton"])
    assert oz[("Kalıp", "")]["miktar"] == pytest.approx(m["toplam"]["kalip"])
    assert oz[("Donatı çeliği", "B420C")]["miktar"] == pytest.approx(m["toplam"]["donati"] / 1000)
    assert ("Duvar (kirişler üstü)", "tugla-delikli-19") in oz
    assert "birim fiyat" not in json.dumps([s["ad"] for t in T for s in t["sutunlar"]])


def test_metraj_donati_tasarimdan(cozumler):
    b, v = cozumler["betonarme-2kat-3x2"]
    m = tb.tablo(tb.bina_tablolari(b, v, kati=True), "metraj_betonarme")
    tas = {(e["tur"], e["no"]): e for e in v["tasarim"]["elemanlar"]}
    kol = next(r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Kolon")
    e = tas[("kolon", kol["no"])]
    assert kol["donati_kaynak"].startswith("tasarım A_s")
    boyuna = e["ozet"]["As_toplam_cm2"] * 1e-4 * 3.0 * tb.CELIK_YOGUNLUK
    assert kol["donati"] > boyuna                                              # + etriye
    assert kol["donati"] == pytest.approx(boyuna + tb._etriye_kg(*(tb._etriye_ayristir(e["ozet"].get("etriye")) or tb.KOLON_ETRIYE),
                                                                  0.4, 0.4, 3.0, 0.03))
    kir = next(r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Kiriş")
    assert kir["donati_kaynak"].startswith("tasarım A_s")
    dos = next(r["degerler"] for r in m["satirlar"] if r["degerler"]["tur"] == "Döşeme")
    assert dos["donati_kaynak"].startswith("yaklaşık")


def test_metraj_celik():
    b = yapi.bina_sablon("celik-1kat-depo")
    b["metraj"] = {"baglanti_payi": 0.12}
    T = tb.bina_tablolari(b, kati=True)
    m = tb.tablo(T, "metraj_celik")
    for r in m["satirlar"]:
        d = r["degerler"]
        p = yv.PROFILLER[d["profil"]]
        assert d["g"] == p["g"] and d["kutle"] == pytest.approx(p["g"] * d["L"])
        assert d["boya"] == pytest.approx((2 * p["h"] + 4 * p["b"] - 2 * p["tw"] - (8 - 2 * math.pi) * p["r"]) / 1000 * d["L"])
    pr = {r["degerler"]["profil"]: r["degerler"] for r in tb.tablo(T, "metraj_profil_ozeti")["satirlar"]}
    assert pr["HEB 240"]["adet"] == 6 and pr["HEB 240"]["L"] == pytest.approx(30.0)
    assert pr["HEB 240"]["kutle_payli"] == pytest.approx(pr["HEB 240"]["kutle"] * 1.12)
    assert pr["HEB 240"]["pay"] == pytest.approx(12.0)
    oz = {r["degerler"]["kalem"]: r["degerler"] for r in tb.tablo(T, "metraj_ozet")["satirlar"]}
    net = sum(r["degerler"]["kutle"] for r in m["satirlar"])
    assert oz["Yapısal çelik (profil)"]["miktar"] == pytest.approx(net * 1.12 / 1000)
    assert oz["Yapısal çelik (profil)"]["birim"] == "t"


def test_metraj_ve_temel_tablosu_surekli_ve_radye():
    b = yapi.bina_sablon("betonarme-2kat-3x2")    # A–B–C (0, 5, 9), 1–2 (0, 4)
    b["temeller"].update({"tip": "surekli", "surekli": {"yon": "xy", "B": 1.2, "h_tabla": 0.4, "b_govde": 0.5, "h_govde": 1.0, "tasma": 0.5}})
    T = tb.bina_tablolari(b, kati=True)
    tt = tb.tablo(T, "temeller")
    assert tt["baslik"].startswith("Temeller (Mütemadi")
    hat = {r["degerler"]["hat"]: r for r in tt["satirlar"]}
    assert set(hat) == {"1", "2", "A", "B", "C"} and hat["1"]["degerler"]["L"] == pytest.approx(10.0) and hat["A"]["degerler"]["L"] == pytest.approx(5.0)
    assert hat["1"]["yol"]["B"] == ["temeller", "surekli", "B"] and hat["1"]["degerler"]["A"] == pytest.approx(1.2 * 0.4 + 0.5 * 0.6)
    yeni = tb.degisiklikleri_uygula(b, [{"yol": hat["A"]["yol"]["h_govde"], "deger": 1.1}])
    assert yapi._bina_oku(yeni).temeller["surekli"]["h_govde"] == 1.1
    tem = [r["degerler"] for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Temel"]
    x = {t["adres"]: t for t in tem if "(X" in t["adres"]}
    y = {t["adres"]: t for t in tem if "(Y" in t["adres"]}
    assert len(x) == 2 and len(y) == 3
    A = 1.2 * 0.4 + 0.5 * (1.0 - 0.4)              # ters T: h_gövde tabla dahil
    assert x["TK-1 (X doğr.)"]["beton"] == pytest.approx(A * (9 + 1.0))
    # kesişim hacmi y hatlarından, hat uçlarıyla kırpılmış dikdörtgenlerle düşülür (köşe 1,1 × 1,1; kenar 1,2 × 1,1 tabla)
    assert y["TK-A (Y doğr.)"]["beton"] == pytest.approx(A * 5.0 - 2 * (1.1 * 1.1 * 0.4 + 0.5 * 0.5 * 0.6))
    assert y["TK-B (Y doğr.)"]["beton"] == pytest.approx(A * 5.0 - 2 * (1.2 * 1.1 * 0.4 + 0.5 * 0.5 * 0.6))
    assert tb.tablo(T, "mesnetler")["satirlar"] == []           # kolon tabanı mesnedi yok: zemin yayları
    b["temeller"].update({"tip": "radye", "radye": {"h": 0.8, "tasma": 1.0, "kiris": {"b": 0.5, "h": 1.2}}})
    T = tb.bina_tablolari(b, kati=True)
    tt = tb.tablo(T, "temeller")
    r = tt["satirlar"][0]
    assert tt["baslik"] == "Temel (Radye plak)" and r["degerler"]["Lx"] == pytest.approx(11.0) and r["degerler"]["Ly"] == pytest.approx(6.0)
    assert r["yol"]["h"] == ["temeller", "radye", "h"] and r["yol"]["kb"] == ["temeller", "radye", "kiris", "b"]
    assert r["degerler"]["kiris"] == "50×120 cm"
    tem = [r["degerler"] for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Temel"]
    assert tem[0]["adres"] == "Radye" and tem[0]["beton"] == pytest.approx((9 + 2) * (4 + 2) * 0.8)
    assert sum(t["beton"] for t in tem[1:]) == pytest.approx(0.5 * 0.4 * (2 * 9 + 3 * (4 - 2 * 0.5)))


@pytest.mark.parametrize("ad", [a for a in SABLONLAR if yapi.bina_sablon(a)["temeller"].get("tip") in ("surekli", "radye")])
def test_winkler_tepkileri_ve_temel_metraji(ad, cozumler):
    """Mütemadi/radye: zemin yayı tepkileri (F_Z = k0·A·w) her durumda yükü dengeler; metraj hacmi motorun temel öz ağırlığıyla aynı."""
    b, v = cozumler[ad]
    tv = v["temel"]
    T = tb.bina_tablolari(b, v, kati=True)
    tep = tb.tablo(T, "mesnet_tepkileri")
    assert "Winkler" in tep["aciklama"] and "zemin yayı" in tep["aciklama"]
    sigma = {r["degerler"]["durum"]: r["degerler"] for r in tep["satirlar"] if r.get("ozet")}
    assert sigma["G"]["FZ"] == pytest.approx(v["yukler"]["toplam"]["G"], rel=1e-6)       # temel öz ağırlığı dahil (korunum "yay")
    assert sigma["G"]["FZ"] == pytest.approx(v["akis"]["korunum"]["G"]["yay"], rel=1e-6)
    assert sigma["Q"]["FZ"] == pytest.approx(v["yukler"]["toplam"]["Q"], rel=1e-6)
    satir = [r["degerler"] for r in tep["satirlar"] if r["degerler"]["durum"] == "G" and r["degerler"]["tip"] == "zemin yayı"]
    assert len(satir) == len(tv["dugumler"])
    d0 = tv["dugumler"][0]
    r0 = next(r for r in satir if r["dugum"] == d0["no"])
    uZ = next(d["uZ"] for d in v["durumlar"]["G"]["dugumler"] if d["no"] == d0["no"])
    assert r0["FZ"] == pytest.approx(tv["model"]["k0"] * d0["A"] * -uZ, rel=1e-9) and r0["FZ"] > 0     # k_z·w, w = −u_Z
    if tv["tip"] == "surekli":
        assert any(abs(r["MX"]) > 1e-6 or abs(r["MY"]) > 1e-6 for r in satir), "tabla dönme yayı momentleri"
    if "EX+" in sigma:
        assert sigma["EX+"]["FX"] == pytest.approx(-v["deprem"]["VtE"], rel=1e-3)
    beton = [m for m in yapi._bina_oku(copy.deepcopy(b)).malzemeler.values() if m["tur"] == "beton"][0]["gamma"]
    tem = [r["degerler"]["beton"] for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Temel"]
    assert sum(tem) == pytest.approx(tv["model"]["W_temel"] / beton, rel=1e-5)
    assert tb.tablo(T, "temeller")["satirlar"]


# ---------------------------------------------------------------------------- genel model (surum 3): okuyucu, metraj, yükler
S3 = [a for a in SABLONLAR if int(yapi.BINA_SABLONLARI[a].get("surum", 1)) >= 3]
GENELLESTIR = "genellestir:betonarme-2kat-3x2"
_GENELLESTIR_BETIK = ('const M=require(process.argv[1]);let v="";process.stdin.on("data",d=>v+=d);'
                      'process.stdin.on("end",()=>{process.stdout.write(JSON.stringify(M.genellestir(JSON.parse(v)).model))});')


@pytest.fixture(scope="module")
def genellestirilmis():
    """docs/model_ops.js ModelOps.genellestir(betonarme-2kat-3x2) → (genel bina, çözüm) — test_yapi_serbest kalıbı."""
    if NODE is None:
        pytest.skip("node kurulu değil")
    r = subprocess.run([NODE, "-e", _GENELLESTIR_BETIK, str(PROJE / "docs" / "model_ops.js")],
                       input=json.dumps(yapi.bina_sablon("betonarme-2kat-3x2")), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    assert g["surum"] == 3 and g["cubuklar"] and not g.get("kolonlar")
    return g, yapi.bina_coz(copy.deepcopy(g), goster="yok", anlat=False).veri


def _genel(request, cozumler, ad):
    return request.getfixturevalue("genellestirilmis") if ad == GENELLESTIR else cozumler[ad]


def _birim_agirlik(S, ks):
    """Çelik kesitin katalog / kesit hesabı birim ağırlığı (kg/m): vute → temel profil."""
    import tasarim
    kt = S.kesitler[ks["temel"]] if ks["tip"] == "vute" else ks
    p = yv.PROFILLER.get(kt.get("profil") or "")
    return p["g"] if p else tasarim.kesit_ozellik(kt["profil"])["g"]


@pytest.mark.parametrize("cozumlu", [False, True], ids=["cozumsuz", "cozumlu"])
@pytest.mark.parametrize("ad", S3 + [GENELLESTIR])
def test_genel_model_okuma_metraj_ve_yukler(request, cozumler, ad, cozumlu):
    """Genel model yapi_serbest ile okunur: sahte 'Model denetimi' yok; çelik metrajı Σ g·L, beton yalnız beton dikdörtgen kesitler,
    tekil temel mesnet başına; çubuk ve panel yük tabloları dolu."""
    b, v = _genel(request, cozumler, ad)
    T = tb.bina_tablolari(b, v if cozumlu else None, kati=True)
    _sema_dogrula(T)
    assert "Model denetimi" not in {r["degerler"]["parametre"] for r in tb.tablo(T, "genel")["satirlar"]}
    S = YS._oku(copy.deepcopy(b))
    assert tb.tablo(T, "metraj_ozet")["satirlar"]
    celik = [c for c in S.cubuklar if S.kesitler[c["kesit"]]["tip"] in ("profil", "basit", "vute")]
    if celik:
        mc = tb.tablo(T, "metraj_celik")
        assert mc is not None and len(mc["satirlar"]) == len(celik)
        gL = sum(_birim_agirlik(S, S.kesitler[c["kesit"]]) * c["L"] for c in celik)
        assert sum(r["degerler"]["kutle"] for r in mc["satirlar"]) == pytest.approx(gL, rel=0.10)
        oz = {r["degerler"]["kalem"]: r["degerler"] for r in tb.tablo(T, "metraj_ozet")["satirlar"]}
        assert oz["Yapısal çelik (profil)"]["miktar"] > 0 and oz["Yapısal çelik (profil)"]["birim"] == "t"
        assert tb.tablo(T, "metraj_profil_ozeti")["satirlar"]
    else:
        assert tb.tablo(T, "metraj_celik") is None
    mb = tb.tablo(T, "metraj_betonarme")
    celik_no = {c["no"] for c in celik}
    assert not [r for r in mb["satirlar"] if r["degerler"]["tur"] not in ("Temel", "Döşeme", "Panel") and r["degerler"]["no"] in celik_no]
    destek = [m for m in S.mesnetler.values() if m["kaynak"] == "temel"]
    temel = [r["degerler"] for r in mb["satirlar"] if r["degerler"]["tur"] == "Temel"]
    h = S.temeller["varsayilan"]["h"]
    assert len(temel) == len(destek) and sum(t["beton"] for t in temel) == pytest.approx(sum(m["B"] * m["L"] * h for m in destek))
    assert len(tb.tablo(T, "temeller")["satirlar"]) == len(destek)
    # yükler: çubuk başına döküm, panel yükleri ve kenar payları (Σ kenar = panel toplamı)
    assert tb.tablo(T, "eleman_yukleri")["satirlar"]
    py = tb.tablo(T, "panel_yukleri")
    assert len(py["satirlar"]) == len(S.paneller) > 0
    pk = tb.tablo(T, "panel_kenar_yukleri")
    assert pk["toplam"]["G"] == pytest.approx(py["toplam"]["G_toplam"], rel=1e-6)
    assert "Panel Yükleri" in tb.tablo(T, "doseme_yukleri")["aciklama"]
    if cozumlu:
        G = sum((c.get("G") or {}).get("toplam_kN") or 0.0 for c in v["yukler"]["cubuklar"])
        assert tb.tablo(T, "eleman_yukleri")["toplam"]["toplam"] >= G - 1e-6
        kor = tb.tablo(T, "korunum")
        adlar = {s_["ad"] for s_ in kor["sutunlar"]}
        assert {"paneller", "cubuk_oz", "toplam", "temel"} <= adlar and not adlar & {"dosemeler", "kiris_oz", "kolon_oz", "tepki"}
        tbs = tb.tablo(T, "temel_basinclari")["satirlar"]
        assert len(tbs) == len(destek)
        for r in tbs:
            d = r["degerler"]
            assert d["N_temel"] == pytest.approx(yapi.GAMMA_BA * d["B"] * d["L"] * h)
    else:
        kat = tb.tablo(T, "kat_agirliklari")["satirlar"]
        assert kat and sum(r["degerler"]["G"] for r in kat) > 0
        assert tb.tablo(T, "kombinasyonlar")["satirlar"]


def test_genel_model_celik_metraji_sanayi(cozumler):
    """celik-sanayi-4hol: I/H profiller ≈ 90.5 t, vute ve boru çaprazlar çelikte (betonda değil), sac kaplama ≈ 4920 m²."""
    b, v = cozumler["celik-sanayi-4hol"]
    T = tb.bina_tablolari(b, v, kati=True)
    mc = [r["degerler"] for r in tb.tablo(T, "metraj_celik")["satirlar"]]
    ih = sum(r["kutle"] for r in mc if r["profil"] in yv.PROFILLER)
    assert ih / 1000 == pytest.approx(90.5, rel=0.02)
    vute = [r for r in mc if r["profil"].endswith("+ vute")]
    boru = [r for r in mc if r["profil"].startswith("BORU")]
    assert vute and boru and all("vute gövde levhası" in r["g_kaynak"] for r in vute)
    for r in vute:                   # temel profil g·L + üçgen gövde levhası (0,4 m × 2 m / 2 × t_w × 7850)
        assert r["kutle"] == pytest.approx(r["g"] * r["L"] + 0.5 * 0.4 * 2.0 * yv.PROFILLER["IPE 400"]["tw"] / 1000 * 7850)
    assert all(r["g"] == pytest.approx(25.17, abs=0.01) and r["cevre"] == pytest.approx(math.pi * 0.1683) for r in boru)
    assert not [r for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] != "Temel"]
    oz = {r["degerler"]["kalem"]: r["degerler"]["miktar"] for r in tb.tablo(T, "metraj_ozet")["satirlar"]}
    assert oz["Çatı kaplaması (sac / panel)"] + oz["Cephe kaplaması (sac / panel)"] == pytest.approx(4920, rel=0.01)
    pr = {r["degerler"]["profil"] for r in tb.tablo(T, "metraj_profil_ozeti")["satirlar"]}
    assert {"IPE 400", "IPE 400 + vute", "BORU 168.3x6.3", "HEA 320"} <= pr
    assert any(r["degerler"]["parametre"].startswith("Vute") for r in tb.tablo(T, "metraj_varsayimlari")["satirlar"])


def test_genel_model_beton_metraji_aks_kat_ile_ayni(genellestirilmis):
    """Genelleştirilmiş betonarme-2kat-3x2 (çubuk/panel) betonu surum 1 metrajıyla aynı (kolon b·h·(H − t), kiriş b·(h − t)·L_net,
    döşeme alan·t, tekil temel B·L·h)."""
    g, v = genellestirilmis

    def beton(T):
        d = {}
        for r in tb.tablo(T, "metraj_betonarme")["satirlar"]:
            d[r["degerler"]["tur"]] = d.get(r["degerler"]["tur"], 0.0) + r["degerler"]["beton"]
        return d
    b1, b3 = beton(tb.bina_tablolari(yapi.bina_sablon("betonarme-2kat-3x2"), kati=True)), beton(tb.bina_tablolari(g, v, kati=True))
    assert sum(b3.values()) == pytest.approx(sum(b1.values()), rel=0.10)
    assert set(b3) == set(b1) == {"Kolon", "Kiriş", "Döşeme", "Temel"}
    for tur in b1:
        assert b3[tur] == pytest.approx(b1[tur], rel=0.02), tur
    T = tb.bina_tablolari(g, v, kati=True)
    assert tb.tablo(T, "duvar_yukleri")["satirlar"] and tb.tablo(T, "metraj_celik") is None


def test_genel_model_betonarme_vute(genellestirilmis):
    """Betonarme vute (temel dikdörtgen kesit): kesit tablosunda 'None' profil yok, birim ağırlık temel malzemeden; metrajda kiriş
    betonuna üçgen vute gövdesi b·Δh·boy/2 eklenir (çelik metrajına girmez)."""
    g, _ = genellestirilmis
    g = copy.deepcopy(g)
    kir = next(c for c in g["cubuklar"] if c["tur"] == "kiris")
    temel = kir["kesit"]
    T0 = tb.bina_tablolari(g, kati=True)
    g["kesitler"]["VUTE-BA"] = {"tip": "vute", "temel": temel, "ek_yukseklik": 0.2, "boy": 1.0}
    kir["kesit"] = "VUTE-BA"
    T = tb.bina_tablolari(g, kati=True)
    _sema_dogrula(T)
    ks = next(r["degerler"] for r in tb.tablo(T, "kesitler")["satirlar"] if r["degerler"]["ad"] == "VUTE-BA")
    assert ks["profil"] == f"vute 200 mm (temel {temel})" and ks["malzeme"] == g["kesitler"][temel]["malzeme"]
    assert ks["g"] == pytest.approx(next(r["degerler"]["g"] for r in tb.tablo(T, "kesitler")["satirlar"] if r["degerler"]["ad"] == temel))

    def satir(T_):
        return next(r["degerler"] for r in tb.tablo(T_, "metraj_betonarme")["satirlar"]
                    if r["degerler"]["tur"] == "Kiriş" and r["degerler"]["no"] == kir["no"])
    b_ = g["kesitler"][temel]["b"]
    assert satir(T)["beton"] == pytest.approx(satir(T0)["beton"] + 0.5 * b_ * 0.2 * 1.0)
    assert "+ vute 20 cm" in satir(T)["olcu"] and tb.tablo(T, "metraj_celik") is None


def test_karma_model_duvar_yolu_aks_kat_kirisine():
    """Aks–kat kirişli + serbest çubuklu (karma) model genel okuyucuyla okunur; kirişten çevrilen çubuğun duvarı o kirişin kaydında
    düzenlenir (cubuklar listesindeki başka bir çubuğa yazılmaz)."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["cubuklar"] = [{"no": 1, "tur": "capraz", "i": {"aks": ["A", "1"], "kat": 0}, "j": {"aks": ["B", "2"], "kat": 1}, "kesit": "S40x40"}]
    T = tb.bina_tablolari(b, kati=True)
    _sema_dogrula(T)
    sat = [r for r in tb.tablo(T, "duvar_yukleri")["satirlar"] if r["degerler"]["duvar"]]
    assert sat and all(r["yol"]["duvar"][0] == "kirisler" for r in sat)
    r = sat[0]
    yeni = tb.degisiklikleri_uygula(b, [{"yol": r["yol"]["h_duvar"], "deger": 1.25}])
    kno = r["yol"]["duvar"][1]["no"]
    assert next(k for k in yeni["kirisler"] if k["no"] == kno)["duvar_h"] == 1.25 and "duvar_h" not in yeni["cubuklar"][0]


def test_genel_model_temel_basinclari_ek_aks_sistemi(cozumler):
    """Ek aks sistemindeki temel kaydı (motor 'sistem' alanı) aks adında sistem önekiyle gösterilir."""
    b, v = cozumler["celik-cbf-3kat"]
    v = copy.deepcopy(v)
    v["akis"]["temeller"][0]["sistem"] = "KANAT"
    sat = tb.tablo(tb.bina_tablolari(b, v, kati=True), "temel_basinclari")["satirlar"]
    aks = "".join(map(str, v["akis"]["temeller"][0]["aks"]))
    assert sat[0]["degerler"]["aks"] == f"KANAT:{aks}" and sat[1]["degerler"]["aks"] == "".join(map(str, v["akis"]["temeller"][1]["aks"]))


def test_genel_model_panel_ruzgari_tablosu(cozumler):
    """Panel yöntemli rüzgâr (sanayi): varsayılan 'C = 1,2' satırı yerine panel başına q(z) ve c_p, yön başına toplam kuvvet; kat yöntemi
    (cbf) eski satırları korur."""
    b, v = cozumler["celik-sanayi-4hol"]
    rz = v["ruzgar"]
    assert rz["yontem"] == "panel"
    for vv in (v, None):
        T = tb.bina_tablolari(b, vv, kati=True)
        kr = {r["degerler"]["parametre"]: r for r in tb.tablo(T, "kar_ruzgar")["satirlar"]}
        assert "C (basınç + emme)" not in kr and "Yöntem: panel basıncı p = c_p·q(z) (panel normaline)" in kr
        panel = [p for p in kr if p.startswith("Panel P")]
        assert len(panel) == len(rz["paneller"])
        assert next(p for p in panel if p.startswith("Panel P1 ")).startswith("Panel P1 (çatı): q(z = ")      # tür Türkçe
        p1 = kr[next(p for p in panel if p.startswith("Panel P1 "))]
        assert p1["degerler"]["deger"] == rz["paneller"][0]["q"] and "c_p W+X" in p1["degerler"]["kaynak"]
        assert kr["Toplam W+X: F_X / F_Y / F_Z"]["degerler"]["deger"] == pytest.approx(rz["toplam"]["W+X"][0], rel=1e-6)
        assert "yol" not in p1
    yd = {r["degerler"]["ad"]: r["degerler"] for r in tb.tablo(tb.bina_tablolari(b, v), "yuk_durumlari")["satirlar"]}
    assert yd["W"]["toplam"] == pytest.approx(max(abs(rz["toplam"]["W+X"][0]), abs(rz["toplam"]["W+Y"][1])))
    b2, v2 = cozumler["celik-cbf-3kat"]
    kr = {r["degerler"]["parametre"] for r in tb.tablo(tb.bina_tablolari(b2, v2), "kar_ruzgar")["satirlar"]}
    assert "C (basınç + emme)" in kr and not any(p.startswith("Panel P") for p in kr)


def test_genel_model_temel_basinclari_acik_mesnet(cozumler):
    """B'siz akis.temeller satırı (açık mesnet; eski çözüm) taban basıncına girmez; N_temel yoksa γ·B·L·h."""
    b, v = cozumler["celik-cbf-3kat"]
    v = copy.deepcopy(v)
    for t in v["akis"]["temeller"]:
        t.pop("N_temel", None)
    n = len(v["akis"]["temeller"])
    v["akis"]["temeller"].append({"dugum": 1001, "kolon_no": None, "aks": None, "tip": "mafsal", "N_G": 5.0, "N_Q": 1.0, "MX": 0.0, "MY": 0.0})
    T = tb.bina_tablolari(b, v, kati=True)
    sat = [r["degerler"] for r in tb.tablo(T, "temel_basinclari")["satirlar"]]
    assert len(sat) == n
    assert all(d["N_temel"] == pytest.approx(yapi.GAMMA_BA * d["B"] * d["L"] * 0.7) for d in sat)
    assert len([r for r in tb.tablo(T, "metraj_betonarme")["satirlar"] if r["degerler"]["tur"] == "Temel"]) == n


def test_genel_model_panel_ek_yuku_tablosu():
    """Panel ek yükü {tur: 'panel', panel, durum, p} Ek Yükler tablosunda 'p' sütunuyla, durum ve p düzenlenebilir."""
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["ek_yukler"] = list(b.get("ek_yukler") or []) + [{"tur": "panel", "panel": 2, "durum": "S", "p": 0.5}]
    T = tb.bina_tablolari(b, kati=True)
    _sema_dogrula(T)
    ek = tb.tablo(T, "ek_yukler")
    r = ek["satirlar"][-1]
    assert r["degerler"]["hedef"] == "Panel 2" and r["degerler"]["p"] == 0.5 and r["degerler"]["durum"] == "S"
    i = len(b["ek_yukler"]) - 1
    assert r["yol"] == {"p": ["ek_yukler", i, "p"], "durum": ["ek_yukler", i, "durum"]}
    assert "p" not in {s_["ad"] for s_ in tb.tablo(tb.bina_tablolari(yapi.bina_sablon("celik-cbf-3kat")), "ek_yukler")["sutunlar"]}


def test_genel_model_okuma_hatasi_yalniz_kendi_okuyucusundan():
    """Model denetimi satırı yalnız genel model okuyucusu (yapi_serbest) başarısız olursa yazılır; mesaj o okuyucunundur."""
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["cubuklar"][0]["kesit"] = "YOK"
    T = tb.bina_tablolari(b)
    md = next(r["degerler"] for r in tb.tablo(T, "genel")["satirlar"] if r["degerler"]["parametre"] == "Model denetimi")
    with pytest.raises(Exception) as h:
        YS._oku(copy.deepcopy(b))
    assert md["aciklama"] == str(h.value) and "YOK" in md["aciklama"]
    assert tb.tablo(T, "metraj_ozet")["satirlar"] == []


# ---------------------------------------------------------------------------- aks sistemi (§19)
def _aks19():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["surum"] = 3
    b["akslar"]["z"] = [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "+3.00", "konum": 3.0, "kat": 1},
                        {"ad": "+6.00", "konum": 6.0, "kat": 2}, {"ad": "Mahya", "konum": 7.5}]
    b["aks_sistemleri"] = [
        {"ad": "KANAT", "tur": "kartezyen", "orijin": [9.0, 0.0, 0.0], "aci": 90,
         "x": [{"ad": "K1", "konum": 0.0}, {"ad": "K2", "konum": 4.0}], "y": [{"ad": "a", "konum": 0.0}, {"ad": "b", "konum": 3.0}], "z": None},
        {"ad": "KUBBE", "tur": "silindirik", "orijin": [4.5, 2.0, 6.0], "aci": 0,
         "r": [{"ad": "R1", "konum": 2.0}], "teta": [{"ad": "T1", "konum": 0}, {"ad": "T2", "konum": 90}],
         "z": [{"ad": "taban", "konum": 0.0}, {"ad": "tepe", "konum": 1.5}]}]
    b["dugumler"] = [{"no": 100001, "tur": "bolme", "cubuk_i": {"aks": ["A", "1"], "z": "+6.00"}, "cubuk_j": {"aks": ["B", "1"], "z": "+6.00"}, "oran": 0.25},
                     {"no": 100002, "aks": ["B", "1"], "z": "Mahya"},
                     {"no": 100003, "tur": "kesisim", "a": [{"aks": ["A", "1"], "kat": 1}, {"aks": ["C", "2"], "kat": 1}],
                      "b": [{"aks": ["A", "2"], "kat": 1}, {"aks": ["C", "1"], "kat": 1}]}]
    b["cubuklar"] = [{"no": 1, "tur": "makas-ust", "i": {"aks": ["A", "1"], "z": "+6.00"}, "j": {"dugum": 100002}, "kesit": "K25x50"},
                     {"no": 2, "tur": "capraz", "i": {"sistem": "KANAT", "aks": ["K2", "b"], "z": "±0.00"}, "j": {"sistem": "KANAT", "aks": ["K1", "a"], "z": "+3.00"}, "kesit": "K25x50"},
                     {"no": 3, "tur": "diger", "i": {"sistem": "KUBBE", "aks": ["R1", "T1"], "z": "taban"}, "j": {"sistem": "KUBBE", "aks": ["R1", "T2"], "z": "tepe"}, "kesit": "K25x50"}]
    return b


def test_aks_sistemi_tablolari_ve_ref_koordinatlari():
    b = _aks19()
    T = tb.bina_tablolari(b, kati=True)
    _sema_dogrula(T)
    ak = tb.tablo(T, "akslar")
    satir = {(r["degerler"]["sistem"], r["degerler"]["yon"], r["degerler"]["ad"]): r for r in ak["satirlar"]}
    assert ("GLOBAL", "Z", "Mahya") in satir and ("KUBBE", "θ", "T2") in satir and ("KANAT", "X", "K2") in satir
    z3 = satir[("GLOBAL", "Z", "+3.00")]
    assert z3["degerler"]["kat"] == 1 and z3["yol"]["konum"] == [["akslar", "z", {"ad": "+3.00"}, "konum"], ["katlar", {"no": 1}, "kot"]]
    assert z3["bag"]["ad"] == {"islem": "aks_ad", "yon": "z", "sistem": None}
    assert satir[("GLOBAL", "X", "B")]["degerler"]["aralik"] == 5.0
    assert satir[("GLOBAL", "X", "A")]["degerler"]["bagli"] > 10
    sis = {r["degerler"]["ad"]: r for r in tb.tablo(T, "aks_sistemleri")["satirlar"]}
    assert set(sis) == {"GLOBAL", "KANAT", "KUBBE"} and "yol" not in sis["GLOBAL"]
    assert sis["KANAT"]["yol"]["aci"] == ["aks_sistemleri", {"ad": "KANAT"}, "aci"] and sis["KANAT"]["bag"]["ad"] == {"islem": "sistem_ad"}
    dg = {r["degerler"]["no"]: r["degerler"] for r in tb.tablo(T, "dugumler")["satirlar"]}
    assert dg[1001]["aks_adresi"] == "A-1 @ +3.00"
    assert (dg[100001]["X"], dg[100001]["Z"]) == (pytest.approx(1.25), pytest.approx(6.0)) and dg[100001]["tur"] == "bölme"
    assert dg[100002]["aks_adresi"] == "B-1 @ Mahya" and dg[100002]["Z"] == 7.5
    assert (dg[100003]["X"], dg[100003]["Y"], dg[100003]["Z"]) == (pytest.approx(4.5), pytest.approx(2.0), pytest.approx(3.0))
    c = tb._Baglam(b, None)
    # KANAT: orijin (9, 0), 90° döndürülmüş: yerel (4, 3) → global (9 − 3, 4)
    assert c.ref_koordinat({"sistem": "KANAT", "aks": ["K2", "b"], "z": "+3.00"}) == (pytest.approx(6.0), pytest.approx(4.0), 3.0)
    # KUBBE silindirik: R = 2, θ = 90° → (4.5, 4.0); kendi Z aksı + orijin Z 6
    assert c.ref_koordinat({"sistem": "KUBBE", "aks": ["R1", "T2"], "z": "tepe"}) == (pytest.approx(4.5), pytest.approx(4.0), pytest.approx(7.5))
    assert c.aks_adresi(6.0, 4.0, 3.0) == "KANAT:K2-b @ +3.00"
    cub = {r["degerler"]["no"]: r["degerler"] for r in tb.tablo(T, "cubuklar")["satirlar"] if r["degerler"]["tur"] not in ("kolon", "kiris")}
    assert cub[1]["i"] == "A-1 @ +6.00" and cub[1]["L"] == pytest.approx(math.hypot(5.0, 1.5))
    assert cub[2]["i"] == "KANAT:K2-b @ ±0.00" and cub[2]["L"] == pytest.approx(math.sqrt(16 + 9 + 9))
    assert cub[3]["L"] == pytest.approx(math.sqrt(2 * 2 + 2 * 2 + 1.5 ** 2))


def test_aks_yeniden_adlandirma_bagli_basvurular():
    b = _aks19()
    y = tb.degisiklikleri_uygula(b, [
        {"yol": ["akslar", "x", {"ad": "A"}, "ad"], "deger": "AA", "bag": {"islem": "aks_ad", "yon": "x", "sistem": None}},
        {"yol": ["akslar", "x", {"ad": "A"}, "konum"], "deger": -0.5},
        {"yol": ["akslar", "z", {"ad": "+6.00"}, "ad"], "deger": "Çatı", "bag": {"islem": "aks_ad", "yon": "z", "sistem": None}},
        {"yol": ["aks_sistemleri", {"ad": "KANAT"}, "ad"], "deger": "KANAT-B", "bag": {"islem": "sistem_ad"}},
        {"yol": ["aks_sistemleri", {"ad": "KANAT"}, "x", {"ad": "K1"}, "ad"], "deger": "K0", "bag": {"islem": "aks_ad", "yon": "x", "sistem": "KANAT"}},
    ])
    assert b["akslar"]["x"][0]["ad"] == "A", "girdi değişmemeli"
    assert y["akslar"]["x"][0] == {"ad": "AA", "konum": -0.5}
    assert all(k["aks"][0] != "A" for k in y["kolonlar"]) and y["kolonlar"][0]["aks"] == ["AA", "1"]
    assert all("A" not in (k["bas"][0], k["son"][0]) for k in y["kirisler"])
    assert all(d["kose"][0][0] != "A" for d in y["dosemeler"])
    assert all(o["aks"][0] != "A" for o in y["temeller"]["ozel"])
    assert y["dugumler"][0]["cubuk_i"] == {"aks": ["AA", "1"], "z": "Çatı"}
    assert y["cubuklar"][0]["i"] == {"aks": ["AA", "1"], "z": "Çatı"}
    assert y["cubuklar"][1]["j"] == {"sistem": "KANAT-B", "aks": ["K0", "a"], "z": "+3.00"}
    assert y["aks_sistemleri"][0]["ad"] == "KANAT-B" and y["aks_sistemleri"][0]["x"][0]["ad"] == "K0"
    assert y["dugumler"][2]["a"][0] == {"aks": ["AA", "1"], "kat": 1}
    B = yapi._bina_oku(y)
    assert B.ax["AA"] == 0 and B.xk[0] == -0.5
    with pytest.raises(ValueError, match="zaten var"):
        tb.degisiklikleri_uygula(b, [{"yol": ["akslar", "x", {"ad": "A"}, "ad"], "deger": "B", "bag": {"islem": "aks_ad", "yon": "x"}}])
    with pytest.raises(ValueError, match="GLOBAL"):
        tb.degisiklikleri_uygula(b, [{"yol": ["aks_sistemleri", {"ad": "KUBBE"}, "ad"], "deger": "GLOBAL", "bag": {"islem": "sistem_ad"}}])
    # Z aksı konumu (kat seviyesi) hem akslar.z hem katlar'a yazılır; kat tablosundan düzenleme de ikisine
    T = tb.bina_tablolari(b, kati=True)
    z = next(r for r in tb.tablo(T, "akslar")["satirlar"] if r["degerler"]["ad"] == "+6.00")
    y = tb.degisiklikleri_uygula(b, [{"yol": z["yol"]["konum"], "deger": 6.4}])
    assert y["akslar"]["z"][2]["konum"] == 6.4 and y["katlar"][2]["kot"] == 6.4
    kat = tb.tablo(T, "katlar")["satirlar"][1]
    y = tb.degisiklikleri_uygula(b, [{"yol": kat["yol"]["kot"], "deger": 3.3}])
    assert y["akslar"]["z"][1]["konum"] == 3.3 and y["katlar"][1]["kot"] == 3.3


# ---------------------------------------------------------------------------- rapor yardımcıları
def test_secili_tablolar_ve_hucre_metni():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    T = tb.bina_tablolari(b)
    s = tb.secili_tablolar(T, ["metraj_ozet", "yok", "doseme_yukleri"], {"doseme_yukleri": {"satirlar": [0, 2, 99]}})
    assert [t["ad"] for t in s] == ["metraj_ozet", "doseme_yukleri"]
    dy = s[1]
    tam = tb.tablo(T, "doseme_yukleri")
    assert len(dy["satirlar"]) == 2 and dy["suzuldu"] and len(tam["satirlar"]) > 2
    assert dy["toplam"]["G_toplam"] == pytest.approx(tam["satirlar"][0]["degerler"]["G_toplam"] + tam["satirlar"][2]["degerler"]["G_toplam"])
    assert tb.hucre_metni(3.14159, {"ondalik": 2}) == "3.14"
    assert tb.hucre_metni(-0.0001, {"ondalik": 2}) == "0.00"
    assert tb.hucre_metni(2.5, {}, ondalik_virgul=True) == "2,5"
    assert tb.hucre_metni(True, {}) == "✓" and tb.hucre_metni(None, {}) == ""
    assert tb.hucre_metni(None, {"secenekler": [{"deger": None, "etiket": "(duvar yok)"}]}) == ""
    assert tb.metraj_ozeti(b)["ad"] == "metraj_ozet"


# ---------------------------------------------------------------------------- köprü
@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_tablo_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def _iste(kopru, islem, girdi):
    return json.loads(kopru.calistir(json.dumps({"islem": islem, "girdi": girdi}, ensure_ascii=False)))


def test_kopru_bina_tablolar(kopru):
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    y = _iste(kopru, "bina_tablolar", {"bina": b})                     # çözümsüz
    assert y["hata"] is None and y["cozumlu"] is False and y["cozum_kimligi"] is None
    assert not any(t["grup"] in ("Analiz", "Tasarım") for t in y["tablolar"])
    c = _iste(kopru, "bina_coz", {"bina": b})
    k = c["veri"]["cozum_kimligi"]
    y = _iste(kopru, "bina_tablolar", {"cozum_kimligi": k})            # önbellekten (bina göndermeden)
    assert y["hata"] is None and y["cozumlu"] and y["cozum_kimligi"] == k
    assert any(t["grup"] == "Analiz" for t in y["tablolar"])
    _katı_json(y)
    y2 = _iste(kopru, "bina_tablolar", {"bina": json.dumps(b), "cozum_kimligi": "eski"})   # aynı bina (metin): kimlik bina'dan
    assert y2["cozumlu"] and y2["cozum_kimligi"] == k
    b2 = copy.deepcopy(b)
    b2["katlar"][2]["kot"] = 6.5                                          # düzenlenmiş bina: eski çözüm kullanılmaz
    y3 = _iste(kopru, "bina_tablolar", {"bina": b2, "cozum_kimligi": k})
    assert y3["cozumlu"] is False and tb.tablo(y3["tablolar"], "katlar")["satirlar"][2]["degerler"]["kot"] == 6.5
    y4 = _iste(kopru, "bina_tablolar", {"cozum_kimligi": "bina-yok"})
    assert y4["hata_turu"] == "girdi" and "bellekte yok" in y4["hata"]


# ---------------------------------------------------------------------------- JS (node)
def _node(*args, girdi=None, zaman=120):
    return subprocess.run([NODE, *args], input=girdi, capture_output=True, text=True, timeout=zaman, cwd=PROJE)


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_js_sozdizimi_ve_birim_testleri():
    r = _node("--check", str(JS))
    assert r.returncode == 0, r.stderr
    r = _node("--test", str(JS_TEST))
    assert r.returncode == 0, r.stdout[-5000:] + r.stderr[-2000:]
    assert "# fail 0" in r.stdout


_ESDEGER = """
const M = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const g = JSON.parse(veri);
  const out = {bina: M._ic.degisiklikleriUygula(g.bina, g.degisiklikler),
               metin: g.hucreler.map(h => M._ic.bicimle(h[0], h[1], h[2])),
               cevir: g.cevir.map(h => M._ic.degerCevir(h[0], h[1]))};
  process.stdout.write(JSON.stringify(out));
});
"""


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_python_js_esdegerligi():
    """Aynı değişiklik listesi Python (tablolar.degisiklikleri_uygula) ve JS'de (MatrisTablo._ic) aynı binayı verir; hücre metni aynı."""
    b = _aks19()
    T = tb.bina_tablolari(b, kati=True)
    degisiklikler = []
    for t, i, r, a, yol in _duzenlenebilir_hucreler(T):    # her düzenlenebilir sütundan bir örnek değişiklik
        if r.get("bag") and a in r["bag"]:
            continue
        v = r["degerler"].get(a)
        tur = (r.get("hucre") or {}).get(a, {}).get("tur") or next(s for s in t["sutunlar"] if s["ad"] == a)["tur"]
        if tur == "sayi" and isinstance(v, (int, float)) and not isinstance(v, bool):
            degisiklikler.append({"yol": yol, "deger": v + 0.25})
        elif tur == "bool":
            degisiklikler.append({"yol": yol, "deger": not v})
    degisiklikler += [
        {"yol": ["akslar", "y", {"ad": "1"}, "ad"], "deger": "1A", "bag": {"islem": "aks_ad", "yon": "y", "sistem": None}},
        {"yol": ["akslar", "z", {"ad": "Mahya"}, "ad"], "deger": "Tepe", "bag": {"islem": "aks_ad", "yon": "z", "sistem": None}},
        {"yol": ["aks_sistemleri", {"ad": "KUBBE"}, "ad"], "deger": "K2", "bag": {"islem": "sistem_ad"}},
        {"yol": ["aks_sistemleri", {"ad": "KUBBE"}, "teta", {"ad": "T1"}, "ad"], "deger": "T0", "bag": {"islem": "aks_ad", "yon": "teta", "sistem": "KUBBE"}},
        {"yol": ["temeller", "ozel", {"aks": ["C", "2"], "_olustur": True}, "L"], "deger": 2.4},
    ]
    assert len(degisiklikler) > 30
    hucreler = [[3.14159, {"ondalik": 2}, False], [-0.0001, {"ondalik": 2}, False], [12, {}, False], [2.5, {}, True], [1.23456789, {}, False],
                [1.5e-6, {}, False], [None, {}, False], [True, {}, False], [False, {}, False], [1000.0, {"ondalik": 0}, True],
                ["tugla19", {"secenekler": [{"deger": "tugla19", "etiket": "Tuğla"}]}, False], [-2.0, {}, False], [0.1 + 0.2, {}, False]]
    cevir = [["1,5", {"tur": "sayi"}], ["evet", {"tur": "bool"}], ["Çelik", {"tur": "secim", "secenekler": ["betonarme", "celik"]}]]
    r = _node("-e", _ESDEGER, str(JS), girdi=json.dumps({"bina": b, "degisiklikler": degisiklikler, "hucreler": hucreler, "cevir": cevir},
                                                          ensure_ascii=False))
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    py = tb.degisiklikleri_uygula(b, degisiklikler)
    assert js["bina"] == json.loads(json.dumps(py)), "Python ve JS değişiklik uygulaması farklı"
    assert js["metin"] == [tb.hucre_metni(v, s, ov) for v, s, ov in hucreler]
    assert js["cevir"] == [{"deger": 1.5}, {"deger": True}, {"deger": "celik"}]


def test_docs_kopyasi_ve_kabuk():
    """web_yap tablolar.py'yi docs'a kopyalar; worker isteğe bağlı yükler; servis çalışanı ve sayfa yeni dosyaları bilir."""
    assert (PROJE / "docs" / "tablolar.py").read_bytes() == (PROJE / "tablolar.py").read_bytes(), "python web_yap.py çalıştırın"
    assert '"tablolar.py"' in (PROJE / "docs" / "motor.worker.js").read_text(encoding="utf-8")
    sw = (PROJE / "docs" / "sw.js").read_text(encoding="utf-8")
    assert '"./tablolar.py"' in sw and '"./tablo_editoru.js"' in sw
    assert '<script src="tablo_editoru.js" defer></script>' in (PROJE / "docs" / "index.html").read_text(encoding="utf-8")
    assert ".tablo-ed-izgara" in (PROJE / "docs" / "style.css").read_text(encoding="utf-8")
