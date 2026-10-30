"""docs/web_kopru.py bina işlemleri: bina_coz, bina_kutuphane, bina_sablonlar, bina_sablon, bina_yuk_yolu, bina_deprem,
bina_kombinasyon, bina_eleman_tasarim, bina_rapor, bina_tablolar (genel model kimliği), bina_kesit_oner (C4), bina_eleman_bilgi (C5)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
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
            "bina_kombinasyon", "bina_eleman_tasarim", "bina_rapor", "bina_tablolar", "bina_alan", "bina_kesit_oner"} <= kopru.BINA_ISLEMLER
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


# ---------------------------------------------------------------------------
# genel model (surum 3) köprü işlemleri: kesit önerisi (C4), tablolar kimliği, eleman bilgi paketi (C5), tahkik eşlemesi (C7),
# rapor (kısaltılmamış tasarım satırları)
# ---------------------------------------------------------------------------
_C4_ALANLARI = {"cubuk", "tur", "kesit", "oneri", "sistem", "malzeme", "b", "h", "kaynak", "dc_once", "dc_oneri", "dc_sonra", "degisim",
                "uygula"}


def test_kesit_oner_aks_kat_yalniz_kimlik(kopru):
    """surum 1 çözümünün kimliğiyle kesit önerisi: genel motorla bir kez yeniden çözülüp önbelleğe alınır; D/C önce, tasarım
    tablosunda görünen aks–kat D/C'si (eskiden 'bina ya da çözüm kimliği gerekir' hatası; ρ satırından D/C 1,00)."""
    kopru._BINA_ONBELLEK.clear()
    kopru._GENEL_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-2kat-3x2")})["veri"]
    kimlik = v["cozum_kimligi"]
    tablo = {(k["tur"], k["no"]): k["dc"] for k in v["tasarim"]["elemanlar"]}
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": kimlik, "hedef": [{"tur": "kolon", "no": 1}, {"tur": "kiris", "no": 1}]})
    assert y["hata"] is None and y["cozum_kimligi"] == kimlik and isinstance(y["uyarilar"], list)
    o = y["oneriler"][0]
    assert _C4_ALANLARI <= set(o) and o["kaynak"] == {"aks_kat": "kolon", "no": 1} and o["sistem"] == "betonarme"
    assert o["dc_once"] == pytest.approx(tablo[("kolon", 1)]) and o["dc_once"] == pytest.approx(0.233, abs=0.001)
    assert o["dc_oneri"] is not None and o["degisim"] in ("büyüt", "küçült", "aynı", "donatı")      # K1: "donatı" (yalnız ρ)
    if o["degisim"] != "aynı":
        u = o["uygula"]
        assert set(u) >= {"ad", "tanim", "yeni"} and u["tanim"]["tip"] == "dikdortgen"
        assert u["tanim"]["b"] == o["b"] and u["tanim"]["h"] == o["h"]
    assert y["oneriler"][1]["dc_once"] == pytest.approx(tablo[("kiris", 1)])
    assert kimlik in kopru._GENEL_ONBELLEK                      # ikinci tıklama yeniden çözmez
    g = kopru._GENEL_ONBELLEK[kimlik]
    y2 = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": kimlik, "hedef": [{"tur": "kolon", "no": 1}]})
    assert y2["oneriler"][0] == y["oneriler"][0] and kopru._GENEL_ONBELLEK[kimlik] is g
    # mütemadi temel: genel motor da gerçek temelle (Winkler ağı) çözer; eskiden tekil temel mesnetleriyle, uyarıyla
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-3kat-surekli-temel")})["veri"]
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": v["cozum_kimligi"], "hedef": [{"tur": "kolon", "no": 5}]})
    assert y["hata"] is None and not any("tekil temel mesnetleriyle" in u for u in y["uyarilar"])
    assert y["oneriler"][0]["dc_once"] == pytest.approx(next(k["dc"] for k in v["tasarim"]["elemanlar"]
                                                             if k["tur"] == "kolon" and k["no"] == 5))
    g = kopru._GENEL_ONBELLEK[v["cozum_kimligi"]]
    assert g["B"].temeller["tip"] == "surekli" and g["alan"]["ag"]["temel"] is not None


def test_kesit_oner_aks_kat_uygula_tabloda_yeterli(kopru):
    """surum 1 kolon önerisi gerekli boyuna donatı oranını uygula tanımına yazar (aks–kat motoru verilmeyen ρ'yu 0,01 alır):
    öneri uygulanıp aks–kat motoruyla çözülünce kolonun tablo D/C'si ≤ 1. Eskiden betonarme-3kat-3x3'te 30x30 önerisi
    uygulanınca D/C 2,17 'donatı artır' görünürdü (öneri ρ = 0,04'e kadar taranmış D/C ile 0,98 derdi)."""
    kopru._BINA_ONBELLEK.clear()
    kopru._GENEL_ONBELLEK.clear()
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    v = iste(kopru, "bina_coz", {"bina": b})["veri"]
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": v["cozum_kimligi"], "hedef": [{"tur": "kolon", "no": 1}]})
    o = y["oneriler"][0]
    u = o["uygula"]
    assert y["hata"] is None and o["degisim"] == "küçült" and o["dc_oneri"] <= 1.0
    assert o["donati_orani"] > 0.01 and u["tanim"]["donati_orani"] == pytest.approx(o["donati_orani"]) and "ρ" in u["ad"]
    b["kesitler"][u["ad"]] = u["tanim"]
    next(k for k in b["kolonlar"] if k["no"] == 1)["kesit"] = u["ad"]
    z = iste(kopru, "bina_coz", {"bina": b})
    assert z["hata"] is None
    k1 = next(k for k in z["veri"]["tasarim"]["elemanlar"] if k["tur"] == "kolon" and k["no"] == 1)
    assert k1["kesit"] == u["ad"] and k1["dc"] <= 1.0 and k1["durum"] == "yeterli"


def test_kesit_oner_yalniz_donati_uygula_kesin(kopru):
    """K1 'donatı' (aks–kat çözüm kimliğiyle): b × h yeterli, ρ yetmiyor → uygula {ad 'B30x30-ρ%2.00', tanım = mevcut kart +
    donati_orani}. ρ rijitliği değiştirmediğinden uygulanınca aks–kat tablosunun D/C'si öneridekiyle aynıdır. Eskiden degisim
    'aynı', uygula null: arayüzde Uygula düğmesi yoktu ve Hepsini uygula kolonu atlardı (KO-1)."""
    kopru._BINA_ONBELLEK.clear()
    kopru._GENEL_ONBELLEK.clear()
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["kesitler"]["S45x45"].update({"b": 0.3, "h": 0.3})
    v = iste(kopru, "bina_coz", {"bina": b})["veri"]
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": v["cozum_kimligi"], "hedef": [{"tur": "kolon", "no": 1}]})
    o = y["oneriler"][0]
    assert y["hata"] is None and o["degisim"] == "donatı" and o["dc_once"] > 1.5 and o["dc_oneri"] <= 1.0
    u = o["uygula"]
    assert u == {"ad": "B30x30-ρ%2.00", "tanim": dict(b["kesitler"]["S45x45"], donati_orani=0.02), "yeni": True}
    b["kesitler"][u["ad"]] = u["tanim"]
    next(k for k in b["kolonlar"] if k["no"] == 1)["kesit"] = u["ad"]
    z = iste(kopru, "bina_coz", {"bina": b})["veri"]
    k1 = next(k for k in z["tasarim"]["elemanlar"] if k["tur"] == "kolon" and k["no"] == 1)
    assert k1["kesit"] == u["ad"] and k1["dc"] == pytest.approx(o["dc_oneri"], rel=1e-4) and k1["durum"] == "yeterli"


_S1_SABLONLAR = [s["ad"] for s in yapi.bina_sablonlar() if yapi.bina_sablon(s["ad"]).get("surum", 1) < 3]


@pytest.mark.parametrize("ad", _S1_SABLONLAR)
def test_kesit_oner_hepsini_uygula_aks_kat_yeterli(kopru, ad):
    """K1 'Hepsini uygula' (yinele 3) + aks–kat motoruyla yeniden çözüm: en büyük D/C ≤ 1, ya da yanıt açık '… turda yakınsamadı'
    uyarısı taşır. Eskiden (yinele 1, grup kartı b·h ile seçilip ρ düşerdi, ρ-only değişiklik hiç uygulanmazdı) 2kat 1,09,
    radye 1,26 (16 kolon) çıkar ve arayüz 'uygulandı' derdi."""
    b = yapi.bina_sablon(ad)
    v = iste(kopru, "bina_coz", {"bina": b})["veri"]
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": v["cozum_kimligi"], "bina": b, "hedef": "hepsi", "yinele": 3})
    assert y["hata"] is None and y["bina"] is not None and y["bina"].get("surum", 1) < 3
    assert "mevcut iç kuvvetlerle tahmin" in y["aciklama"]
    z = iste(kopru, "bina_coz", {"bina": y["bina"]})
    assert z["hata"] is None
    dc = z["veri"]["tasarim"]["en_buyuk_dc"]
    assert dc <= 1.0 or any("turda yakınsamadı" in u for u in y["uyarilar"]), (ad, dc, y["turlar"])
    assert y["dc_sonra"] == pytest.approx(dc, abs=0.01)           # genel motorun son çözümü ≈ aks–kat tablosu
    for t in y["turlar"][1:]:                                     # onarım turları küçültmez
        assert all(d["degisim"] in ("büyüt", "donatı") for d in t.get("degisen") or [])
    # turlarda eklenip kullanılmayan kesit kartı kalmaz; yakınsayınca ρ yalnız azalır ve kart kullanılır
    yb = y["bina"]
    kullanilan = {e["kesit"] for a in ("kolonlar", "kirisler") for e in yb.get(a) or []}
    assert set(yb["kesitler"]) <= kullanilan | set(b["kesitler"])
    for d in y["donati_azaltma"]:
        assert d["donati_orani"] < d["rho_once"] and d["yeni"] in kullanilan and d["kesit"] not in yb["kesitler"]
    # öneriler yalnız D/C'ye göre seçilir (0. tur küçültür): aks–kat çözümünde göreli kat ötelemesini yeni aşan kat varsa yanıt
    # bunu söyler (eskiden 3kat-3x3 'yakınsadı' derken X yönünde bütün katlarda öteleme sınırı aşılırdı, uyarısız). Genel motorun
    # karşılaştırması tekil temelli çözümledir: mütemadi/radye şablonlarında aks–kat katları farklı olabilir, yalnız tekil denetlenir.
    if (b.get("temeller") or {}).get("tip", "tekil") == "tekil":
        asan = lambda vv: {yn: {k["kat"] for k in (vv.get("deprem") or {}).get("katlar") or [] if k.get(f"uygun_{yn}") is False}  # noqa: E731
                           for yn in "xy"}
        a0, a1 = asan(v), asan(z["veri"])
        yeni = {yn: sorted(a1[yn] - a0[yn]) for yn in "xy" if a1[yn] - a0[yn]}
        u = [x for x in y["uyarilar"] if "göreli kat ötelemesi" in x]
        if yeni:
            assert len(u) == 1 and all(f"{yn.upper()} yönü kat {', '.join(map(str, k))}" in u[0] for yn, k in yeni.items()), (ad, yeni, u)
        else:
            assert not u, (ad, u)


def test_kesit_oner_genel_model_c4(kopru):
    kopru._BINA_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("celik-cbf-3kat")})["veri"]
    tablo = {k["cubuk"]: k["dc"] for k in v["tasarim"]["elemanlar"]}
    y = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": v["cozum_kimligi"], "hedef": [{"tur": "cubuk", "no": 32}, {"tur": "cubuk", "no": 1}]})
    assert y["hata"] is None and y["uyarilar"] == []
    o32, o1 = y["oneriler"]
    for o in (o32, o1):
        assert _C4_ALANLARI <= set(o) and o["sistem"] == "celik" and o["kaynak"] is None and o["malzeme"]
        assert o["dc_once"] == pytest.approx(tablo[o["cubuk"]])            # tasarım tablosundaki D/C (narinlik satırı hariç)
    assert o32["degisim"] == "aynı" and o32["uygula"] is None and o32["dc_oneri"] == pytest.approx(o32["dc_once"])
    assert o1["degisim"] in ("büyüt", "küçült") and o1["dc_oneri"] <= 1.0
    u = o1["uygula"]
    assert u["yeni"] and u["tanim"] == {"tip": "profil", "profil": o1["oneri"], "malzeme": o1["malzeme"]}
    b = yapi.bina_sablon("celik-cbf-3kat")                     # uygula: tanım eklenip ad atanınca model çözülür
    b["kesitler"][u["ad"]] = u["tanim"]
    b["cubuklar"][0]["kesit"] = u["ad"]
    z = iste(kopru, "bina_coz", {"bina": b})
    assert z["hata"] is None and next(k for k in z["veri"]["tasarim"]["elemanlar"] if k["cubuk"] == 1)["kesit"] == u["ad"]


def test_kesit_oner_vute_uygula(kopru):
    """Vute çubuğunda öneri yeni bir vute kartı (temel profili değişen) ve temel profil kartını (ek_kesitler) verir."""
    b = yapi.bina_sablon("celik-sanayi-4hol")
    b["kesitler"]["MERTEK"]["profil"] = "IPE 200"                # yetersiz: büyüt
    y = iste(kopru, "bina_kesit_oner", {"bina": b, "hedef": [{"tur": "cubuk", "no": 8}]})
    assert y["hata"] is None
    o = y["oneriler"][0]
    assert o["kesit"] == "VUTE" and o["degisim"] == "büyüt"
    u = o["uygula"]
    assert u["tanim"]["tip"] == "vute" and u["ad"].startswith("VUTE-") and u["tanim"]["temel"] in u.get("ek_kesitler", b["kesitler"])
    b["kesitler"].update(u.get("ek_kesitler") or {})
    b["kesitler"][u["ad"]] = u["tanim"]
    b["cubuklar"][7]["kesit"] = u["ad"]
    import yapi_serbest
    B = yapi_serbest._oku(b)                                     # yeni kesitlerle model okunur
    assert B.cubuk_no[8]["kesit"] == u["ad"] and B.kesitler[u["ad"]]["tip"] == "vute"


def test_bina_tablolar_genel_model_kimlik(kopru):
    kopru._BINA_ONBELLEK.clear()
    b = yapi.bina_sablon("celik-cbf-3kat")
    k = iste(kopru, "bina_coz", {"bina": b})["veri"]["cozum_kimligi"]
    y = iste(kopru, "bina_tablolar", {"cozum_kimligi": k, "bina": b})
    assert y["hata"] is None and y["cozumlu"] is True and y["cozum_kimligi"] == k
    b["kesitler"]["KOLON"]["profil"] = "HEB 260"                # düzenlenmiş bina: eski çözüm kullanılmaz
    y = iste(kopru, "bina_tablolar", {"cozum_kimligi": k, "bina": b})
    assert y["hata"] is None and y["cozumlu"] is False


def _bolum_bicimi(b):
    assert set(b) <= {"baslik", "tablo", "satirlar", "not", "notlar", "acilir"}, b
    if "tablo" in b:
        t = b["tablo"]
        assert t["satirlar"] and all(len(r) == len(t["basliklar"]) and all(isinstance(x, str) for x in r) for r in t["satirlar"])
    for r in b.get("satirlar") or []:
        assert len(r) == 3 and all(isinstance(x, str) for x in r)


def test_bina_eleman_bilgi(kopru):
    assert "bina_eleman_bilgi" in kopru.BINA_ISLEMLER
    kopru._BINA_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("celik-cbf-3kat")})["veri"]
    k = v["cozum_kimligi"]
    y = iste(kopru, "bina_eleman_bilgi", {"cozum_kimligi": k, "tur": "cubuk", "no": 1, "durum": "G"})
    assert y["hata"] is None and y["cozum_kimligi"] == k
    p = y["paket"]
    assert set(p["sekmeler"]) == {"ic", "yer"} and p["uyarilar"] == [] and p["fe"] == next(c["fe"] for c in v["ag"]["cubuklar"] if c["no"] == 1)
    for b in p["sekmeler"]["ic"] + p["sekmeler"]["yer"]:
        _bolum_bicimi(b)
    ist = p["sekmeler"]["ic"][0]
    assert ist["tablo"]["basliklar"][0] == "x (m)" and len(ist["tablo"]["satirlar"]) >= 21
    assert any("Uç yer değiştirmeleri" in (b.get("baslik") or "") for b in p["sekmeler"]["yer"])
    z = iste(kopru, "bina_eleman_bilgi", {"cozum_kimligi": k, "tur": "cubuk", "no": 1, "durum": "Zarf"})
    assert z["hata"] is None and z["paket"]["durum"] == "zarf+" and "not" in z["paket"]["sekmeler"]["yer"][0]
    # aks–kat çözümü: kolon (aks–kat no'su)
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("betonarme-2kat-3x2")})["veri"]
    y = iste(kopru, "bina_eleman_bilgi", {"cozum_kimligi": v["cozum_kimligi"], "tur": "kolon", "no": 1, "durum": "1.4G+1.6Q"})
    assert y["hata"] is None and y["paket"]["sekmeler"]["ic"] and y["paket"]["sekmeler"]["yer"]
    for girdi, desen in (({"cozum_kimligi": k, "tur": "panel", "no": 1}, "tur"), ({"cozum_kimligi": k, "tur": "cubuk"}, "no"),
                         ({"cozum_kimligi": "bina-yok", "tur": "cubuk", "no": 1}, "bellekte yok"),
                         ({"cozum_kimligi": v["cozum_kimligi"], "tur": "cubuk", "no": 999}, "yok")):
        h = iste(kopru, "bina_eleman_bilgi", girdi)
        assert h["hata_turu"] == "girdi" and desen in h["hata"], h


def test_genel_model_rapor_tam_tasarim(kopru, monkeypatch):
    """Büyük genel modelde yanıttaki tasarım satırları 3'e kısaltılır; rapor kısaltılmamış satırları (ic["tas_tam"]) kullanır."""
    import rapor
    kopru._BINA_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("celik-sanayi-4hol")})["veri"]
    assert v["ozet"].get("tasarim_kisaltildi") and max(len(k["kontroller"]) for k in v["tasarim"]["elemanlar"]) <= 3
    gelen = {}
    asil = rapor.statik_rapor

    def yakala(bina, veri, secenek=None):
        gelen["veri"] = veri
        return asil(bina, veri, secenek=secenek)
    monkeypatch.setattr(rapor, "statik_rapor", yakala)
    y = iste(kopru, "bina_rapor", {"cozum_kimligi": v["cozum_kimligi"], "secenek": {"eleman_detay": "yok"}})
    assert y["hata"] is None
    assert max(len(k["kontroller"]) for k in gelen["veri"]["tasarim"]["elemanlar"]) > 3
    assert max(len(k["kontroller"]) for k in kopru._BINA_ONBELLEK[v["cozum_kimligi"]]["veri"]["tasarim"]["elemanlar"]) <= 3


_GENEL_BETIK = ('const M=require(process.argv[1]);let v="";process.stdin.on("data",d=>v+=d);'
                'process.stdin.on("end",()=>{process.stdout.write(JSON.stringify(M.genellestir(JSON.parse(v)).model))});')


@pytest.mark.skipif(shutil.which("node") is None, reason="node kurulu değil")
def test_eleman_tasarim_genellestirilmis_model_eslesmesi(kopru):
    """C7: genelleştirilmiş modelde her tasarım kaydı hem (cubuk, rec.cubuk) hem (rec.tur, rec.no) ile kendi çubuğuna gider
    (eskiden kiriş 13 → çubuk 25)."""
    r = subprocess.run([shutil.which("node"), "-e", _GENEL_BETIK, str(PROJE / "docs" / "model_ops.js")],
                       input=json.dumps(yapi.bina_sablon("betonarme-2kat-3x2")), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    kopru._BINA_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": g})["veri"]
    assert v["model"] == "genel"
    k = v["cozum_kimligi"]
    for rec in v["tasarim"]["elemanlar"]:
        for tur, no in (("cubuk", rec["cubuk"]), (rec["tur"], rec["no"])):
            z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": k, "tur": tur, "no": no})
            assert z["hata"] is None and z["sonuc"]["cubuk"] == rec["cubuk"] and z["sonuc"]["dc"] == rec["dc"], (tur, no, z.get("hata"))


@pytest.mark.skipif(shutil.which("node") is None, reason="node kurulu değil")
def test_genellestirilmis_mutemadi_temel_kopru_islemleri(kopru):
    """K-1 (C11): genelleştirilmiş mütemadi temel modeli bütün köprü işlemlerinden geçer: çözüm (veri.temel), kombinasyon
    (out.temel), ısı haritası radye katmanı, temel elemanında eleman bilgisi, tasarım, rapor, tablolar, kesit önerisi."""
    b = yapi.bina_sablon("betonarme-3kat-surekli-temel")
    r = subprocess.run([shutil.which("node"), "-e", _GENEL_BETIK, str(PROJE / "docs" / "model_ops.js")], input=json.dumps(b),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    g["temeller"] = b["temeller"]
    kopru._BINA_ONBELLEK.clear()
    y = iste(kopru, "bina_coz", {"bina": g})
    assert y["hata"] is None
    v = y["veri"]
    k = v["cozum_kimligi"]
    assert v["model"] == "genel" and v["temel"]["tip"] == "surekli" and v["temel"]["tasarim"]
    km = iste(kopru, "bina_kombinasyon", {"cozum_kimligi": k, "ad": "G+Q"})
    assert km["hata"] is None and km["sonuc"]["temel"]["p_maks"] == pytest.approx(v["temel"]["p_maks"], rel=1e-6)
    for durum in ("G", "zarf+"):
        a = iste(kopru, "bina_alan", {"cozum_kimligi": k, "durum": durum})
        assert a["hata"] is None
        rd = a["alan"]["radye"]
        assert rd is not None and (len(rd["x"]), len(rd["y"])) == (25, 23)
    tem = next(e["no"] for e in v["ag"]["elemanlar"] if e["tur"] == "temel-kirisi")
    eb = iste(kopru, "bina_eleman_bilgi", {"cozum_kimligi": k, "tur": "fe", "no": tem})
    assert eb["hata"] is None and eb["paket"]["sekmeler"]["ic"]
    kolon = next(c["no"] for c in v["ag"]["cubuklar"] if c["tur"] == "kolon")
    assert iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": k, "tur": "cubuk", "no": kolon})["hata"] is None
    assert iste(kopru, "bina_eleman_bilgi", {"cozum_kimligi": k, "tur": "cubuk", "no": kolon})["hata"] is None
    rp = iste(kopru, "bina_rapor", {"cozum_kimligi": k, "secenek": {"eleman_detay": "yok"}})
    assert rp["hata"] is None and rp["html"]
    tb = iste(kopru, "bina_tablolar", {"cozum_kimligi": k, "bina": g})
    assert tb["hata"] is None and tb["cozumlu"]
    ko = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": k, "hedef": [{"tur": "cubuk", "no": kolon}]})
    assert ko["hata"] is None and ko["oneriler"] and not any("tekil temel" in u for u in ko["uyarilar"])


def test_karma_model_panel_kaynagi(kopru):
    """K-20 (C17): aks–kat döşemeleri genel modelde panel olur; veri.yukler.paneller[i].kaynak = {aks_kat: 'doseme', no} (öteki
    paneller null) — eleman bilgisi döşemeyi panele bağlar."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["mesnetler"] = [{"dugum": {"aks": ["B", "2"], "z": "Temel"}, "ux": True, "uy": True, "uz": True}]
    kopru._BINA_ONBELLEK.clear()
    v = iste(kopru, "bina_coz", {"bina": b})["veri"]
    assert v["model"] == "genel"
    pan = v["yukler"]["paneller"]
    assert pan and all("kaynak" in p for p in pan)
    assert any(p["kaynak"] == {"aks_kat": "doseme", "no": 1} for p in pan)
    assert {p["kaynak"]["no"] for p in pan if p["kaynak"]} == {d["no"] for d in b["dosemeler"]}


def test_sure_ms_bina_coz_ve_kesit_oner(kopru, yanit):
    """K-31 / C19: bina_coz ve bina_kesit_oner yanıtında üst düzey tam sayı sure_ms; bina_coz veri.ozet.cozum_sure_ms'e de yazar."""
    assert isinstance(yanit["sure_ms"], int) and yanit["sure_ms"] >= 0
    assert yanit["veri"]["ozet"]["cozum_sure_ms"] == yanit["sure_ms"]
    y = iste(kopru, "bina_kesit_oner", {"bina": yapi.bina_sablon("betonarme-2kat-3x2"), "hedef": [{"tur": "kolon", "no": 1}]})
    assert y["hata"] is None and isinstance(y["sure_ms"], int) and y["sure_ms"] >= 0
    g = iste(kopru, "bina_coz", {"bina": yapi.bina_sablon("celik-cbf-3kat")})
    assert isinstance(g["sure_ms"], int) and g["veri"]["ozet"]["cozum_sure_ms"] == g["sure_ms"]
