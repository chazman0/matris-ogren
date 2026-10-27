"""docs/web_kopru.py bina işlemleri: bina_coz, bina_kutuphane, bina_sablonlar, bina_sablon, bina_yuk_yolu, bina_deprem,
bina_kombinasyon, bina_eleman_tasarim, bina_rapor."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

import yapi

PROJE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_bina_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, islem, girdi=None, ayarlar=None):
    istek = {"islem": islem, "girdi": girdi or {}}
    if ayarlar is not None:
        istek["ayarlar"] = ayarlar
    return json.loads(kopru.calistir(json.dumps(istek)))


@pytest.fixture(scope="module")
def yanit(kopru):
    return iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-2kat-3x2")})


def test_islemler_tanimli(kopru):
    assert {"bina_coz", "bina_sablonlar", "bina_sablon", "bina_kutuphane", "bina_yuk_yolu", "bina_deprem",
            "bina_kombinasyon", "bina_eleman_tasarim", "bina_rapor", "bina_tablolar", "bina_alan"} <= kopru.BINA_ISLEMLER
    assert kopru._yapi_modulu() is not None


def test_sablonlar(kopru):
    y = iste(kopru, "bina_sablonlar")
    assert y["hata"] is None and [s["ad"] for s in y["sablonlar"]] == list(yapi.BINA_SABLONLARI)
    y = iste(kopru, "bina_sablon", {"ad": "celik-1kat-depo"})
    assert y["hata"] is None and y["bina"]["sistem"] == "celik" and y["bina"]["tur"] == "bina"
    y = iste(kopru, "bina_sablon", {"ad": "yok"})
    assert y["hata_turu"] == "girdi" and "şablonu yok" in y["hata"]


def test_kutuphane(kopru):
    y = iste(kopru, "bina_kutuphane")
    assert y["hata"] is None
    assert {"malzemeler", "kesit_katalogu", "kullanim_siniflari", "duvarlar", "kaplamalar", "kombinasyon_kumeleri", "sablonlar", "dogrulanmamis"} <= set(y)
    assert y["kesit_katalogu"]["profiller"]["HEA"][0] == "HEA 100" and y["kesit_katalogu"]["dikdortgen_onerileri"]
    assert y["kombinasyon_kumeleri"]["ts500"]["liste"][0]["ad"] == "1.4G+1.6Q"


def test_bina_coz_yaniti(kopru, yanit):
    y = yanit
    assert y["hata"] is None and y["ad"] == "bina" and y["zincir"] is False and y["sonuc_metin"]
    assert y["bloklar"] and {b["tur"] for b in y["bloklar"]} <= {"md", "math", "kod", "sema"}
    assert any(b["tur"] == "sema" and b["icerik"]["kareler"] for b in y["bloklar"])
    assert any(b["tur"] == "kod" for b in y["bloklar"])
    v = y["veri"]
    assert v["tur"] == "bina" and set(v["durumlar"]) == {"G", "Q"} and set(v["sonuclar"]) == {"1.4G+1.6Q"}
    assert v["cozum_kimligi"].startswith("bina-") and v["zarf"]["kombinasyon_sayisi"] == 2
    assert v["ozet"]["sd_sayisi"] == 108 and v["ozet"]["dugum"] == 18 and v["ozet"]["eleman"] == 26
    assert v["akis"]["kolonlar"] and v["akis"]["temeller"] and v["akis"]["sankey"]
    assert isinstance(v["ozet"]["uyarilar"], list)
    assert v["ozet"]["uyarilar"] == []      # şablon yalnız doğrulanmış değer kullanır; kullanılmayan kayıtlar uyarı değildir
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["dosemeler"][0]["kullanim"] = "depo"
    y2 = iste(kopru, "bina_coz", {"bina": b})
    assert any("TS498_HAREKETLI.depo" in u for u in y2["veri"]["ozet"]["uyarilar"])
    assert v["fe_model"]["tip"] == "cerceve3b" and v["fe_model"]["yayili"]


def test_yanit_kati_json_ve_boyut(kopru):
    ham = kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": yapi.bina_sablon("betonarme-3kat-3x3")}}))
    json.loads(ham, parse_constant=lambda c: pytest.fail(f"geçersiz JSON sabiti: {c}"))
    assert len(ham) < 1_500_000


def test_json_metni_olarak_bina(kopru):
    y = iste(kopru, "bina_coz", {"bina": json.dumps(yapi.bina_sablon("betonarme-tek-aciklik"))})
    assert y["hata"] is None and y["veri"]["ozet"]["sd_sayisi"] == 48


def test_sema_kapali(kopru):
    y = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-tek-aciklik")}, ayarlar={"sema": False})
    assert y["hata"] is None and not any(b["tur"] == "sema" for b in y["bloklar"])


def test_yuk_yolu(kopru, yanit):
    bina = yapi.bina_sablon("betonarme-2kat-3x2")
    y = iste(kopru, "bina_yuk_yolu", {"bina": bina, "veri": yanit["veri"], "hedef": {"tur": "doseme", "no": 1, "durum": "G"}})
    assert y["hata"] is None and len(y["adimlar"]) >= 4 and y["adimlar"][0]["vurgu"]["dosemeler"] == [1]
    y = iste(kopru, "bina_yuk_yolu", {"bina": bina, "hedef": {"tur": "doseme", "no": 1}})
    assert y["hata_turu"] == "girdi" and "önce" in y["hata"]


def test_hatalar(kopru):
    for girdi in ({}, {"bina": ""}, {"bina": "   "}):
        y = iste(kopru, "bina_coz", girdi)
        assert y["hata_turu"] == "girdi" and "boş" in y["hata"]
    y = iste(kopru, "bina_coz", {"bina": "{bozuk"})
    assert y["hata_turu"] == "girdi" and "JSON" in y["hata"]
    y = iste(kopru, "bina_coz", {"bina": "{" + " " * (kopru.BINA_EN_FAZLA + 5)})
    assert y["hata_turu"] == "girdi" and "uzun" in y["hata"]
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kirisler"] = b["kirisler"][:3]
    y = iste(kopru, "bina_coz", {"bina": b})
    assert y["hata_turu"] == "girdi" and "yüzen döşeme" in y["hata"] and "iz" not in y


def test_ders_kodu_yapi_ad_alani(kopru):
    y = iste(kopru, "ders_calistir", {"kod": "b = yapi.bina_sablon('betonarme-tek-aciklik')\nr = yapi.bina_coz(b, anlat=False)\nr.veri['ozet']['sd_sayisi']"})
    assert y["hata"] is None and y["sonuc_metin"] == "48"


def test_se_ve_matris_islemleri_bozulmadi(kopru):
    y = iste(kopru, "se_ornekler")
    assert y["hata"] is None and len(y["ornekler"]) == 20
    y = iste(kopru, "determinant", {"A": "1 2; 3 4"})
    assert y["hata"] is None and y["sonuc_metin"] == "-2"


# ---------------------------------------------------------------------------
# Dilim 2: bina_deprem (çözümsüz önizleme), bina_kombinasyon (tembel tam kayıt, önbellek), taşıyıcı sistemler
# ---------------------------------------------------------------------------
def hepsi_acik(ad):
    b = yapi.bina_sablon(ad)
    for d in ("S", "W", "E"):
        b["yuk_durumlari"][d]["acik"] = True
    return b


def test_bina_deprem_onizleme(kopru):
    b = yapi.bina_sablon("betonarme-2kat-3x2")          # E kapalı: önizleme yine çalışır (arayüz girdileri canlı)
    b["deprem"].update({"SS_DD3": 0.4, "S1_DD3": 0.12})
    y = iste(kopru, "bina_deprem", {"bina": b})
    assert y["hata"] is None and set(y) == {"deprem", "hata"}
    d = y["deprem"]
    assert d["tahmin"] is True and d["VtE"] > 0 and d["SDS_DD3"] > 0 and 0 < d["lambda"] < 1
    assert abs(sum(k["F_x"] for k in d["katlar"]) - d["VtE"]) < 1e-6 and d["katlar"][0]["V_x"] == d["VtE"]
    assert d["spektrum"] and isinstance(d["kaynaklar"]["SDS"], str)
    b_e = json.loads(json.dumps(b))
    b_e["yuk_durumlari"]["E"]["acik"] = True             # aynı kütle (kar kapalı)
    r = yapi.bina_coz(b_e, anlat=False).veri["deprem"]
    assert abs(d["VtE"] - r["VtE"]) < 1e-6 * r["VtE"]          # ampirik periyotlu şablonda çözümle aynı
    for girdi, desen in (({"bina": dict(b, deprem=dict(b["deprem"], zemin_sinifi="ZQ"))}, "zemin"), ({}, "boş"),
                         ({"bina": {k: v for k, v in b.items() if k != "deprem"}}, "deprem")):
        y = iste(kopru, "bina_deprem", girdi)
        assert y["hata_turu"] == "girdi" and desen in y["hata"]


def test_bina_kombinasyon_onbellek(kopru):
    kopru._BINA_ONBELLEK.clear()
    b = hepsi_acik("betonarme-2kat-3x2")
    y = iste(kopru, "bina_coz", {"bina": b})
    v = y["veri"]
    kimlik = v["cozum_kimligi"]
    assert kimlik in kopru._BINA_ONBELLEK
    k = next(k for k in v["kombinasyonlar"] if k["ad"] == "G+Q+0.2S+EX++0.3EY++0.3EZ")
    z = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": k["ad"], "katsayilar": k["katsayilar"]})
    assert z["hata"] is None and z["ad"] == k["ad"] and z["cozum_kimligi"] == kimlik
    s = z["sonuc"]
    assert s["diyagram"] is True and all(len(e["M"]) == len(e["x"]) >= 11 for e in s["elemanlar"])
    assert all(abs(x) < 1e-6 for x in s["denge"].values())
    # durumların (ince kayıt: uç kuvvetleri) katsayılı toplamıyla aynı uç kuvvetleri; deprem birleşimi G, Q, S'yi çatlamış
    # kesitli kopyalardan (G~c …, TBDY 4.5.8.3) alır — bunlar yanıtta yok, motordan tek durum olarak istenir
    assert k["catlamis"] is True
    D = dict(v["durumlar"])
    for ad in ("G", "Q", "S"):
        y = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": ad + "~c"})
        assert y["hata"] is None
        D[ad] = y["sonuc"]
    for i, e in enumerate(s["elemanlar"]):
        for j in range(12):
            top = sum(g * D[ad]["elemanlar"][i]["uc_kuvvetleri"][j] for ad, g in k["katsayilar"].items())
            assert abs(e["uc_kuvvetleri"][j] - top) < 1e-3 * max(1.0, abs(top))
    # serbest katsayılar (arayüzün kendi birleşimi), tek durum
    z = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": "deneme", "katsayilar": {"G": 1.0, "W+X": 2.0}})
    assert z["hata"] is None
    z = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": "EY-"})
    assert z["hata"] is None and len(z["sonuc"]["elemanlar"][0]["M"]) >= 11
    # hatalar
    for girdi, desen in (({"cozum_kimligi": kimlik, "ad": ""}, "boş"), ({"cozum_kimligi": kimlik, "ad": "x", "katsayilar": {"T": 1}}, "yük durumu"),
                         ({"cozum_kimligi": "bina-yok", "ad": "G"}, "bellekte yok"), ({"cozum_kimligi": kimlik, "ad": "x", "katsayilar": [1]}, "sözlük")):
        z = iste(kopru, "bina_kombinasyon", girdi)
        assert z["hata_turu"] == "girdi" and desen in z["hata"], z
    # önbellek en çok 3 çözüm; eskisi düşer, bina verilirse sessizce yeniden çözülür
    for ad in ("betonarme-tek-aciklik", "celik-1kat-depo", "betonarme-3kat-3x3"):
        iste(kopru, "bina_coz", {"bina": yapi.bina_sablon(ad)})
    assert len(kopru._BINA_ONBELLEK) == kopru.BINA_ONBELLEK_EN_FAZLA == 3 and kimlik not in kopru._BINA_ONBELLEK
    z = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": "G"})
    assert z["hata_turu"] == "girdi" and "yeniden çözün" in z["hata"]
    z = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": kimlik, "ad": "1.4G+1.6Q", "bina": b})
    assert z["hata"] is None and z["cozum_kimligi"] == kimlik and kimlik in kopru._BINA_ONBELLEK


def test_kutuphane_tasiyici_sistemler(kopru):
    y = iste(kopru, "bina_kutuphane")
    ts = y["tasiyici_sistemler"]
    assert isinstance(ts, list) and len(ts) == 10
    assert all({"ad", "etiket", "R", "D", "BYS_izin", "kaynak"} <= set(t) for t in ts)
    ad = {t["ad"]: t for t in ts}
    assert (ad["celik-merkezi-capraz"]["R"], ad["celik-merkezi-capraz"]["D"]) == (5, 2)
    assert ad["betonarme-perde-cerceve"]["etiket"].startswith("A15")


def test_hepsi_acik_yanit_boyutu_ve_json(kopru):
    for ad, sinir in (("betonarme-2kat-3x2", 550_000), ("betonarme-4kat-4x3", 1_600_000)):   # Dilim 3: tasarım + 12. adım dahil
        ham = kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": hepsi_acik(ad)}}))
        y = json.loads(ham, parse_constant=lambda c: pytest.fail(f"geçersiz JSON sabiti: {c}"))
        assert y["hata"] is None and len(ham) < sinir, (ad, len(ham))
        assert len(json.dumps(y["veri"], ensure_ascii=False)) < 1_300_000


def test_bina_eleman_tasarim(kopru):
    """Dilim 3 köprüsü: kiriş (kesit şeması anlatımda), kolon (egri_x, egri_y, noktalar), çelik; önbellek bina_kombinasyon ile aynı."""
    kopru._BINA_ONBELLEK.clear()
    y = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-2kat-3x2")})
    v = y["veri"]
    kimlik = v["cozum_kimligi"]
    assert v["tasarim"]["elemanlar"] and v["ozet"]["en_buyuk_dc"] == v["tasarim"]["en_buyuk_dc"]
    assert any(b["tur"] == "md" and "12. Adım: Kesit tahkikleri" in b["icerik"] for b in y["bloklar"])
    z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": kimlik, "tur": "kiris", "no": 1})
    assert z["hata"] is None and z["cozum_kimligi"] == kimlik and z["ad"] == "kiris 1"
    kay = next(e for e in v["tasarim"]["elemanlar"] if e["tur"] == "kiris" and e["no"] == 1)
    assert z["sonuc"]["dc"] == kay["dc"] and z["sonuc"]["ozet"] == kay["ozet"] and z["sonuc"]["kontroller"] == kay["kontroller"]
    assert any(b["tur"] == "sema" for b in z["bloklar"]) and any(b["tur"] == "math" for b in z["bloklar"])
    z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": kimlik, "tur": "kolon", "no": 2})
    s = z["sonuc"]
    assert z["hata"] is None and {"egri_x", "egri_y", "noktalar"} <= set(s)
    assert all(set(p) == {"N", "M"} for p in s["egri_x"] + s["egri_y"])
    assert all({"ad", "N", "Mx", "My", "dc"} <= set(p) for p in s["noktalar"])
    assert len(s["noktalar"]) == 2 * v["tasarim"]["kombinasyon_sayisi"]
    json.loads(json.dumps(z), parse_constant=lambda c: pytest.fail(c))
    # çelik şablon; kimlik önbellekte yoksa bina verilerek yeniden çözülür
    b = yapi.bina_sablon("celik-1kat-depo")
    z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": "bina-yok", "tur": "kolon", "no": 1, "bina": b})
    assert z["hata"] is None and z["sonuc"]["sistem"] == "celik" and 0 < z["sonuc"]["dc"] < 5 and z["sonuc"]["kuvvetler"]
    assert z["cozum_kimligi"] in kopru._BINA_ONBELLEK
    z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": z["cozum_kimligi"], "tur": "kiris", "no": 2})
    assert z["hata"] is None and z["sonuc"]["ozet"]["Lb_m"] == 0.0
    # hatalar
    for girdi, desen in (({"cozum_kimligi": kimlik, "tur": "doseme", "no": 1}, "kiris"),
                         ({"cozum_kimligi": kimlik, "tur": "kolon"}, "no"),
                         ({"cozum_kimligi": kimlik, "tur": "kolon", "no": 99}, "yok"),
                         ({"cozum_kimligi": "bina-yok", "tur": "kolon", "no": 1}, "bellekte yok")):
        z = iste(kopru, "bina_eleman_tasarim", girdi)
        assert z["hata_turu"] == "girdi" and desen in z["hata"], z


# ---------------------------------------------------------------------------
# bina_rapor: statik hesap raporu (rapor.py), önbellekteki çözümden
# ---------------------------------------------------------------------------
def test_bina_rapor(kopru, monkeypatch):
    kopru._BINA_ONBELLEK.clear()
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    v = iste(kopru, "bina_coz", {"bina": b})["veri"]
    kimlik = v["cozum_kimligi"]
    assert kopru._BINA_ONBELLEK[kimlik]["veri"]["cozum_kimligi"] == kimlik    # rapor için çözüm verisi de saklanır

    def cozme(*a, **k):
        raise AssertionError("bina_rapor önbellekteki çözümü yeniden çözmemeli")

    monkeypatch.setattr(yapi, "bina_coz", cozme)
    secenek = {"proje": {"ad": "Deneme <Konut>", "il": "Ankara", "hazirlayan": "A. Yazar"}, "eleman_detay": "yok"}
    y = iste(kopru, "bina_rapor", {"cozum_kimligi": kimlik, "secenek": secenek})
    assert y["hata"] is None and set(y) == {"html", "dosya_adi", "cozum_kimligi", "hata"}
    assert y["dosya_adi"] == "statik_rapor_deneme_konut.html" and y["cozum_kimligi"] == kimlik
    h = y["html"]
    assert h.startswith("<!DOCTYPE html>") and "Deneme &lt;Konut&gt;" in h and "A. Yazar" in h and "Ankara" in h
    assert "Deprem parametreleri (TBDY 2018)" in h and "Ek B — Çubuk bağlantı tablosu" in h and kimlik in h
    assert '<div class="eleman">' not in h and "eğitim amaçlıdır" in h
    monkeypatch.undo()
    # kimlik önbellekte yoksa model verilirse çözülür (ve önbelleğe girer); verilmezse öğretici hata
    kopru._BINA_ONBELLEK.clear()
    y = iste(kopru, "bina_rapor", {"cozum_kimligi": kimlik})
    assert y["hata_turu"] == "girdi" and "bellekte yok" in y["hata"]
    y = iste(kopru, "bina_rapor", {"bina": json.dumps(yapi.bina_sablon("celik-1kat-depo"))})
    assert y["hata"] is None and "Çelik eleman kontrolleri" in y["html"] and "HEB 240" in y["html"]
    assert y["cozum_kimligi"] in kopru._BINA_ONBELLEK
    for girdi, desen in (({}, "boş"), ({"bina": b, "secenek": ["x"]}, "sözlük")):
        y = iste(kopru, "bina_rapor", girdi)
        assert y["hata_turu"] == "girdi" and desen in y["hata"], y


def test_bina_rapor_rapor_modulu_yok(kopru, monkeypatch):
    monkeypatch.setattr(kopru, "_rapor_modulu", lambda: None)
    y = iste(kopru, "bina_rapor", {"bina": yapi.bina_sablon("betonarme-tek-aciklik")})
    assert y["hata_turu"] == "girdi" and "rapor.py" in y["hata"]
