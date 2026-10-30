# -*- coding: utf-8 -*-
"""docs/bina_cizim.js (aks tabanlı çizim, Dilim 4f 2. aşama) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/bina_cizim.test.js`` (saf mantık; node'un yerleşik test koşucusu).
- Kablolama: index.html'de bina.js'ten SONRA yüklenir (MatrisBina hazır olunca kurulur); servis çalışanı kabuğunda ve
  stil dosyasında yer alır.
- Sözleşme: serbest koordinatla düğüm üretmez (çizim kipleri yakalama sonucunun REF'ini yazar; üreteç / kopya sonuçları
  aksaBaglaHepsi'nden geçer); bütün model değişiklikleri MatrisBina.binaAyarla ile tek geri al yığınından geçer;
  araç kutusunun aks / çizim / düzenleme / değiştirme komutlarını bağlar ve bina.js'teki "sonraki aşama" listesindeki
  her komut burada karşılanır.
- Uçtan uca: SAF yük (C10: düğüm, kiriş, döşeme) ve mesnet kayıtları aks–kat şablonunda köprüden (web_kopru bina_coz) çözülür;
  G/Q toplamları yükle birlikte değişir; mesnet modeli genelleştirir (surum 3).
- Masaüstü menüsünün her araç hedefi kayıtlı bir komuttur (katalog, bina.js aracKomutlari ya da burada komutBagla); kesit
  önerisinin Uygula'sı tanımsız kesit adı atamaz; genel model kapısı (onay, iptal, rette not yok) kablolanmıştır.
node yoksa node gerektiren testler atlanır.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MODUL = PROJE / "docs" / "bina_cizim.js"
KAYNAK = MODUL.read_text(encoding="utf-8")
BINA = (PROJE / "docs" / "bina.js").read_text(encoding="utf-8")
JS_TEST = PROJE / "testler" / "js" / "bina_cizim.test.js"
NODE = shutil.which("node")

node_gerekli = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, zaman=120):
    return subprocess.run([NODE, *args], capture_output=True, text=True, timeout=zaman, cwd=PROJE)


@node_gerekli
def test_sozdizimi():
    r = _node("--check", str(MODUL))
    assert r.returncode == 0, r.stderr


@node_gerekli
def test_node_birim_testleri():
    r = _node("--test", str(JS_TEST), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


def test_index_servis_calisani_ve_stil():
    html = (PROJE / "docs" / "index.html").read_text(encoding="utf-8")
    sira = [m.group(1) for m in re.finditer(r'<script src="([^"]+)"', html)]
    assert "bina_cizim.js" in sira
    assert sira.index("aks_sistemi.js") < sira.index("bina.js") < sira.index("bina_cizim.js")
    sw = (PROJE / "docs" / "sw.js").read_text(encoding="utf-8")
    assert '"./bina_cizim.js"' in sw
    css = (PROJE / "docs" / "style.css").read_text(encoding="utf-8")
    for sinif in (".b3-cubuk", ".b3-panel", ".b3-mafsal", ".b3-yc-c", ".bc-onizleme", ".bn-duzlem", ".bc-uretec"):
        assert sinif in css, sinif


@node_gerekli
def test_araclar_bagli_ve_sonraki_asama_karsilaniyor():
    cikti = _node("-e", "process.stdout.write(JSON.stringify(require('./docs/arac_kutusu.js').KATALOG.map(k => k.id)))").stdout
    katalog = set(json.loads(cikti))
    bagla = KAYNAK[KAYNAK.index("MB.komutBagla({"):]
    bagla = bagla[:bagla.index("\n    });")]
    bagli = set(re.findall(r'(?:^|[\s{,])"?([a-z][a-z0-9-]*)"?\s*:\s*(?:secenekli|kipK|\{|aks|makas|besik|kren|dugum|function)', bagla, re.M))
    sonraki = set(re.findall(r'"([a-z0-9-]+)"', re.search(r"const SONRAKI = \[(.*?)\];", BINA, re.S).group(1)))
    # bina.js'in 2. aşamaya bıraktığı her komut (katalogda olanlar) burada bağlanır
    eksik = sorted(k for k in sonraki & katalog if k not in bagli and k not in ("aks-yapisik", "yakalama", "aks-balon", "aks-olcu"))
    assert not eksik, f"bina_cizim.js'te bağlanmayan komut: {eksik}"
    for k in ("aks-sihirbaz", "aks-ekle", "aks-sil", "aks-tasi", "aks-sistemi", "aks-gorunurluk", "cubuk-ciz", "hizli-kolon", "hizli-kiris",
              "hizli-capraz", "hizli-panel", "egik-cubuk", "makas", "besik-cerceve", "asik", "kren-yolu", "mesnet", "yuk-ata",
              "tasi", "dondur", "ayna", "dogrusal-dizi", "ozellik-ata", "mafsal", "yalniz-cekme", "bol", "kesisimde-bol",
              "duzlemle-bol", "birlestir", "dugum-birlestir", "kesit-degistir", "aci", "kesit-oner", "uretec-duzenle"):
        assert k in bagli, k


def test_serbest_koordinat_yok_ve_tek_geri_al():
    # düğümler yalnız yakalama sonucunun REF'i ya da aksa bağlanmış işlem sonucu; serbest {X, Y, Z} düğümü yazılmaz
    assert not re.search(r"dugumler\.push\(\s*\{[^}]*\bX\s*:", KAYNAK)
    assert "aksaBaglaHepsi(" in KAYNAK and "serbestleriBagla(" in KAYNAK
    assert "MB.binaAyarla(" in KAYNAK
    assert "localStorage" not in KAYNAK, "model durumu tarayıcı deposuna yazılmaz (bina.js taslağı tek kaynak)"
    # MatrisBina hazır olunca kurulur
    assert 'addEventListener("matris-bina-hazir"' in KAYNAK
    assert "matris-bina-hazir" in BINA


def test_bina_js_surum3_kablolamasi():
    for ad in ("s3Var", "aksKatModu", "duzlemSec", "duzlemGec", "zAkslari", "refKoordinat", "geometri", "motorS3", "firca", "ayarla"):
        assert re.search(r"(^|[\s,{])" + ad + r"\s*:", BINA), ad
    # surum 3 modelini çözemeyen motor için öğretici hata; genel model çözümü
    assert "S3_MOTOR_YOK" in BINA and 'veri.model !== "genel"' in BINA
    # aks–kat şablonları eskisi gibi: aks–kat kipleri aksKatModu'nda
    assert "eskiMi" in BINA



# ---------------------------------------------------------------------------------------------------------------------------
# Uçtan uca: SAF yük / mesnet kayıtları aks–kat şablonunda köprüden çözülür (ui-akskat-3, ui-akskat-1, ui-akskat-16)
_YUK_BETIGI = r"""
const BC = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const t = JSON.parse(veri);
  const k1 = t.kirisler.find(k => k.no === 1), d1 = t.dosemeler.find(d => d.no === 1);
  let m = BC.yukEkle(t, { tur: "dugum", ref: { aks: ["C", "2"], kat: 2 } }, { durum: "G", FZ: -50 }).model;
  const dugum = m;
  m = BC.yukEkle(m, { tur: "kiris", no: 1 }, { durum: "Q", q1: -3 }).model;
  const kiris = m;
  m = BC.yukEkle(m, { tur: "doseme", no: 1 }, { g: 1, q: 2 }).model;
  const mesnet = BC.mesnetAta(t, { aks: ["C", "2"], kat: 1 }, "mafsal");
  process.stdout.write(JSON.stringify({ dugum, kiris, doseme: m, mesnet: mesnet.model, genelMi: [BC.genelMi(t), BC.genelMi(m), BC.genelMi(mesnet.model)],
    kiris1: k1, doseme1: d1 }));
});
"""


@pytest.fixture(scope="module")
def kopru():
    import importlib.util
    oz = importlib.util.spec_from_file_location("web_kopru_bina_cizim_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(oz)
    oz.loader.exec_module(modul)
    return modul


def _coz(kopru, bina):
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": bina}})))
    assert y.get("hata") in (None, ""), y.get("hata")
    return y["veri"]


@node_gerekli
def test_aks_kat_yuk_ve_mesnet_kopruden_cozulur(kopru):
    import yapi
    t = yapi.bina_sablon("betonarme-2kat-3x2")
    r = subprocess.run([NODE, "-e", _YUK_BETIGI, str(MODUL)], input=json.dumps(t), capture_output=True, text=True, timeout=120, cwd=PROJE)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o["genelMi"] == [False, False, True], "aks–kat yükleri (C10) modeli genel yapmaz; mesnet genelleştirir"
    assert o["doseme"]["surum"] == t.get("surum", 1)
    assert o["doseme"]["ek_yukler"][-3:] == [
        {"tur": "dugum", "aks": ["C", "2"], "kat": 2, "durum": "G", "FZ": -50},
        {"tur": "kiris", "kiris": 1, "durum": "Q", "q": 3},
        {"tur": "doseme", "doseme": 1, "g": 1, "q": 2}]
    v0 = _coz(kopru, t)["ozet"]
    B = yapi._bina_oku(t)
    L1 = next(k["L"] for k in B.kirisler if k["no"] == 1)
    d1 = next(d for d in B.dosemeler if d["no"] == 1)
    alan = d1["dx"] * d1["dy"]
    v1 = _coz(kopru, o["dugum"])["ozet"]
    assert v1["toplam_G"] == pytest.approx(v0["toplam_G"] + 50, abs=1e-6)
    assert v1["toplam_Q"] == pytest.approx(v0["toplam_Q"], abs=1e-6)
    v2 = _coz(kopru, o["kiris"])["ozet"]
    assert v2["toplam_Q"] == pytest.approx(v0["toplam_Q"] + 3 * L1, abs=1e-6)
    v3 = _coz(kopru, o["doseme"])["ozet"]
    dG, dQ = v3["toplam_G"] - v2["toplam_G"], v3["toplam_Q"] - v2["toplam_Q"]
    assert dG == pytest.approx(1 * alan, rel=1e-6) and dQ == pytest.approx(2 * alan, rel=1e-6), (dG, dQ, alan)
    vm = _coz(kopru, o["mesnet"])
    assert vm["ozet"]["toplam_G"] == pytest.approx(v0["toplam_G"], rel=1e-3)
    assert o["mesnet"]["surum"] == 3 and o["mesnet"]["mesnetler"]


# ---------------------------------------------------------------------------------------------------------------------------
# Masaüstü menüsü → araç kutusu komutu: her hedef bir katalog kimliği, bina.js aracKomutlari anahtarı ya da bina_cizim.js
# komutBagla anahtarı olmalı (kablolama-statik-1, belge-masaustu-1: "kesit-oner" hiçbir yerde kayıtlı değildi)
def _komut_anahtarlari(blok: str) -> set[str]:
    return set(re.findall(r'^\s{6}"?([a-z][a-z0-9-]*)"?\s*:', blok, re.M))


@node_gerekli
def test_masaustu_arac_hedefleri_kayitli():
    cikti = _node("-e", "process.stdout.write(JSON.stringify(require('./docs/arac_kutusu.js').KATALOG.map(k => k.id)))").stdout
    katalog = set(json.loads(cikti))
    harita = re.search(r"const MASAUSTU_ARAC = \{(.*?)\n  \};", BINA, re.S).group(1)
    hedefler = set(re.findall(r':\s*"([a-z0-9-]+)"', harita))
    assert "kesit-oner" in hedefler
    ak = BINA[BINA.index("function aracKomutlari() {"):]
    ak = ak[:ak.index("\n    return h;")]
    bina_k = _komut_anahtarlari(ak) | set(re.findall(r'"(olc-[a-z]+)"\s*:', BINA))
    bagla = KAYNAK[KAYNAK.index("MB.komutBagla({"):]
    bagla = bagla[:bagla.index("\n    });")]
    cizim_k = _komut_anahtarlari(bagla)
    assert {"kesit-oner", "uretec-duzenle", "aks-sistemi", "mafsal"} <= cizim_k
    eksik = sorted(h for h in hedefler if h not in katalog and h not in bina_k and h not in cizim_k)
    assert not eksik, f"masaüstü menüsünün kayıtsız araç hedefleri: {eksik}"


def test_kesit_onerisi_tanimsiz_kesit_atamaz():
    # Uygula: öneri SAF oneriUygula'dan geçer (kesit tanımı eklenir, yoksa hata); ozellikAta ile doğrudan ad atanmaz
    i = KAYNAK.index("function kesitOner(hedef)")
    govde = KAYNAK[i:KAYNAK.index("\n    }\n", i)]
    assert "oneriUygula(" in govde and "ozellikAta" not in govde
    assert "oneriUygulanir" in govde, "Uygula yalnız değişiklik varken (degisim ≠ 'aynı')"
    # K1: Hepsini uygula en çok 3 tur yineler (yinele: 1 tek turda kalıp D/C > 1 bırakıyordu), uygular, yeniden çözer; aşanlar söylenir.
    # Tek yinele: 1 isteği kesit grubu isteğidir (K-32, C19: grup: true + üye listesi)
    assert "istek({ yinele: 3 })" in govde and "Hepsini uygula" in govde and "MB.binaAyarla(y2.bina" in govde
    assert govde.count("yinele: 1") == 1 and "grup: true, yinele: 1" in govde
    assert govde.count("MB.coz()") >= 3, "Hepsini, tek Uygula ve grup sonrası model yeniden çözülür"
    assert "hepsiOzeti(y2)" in govde and "öneriler yetmedi" in govde
    # motorun yinele uyarıları (öteleme sınırı, yakınsamadı nedeni) kaybolmaz; başarılı yeniden çözümde eski ⚠ ipucu kalmaz
    assert "hepsiEkUyarilari(y2, y)" in govde and "hepsiUygula(y2, y)" in govde
    assert 'S.sonUyari = oz.asiyor ? etiket : ""' in govde
    saf = KAYNAK[KAYNAK.index("function oneriKesitleriEkle("):]
    saf = saf[:saf.index("\n  }\n")]
    assert 'if (!m.kesitler[k.ad]) throw' in saf
    for ad in ("function oneriUygula(", "function grupUygula("):
        f = KAYNAK[KAYNAK.index(ad):]
        assert "oneriKesitleriEkle(m, o)" in f[:f.index("\n  }\n")], ad
    assert "oneriEtiketi(o)" in govde and "oneriSatiri(o" in govde and "uyarilar" in govde
    # motorun açıklaması (öneri mevcut iç kuvvetlerle tahmin) iki kipte de gösterilir; satır etiketi tahmini
    assert "y.aciklama" in govde and "notlar(y)" in govde
    satir = KAYNAK[KAYNAK.index("function oneriSatiri("):]
    assert "tahmini (mevcut iç kuvvetlerle)" in satir[:satir.index("\n  }\n")]


def test_genel_model_kapisi_kablolamasi():
    # Çeviren her yol önce sorar (window.confirm); iptal → model değişmez; rette "genelleştirildi" notu yazılmaz
    assert "function genelModeleGec(" in KAYNAK and "window.confirm(genelGecisMetni(" in KAYNAK
    assert '"İşlem iptal edildi."' in KAYNAK
    secimli = KAYNAK[KAYNAK.index("function secimli("):]
    secimli = secimli[:secimli.index("\n    }\n")]
    assert "genelModeleGec(" in secimli and "MOp.genellestir(" not in secimli
    # K-23: kapının ön eki işlem adıdır (GENEL_ISLEM_ADLARI), geçmiş zamanlı etiket değil
    for etiket in ('genel: tur !== "kaldir" ? GENEL_ISLEM_ADLARI.mesnet : false', 'genel: GENEL_ISLEM_ADLARI["hizli-capraz"]', 'genel: GENEL_ISLEM_ADLARI["hizli-panel"]',
                   "{ genel: duzen ? GENEL_ISLEM_ADLARI.uretec : baslik }"):
        assert etiket in KAYNAK, etiket
    # rapor reddedildiyse notlar bildirilmez (uygula: reddedildi dalı notları eklemez)
    uyg = KAYNAK[KAYNAK.index("function uygula(fn, etiket, sc)"):]
    uyg = uyg[:uyg.index("\n    }\n")]
    red = uyg[uyg.index("if (r.reddedildi)"):]
    assert "notlar" not in red[:red.index("\n")]
    assert "yeniEngeller(" in uyg and "Değişiklik yok." in uyg
    # aks–kat kolonuna yük: öğretici ret; kur(): eksik modül adı
    assert "Aks–kat kolonuna ek yük verilemez; kolonun üst düğümüne düğüm yükü verin." in KAYNAK
    assert "aks_sistemi.js (MatrisAks)" in KAYNAK and "model_ops.js (ModelOps)" in KAYNAK
    # C8 neden alanları
    assert KAYNAK.count("neden: secimNedeni") >= 7 and "Yalnız çapraz/bağ çubuklarında kullanılır" in KAYNAK
    assert 'SECIM_NEDENI = "Önce bir çubuk, kolon ya da kiriş seçin."' in KAYNAK


# ---------------------------------------------------------------------------------------------------------------------------
# Taşıyan kenar (uygula'nın engeli): SAF tasiyanKenarMi motorla aynı karar verir — taşıyan kenarı boşalan panel motorca
# reddedilir, kenar taşımayan dağıtımda çözülür; şablonda zaten var olan (taşımayan) kenar bulguları engel sayılmaz.
_KENAR_BETIGI = r"""
const BC = require(process.argv[1]);
const O = require(process.argv[2]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const t = JSON.parse(veri);
  const g = (t.kolonlar || []).length ? O.genellestir(t).model : t;
  const kenar = m => O.denetle(m).uyarilar.filter(u => u.kod === "panel-kenari");
  const once = kenar(g);
  const out = { once: once.length, onceTasiyan: once.filter(u => BC.tasiyanKenarMi(g, u)).length };
  if ((t.kolonlar || []).length) {
    // 1. kattaki ilk kiriş çubuğu kendi ucu çevresinde 180° döndürülür (koparak): komşu panellerin kenarı boşalır
    const k = g.cubuklar.find(c => c.tur === "kiris" && c.kat === 1);
    const P = O.dugumKonumu(g, k.i);
    const r = O.dondur(g, { cubuklar: [k.no] }, { nokta: P, yon: [0, 0, 1] }, 180);
    const yeni = BC.yeniEngeller(g, r.model, ["panel-kenari"]);
    out.reddedildi = !!r.reddedildi;
    out.yeni = yeni.map(u => ({ panel: u.panel, kenar: u.kenar, tasiyan: BC.tasiyanKenarMi(r.model, u) }));
    out.model = r.model;
    // aynı modelde boşalan kenarları taşımayan dağıtım (tek-13 ↔ tek-24)
    const m2 = JSON.parse(JSON.stringify(r.model));
    for (const u of yeni) { const p = m2.paneller.find(x => x.no === u.panel); p.dagitim = (u.kenar % 2) ? "tek-24" : "tek-13"; }
    out.model2 = m2;
    out.yeni2 = BC.yeniEngeller(g, m2, ["panel-kenari"]).map(u => BC.tasiyanKenarMi(m2, u));
  }
  process.stdout.write(JSON.stringify(out));
});
"""


@node_gerekli
@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "celik-sanayi-4hol"])
def test_tasiyan_kenar_motorla_ayni(ad, kopru):
    import yapi
    r = subprocess.run([NODE, "-e", _KENAR_BETIGI, str(MODUL), str(PROJE / "docs" / "model_ops.js")],
                       input=json.dumps(yapi.bina_sablon(ad)), capture_output=True, text=True, timeout=300, cwd=PROJE)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o["onceTasiyan"] == 0, "çözülen şablonda taşıyan kenar bulgusu olmamalı"
    if ad == "celik-sanayi-4hol":
        assert o["once"] > 0      # cephe / çatı panellerinin taşımayan kenarları: engel sayılmaz
        return
    assert not o["reddedildi"] and o["yeni"] and all(u["tasiyan"] for u in o["yeni"]), o["yeni"]
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": o["model"]}})))
    assert y.get("hata") and "kenarında" in y["hata"], "motor taşıyan kenarı boş paneli reddeder"
    assert o["yeni2"] and not any(o["yeni2"])
    _coz(kopru, o["model2"])


def test_genel_kapi_degisiklik_yoksa_cevirmez():
    # NEW-5: işlem genelleştirilmiş modelde hiçbir şeyi değiştirmiyorsa (ya da reddediliyorsa) model çevrilmez ve "bölündü" denmez
    secimli = KAYNAK[KAYNAK.index("function secimli("):]
    secimli = secimli[:secimli.index("\n    }\n")]
    kuru = secimli.index("genellestirHazirla(m).model")
    assert kuru < secimli.index('genelModeleGec(m, typeof sc.genel === "string" ? sc.genel : null)'), "kuru çalıştırma onaydan önce"
    assert "r0.reddedildi" in secimli and "JSON.stringify(r0.model) === JSON.stringify(m0)" in secimli
    assert "model genel modele çevrilmedi" in secimli and "cevrildi: cevrildi" in secimli
    uyg = KAYNAK[KAYNAK.index("function uygula(fn, etiket, sc)"):]
    uyg = uyg[:uyg.index("\n    }\n")]
    # ölçüt modelin kendisi: rapor degisen'i doldursa da (özellik zaten aynı) model aynıysa çevrilmez
    assert "if (cevrildi && JSON.stringify(m) === JSON.stringify(m0))" in uyg
    assert uyg.index("if (cevrildi && JSON.stringify(m)") < uyg.index("MB.binaAyarla(m,"), "çevrilmiş ama değişmemiş model uygulanmaz"
    assert "!ozet(r0)" not in secimli
    # Düzlemle böl penceresi yalnız seçimi kesen düzlemleri sunar; yoksa açılmaz
    dz = KAYNAK[KAYNAK.index("function duzlemleBolPenceresi("):]
    dz = dz[:dz.index("\n    }\n")]
    assert "kesenDuzlemler(mk, ay.cubuklar)" in dz and "Seçili çubukları kesen aks düzlemi yok" in dz


def test_aks_sil_kapisi():
    # ui-s3-13: "Bağlı elemanları en yakın aksa taşı" sonrası motorun reddettiği yeni bozukluk kaldıysa aks silinmez (uygula kapısı)
    akis = KAYNAK[KAYNAK.index("function aksSilAkisi("):]
    akis = akis[:akis.index("\n    }\n")]
    assert "aksSilEngelleri(m0, q.model)" in akis
    assert akis.index("aksSilEngelleri(m0, q.model)") < akis.index("MB.binaAyarla(q.model")
    assert "Elemanlarla birlikte sil" in akis


# ---------------------------------------------------------------------------------------------------------------------------
# K-23: kapıdan geçen her secimli() / uygula() çağrısı işlem adını (sc.genel) verir; onay metnine etiket (geçmiş zaman) girmez
def test_kapi_islem_adlari_kablolamasi():
    uyg = KAYNAK[KAYNAK.index("function uygula(fn, etiket, sc)"):]
    uyg = uyg[:uyg.index("\n    }\n")]
    assert 'genelModeleGec(m0, typeof sc.genel === "string" ? sc.genel : (sc.islem || null))' in uyg
    i = KAYNAK.index("function kur(MB)")
    arayuz = KAYNAK[i:]
    cagrilar = []
    for m in re.finditer(r"(?<!function )\bsecimli\(", arayuz):
        d, j = 0, m.end() - 1
        while True:           # dengeli ayraç: çağrının bütün argümanları
            d += {"(": 1, ")": -1}.get(arayuz[j], 0)
            if d == 0:
                break
            j += 1
        cagrilar.append(arayuz[m.end():j])
    assert len(cagrilar) >= 12
    for c in cagrilar:
        assert "genel: GENEL_ISLEM_ADLARI" in c, c[:120]
    assert "genelGecisMetni(m, islemAdi)" in arayuz


# ---------------------------------------------------------------------------------------------------------------------------
# K-10 / K-15: Mesnet aracının yaylı mesnet penceresi ve rijit diyafram sorusu kablolanmıştır
def test_mesnet_araci_yay_ve_diyafram_kablolamasi():
    i = KAYNAK.index("function mesnetYaz(")
    blok = KAYNAK[i:KAYNAK.index('kip("mesnet", {', i) + 1200]
    assert 'MB.kaplamaAc("mesnet-yay", "Yaylı mesnet"' in blok and "yayDegerleri(oku(k.govde))" in blok
    assert "YAY_ANAHTARLARI.map(" in blok and "YAY_VARSAYILAN[a.a]" in blok
    assert "mesnetDiyaframSorusu(B(), y.ref, tur" in blok and 'MB.kaplamaAc("mesnet-diyafram", q.baslik' in blok
    assert '<button type="button"' in blok and "data-diyafram" in blok, "seçenekler klavyeyle erişilen düğmeler"
    assert 'if (s_ === "vazgec")' in blok and "diyafram: s_" in blok
    assert 'if (tur === "yay") { yayPenceresi(y); return; }' in blok
    assert "mesnetAta(m, aksRefZ(m, y.ref), tur, sec)" in blok


# ---------------------------------------------------------------------------------------------------------------------------
# K-22: makas üreteci iki kolon başı arasında her tipte mekanizmasız çözülür (iki portal çerçeve, 12 m, 4 göz, KUTU 80x5,
# varsayılan mafsallı gövde; eski üreteçte pratt, howe, warren, warren-dikmeli ve k "Yapı mekanizma" veriyordu)
_MAKAS_BETIGI = r"""
const O = require(process.argv[1]);
const out = {};
for (const tip of O.MAKAS_TIPLERI) {
  for (const yanal of [null, "yok"]) {
    const m = {
      tur: "bina", surum: 3, baslik: "makas " + tip, sistem: "celik",
      akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 12 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 6 }],
        z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+6.00", konum: 6, kat: 1 }] },
      malzemeler: { S275: { kutuphane: "S275" } },
      kesitler: { HEA200: { tip: "profil", profil: "HEA200", malzeme: "S275" }, KUTU: { tip: "profil", profil: "KUTU 80x5", malzeme: "S275" } },
      cubuklar: [], paneller: [], mesnetler: [], temeller: { tip: "tekil", mesnet: "ankastre" },
    };
    let n = 1;
    for (const ay of ["1", "2"]) for (const ax of ["A", "B"]) m.cubuklar.push({ no: n++, tur: "kolon", i: { aks: [ax, ay], z: "±0.00" }, j: { aks: [ax, ay], z: "+6.00" }, kesit: "HEA200" });
    m.cubuklar.push({ no: n++, tur: "kiris", i: { aks: ["A", "1"], z: "+6.00" }, j: { aks: ["A", "2"], z: "+6.00" }, kesit: "HEA200" });
    m.cubuklar.push({ no: n++, tur: "kiris", i: { aks: ["B", "1"], z: "+6.00" }, j: { aks: ["B", "2"], z: "+6.00" }, kesit: "HEA200" });
    let r = { model: m, uyarilar: [] };
    for (const ay of ["1", "2"]) {
      const p = { tip: tip, bas: { aks: ["A", ay], z: "+6.00" }, son: { aks: ["B", ay], z: "+6.00" }, goz: 4, kesitler: { ust: "KUTU", alt: "KUTU", dikme: "KUTU", diyagonal: "KUTU" } };
      if (tip.startsWith("besik") || tip === "fink") p.egim = 15; else p.yukseklik = 1.5;
      if (yanal) p.yanal_tutma = yanal;
      r = O.makasUret(r.model, p);
    }
    out[tip + (yanal ? "|" + yanal : "")] = { model: r.model, uyarilar: r.uyarilar };
  }
}
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def makaslar():
    if NODE is None:
        pytest.skip("node kurulu değil")
    r = subprocess.run([NODE, "-e", _MAKAS_BETIGI, str(PROJE / "docs" / "model_ops.js")], capture_output=True, text=True, timeout=120, cwd=PROJE)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@node_gerekli
@pytest.mark.parametrize("tip", ["pratt", "howe", "warren", "warren-dikmeli", "k", "fink", "besik-pratt", "besik-howe"])
def test_makas_tipleri_mekanizmasiz_cozulur(tip, makaslar, kopru):
    o = makaslar[tip]
    assert "Üst başlığın düzlem dışı burkulma boyu, aşık ya da düzlem dışı bağ yoksa bütün açıklıktır." in o["uyarilar"]
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": o["model"]}})))
    assert y.get("hata") in (None, ""), f"{tip}: {y.get('hata')}"
    assert "Yapı mekanizma" not in json.dumps(y["veri"].get("uyarilar") or [], ensure_ascii=False), y["veri"].get("uyarilar")
    assert y["veri"]["model"] == "genel"


@node_gerekli
@pytest.mark.parametrize("tip", ["pratt", "warren", "k"])
def test_makas_yanal_tutma_yok_eski_mekanizma(tip, makaslar, kopru):
    # yanal_tutma "yok": bütün gövde mafsallı — aşık / bağ olmadan motor mekanizmayı bildirir; üreteç de uyarır
    o = makaslar[tip + "|yok"]
    assert any("yanal_tutma: yok" in u for u in o["uyarilar"])
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": o["model"]}})))
    assert y.get("hata") and "mekanizma" in y["hata"], y.get("hata")
