# -*- coding: utf-8 -*-
"""rapor.py testleri: statik hesap raporu (tasarım belgesi §14.1) ve genel tablo biçimi (§15.1 TABLO → HTML).

Bütün şablonlar için rapor üretilir; HTML etiket dengesi, 14 bölüm başlığı, dış kaynak olmaması, yazdırma düzeni, deprem
parametreleri (S_DS, R, V_tE), malzeme (f_ck), kombinasyon ifadeleri, Σ tepki korunumu, çelikte kesit sınıfı, betonarmede A_s,
proje künyesi ve kaçış, seçilen tablolar (Ek C, metraj özeti), eksik/gelecek veri alanlarına dayanıklılık denetlenir."""
from __future__ import annotations

import copy
import json
import re
import sys
import types
from html.parser import HTMLParser

import pytest

import rapor
import yapi

BOS_ETIKETLER = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Denge(HTMLParser):
    """Açılan her etiketin aynı sırayla kapandığını denetler (boş öğeler ve kendiliğinden kapanan SVG öğeleri hariç)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.yigin, self.hatalar = [], []

    def handle_starttag(self, etiket, nitelikler):
        if etiket not in BOS_ETIKETLER:
            self.yigin.append(etiket)

    def handle_startendtag(self, etiket, nitelikler):
        pass

    def handle_endtag(self, etiket):
        if etiket in BOS_ETIKETLER:
            return
        if not self.yigin or self.yigin[-1] != etiket:
            self.hatalar.append(f"</{etiket}> beklenmedik (yığın sonu: {self.yigin[-3:]}, konum {self.getpos()})")
            if etiket in self.yigin:
                while self.yigin.pop() != etiket:
                    pass
        else:
            self.yigin.pop()


def dengeli(html: str) -> None:
    d = _Denge()
    d.feed(html)
    d.close()
    assert not d.hatalar, d.hatalar[:5]
    assert not d.yigin, f"kapanmamış etiketler: {d.yigin}"


@pytest.fixture(scope="module")
def cozumler():
    return {ad: (yapi.bina_sablon(ad), yapi.bina_coz(yapi.bina_sablon(ad), anlat=False, goster="yok").veri)
            for ad in yapi.BINA_SABLONLARI}


@pytest.fixture(scope="module")
def betonarme(cozumler):
    b, v = cozumler["betonarme-3kat-3x3"]
    return b, v, rapor.statik_rapor(b, v)


@pytest.fixture(scope="module")
def celik(cozumler):
    b, v = cozumler["celik-1kat-depo"]
    return b, v, rapor.statik_rapor(b, v)


def metin(html: str) -> str:
    """Etiketsiz düz metin (sayı/simge aramaları için); tablo hücreleri " | " ile ayrılır."""
    html = re.sub(r"</t[dh]>", " | ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).replace("&nbsp;", " ")


# ---------------------------------------------------------------------------
# genel yapı
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", list(yapi.BINA_SABLONLARI))
def test_butun_sablonlar(cozumler, ad):
    b, v = cozumler[ad]
    h = rapor.statik_rapor(b, v)
    assert h.startswith("<!DOCTYPE html>") and '<html lang="tr">' in h and h.rstrip().endswith("</html>")
    dengeli(h)
    for no, baslik in rapor.BOLUM_BASLIKLARI.items():
        if no == 1:
            assert "STATİK HESAP RAPORU" in h
            continue
        assert re.search(rf'<section class="bolum[^"]*" id="b{no}"><h2><span class="no">{no}\.</span>{re.escape(baslik)}</h2>', h), baslik
        assert f'<a href="#b{no}">{baslik}</a>' in h          # bağlantılı içindekiler
    for ek in ("Ek A — Düğüm koordinatları", "Ek B — Çubuk bağlantı tablosu"):
        assert ek in h
    assert "eğitim amaçlıdır, resmî proje yerine geçmez" in h
    # kendi içinde tam: dış kaynak, betik, dış stil yok; gömülü CSS + A4 yazdırma düzeni
    assert "<script" not in h.lower() and "<link" not in h.lower() and "@import" not in h
    assert not re.search(r'(src|href)="(https?:)?//', h)
    assert "<style>" in h and "@media print" in h and "size:A4" in h and "break-before:page" in h and "counter(page)" in h
    # Ek A: aks adresli düğümler; Ek B: bütün FE elemanları
    for d in v["ag"]["dugumler"][:5]:
        assert f"<td>{d['adres']}</td>" in h
    assert h.count("<tr>") > len(v["ag"]["elemanlar"])
    assert "Bu belge eğitim amaçlıdır" in h


def test_bolum_sirasi_sabit(betonarme):
    _, _, h = betonarme
    konumlar = [h.index(f'id="b{no}"') for no in range(1, 15)] + [h.index('id="ekA"'), h.index('id="ekB"')]
    assert konumlar == sorted(konumlar)
    assert h.index('id="icindekiler"') < h.index('id="b2"')


# ---------------------------------------------------------------------------
# içerik: parametreler ve hesaplar
# ---------------------------------------------------------------------------
def test_deprem_parametreleri(betonarme):
    _, v, h = betonarme
    d = v["deprem"]
    m = metin(h)
    assert "<i>S</i><sub>DS</sub>" in h and "<i>S</i><sub>D1</sub>" in h and "<i>V</i><sub>tE</sub>" in h
    assert f"= {rapor._f(d['SDS'], 4)}" in m and f"= {rapor._f(d['SD1'], 4)}" in m        # S_DS = S_S·F_S = … = 1.2
    assert f"{rapor._f(d['R'], 2)} / {rapor._f(d['D'], 2)}" in m                              # R / D
    assert f"{rapor._f(d['X']['VtE'], 2)} kN" in m and f"{rapor._f(d['m_t'], 2)}·" in m       # V_tE = m_t·S_aR·g
    assert "0.04·" in m and rapor._f(d["X"]["VtE_min"], 2) in m                               # alt sınır
    assert "Δ<i>F</i><sub>NE</sub>" in h and "<i>θ</i><sub>II</sub>" in h and "<i>η</i><sub>bi</sub>" in h
    # satır içi SVG spektrum: iki eğri ve T_p işareti
    svg = h[h.index("<svg"):h.index("</svg>")]
    assert svg.count("<polyline") == 2 and "Tp = " in svg and 'viewBox="0 0' in svg
    for k in d["katlar"]:                                                                      # kat tablosu F_iE, V_i
        assert rapor._f(k["F_x"], 2) in m and rapor._f(k["V_x"], 2) in m


def test_malzeme_ve_kesitler(betonarme, celik):
    _, v, h = betonarme
    m = metin(h)
    assert "<i>f</i><sub>ck</sub>" in h and "<i>f</i><sub>cd</sub>" in h and "<i>f</i><sub>ctd</sub>" in h
    assert "| 30 MPa |" in m and "fcd | fck/γmc = 30/1.5 | 20 MPa |" in m                       # C30/37: f_cd = f_ck/γ_mc
    assert "<i>E</i><sub>c</sub>" in h and "<i>f</i><sub>yd</sub>" in h and "fyk/γms = 420/1.15 | 365.22 MPa" in m
    assert "S45x45" in h and "K25x55" in h and "Çatlamış kesit (etkin) rijitlikleri" in h and "TBDY 2018 Tablo 4.2" in h
    _, _, hc = celik
    mc = metin(hc)
    assert "<i>F</i><sub>y</sub>" in hc and "275 MPa" in mc and "IPE 300" in hc and "HEB 240" in hc


def test_yukler_ve_birlesimler(betonarme):
    _, v, h = betonarme
    m = metin(h)
    assert "TS 498:2021 md. 15.1 Çizelge 6" in h                          # hareketli yük kaynağı
    assert "<i>S</i><sub>k</sub>" in h and "<i>W</i> = <i>C</i>·<i>q</i>(<i>z</i>)·<i>A</i>" in h
    # kombinasyon ifadeleri (tam katsayılı)
    assert "1.4·G + 1.6·Q" in h
    assert "G + Q + 0.2·S + (EX+) + 0.3·(EY+) + 0.3·EZ" in h
    assert "0.9·G + 1.3·(W+X)" in h
    assert "TS 500 Denk. (6.3)" in h and "TBDY 2018 md. 4.4.4.1 Denk. (4.11)" in h
    uygulanan = sum(1 for k in v["kombinasyonlar"] if k["uygulandi"])
    assert f"Uygulanan birleşim sayısı: <b>{uygulanan}</b>" in h
    assert m.count("uygulanmadı") >= sum(1 for k in v["kombinasyonlar"] if not k["uygulandi"])


def test_sigma_tepki_korunumu(betonarme):
    _, v, h = betonarme
    i = h.index("Korunum denetimi")
    tablo = h[i:h.index("</table>", i)]
    satirlar = re.findall(r"<tr>(.*?)</tr>", tablo)[1:]
    assert len(satirlar) == len(v["durumlar"]) == 12
    for s in satirlar:
        assert "✔" in s and "✘" not in s, metin(s)
    G = v["yukler"]["toplam"]["G"]
    assert rapor._f(G, 3) in metin(satirlar[0]) and "(0; 0; " in metin(satirlar[0])
    # mesnet tepkileri tablosunun Σ satırı: Σ R_Z = toplam G
    i = h.index("Durum G (sabit yük)")
    tablo = h[i:h.index("</table>", i)]
    assert metin(tablo[tablo.index("<tfoot>"):]).startswith(f"Σ | | 0 | 0 | {rapor._f(G, 3)} |")
    assert "Yük akışı korunumu" in h and "kolon tabanları ΣN" in h


def test_betonarme_kesit_hesaplari(betonarme):
    _, v, h = betonarme
    m = metin(h)
    i11, i12 = h.index('id="b11"'), h.index('id="b12"')
    b11 = h[i11:i12]
    assert "<i>A</i><sub>s,gerekli</sub>" in b11 and "<i>ρ</i><sub>min</sub>" in b11 and "<i>V</i><sub>cr</sub>" in b11
    assert "<i>N</i><sub>dm</sub> ≤ 0.40<i>f</i><sub>ck</sub><i>A</i><sub>c</sub>" in b11 and "<i>e</i><sub>min</sub> = 15 mm + 0.03<i>h</i>" in b11
    kir = next(e for e in v["tasarim"]["elemanlar"] if e["tur"] == "kiris")
    assert kir["ozet"]["oneri_ust"] in b11 and kir["ozet"]["etriye"] in b11
    # her kontrol satırı: formül → yerine konmuş değerler → sonuç ✔/✘
    assert b11.count('class="kontrol"') >= 5 and "Formül → yerine konmuş değerler" in b11
    assert "✔" in b11
    # varsayılan "kritik": her türde en büyük 5 (+ D/C > 1)
    assert b11.count('<div class="eleman">') == 10
    assert "Modelde çelik eleman yok" in h[i12:h.index('id="b13"')]
    assert "Bütün betonarme elemanların kontrol satırları" in m


def test_celik_kontrolleri(celik):
    _, v, h = celik
    b12 = h[h.index('id="b12"'):h.index('id="b13"')]
    assert "Kesit sınıfı (ÇYTHYE md. 5.4.1, Tablo 5.1A/5.1B)" in h and "kompakt" in h
    for parca in ("<i>L</i><sub>p</sub>", "<i>L</i><sub>r</sub>", "<i>C</i><sub>b</sub>", "<i>M</i><sub>n</sub>", "<i>F</i><sub>cr</sub>",
                  "<i>P</i><sub>n</sub>", "<i>KL</i>/<i>i</i>", "Bileşik etki (Denk. 11.1", "Kesme (güçlü eksen)"):
        assert parca in b12, parca
    assert "YDKT" in b12 and "φ<sub>b</sub>" in b12
    assert "Modelde betonarme eleman yok" in h[h.index('id="b11"'):h.index('id="b12"')]


def test_temel_ve_sonuc(betonarme):
    _, v, h = betonarme
    b13 = h[h.index('id="b13"'):h.index('id="b14"')]
    t = max(v["akis"]["temeller"], key=lambda x: x["DC"])
    assert "σ<sub>maks</sub>" in b13 and rapor._f(t["sigma_max"], 2) in metin(b13) and "Belirleyici temel" in b13
    b14 = h[h.index('id="b14"'):h.index('id="ekA"')]
    assert "D/C dağılımı" in b14 and "D/C &gt; 1 olan eleman yok" in b14 and "Genel değerlendirme" in b14
    assert rapor._f(v["tasarim"]["en_buyuk_dc"], 3) in b14


# ---------------------------------------------------------------------------
# seçenekler, künye, kaçış
# ---------------------------------------------------------------------------
def test_proje_kunyesi_ve_kacis(cozumler):
    b, v = cozumler["betonarme-2kat-3x2"]
    proje = {"ad": "<script>alert('x')</script> Konut", "yer": "Atatürk Cad. No: 5", "il": "İzmir", "ilce": "Bornova",
             "ada": "123", "parsel": "45", "malik": "A & B Ltd.", "hazirlayan": "Ayşe Yılmaz", "kontrol": "Mehmet Demir",
             "tarih": "01.02.2026"}
    h = rapor.statik_rapor(b, v, secenek={"proje": proje, "program_surumu": "Matris Öğren <deneme>"})
    dengeli(h)
    assert "<script" not in h and "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt; Konut" in h
    for x in ("Atatürk Cad. No: 5", "İzmir / Bornova", "123 / 45", "A &amp; B Ltd.", "Ayşe Yılmaz", "Mehmet Demir", "01.02.2026",
              "Matris Öğren &lt;deneme&gt;"):
        assert x in h, x
    assert "<title>Statik Hesap Raporu — &lt;script&gt;" in h
    assert rapor.dosya_adi(b, v, {"proje": {"ad": "Örnek Büro Binası"}}) == "statik_rapor_ornek_buro_binasi.html"
    assert rapor.dosya_adi(b, v).startswith("statik_rapor_2_katli_betonarme_konut")


def test_bolum_ve_detay_secimi(cozumler):
    b, v = cozumler["betonarme-3kat-3x3"]
    h = rapor.statik_rapor(b, v, secenek={"bolumler": [3, 9, "B"], "eleman_detay": "yok"})
    dengeli(h)
    assert 'id="b1"' in h and 'id="b3"' in h and 'id="b9"' in h and 'id="ekB"' in h
    assert 'id="b7"' not in h and 'id="b11"' not in h and 'id="ekA"' not in h
    h = rapor.statik_rapor(b, v, secenek={"bolumler": [11], "eleman_detay": "hepsi"})
    assert h.count('<div class="eleman">') == len(v["tasarim"]["elemanlar"])
    h = rapor.statik_rapor(b, v, secenek={"bolumler": [11], "eleman_detay": "yok"})
    assert h.count('<div class="eleman">') == 0 and "Ayrıntılı hesap seçilmedi" in h
    with pytest.raises(TypeError):
        rapor.statik_rapor(b, v, secenek=["proje"])


def test_json_metni_ve_bos_veri():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    v = yapi.bina_coz(b, anlat=False, goster="yok").veri
    h = rapor.statik_rapor(json.dumps(b), json.dumps(v))
    dengeli(h)
    assert "Yapı genel bilgileri" in h and "S-A1/k1" in h
    for bos in (({}, {}), (None, None), ("{bozuk", "[]")):
        h = rapor.statik_rapor(*bos)
        dengeli(h)
        assert rapor.UYGULANMADI in h and h.count("<h2>") >= 15


def test_tasarim_modulu_yokken(cozumler, monkeypatch):
    b, v = cozumler["betonarme-2kat-3x2"]
    v = {k: x for k, x in v.items() if k != "tasarim"}
    monkeypatch.setattr(rapor, "_tasarim_modulu", lambda: None)
    h = rapor.statik_rapor(b, v)
    dengeli(h)
    assert "tasarım modülü yüklenmedi" in h and "Kesit tahkiki yapılmadı" in h


# ---------------------------------------------------------------------------
# gelecek şema alanları: surum 3 (aks sistemleri, çubuk/panel, kren), veri.temel (§13)
# ---------------------------------------------------------------------------
def test_surum3_kren_temel_dayanikli(cozumler):
    b, v = cozumler["betonarme-2kat-3x2"]
    b3, v3 = copy.deepcopy(b), copy.deepcopy(v)
    b3["surum"] = 3
    b3["akslar"]["z"] = [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Saçak", "konum": 6.0, "kat": 2}, {"ad": "Mahya", "konum": 7.5}]
    b3["aks_sistemleri"] = [{"ad": "KANAT-B", "tur": "kartezyen", "orijin": [30, 0, 0], "aci": 30, "x": [{"ad": "A", "konum": 0}],
                             "y": [{"ad": "1", "konum": 0}], "z": None}]
    b3["cubuklar"] = [{"no": 1, "i": {"aks": ["A", "1"], "kat": 1}, "j": {"aks": ["B", "2"], "kat": 2}, "tur": "capraz",
                       "kesit": "K25x50", "serbest": {"i": ["My", "Mz"], "j": ["My", "Mz"]}, "yalniz_cekme": True}]
    b3["paneller"] = [{"no": 1, "tur": "cati", "kalinlik": 0.0, "g": 0.35, "q": 0.75, "kullanim": "cati-gezilmeyen", "kar": True,
                       "dagitim": "iki"}]
    b3["kren"] = [{"no": 1, "yol": [11, 12], "tekerlek": {"P_maks": 80, "P_min": 25, "H_yanal": 8, "H_fren": 6, "aralik": 3.5, "adet": 2},
                   "dinamik": 1.25, "konum_sayisi": 9}]
    b3["temeller"] = {"tip": "radye", "zemin": {"q_em": 200, "k0": 20000, "gamma": 18},
                      "radye": {"h": 0.8, "tasma": 1.0, "ag": 0.5, "kiris": {"b": 0.5, "h": 1.2}}}
    v3["temel"] = {"tip": "radye", "p_maks": 123.4, "p_min": 40.0, "q_em": 200.0, "DC_zemin": 0.617, "oturma_maks_mm": 6.17,
                   "farkli_oturma": 0.0011,
                   "dugumler": [{"no": 1, "X": 0.0, "Y": 0.0, "w_mm": 6.17, "p_kNm2": 123.4}],
                   "elemanlar": [{"no": 1, "tur": "radye-serit", "kaynak": {"yon": "x"}, "enb": {"N": 1.0, "V": 22.5, "M": 31.25, "T": 0.0},
                                  "M": [0.0, 31.25]}],
                   "tasarim": [{"ad": "S-B1 zımbalama", "kontroller": [{"ad": "Zımbalama Vpd ≤ Vpr", "formul": "Vpd ≤ γ fctd up d",
                                                                      "adimlar": ["up = 3.6 m"], "talep": 512.0, "kapasite": 800.0,
                                                                      "dc": 0.64, "birim": "kN", "kaynak": "TS 500 md. 8.3",
                                                                      "saglandi": True}]}],
                   "uyarilar": ["<b>radye</b> uyarısı"], "gelecek_alan": {"x": 1}}
    v3["durumlar"]["K"] = v3["durumlar"]["Q"]
    h = rapor.statik_rapor(b3, v3, secenek={"eleman_detay": "hepsi"})
    dengeli(h)
    m = metin(h)
    assert "surum 3" in m and "Mahya" in h and "KANAT-B" in h and "Ek aks sistemleri" in h
    assert "6.6 Kren yükleri" in h and "80 kN" in m and "Dinamik katsayı" in h and "Bu modelde kren yükü yok" not in h
    assert "kren (tekerlek yükleri" in h                                      # K durumu adı
    assert "Radye temel boyutları" in h and "123.4" in m and "0.617" in m and "S-B1 zımbalama" in h and "TS 500 md. 8.3" in h
    assert "&lt;b&gt;radye&lt;/b&gt; uyarısı" in h and "gelecek_alan" in h
    assert "yalnız çekme" in m and "My, Mz" in m                                 # uç serbestliği tablosu
    hb = rapor.statik_rapor(b, v)
    assert "Bu modelde kren yükü yok" in hb


# ---------------------------------------------------------------------------
# tablolar: tablo_html (§15.1) ve Ek C / metraj özeti
# ---------------------------------------------------------------------------
def sahte_tablo(ad="kesit_kontrol", grup="Tasarım", n_sutun=3):
    sut = [{"ad": "eleman", "baslik": "Eleman", "tur": "metin"}]
    sut += [{"ad": f"s{i}", "baslik": f"Değer {i}", "birim": "kN", "tur": "sayi", "ondalik": 2} for i in range(n_sutun)]
    sut += [{"ad": "dc", "baslik": "D/C", "tur": "sayi", "ondalik": 3}, {"ad": "uygun", "baslik": "Uygun", "tur": "bool"}]
    sat = [{"degerler": {"eleman": "<K1>", **{f"s{i}": 10.0 + i for i in range(n_sutun)}, "dc": 1.25, "uygun": False}},
           {"degerler": {"eleman": "K2", **{f"s{i}": 1.0 / 3 for i in range(n_sutun)}, "dc": 0.5, "uygun": True}},
           {"degerler": {"eleman": "K3", "dc": None}}]
    return {"ad": ad, "baslik": f"Sahte {ad}", "grup": grup, "sutunlar": sut, "satirlar": sat,
            "toplam": {"eleman": "Toplam", "s0": 99.5}, "aciklama": "Açıklama <i>", "kaynak": "TS 500 md. 7"}


def test_tablo_html():
    h = rapor.tablo_html(sahte_tablo())
    dengeli(h)
    assert "<h4>Sahte kesit_kontrol <span class=\"grup\">(Tasarım)</span></h4>" in h
    assert "&lt;K1&gt;" in h and "Açıklama &lt;i&gt;" in h and "Kaynak: TS 500 md. 7" in h
    assert '<span class="birim">[kN]</span>' in h and ">10.00<" not in h and ">10<" in h and ">0.33<" in h
    assert 'class="s asim">1.25<' in h and "✔" in h and "—" in h
    assert "<tfoot><tr><td>Toplam</td>" in h and ">99.5<" in h
    h = rapor.tablo_html(sahte_tablo(), satirlar=[1])
    assert "&lt;K1&gt;" not in h and "K2" in h
    genis = rapor.tablo_html(sahte_tablo(n_sutun=14))                       # 17 sütun → yatay parçalar, ilk sütun yinelenir
    assert genis.count("<table") == 2 and genis.count("&lt;K1&gt;") == 2 and "Sütunlar 1/2" in genis
    assert "Tabloda sütun yok" in rapor.tablo_html({"ad": "x"})
    assert "Tabloda satır yok" in rapor.tablo_html({"ad": "x", "sutunlar": [{"ad": "a"}], "satirlar": []})


def test_ek_c_ve_metraj(cozumler):
    b, v = cozumler["betonarme-2kat-3x2"]
    metraj = sahte_tablo("metraj_beton", "Metraj")
    h = rapor.statik_rapor(b, v, secenek={"ek_tablolar": [sahte_tablo(), metraj], "tablo_filtre": {"metraj_beton": {"satirlar": [1]}}})
    dengeli(h)
    assert '<a href="#ekC">Ek C — Seçilen tablolar</a>' in h and '<a href="#metraj">Metraj özeti</a>' in h
    konum = [h.index('id="b14"'), h.index('id="metraj"'), h.index('id="ekA"'), h.index('id="ekB"'), h.index('id="ekC"')]
    assert konum == sorted(konum)
    ekc = h[h.index('id="ekC"'):]
    assert "Sahte kesit_kontrol" in ekc and "Sahte metraj_beton" not in ekc and "Metraj özeti" in ekc
    mtr = h[h.index('id="metraj"'):h.index('id="ekA"')]
    assert "Sahte metraj_beton" in mtr and "K2" in mtr and "&lt;K1&gt;" not in mtr        # satır süzgeci
    # tablo seçilmezse Ek C ve metraj bölümü yok
    h0 = rapor.statik_rapor(b, v)
    assert 'id="ekC"' not in h0 and 'id="metraj"' not in h0


def test_tablolar_modulu(cozumler, monkeypatch):
    b, v = cozumler["betonarme-2kat-3x2"]
    monkeypatch.setitem(sys.modules, "tablolar", None)                    # modül yok → not
    h = rapor.statik_rapor(b, v, secenek={"tablolar": ["dugumler"]})
    dengeli(h)
    assert "tablo modülü (tablolar.py) bu kurulumda yok" in h and 'id="ekC"' in h
    sahte = types.ModuleType("tablolar")
    cagri = []

    def bina_tablolari(bina, veri=None):
        cagri.append((bina, veri))
        return [sahte_tablo("dugumler", "Model"), sahte_tablo("metraj_ozet", "Metraj"), sahte_tablo("kat_kutle", "Deprem")]

    sahte.bina_tablolari = bina_tablolari
    monkeypatch.setitem(sys.modules, "tablolar", sahte)
    h = rapor.statik_rapor(b, v, secenek={"tablolar": ["dugumler", "metraj_ozet", "yok_boyle"]})
    dengeli(h)
    assert cagri and cagri[0][1] is v
    assert "Sahte dugumler" in h and "Sahte kat_kutle" not in h and "Tablo bulunamadı: yok_boyle" in h
    assert "Sahte metraj_ozet" in h[h.index('id="metraj"'):h.index('id="ekA"')]

    def bozuk(bina, veri=None):
        raise ValueError("deneme")

    sahte.bina_tablolari = bozuk
    h = rapor.statik_rapor(b, v, secenek={"tablolar": ["dugumler"]})
    assert "Seçilen tablolar üretilemedi: ValueError: deneme" in h


# ---------------------------------------------------------------------------
# genel model (surum 3, yapi_serbest): kesitler, panel yükleri, panel rüzgârı, korunum, çelik ayrıntısı, temel
# ---------------------------------------------------------------------------
GENEL = ["celik-cbf-3kat", "celik-sanayi-4hol"]


@pytest.fixture(scope="module")
def genel_raporlar(cozumler):
    return {ad: rapor.statik_rapor(*cozumler[ad]) for ad in GENEL}


def bolum(h: str, no) -> str:
    """Bölüm HTML'i (b<no> … sonraki bölüm)."""
    i = h.index(f'id="b{no}"')
    return h[i:h.index("</section>", i)]


@pytest.mark.parametrize("ad", GENEL)
def test_genel_kesitler_betonarme_tablosunda_celik_yok(cozumler, genel_raporlar, ad):
    _, v = cozumler[ad]
    h = genel_raporlar[ad]
    dengeli(h)
    b5 = bolum(h, 5)
    kes = v["kutuphane_ozeti"]["kesitler"]
    celik = [a for a, k in kes.items() if k["tip"] in ("profil", "basit", "vute")]
    assert celik and {"CAPRAZ-V", "CAPRAZ-X"} & set(celik) or {"VUTE", "CATI-CAPRAZ"} <= set(celik)
    i = b5.find("Dikdörtgen (betonarme) kesitler")
    if i >= 0:
        rc = b5[i:b5.index("</table>", i)]
        for a in celik:
            assert f"<b>{a}</b>" not in rc, a
    assert "Çelik basit kesitler (kutu/boru/korniyer/U)" in b5
    i = b5.index("Çelik basit kesitler")
    m = metin(b5[i:b5.index("</table>", i)])
    assert "BORU 168.3x6.3" in m and "| 125.2 |" in m and "| 5.73 |" in m          # W_el = I/(D/2), i = √(I/A) (b·h²/6 değil)
    assert "794.5" not in m
    if ad == "celik-sanayi-4hol":
        assert "+ vute: ek yükseklik 400 mm" in b5 and "temel MERTEK" in b5
    b3 = metin(bolum(h, 3))
    assert "Kolon / kiriş / döşeme sayısı" not in b3 and "Çubuk sayısı (türe göre)" in b3
    n = len(v["ag"]["cubuklar"])
    assert f"| {n}: kolon " in b3
    if ad == "celik-cbf-3kat":
        assert "Toplam döşeme alanı (döşeme panelleri) | 648 m²" in b3 and "Panel sayısı (türe göre) | 18: döşeme 18" in b3


@pytest.mark.parametrize("ad", GENEL)
def test_genel_panel_ve_cubuk_yukleri(cozumler, genel_raporlar, ad):
    _, v = cozumler[ad]
    b6 = bolum(genel_raporlar[ad], 6)
    m = metin(b6)
    assert "6.2 Panel yükleri ve çubuklara dağıtım" in b6 and "6.3 Çubuk yük dökümü" in b6
    assert "Modelde aks–kat döşemesi yok" not in b6 and "Aks–kat kirişi yok" not in b6 and "Paneller (surum 3)" not in b6
    p = v["yukler"]["paneller"][0]
    assert f"Panel yükleri ({len(v['yukler']['paneller'])} panel)" in b6 and rapor._f(p["G_toplam"], 2) in m
    assert "Kenar payları (panel → çubuk)" in b6
    k = next(k for k in p["kenarlar"] if k["pay"] > 0)
    assert f"Ç{k['cubuklar'][0]}" in b6
    if len(v["yukler"]["cubuklar"]) > 60:
        assert f"{len(v['yukler']['cubuklar'])} çubuktan G + Q + S toplamı en büyük 30 çubuk gösterildi" in m
    rz = b6[b6.index("6.5 Rüzgâr"):b6.index("6.6 Kren")]
    assert "Kayıt yok" not in rz and "C = –" not in metin(rz)
    if v["ruzgar"]["yontem"] == "panel":
        assert "Panel basınç katsayıları" in rz and "Yön başına toplam rüzgâr kuvveti" in rz
        assert metin(rz).count("| çatı |") + metin(rz).count("| cephe |") == len(v["ruzgar"]["paneller"])
        assert "Şekil 1" in rz
    if v.get("kren"):
        kr = metin(b6[b6.index("Kren çözüm özeti"):b6.index("6.7 Ek yükler")])
        assert ", ".join(v["kren"]["durumlar"][:3]) in kr and "durumlarK1" not in kr.replace(" ", "")


@pytest.mark.parametrize("ad", GENEL)
def test_genel_korunum_ruzgar_tepkisi_ve_cubuk_ayrintisi(cozumler, genel_raporlar, ad):
    _, v = cozumler[ad]
    h = genel_raporlar[ad]
    b10 = bolum(h, 10)
    i = b10.index("Korunum denetimi")
    tablo = b10[i:b10.index("</table>", i)]
    for s in re.findall(r"<tr>(.*?)</tr>", tablo)[1:]:
        assert "✔" in s and "– | – | –" not in metin(s), metin(s)
    i = b10.index("Yük akışı korunumu")
    kor = metin(b10[i:b10.index("</table>", i)])
    assert "| paneller |" in kor and "| çubuk öz ağırlığı |" in kor and "döşemeler" not in kor and "kiriş öz" not in kor
    assert rapor._f(v["akis"]["korunum"]["G"]["paneller"], 3) in kor
    if v["ruzgar"]["yontem"] == "panel":
        assert "panel rüzgârı" in metin(b10).lower() and "kat kesmesi uygulanmaz" in b10
        assert "Rüzgâr taban kesmesi" in b10
    b12 = bolum(h, 12)
    assert "Denk. 9.8b" in b12                                     # I profil kolon/kiriş ayrıntılı ÇYTHYE hesabı
    assert "(güçlü / zayıf eksen)" in b12
    b14 = metin(bolum(h, 14))
    assert f"Modelde {len(v['tasarim']['elemanlar'])} çubuk kesit tahkikinden" in b14 and "(kiriş ve kolon)" not in b14


def test_genel_beklenen_tepki_panel_ruzgari(cozumler):
    _, v = cozumler["celik-sanayi-4hol"]
    r = rapor._Rapor({}, v, {})
    for ad in ("W+X", "W-X", "W+Y", "W-Y"):
        F = v["ruzgar"]["toplam"][ad]
        R, metin_ = r.beklenen_tepki(ad)
        assert (R["FX"], R["FY"], R["FZ"]) == pytest.approx((-F[0], -F[1], -F[2]))
        assert "panel basınçları" in metin_
        S = r.tepki_toplami(v["durumlar"][ad])
        assert (S["FX"], S["FY"], S["FZ"]) == pytest.approx((R["FX"], R["FY"], R["FZ"]), abs=1e-2)


def test_genel_temel_bolumu(cozumler):
    b, v = cozumler["celik-cbf-3kat"]
    b13 = bolum(rapor.statik_rapor(b, v), 13)
    m = metin(b13)
    assert "Ntemel –" not in m and " + – = " not in m
    t = max(v["akis"]["temeller"], key=lambda x: x["DC"])
    assert f"+ {rapor._f(yapi.GAMMA_BA * t['B'] * t['L'] * t['h'], 2)} = {rapor._f(t['N_servis'], 2)} kN" in m
    # açık (temelsiz) mesnet: tekil temel tablosuna girmez, ayrı tabloda; N_temel yoksa γ·B·L·h
    v2 = copy.deepcopy(v)
    for x in v2["akis"]["temeller"]:
        x.pop("N_temel", None)
    v2["akis"]["mesnetler"] = [{"dugum": 1001, "adres": "A1/+3.50", "tip": "mafsal", "N_G": 12.5, "N_Q": 3.0, "MX": 0.0, "MY": 0.0}]
    h2 = rapor.statik_rapor(b, v2)
    dengeli(h2)
    b13 = bolum(h2, 13)
    assert "Açık mesnet tepkileri" in b13 and "A1/+3.50" in b13 and "12.5" in metin(b13)
    assert rapor._f(yapi.GAMMA_BA * t["B"] * t["L"] * t["h"], 1) in metin(b13)
    # eski çözüm: B'siz akis.temeller satırı açık mesnet sayılır
    v3 = copy.deepcopy(v)
    v3["akis"]["temeller"].append({"dugum": 1001, "kolon_no": None, "aks": None, "tip": "mafsal", "N_G": 7.0, "N_Q": 1.0, "MX": 0, "MY": 0})
    b13 = bolum(rapor.statik_rapor(b, v3), 13)
    i = b13.index("13.1 Tekil temeller")
    j = b13.index("Açık mesnet tepkileri")
    assert j > i and "| 1001 |" in metin(b13[j:]) and "| 7 |" in metin(b13[j:])
    assert b13[i:b13.index("</table>", i)].count("<tr>") - 1 == len(v["akis"]["temeller"])       # başlık satırı + temeller
    # genel modelde mütemadi/radye analizi yok: geometri yerine açık not
    b4 = copy.deepcopy(b)
    b4["temeller"]["tip"] = "radye"
    b13 = bolum(rapor.statik_rapor(b4, v), 13)
    assert "Mütemadi/radye temel analizi bu çözümde yapılmadı (genel model: kolon tabanları tekil mesnet)." in b13
    assert "Radye temel boyutları" not in b13


def test_genel_eski_veri_ile_aks_kat_raporu_degismez(cozumler):
    """Aks–kat (surum 1/2) çözümüyle rapor eski bölümleri korur: 'Kolon / kiriş / döşeme sayısı', döşeme ve kiriş yük dökümü."""
    b, v = cozumler["betonarme-2kat-3x2"]
    h = rapor.statik_rapor(b, v)
    assert "Kolon / kiriş / döşeme sayısı" in h and "6.2 Döşeme yükleri (G, Q) ve kirişlere aktarım" in h and "6.3 Kiriş yük dökümü" in h
    assert "Panel yükleri ve çubuklara dağıtım" not in h and "Çelik basit kesitler" not in h
    assert "Yük akışı korunumu (döşeme → kiriş → kolon → temel)" in h and "(kiriş ve kolon)" in h
