# -*- coding: utf-8 -*-
"""dersler\\*.md ders kaynaklarını denetler ve docs\\dersler.json dosyasına derler.

Biçim sözleşmesi: dersler\\BICIM.md. Yalnız standart kütüphane gerekir.

Kullanım (proje klasöründen):
  python ders_derle.py                   denetle ve docs\\dersler.json yaz
  python ders_derle.py --denetle         yalnız denetle (dosya yazmaz)
  python ders_derle.py --json yol.json   başka bir hedefe yaz
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
DERS_KLASORU = KOK / "dersler"
HEDEF = KOK / "docs" / "dersler.json"

BOLUMLER = {"matris": "Matris", "se": "Sonlu elemanlar", "yapi": "Yapı analizi"}
# Numara aralıkları (BICIM.md §1): 01–09 matris, 10–20 sonlu elemanlar, 21 ve üstü yapı analizi.
BOLUM_ARALIGI = {"matris": (1, 9), "se": (10, 20), "yapi": (21, 99)}

# Etkileşim ve alıştırma katalogları (BICIM.md §6 ve §7): ad → varsayılan başlık.
ETKILESIMLER = {
    "matris-gezgini": "Matris gezgini",
    "eleman-eleman": "Eleman eleman işlem",
    "carpim-gezgini": "Çarpım gezgini",
    "transpoz-aynasi": "Transpoz aynası",
    "kofaktor-acilim": "Kofaktör açılımı",
    "donusum-2b": "Matris bir dönüşümdür",
    "gauss-adim": "Gauss eliminasyonu adım adım",
    "ozvektor-2b": "Özvektör avı",
    "yay-sistemi": "Yay sistemi ve birleştirme",
    "cubuk-sekil": "Çubuk eleman ve şekil fonksiyonları",
    "kafes-aci": "Açılı kafes elemanı",
    "dof-haritasi": "Serbestlik haritası",
    "kiris-sekil": "Kiriş şekil fonksiyonları",
    "esdeger-yuk": "Eşdeğer düğüm yükleri",
    "kiris-nvm": "Kesme ve moment diyagramı",
    "cerceve-k": "Çerçeve eleman matrisi",
    "modal-titresim": "Titreşim modları",
    "uzay-kafes-cubuk": "Uzay kafes çubuğu ve doğrultu kosinüsleri",
    "uzay-cerceve-k": "Uzay çerçeve eleman matrisi",
    "elastik-mesnet": "Elastik mesnetli kiriş",
    "winkler-kiris": "Winkler zeminine oturan kiriş",
    "doseme-dagilimi": "Döşemeden kirişe: 45° kuralı",
    "kolon-birikimi": "Kolonda yük birikimi ve yük alanı",
    "deprem-spektrumu": "TBDY 2018 tasarım spektrumu",
    "kombinasyon-zarfi": "Kombinasyon ve zarf",
    "ruzgar-kat-kuvveti": "Rüzgâr kat kuvvetleri (TS 498:2021 md. 14)",
    "kat-kuvvetleri": "Eşdeğer deprem yükü: kat kuvvetleri",
    "kiris-donati": "Kiriş donatısı: basınç bloğu ve A_s",
    "kolon-nm": "Kolon N–M etkileşim eğrisi",
    "celik-burkulma": "Çelik basınç elemanı: F_cr eğrisi",
    "celik-yanal-burulma": "Yanal burulmalı burkulma: M_n – L_b",
    "rijit-diyafram": "Rijit diyafram: öteleme, dönme ve kolon payları",
}
ALISTIRMALAR = {
    "boyut": "Boyut ve indis",
    "toplama": "Toplama ve çıkarma",
    "skaler": "Skalerle çarpma",
    "carpim": "Matris çarpımı",
    "transpoz": "Transpoz",
    "determinant": "Determinant",
    "ters": "Ters matris",
    "coz": "Doğrusal sistem",
    "ozdeger": "Özdeğer",
    "cubuk-k": "Çubuk eleman matrisi",
    "kafes-k": "Kafes eleman matrisi",
    "birlestir": "Birleştirme",
    "sinir-kosulu": "Sınır koşulu ve çözüm",
    "yay-seri": "Seri yaylar",
    "doseme-esdeger": "Döşeme payı ve eşdeğer yük",
    "kombinasyon": "Kombinasyon ve zarf",
    "deprem-vt": "Taban kesme kuvveti V_tE",
    "kiris-as": "Kiriş donatısı A_s",
    "celik-mn": "Çelik kirişte M_n",
}
# SE_GRUBU docs/etkilesim_se.js, YAPI_GRUBU docs/etkilesim_yapi.js içinde, ötekiler docs/etkilesim_matris.js içinde
# kaydedilir. Alıştırmalar kayıtta "alistirma:<ad>" adını taşır.
SE_GRUBU = frozenset({
    "yay-sistemi", "cubuk-sekil", "kafes-aci", "dof-haritasi", "kiris-sekil", "esdeger-yuk", "kiris-nvm",
    "cerceve-k", "modal-titresim", "uzay-kafes-cubuk", "uzay-cerceve-k",
    "cerceve-k", "modal-titresim", "elastik-mesnet", "winkler-kiris",
    "cubuk-k", "kafes-k", "birlestir", "sinir-kosulu", "yay-seri",
})
YAPI_GRUBU = frozenset({
    "doseme-dagilimi", "kolon-birikimi", "deprem-spektrumu", "kombinasyon-zarfi", "ruzgar-kat-kuvveti", "kat-kuvvetleri",
    "kiris-donati", "kolon-nm", "celik-burkulma", "celik-yanal-burulma", "rijit-diyafram",
    "doseme-esdeger", "kombinasyon", "deprem-vt", "kiris-as", "celik-mn",
})


def etkilesim_dosyasi(ad: str) -> str:
    """Katalog adının kayıtlı olduğu docs/etkilesim_*.js dosya adı."""
    if ad in YAPI_GRUBU:
        return "etkilesim_yapi.js"
    return "etkilesim_se.js" if ad in SE_GRUBU else "etkilesim_matris.js"

KUTULAR = {
    "not": "Not", "uyari": "Dikkat", "ipucu": "İpucu", "tanim": "Tanım", "ozet": "Özet",
    "hata": "Sık yapılan hata", "muhendislik": "Mühendislikte",
}
ORNEK_BOLUMLERI = ("ipucu", "cevap", "kod", "kontrol", "yorum", "sekil")
ON_BILGI_ALANLARI = ("baslik", "bolum", "ozet", "sure")
SEKIL_EN_FAZLA = 8000

# Pedagoji alt sınırları (BICIM.md §8.1); --denetle uyarı olarak yazar, test zorunlu tutar.
EN_AZ = {"ornek": 6, "kodlu_ornek": 4, "etkilesim": 2, "alistirma": 1}
GEREKLI_KUTULAR = ("hata", "muhendislik", "ozet")

_DOSYA_ADI = re.compile(r"^(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ACILIS = re.compile(r"^:::\s*([a-z-]+)(?:\s+(.*?))?\s*$")
_KAPANIS = re.compile(r"^:::\s*$")
_BOLUM = re.compile(r"^---\s*([a-z]+)\s*$")
_CIT = re.compile(r"^\s*(`{3,}|~{3,})")
_SATIR_ICI_KOD = re.compile(r"`[^`]*`")
_SVG_YASAK = (
    (re.compile(r"<\s*script", re.I), "<script>"),
    (re.compile(r"<\s*foreignobject", re.I), "<foreignObject>"),
    (re.compile(r"<\s*iframe", re.I), "<iframe>"),
    (re.compile(r"<\s*image\b", re.I), "<image>"),
    (re.compile(r"<\s*marker\b", re.I), "<marker>"),
    (re.compile(r"<\s*style\b", re.I), "<style> (bütün sayfayı etkiler; style=\"…\" özniteliği kullan)"),
    (re.compile(r"<\s*a\b", re.I), "<a> bağlantısı"),
    (re.compile(r"<[^>]*\son[a-z]+\s*=", re.I), "on… olay özniteliği"),
    (re.compile(r"javascript\s*:", re.I), "javascript:"),
)
_HREF = re.compile(r"""(?:xlink:)?href\s*=\s*["']?([^"'\s>]*)""", re.I)
_MAKRO = re.compile(r"\\(kutusil|kutua|kutub|kutuc|ksil|ka|kb|kc)(?=\s*\{)")
_MAKRO_KARSILIK = {
    "ka": r"\textcolor{#2563eb}", "kb": r"\textcolor{#d97706}", "kc": r"\textcolor{#059669}",
    "ksil": r"\textcolor{#dc2626}", "kutua": r"\boxed", "kutub": r"\boxed", "kutuc": r"\boxed",
    "kutusil": r"\boxed",
}
_YASAK_ADLAR = {"open", "exec", "eval", "compile", "input", "__import__", "globals", "locals", "breakpoint"}


class DersHatasi(ValueError):
    """Ders kaynağında biçim hatası. İleti "dosya:satır: açıklama" satırlarından oluşur."""


# ---------------------------------------------------------------- yardımcılar

def _cit_ac(satir: str) -> str | None:
    m = _CIT.match(satir)
    return m.group(1) if m else None


def _cit_kapanir(satir: str, cit: str) -> bool:
    m = _CIT.match(satir)
    if not m or m.group(1)[0] != cit[0] or len(m.group(1)) < len(cit):
        return False
    return not satir.strip()[len(m.group(1)):].strip()


# ---------------------------------------------------------------- denetimler

def _md_denetle(metin: str, yer: str) -> None:
    """Başlık düzeyi ve $ / $$ dengesini denetler (kod çitleri ve satır içi kod hariç)."""
    cit = None
    blok = False
    for k, satir in enumerate(metin.split("\n")):
        if cit is not None:
            if _cit_kapanir(satir, cit):
                cit = None
            continue
        acilan = _cit_ac(satir)
        if acilan:
            cit = acilan
            continue
        if re.match(r"^#\s", satir):
            raise DersHatasi(f"{yer}: '# başlık' kullanılmaz; '##' ya da '###' kullan (bölüm satırı {k + 1})")
        temiz = _SATIR_ICI_KOD.sub("", satir).replace("\\$", "")
        cift = temiz.count("$$")
        tek = temiz.replace("$$", "").count("$")
        onceki = blok
        if cift % 2:
            blok = not blok
        if not onceki and not blok and tek % 2:
            raise DersHatasi(f"{yer}: satır içi '$' kapanmamış (satır içi matematik tek satırda kalmalı): {satir.strip()[:80]}")
    if cit is not None:
        raise DersHatasi(f"{yer}: kod çiti ({cit}) kapanmamış")
    if blok:
        raise DersHatasi(f"{yer}: '$$' blok matematiği kapanmamış")


def _svg_denetle(svg: str, yer: str) -> None:
    s = svg.strip()
    if not s.startswith("<svg") or not s.endswith("</svg>"):
        raise DersHatasi(f"{yer}: şekil '<svg' ile başlayıp '</svg>' ile bitmeli")
    if len(s) > SEKIL_EN_FAZLA:
        raise DersHatasi(f"{yer}: şekil {len(s)} karakter; en çok {SEKIL_EN_FAZLA}")
    if "viewBox" not in s:
        raise DersHatasi(f"{yer}: şekilde viewBox zorunlu")
    for desen, ad in _SVG_YASAK:
        if desen.search(s):
            raise DersHatasi(f"{yer}: şekilde yasak öğe: {ad}")
    for m in _HREF.finditer(s):
        if not m.group(1).startswith("#"):
            raise DersHatasi(f"{yer}: şekilde dış bağlantı yasak (href yalnız #kimlik olabilir): {m.group(1)[:60]}")


def _kod_denetle(kod: str, yer: str) -> None:
    try:
        agac = ast.parse(kod)
    except SyntaxError as h:
        raise DersHatasi(f"{yer}: kod sözdizimi hatası: {h.msg} (kod satırı {h.lineno})") from None
    if not agac.body or not isinstance(agac.body[-1], ast.Expr):
        raise DersHatasi(f"{yer}: kodun son satırı Sonuc döndüren bir ifade olmalı (ör. mo.carp(A, B))")
    for d in ast.walk(agac):
        if isinstance(d, (ast.Import, ast.ImportFrom)):
            raise DersHatasi(f"{yer}: kodda import yazılmaz; mo, sp, se, yapi ve tasarim hazır")
        if isinstance(d, ast.Attribute) and d.attr.startswith("__"):
            raise DersHatasi(f"{yer}: kodda çift alt çizgili öznitelik kullanılmaz: {d.attr}")
        if isinstance(d, ast.Name) and (d.id in _YASAK_ADLAR or d.id.startswith("__")):
            raise DersHatasi(f"{yer}: kodda '{d.id}' kullanılmaz")


def _kontrol_denetle(kontrol: str, yer: str) -> None:
    try:
        ast.parse(kontrol, mode="eval")
    except SyntaxError as h:
        raise DersHatasi(f"{yer}: kontrol tek bir ifade olmalı: {h.msg}") from None


# ---------------------------------------------------------------- ayrıştırma

def _on_bilgi(satirlar: list[str], ad: str) -> tuple[dict, int]:
    if not satirlar or satirlar[0].strip() != "---":
        raise DersHatasi(f"{ad}:1: dosya '---' ön bilgi satırıyla başlamalı")
    for son in range(1, len(satirlar)):
        if satirlar[son].strip() == "---":
            break
    else:
        raise DersHatasi(f"{ad}: ön bilgi kapanmamış (ikinci '---' satırı yok)")
    alanlar: dict = {}
    for j in range(1, son):
        s = satirlar[j].strip()
        if not s:
            continue
        anahtar, ayrac, deger = s.partition(":")
        anahtar, deger = anahtar.strip(), deger.strip()
        if not ayrac:
            raise DersHatasi(f"{ad}:{j + 1}: ön bilgide 'anahtar: değer' bekleniyordu")
        if anahtar not in ON_BILGI_ALANLARI:
            raise DersHatasi(f"{ad}:{j + 1}: bilinmeyen ön bilgi alanı '{anahtar}'; geçerli: {', '.join(ON_BILGI_ALANLARI)}")
        if len(deger) >= 2 and deger[0] == deger[-1] and deger[0] in "\"'":
            deger = deger[1:-1]
        alanlar[anahtar] = deger
    eksik = [a for a in ON_BILGI_ALANLARI if not alanlar.get(a)]
    if eksik:
        raise DersHatasi(f"{ad}: ön bilgide eksik alan: {', '.join(eksik)}")
    if alanlar["bolum"] not in BOLUMLER:
        raise DersHatasi(f"{ad}: bolum '{alanlar['bolum']}' geçersiz; geçerli: {', '.join(BOLUMLER)}")
    try:
        sure = int(alanlar["sure"])
    except ValueError:
        sure = 0
    if sure <= 0:
        raise DersHatasi(f"{ad}: sure pozitif tam sayı (dakika) olmalı")
    alanlar["sure"] = sure
    return alanlar, son + 1


def _katalog_parca(tur: str, katalog: dict, ad_: str, govde: str, yer: str) -> dict:
    if not ad_:
        raise DersHatasi(f"{yer}: '::: {tur}' yönergesinde ad gerekli")
    if ad_ not in katalog:
        raise DersHatasi(f"{yer}: bilinmeyen {tur} adı '{ad_}'; geçerli: {', '.join(katalog)}")
    param: dict = {}
    if govde:
        try:
            param = json.loads(govde)
        except json.JSONDecodeError as h:
            raise DersHatasi(f"{yer}: parametre JSON'u okunamadı: {h.msg} (satır {h.lineno})") from None
        if not isinstance(param, dict):
            raise DersHatasi(f"{yer}: parametreler tek bir JSON nesnesi ({{…}}) olmalı")
    baslik = str(param.pop("baslik", "") or katalog[ad_])
    return {"tur": tur, "ad": ad_, "baslik": baslik, "param": param}


def _ornek(baslik: str, satirlar: list[str], satir0: int, ad: str) -> dict:
    yer = f"{ad}:{satir0}"
    if not baslik:
        raise DersHatasi(f"{yer}: '::: ornek' yönergesinde başlık gerekli")
    soru: list[str] = []
    bolumler: dict[str, list[str]] = {}
    hedef = soru
    cit = None
    for k, s in enumerate(satirlar):
        if cit is not None:
            if _cit_kapanir(s, cit):
                cit = None
            hedef.append(s)
            continue
        acilan = _cit_ac(s)
        if acilan:
            cit = acilan
            hedef.append(s)
            continue
        b = _BOLUM.match(s)
        if b:
            ad_ = b.group(1)
            if ad_ not in ORNEK_BOLUMLERI:
                raise DersHatasi(f"{ad}:{satir0 + 1 + k}: bilinmeyen örnek bölümü '{ad_}'; geçerli: {', '.join(ORNEK_BOLUMLERI)}")
            if ad_ in bolumler:
                raise DersHatasi(f"{ad}:{satir0 + 1 + k}: '--- {ad_}' bölümü iki kez yazılmış")
            bolumler[ad_] = []
            hedef = bolumler[ad_]
            continue
        hedef.append(s)
    metin = {b: "\n".join(bolumler.get(b, [])).strip() for b in ORNEK_BOLUMLERI}
    soru_metni = "\n".join(soru).strip()
    if not soru_metni:
        raise DersHatasi(f"{yer}: örneğin sorusu boş (ilk '--- bölüm' satırından önce yazılır)")
    if not metin["cevap"]:
        raise DersHatasi(f"{yer}: '--- cevap' bölümü zorunlu")
    if metin["kod"] and not metin["kontrol"]:
        raise DersHatasi(f"{yer}: kod varsa '--- kontrol' bölümü zorunlu")
    if metin["kontrol"] and not metin["kod"]:
        raise DersHatasi(f"{yer}: kontrol var ama kod yok")
    if metin["kod"]:
        _kod_denetle(metin["kod"], yer)
        _kontrol_denetle(metin["kontrol"], yer)
    if metin["sekil"]:
        _svg_denetle(metin["sekil"], yer)
    _md_denetle(soru_metni, yer + " (soru)")
    for b in ("ipucu", "cevap", "yorum"):
        _md_denetle(metin[b], f"{yer} ({b})")
    return {"tur": "ornek", "no": 0, "baslik": baslik, "soru": soru_metni, **metin}


def _yonerge_parca(y: dict, ad: str) -> dict:
    tur, arg, yer = y["tur"], y["arg"], f"{ad}:{y['satir']}"
    govde = "\n".join(y["govde"]).strip()
    if tur == "etkilesim":
        return _katalog_parca(tur, ETKILESIMLER, arg, govde, yer)
    if tur == "alistirma":
        return _katalog_parca(tur, ALISTIRMALAR, arg, govde, yer)
    if tur == "ornek":
        return _ornek(arg, y["govde"], y["satir"], ad)
    if tur in KUTULAR:
        if not govde:
            raise DersHatasi(f"{yer}: '::: {tur}' kutusu boş")
        _md_denetle(govde, yer)
        return {"tur": "kutu", "cesit": tur, "baslik": arg or KUTULAR[tur], "icerik": govde}
    if tur == "sekil":
        _svg_denetle(govde, yer)
        return {"tur": "sekil", "baslik": arg, "svg": govde}
    gecerli = ["etkilesim", "alistirma", "ornek", "sekil", *KUTULAR]
    raise DersHatasi(f"{yer}: bilinmeyen yönerge '::: {tur}'; geçerli: {', '.join(gecerli)}")


def _govde(satirlar: list[str], ad: str, ilk: int) -> list[dict]:
    parcalar: list[dict] = []
    tampon: list[str] = []
    tampon_bas = ilk
    yonerge: dict | None = None
    cit = None

    def ekle(satir: str, no: int) -> None:
        nonlocal tampon_bas
        if yonerge is not None:
            yonerge["govde"].append(satir)
            return
        if not tampon:
            tampon_bas = no
        tampon.append(satir)

    def bosalt(bitis: int) -> None:
        metin = "\n".join(tampon).strip()
        tampon.clear()
        if metin:
            _md_denetle(metin, f"{ad}:{tampon_bas}-{bitis}")
            parcalar.append({"tur": "md", "icerik": metin})

    for k, satir in enumerate(satirlar):
        no = ilk + k
        if cit is not None:
            if _cit_kapanir(satir, cit):
                cit = None
            ekle(satir, no)
            continue
        acilan = _cit_ac(satir)
        if acilan:
            cit = acilan
            ekle(satir, no)
            continue
        if yonerge is None:
            a = _ACILIS.match(satir)
            if a:
                bosalt(no - 1)
                yonerge = {"tur": a.group(1), "arg": (a.group(2) or "").strip(), "satir": no, "govde": []}
                continue
            if _KAPANIS.match(satir):
                raise DersHatasi(f"{ad}:{no}: açılmamış bir yönergenin kapanışı (':::')")
            ekle(satir, no)
        else:
            if _KAPANIS.match(satir):
                parcalar.append(_yonerge_parca(yonerge, ad))
                yonerge = None
                continue
            if _ACILIS.match(satir):
                raise DersHatasi(
                    f"{ad}:{no}: iç içe yönerge; önce {yonerge['satir']}. satırdaki '::: {yonerge['tur']}' kapanmalı")
            ekle(satir, no)
    if cit is not None:
        raise DersHatasi(f"{ad}: kod çiti ({cit}) dosya sonuna kadar kapanmamış")
    if yonerge is not None:
        raise DersHatasi(f"{ad}:{yonerge['satir']}: '::: {yonerge['tur']}' yönergesi kapanmamış")
    bosalt(ilk + len(satirlar))
    return parcalar


# ---------------------------------------------------------------- md yedeği (Colab ve eski görünüm)

def makro_cevir(metin: str) -> str:
    r"""Uygulamaya özgü renk ve kutu makrolarını standart LaTeX'e çevirir (\ka → \textcolor, \kutua → \boxed)."""
    return _MAKRO.sub(lambda m: _MAKRO_KARSILIK[m.group(1)], metin)


def _alinti(metin: str) -> str:
    return "\n".join(("> " + s) if s.strip() else ">" for s in metin.split("\n"))


def md_yedegi(ders: dict) -> str:
    """Yönergesiz düz markdown: Colab defteri ve parça çizicisi olmayan eski görünüm için."""
    p = [f"## {ders['no']}) {ders['baslik']}", f"*{ders['ozet']}* · yaklaşık {ders['sure']} dk"]
    for pr in ders["parcalar"]:
        t = pr["tur"]
        if t == "md":
            p.append(pr["icerik"])
        elif t == "etkilesim":
            p.append(f"> 🖱️ **Etkileşimli çizim:** {pr['baslik']} (uygulamanın Dersler sayfasında açılır)")
        elif t == "alistirma":
            p.append(f"> ✍️ **Alıştırma:** {pr['baslik']} (uygulamada sınırsız soru üretir)")
        elif t == "sekil":
            p.append(f"> 🖼️ **Şekil:** {pr['baslik'] or 'çizim'} (uygulamada görünür)")
        elif t == "kutu":
            p.append(_alinti(f"**{pr['baslik']}**\n\n{pr['icerik']}"))
        elif t == "ornek":
            s = [f"#### Örnek {ders['no']}.{pr['no']}: {pr['baslik']}", "", pr["soru"]]
            if pr["ipucu"]:
                s += ["", "<details><summary>İpucu</summary>", "", pr["ipucu"], "", "</details>"]
            s += ["", "<details><summary>Cevap</summary>", "", pr["cevap"], ""]
            if pr["kod"]:
                s += ["Motorla çözüm:", "", "```python", pr["kod"], "```", ""]
            s.append("</details>")
            if pr["yorum"]:
                s += ["", pr["yorum"]]
            p.append("\n".join(s))
    return makro_cevir("\n\n".join(p))


# ---------------------------------------------------------------- ders ve klasör

def ders_oku(yol: Path) -> dict:
    yol = Path(yol)
    ad = yol.name
    m = _DOSYA_ADI.match(ad)
    if not m:
        raise DersHatasi(f"{ad}: dosya adı 'NN-kisa-ad.md' biçiminde olmalı (küçük harf, rakam, tire)")
    no = int(m.group(1))
    metin = yol.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    satirlar = metin.split("\n")
    on, govde_bas = _on_bilgi(satirlar, ad)
    alt, ust = BOLUM_ARALIGI[on["bolum"]]
    if not alt <= no <= ust:
        raise DersHatasi(f"{ad}: numara {no:02d} ile bölüm '{on['bolum']}' uyuşmuyor (01–09 matris, 10–20 se, 21 ve üstü yapi)")
    parcalar = _govde(satirlar[govde_bas:], ad, govde_bas + 1)
    if not parcalar:
        raise DersHatasi(f"{ad}: ders gövdesi boş")
    _md_denetle(on["baslik"], f"{ad} (baslik)")
    sayac = 0
    for p in parcalar:
        if p["tur"] == "ornek":
            sayac += 1
            p["no"] = sayac
    ders = {"no": no, "id": yol.stem, "baslik": on["baslik"], "bolum": on["bolum"],
            "bolum_adi": BOLUMLER[on["bolum"]], "ozet": on["ozet"], "sure": on["sure"], "md": "", "parcalar": parcalar}
    ders["md"] = md_yedegi(ders)
    return ders


def ders_dosyalari(klasor: Path = DERS_KLASORU) -> list[Path]:
    klasor = Path(klasor)
    if not klasor.is_dir():
        return []
    return sorted(p for p in klasor.glob("*.md") if p.name != "BICIM.md" and not p.name.startswith("_"))


def derle(klasor: Path = DERS_KLASORU) -> list[dict]:
    """Bütün dersleri okur; hataların hepsini tek DersHatasi içinde toplar. Dönen veri 'kontrol' alanlarını içerir."""
    dersler, hatalar = [], []
    for yol in ders_dosyalari(klasor):
        try:
            dersler.append(ders_oku(yol))
        except DersHatasi as h:
            hatalar.append(str(h))
    goruldu: dict[int, str] = {}
    for d in dersler:
        if d["no"] in goruldu:
            hatalar.append(f"{d['id']}.md: ders numarası {d['no']:02d}, {goruldu[d['no']]}.md ile çakışıyor")
        goruldu.setdefault(d["no"], d["id"])
    if hatalar:
        raise DersHatasi("\n".join(hatalar))
    return sorted(dersler, key=lambda d: d["no"])


def kalite(ders: dict) -> list[str]:
    """BICIM.md §8.1 alt sınırlarına göre eksikleri döndürür (boş liste: tamam)."""
    p = ders["parcalar"]
    say = {
        "ornek": sum(1 for x in p if x["tur"] == "ornek"),
        "kodlu_ornek": sum(1 for x in p if x["tur"] == "ornek" and x["kod"]),
        "etkilesim": sum(1 for x in p if x["tur"] == "etkilesim"),
        "alistirma": sum(1 for x in p if x["tur"] == "alistirma"),
    }
    eksik = [f"{ders['id']}: {ad} {say[ad]} < {en_az}" for ad, en_az in EN_AZ.items() if say[ad] < en_az]
    kutular = {x["cesit"] for x in p if x["tur"] == "kutu"}
    eksik += [f"{ders['id']}: '::: {k}' kutusu yok" for k in GEREKLI_KUTULAR if k not in kutular]
    return eksik


def json_yaz(dersler: list[dict], hedef: Path = HEDEF) -> None:
    """Uygulama için dersler.json yazar; testlere ait 'kontrol' alanları çıkarılır."""
    cikti = []
    for d in dersler:
        d2 = dict(d)
        d2["parcalar"] = [{k: v for k, v in p.items() if k != "kontrol"} for p in d["parcalar"]]
        cikti.append(d2)
    Path(hedef).write_text(json.dumps(cikti, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def sayim_ozeti(dersler: list[dict]) -> str:
    def say(tur):
        return sum(1 for d in dersler for p in d["parcalar"] if p["tur"] == tur)
    kodlu = sum(1 for d in dersler for p in d["parcalar"] if p["tur"] == "ornek" and p["kod"])
    return (f"{len(dersler)} ders · {say('ornek')} çözümlü örnek ({kodlu} kodlu) · {say('etkilesim')} etkileşim · "
            f"{say('alistirma')} alıştırma · {say('sekil')} şekil · {say('kutu')} kutu")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="dersler\\*.md → docs\\dersler.json (biçim: dersler\\BICIM.md)")
    ap.add_argument("--denetle", action="store_true", help="yalnız denetle, dosya yazma")
    ap.add_argument("--json", type=Path, default=HEDEF, help="hedef JSON dosyası")
    ap.add_argument("--klasor", type=Path, default=DERS_KLASORU, help="ders klasörü")
    a = ap.parse_args(argv)
    try:
        dersler = derle(a.klasor)
    except DersHatasi as h:
        print("❌ Ders biçimi hataları:")
        print(h)
        return 1
    print(sayim_ozeti(dersler))
    for d in dersler:
        for uyari in kalite(d):
            print("⚠️", uyari)
    if a.denetle:
        return 0
    if not dersler:
        print("⚠️ Ders yok; hedef değiştirilmedi.")
        return 0
    json_yaz(dersler, a.json)
    print(f"✅ {a.json} yazıldı")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
