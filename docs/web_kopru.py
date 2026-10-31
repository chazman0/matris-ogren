# -*- coding: utf-8 -*-
"""Pyodide köprüsü: tarayıcıdan gelen JSON isteğini matris_ogren'e iletir, yanıtı JSON olarak döndürür.

İstek (JSON metni):
  {"islem": "topla", "girdi": {"A": "1 2; 3 4", "B": "5 6; 7 8"},
   "ayarlar": {"ondalik": false, "basamak": 4, "en_fazla_eleman": 36, "sema": true}}
  "sema" (varsayılan true): adım adım oklu şema bloklarını da üret. Kapalıysa motor SVG hiç çizmez.

Yanıt (JSON metni):
  {"ad": "C",
   "bloklar": [{"tur": "md" | "math", "icerik": "...", "etiket": "adim" | "kural" | "sonuc"},
               {"tur": "kod", "baslik": "🐍 Python ile", "kod": "...", "cikti": "...", "etiket": "python"},
               {"tur": "sema", "icerik": {"baslik": "...", "kareler": [{"baslik": "...", "svg": "<svg ...>"}, ...]},
                "etiket": "sema"}],
   "sonuc_etiket": "\\mathbf{C}", "sonuc_latex": "\\begin{bmatrix}...", "sonuc_metin": "6 8; 10 12",
   "zincir": true, "hata": null}
  "sema" bloğunun "icerik" değeri metin değil sözlüktür (her kare = bir adım: başlık + eksiksiz, durağan SVG);
  tarayıcı bunu markdown'a değil, adım adım oynatıcıya (app.js) verir.
Hata durumunda: {"hata": "...", "hata_turu": "girdi" | "ic", "iz": "..."}

Sonlu eleman işlemleri (sonlu_eleman.py):
  "se_coz":      girdi {"model": {...} | "JSON metni"} → yukarıdaki yanıt biçimi + "veri" (Sonuc.veri: düğümler, elemanlar,
                 diyagramlar, tepkiler, yaylar, çökmeler, denge, boyut ...); "zincir" her zaman false. Model türleri:
                 yay, cubuk, kafes, kiris, cerceve, kafes3b, cerceve3b; isteğe bağlı yaylar, cokmeler ve eleman zemin'i.
  "se_ornekler": → {"ornekler": [{ad, baslik, tip, aciklama}], "hata": null}
  "se_ornek":    girdi {"ad": "kafes-iki-cubuk"} → {"ad", "model": {...}, "hata": null}

Bina işlemleri (yapi.py + yapi_veri.py):
  "bina_coz":       girdi {"bina": {...} | "JSON metni"} → {"ad": "bina", "bloklar", "veri" (yapi.bina_coz şeması: bina, ag,
                    yukler, durumlar, kombinasyonlar, sonuclar, zarf, akis, ozet, fe_model, deprem, ruzgar, kar, kutle_merkezi,
                    cozum_kimligi), "sonuc_metin", "zincir": false, "hata"}; çözümün iç paketi tembel kombinasyonlar için
                    önbelleğe alınır. Genel modelde veri.akis.sankey [{kaynak, hedef, durum (G | Q | S), kN, tur}]: tur
                    "panel-cubuk" (P{n} → Ç{n}), "cubuk-cubuk" (Ç → Ç), "cubuk-mesnet" (Ç → M{düğüm}), "dugum-cubuk" (D{düğüm} →
                    Ç), "dugum-mesnet" (D → M); durum başına en çok 600 panel bandı + 600 öteki kenar (atılan sayı
                    veri.akis.sankey_kesildi {durum: n}). "sure_ms": işlemin motordaki duvar süresi (ms, tam sayı; aynı değer
                    veri.ozet.cozum_sure_ms)
  "bina_kutuphane": → {"malzemeler", "kesit_katalogu", "kullanim_siniflari", "duvarlar", "kaplamalar", "kombinasyon_kumeleri",
                    "sablonlar", "dogrulanmamis", ..., "hata": null}
  "bina_sablonlar": → {"sablonlar": [{ad, baslik, sistem, aciklama, kat, aks}], "hata": null}
  "bina_sablon":    girdi {"ad": "betonarme-2kat-3x2"} → {"ad", "bina": {...}, "hata": null}
  "bina_yuk_yolu":  girdi {"bina", "veri", "hedef": {"tur": "doseme"|"kiris"|"kolon", "no", "durum"}} → {"adimlar": [...], "hata": null}
  "bina_deprem":    girdi {"bina"} → {"deprem": (veri.deprem şeması, çözümsüz önizleme: spektrum, V_tE, F_i, V_i; "tahmin": true),
                    "hata": null}
  "bina_kombinasyon": girdi {"cozum_kimligi", "ad", "katsayilar"?, "bina"?} → {"ad", "cozum_kimligi", "sonuc": KISA (tam diziler),
                    "hata": null}. Son çözümler (en çok BINA_ONBELLEK_EN_FAZLA) bellekte tutulur; kimlik önbellekte yoksa ve
                    "bina" verilmişse bina anlatımsız yeniden çözülür, yoksa öğretici hata.
  "bina_eleman_tasarim": girdi {"cozum_kimligi", "tur": "kiris"|"kolon", "no" (bina eleman no'su), "bina"?} → {"ad", "bloklar"
                    (tasarim.py anlatımı: kesit şeması, formüller, N–M eğrisi), "sonuc": veri.tasarim.elemanlar[] kaydı (§11) +
                    kolonda "egri_x", "egri_y" [{N, M}] ve "noktalar" [{ad, kombinasyon, uc, N, Mx, My, dc}], çelikte "kuvvetler",
                    "uyarilar"; "cozum_kimligi", "hata": null}. Önbellek bina_kombinasyon ile aynı (tasarim.py yoksa öğretici hata).
                    Genel (surum 3) modelde "tur": "cubuk" ve "no" çubuk numarasıdır (tam eşleşme; kayıtta "cubuk" alanı varsa
                    bunu gönderin); "kolon"/"kiris" + no: genel modelde aynı türden çubuk numarası, yalnız aks–kat girdisinin
                    genel motorla çözümünde aks–kat no'su (kaynak).
  "bina_kesit_oner": girdi {"cozum_kimligi" | "bina", "hedef": "hepsi" | [{"tur", "no"}], "yinele": 0..3, "grup"?: true} → {"oneriler":
                    [{cubuk, tur, kesit, oneri (profil adı ya da "bxh" cm), sistem ("celik" | "betonarme"), malzeme, b, h (m,
                    betonarme), kaynak ({aks_kat, no} | null), gerekce [metin], dc_once (tasarım tablosundaki D/C), dc_oneri
                    (önerilen kesitle aynı kural), dc_sonra, degisim ("büyüt" | "küçült" | "aynı" | "donatı": betonarme kolonda b × h aynı, gerekli ρ büyük), uygula ({ad, tanim, yeni,
                    ek_kesitler?} | null: atanacak kesit adı, yeni ise kesitler'e eklenecek tanım; vute çubuğunda temel profil
                    kartı ek_kesitler'de; değişiklik yoksa null)}], "turlar": [{tur, dc_maks, oneri_sayisi, degisen}], "dc_once",
                    "dc_sonra", "donati_azaltma" ([{kesit, yeni, donati_orani, rho_once, cubuklar}]: yakınsamadan sonra en küçük yeterli ρ), "bina" (yinele > 0: öneriler uygulanmış bina JSON'u; aynı (kesit, tür) grubuna grubun en ağır
                    önerisi), "uyarilar" [metin], "cozum_kimligi", "aciklama", "hata": null}. yinele > 0: öneri uygulanıp yeniden
                    çözülür (rijitlik değişince kuvvetler değişir), en çok 3 tur. Aks–kat çözümünde (kimlik) bina genel motorla bir
                    kez yeniden çözülüp önbelleğe alınır (gerçek temel tipiyle: tekil, mütemadi ya da radye); dc_once
                    görünen aks–kat tasarım tablosundandır. "sure_ms": işlemin motordaki duvar süresi (ms, tam sayı). Depremli
                    modelde yinele > 0 yanıtı "oteleme" {sinir, katlar, once: {X: [δ/h kat sırasıyla], Y}, sonra: {X, Y}} taşır
                    (TBDY 2018 md. 4.9.1; aciklama önce/sonra en büyük oranları yazar); "turlar"da oteleme_asan (sınırı yeni aşan
                    katlar) ve oteleme_kisiti ({katlar, gruplar}: 0. turda küçültülmeyen gruplar), degisen[].neden "öteleme".
                    "grup": true (hedef üye listesiyle; üyelerin kesiti ve türü aynı olmalı): tek öneri — grup {kesit, tur, uye},
                    cubuklar (üye çubukları), uygula ortak kart (betonarme: en büyük b × h, kolonda ρ üyeler doğrulanarak; çelik:
                    en ağır üye önerisi), dc_oneri üyelerin en büyüğü; yinele ≥ 1'de kart bütün üyelere uygulanır, dc_sonra
                    üyelerin gerçek D/C'lerinin en büyüğü, "bina" uygulanmış model.
  "bina_eleman_bilgi": girdi {"cozum_kimligi", "tur": "cubuk" | "kolon" | "kiris" | "fe", "no", "durum"? (yük durumu,
                    kombinasyon, "zarf+"/"zarf-"/"Zarf"; varsayılan "G"), "bina"?} → {"paket": {"sekmeler": {"ic": [bölüm],
                    "yer": [bölüm]}, "sekme_adlari", "uyarilar": [], "durum", "fe"}, "cozum_kimligi", "hata": null}. Eleman bilgi
                    panelinin "Motor ayrıntısı" (docs/eleman_bilgi.js paketBirlestir): alan.eleman_bilgi_alani'ndan parça başına
                    istasyon iç kuvvetleri, en büyük değerler, uç yer değiştirmeleri (bina ve yerel eksen) ve eğri yer
                    değiştirmenin en büyüğü. bölüm: {baslik, tablo: {basliklar, satirlar}, satirlar, not, notlar, acilir}.
                    "kolon"/"kiris" + no genel modelde bina_eleman_tasarim ile aynı kuralla çözülür (çubuk numarası; yalnız
                    aks–kat girdisinin genel motorla çözümünde aks–kat no'su). Önbellek bina_kombinasyon ile aynı.

Genel model (yapi._serbest_mi: bina "surum" ≥ 3 ya da cubuklar / paneller / dugumler / mesnetler / uretecler dolu ya da REF
düğüm / çubuk / panel ek yükü; yapi_serbest.py): bina_coz veri'sine ek alanlar — ag.cubuklar, ag.paneller (kenarlar, taşıyan
kenarlar), ag.dugumler[].tur ("aks" | "bolme" | "kesisim" | "ic" | "efendi"), ag.donme_tutulan, ag.diyafram_seviye,
yukler.paneller / yukler.cubuklar, akis.temeller (yalnız temel mesnetleri: B, L, h, N_temel) ve akis.mesnetler (açık mesnet
kayıtları: dugum, adres, tip, N_G, N_Q, MX, MY), bina.seviyeler (kat, kot, diyafram), kren (kopruler, durumlar, zarf),
yalniz_cekme (var, kombinasyonlar: etkin_degil, yineleme), uyarilar; tasarim.elemanlar[] her çubuk için (tur: kolon, kiris,
capraz, makas-*, asik, kren, bag, diger; cubuk, grup, L, varsayimlar, kaynak; kontroller[0] D/C'yi belirleyen satır).
Isı haritası (bina_alan) ve bina_eleman_bilgi genel modelde de çalışır.
  "bina_rapor":     girdi {"cozum_kimligi" | "bina", "secenek"?} → {"html": tam, kendi içinde HTML statik hesap raporu (rapor.py;
                    gömülü CSS, A4 yazdırma), "dosya_adi": "statik_rapor_<ad>.html", "cozum_kimligi", "hata": null}. Önbellekteki
                    çözüm kullanılır (yeniden çözülmez; genel modelde yanıtta kısaltılan tasarım satırlarının tamamı, ic["tas_tam"]);
                    kimlik önbellekte yoksa "bina" anlatımsız çözülür. "secenek": {"proje": {ad, yer,
                    il, ilce, ada, parsel, malik, hazirlayan, kontrol, tarih}, "bolumler": [1..14, "A", "B", "C", "metraj"],
                    "eleman_detay": "kritik" | "hepsi" | "yok", "ek_tablolar": [TABLO...], "tablolar": [tablo adı...],
                    "tablo_filtre": {ad: {"satirlar": [indeks...]}}}.
  "bina_tablolar":  girdi {"cozum_kimligi" | "bina"} → {"tablolar": [TABLO...] (tablolar.bina_tablolari şeması: ad, baslik, grup,
                    sutunlar, satirlar (degerler, yol), toplam, aciklama, kaynak), "cozum_kimligi" (kullanılan çözüm ya da null),
                    "cozumlu": bool, "hata": null}. Önbellekte bu binanın çözümü varsa (kimlik eşleşir; yapi.cozum_kimligi, genel
                    modelde de) Analiz/Deprem/Tasarım/Temel tabloları da gelir; yoksa çözmeden Model + Yükler + Metraj (deprem
                    kartı varsa önizleme) tabloları.
  "bina_alan":      girdi {"cozum_kimligi" | "bina", "durum" (yük durumu | kombinasyon adı | "zarf+" | "zarf-"), "istasyon"? (2…61,
                    varsayılan 21), "katsayilar"? ({"G": 1.2, ...} serbest birleşim), "elemanlar"? ([FE no] yalnız bunlar; döşemesiz)}
                    → {"alan": alan.eleman_alanlari (§16.1: durum, birim, elemanlar [istasyonlarda N, Vy, Vz, T, My, Mz, eğri u,
                    σ_maks/σ_min, τ, von Mises, kullanım, ekstremum], dugumler, aralik, secenekler, not) + "paneller" (§16.2 Navier
                    plak ızgarası w/mx/my ve 45° yük payı poligonları) + "radye" (temel modülü varsa Winkler basıncı), "cozum_kimligi",
                    "hata": null}. Önbellekteki çözümden (yeniden çözmez): kombinasyon = durumların katsayılı toplamı, zarf =
                    istasyon bazında en büyük / en küçük. alan.py yoksa öğretici hata.

op4 (yerel program; MIMARI §8.6) eklemeleri — yalnız eklemeli, varsayılanlar web davranışını korur:
  "bina_coz" girdi.anlat ya da ayarlar.anlat (varsayılan true): false ise motor anlatımsız çözer (`anlat=False`), yanıtta
                    "bloklar": [] olur; "veri" anlatımlı çözümle aynıdır (op4 F5 çözümü bunu kullanır).
  "bina_kimlik":    girdi {"bina"} → {"cozum_kimligi": yapi.cozum_kimligi(bina) (çözmeden; bina_coz veri.cozum_kimligi ile
                    aynı), "onbellekte": bu çözüm köprünün önbelleğinde mi, "hata": null}. op4 .op4 açılışında saklı sonuçların
                    modele ait olup olmadığını bununla denetler.
  ayarlar.sd_siniri (isteğe bağlı, bütün bina işlemleri): istek süresince yapi.EN_FAZLA_SD ve yapi_serbest.EN_FAZLA_SD bu
                    değere, temel.EN_KUCUK_AG 0,10·√(1500/sd_siniri) m'ye (en az 0,02 m; yalnız sd_siniri > 1500 iken)
                    çekilir; istek bitince eski değerler geri yüklenir. Bu durumda "tarayıcı sınırı" iletileri "bellek ve süre
                    sınırı" diye yazılır.
  İptal: hesap sırasında KeyboardInterrupt (op4 motor sunucusu `_thread.interrupt_main` ile keser) →
                    {"hata": "İşlem iptal edildi.", "hata_turu": "iptal"}. MemoryError → öğretici "ic" hatası.
"""
from __future__ import annotations

import ast
import importlib
import json
import math
import sys
import time
import traceback
from collections import OrderedDict

import sympy as sp

import matris_ogren as mo

mo.ayarla(goster="yok")

ISLEMLER = {
    "topla", "cikar", "skaler", "carp", "transpoz", "iz", "rank", "determinant", "ters", "coz", "ozdeger",
    "cubuk_eleman", "kiris_eleman", "kafes_eleman", "birlestir", "sinir_kosulu", "yardim",
}


def surum_json() -> str:
    return json.dumps({
        "motor": getattr(mo, "__version__", "?"),
        "sympy": sp.__version__,
        "python": sys.version.split()[0],
    })


# ---------------------------------------------------------------------------
# yardımcılar
# ---------------------------------------------------------------------------
def _sayi_listesi(v) -> list[int]:
    """'1 4' / '1,4' / [1, 4] → [1, 4]"""
    if isinstance(v, (list, tuple)):
        return [int(x) for x in v]
    return [int(p) for p in str(v).replace(",", " ").replace(";", " ").split()]


def _sayi(v):
    """Açı gibi sayısal alanlar: '45' → 45, '22.5' → 22.5"""
    s = str(v).strip()
    try:
        return int(s)
    except ValueError:
        return float(sp.sympify(s))


def _metin(d) -> str:
    """Sonucu yeniden girdi olarak kullanılabilecek 'a b; c d' metnine çevirir."""
    if isinstance(d, sp.MatrixBase):
        return "; ".join(" ".join(str(d[i, j]) for j in range(d.cols)) for i in range(d.rows))
    if isinstance(d, tuple) and d and isinstance(d[0], (list, tuple)):  # ozdeger: (degerler, ozvektorler)
        return " ".join(str(x) for x in d[0])
    return str(d)


def _zincir(d) -> bool:
    return isinstance(d, (sp.MatrixBase, sp.Expr))


def _latex(islem: str, r) -> str:
    d = r.deger
    if islem == "ozdeger":
        ozd = d[0] if isinstance(d, tuple) else d
        return r",\quad ".join(rf"\lambda_{{{i + 1}}} = {mo.L(x)}" for i, x in enumerate(ozd))
    try:
        return r.latex()
    except Exception:
        return sp.latex(d)


def _etiket(islem: str, ad) -> str:
    if islem == "ozdeger" or not ad:
        return ""
    ozel = {
        "det": r"\det(\mathbf{A})",
        "tr": r"\operatorname{tr}(\mathbf{A})",
        "rank": r"\operatorname{rank}(\mathbf{A})",
        "A^T": r"\mathbf{A}^{T}",
        "A^{-1}": r"\mathbf{A}^{-1}",
    }
    if ad in ozel:
        return ozel[ad]
    return rf"\mathbf{{{ad}}}"


def _sema(icerik) -> dict:
    """Ok şeması bloğunu JSON'a güvenli biçime getirir: {"baslik": str, "kareler": [{"baslik": str, "svg": str}]}.

    Motor her kareyi eksiksiz, durağan bir SVG olarak üretir (metinleri kaçışlıdır); burada yalnız tür/boşluk
    denetimi yapılır. SVG'siz kareler atılır."""
    if not isinstance(icerik, dict):
        return {"baslik": "", "kareler": []}
    kareler = []
    for k in icerik.get("kareler") or []:
        if isinstance(k, dict) and str(k.get("svg", "")).strip():
            kareler.append({"baslik": str(k.get("baslik", "")), "svg": str(k["svg"])})
    return {"baslik": str(icerik.get("baslik", "")), "kareler": kareler}


def _bloklar(anl) -> list[dict]:
    cikti = []
    for tur, icerik, etiket in anl.bloklar:
        if tur == "kod":
            baslik, kod, ck = icerik
            cikti.append({"tur": "kod", "baslik": baslik, "kod": kod, "cikti": ck, "etiket": etiket})
        elif tur == "sema":
            sema = _sema(icerik)
            if sema["kareler"]:
                cikti.append({"tur": "sema", "icerik": sema, "etiket": etiket})
        else:
            cikti.append({"tur": tur, "icerik": icerik, "etiket": etiket})
    return cikti


def _liste(g: dict, anahtar: str) -> list:
    v = g.get(anahtar)
    return list(v) if isinstance(v, (list, tuple)) else []


def _bos(v) -> bool:
    return v is None or not str(v).strip()


# ---------------------------------------------------------------------------
# işlem dağıtıcı
# ---------------------------------------------------------------------------
def _calistir(islem: str, g: dict):
    A, B = g.get("A", ""), g.get("B", "")
    if islem in ("topla", "cikar", "skaler", "transpoz", "iz", "rank", "determinant", "ters", "coz", "ozdeger") and _bos(A):
        raise mo.MatrisHatasi("A matrisini girin (örnek: 1 2; 3 4).")

    if islem in ("topla", "cikar"):
        if _bos(B):
            raise mo.MatrisHatasi("B matrisini girin.")
        return getattr(mo, islem)(A, B)
    if islem == "skaler":
        return mo.skaler(g.get("k") if not _bos(g.get("k")) else "1", A)
    if islem == "carp":
        m = [x for x in _liste(g, "matrisler") if not _bos(x)]
        if len(m) < 2:
            raise mo.MatrisHatasi("Çarpım için en az iki matris girin.")
        return mo.carp(*m)
    if islem in ("transpoz", "iz", "rank"):
        return getattr(mo, islem)(A)
    if islem == "determinant":
        kw = {"yontem": g["yontem"]} if not _bos(g.get("yontem")) else {}
        return mo.determinant(A, **kw)
    if islem == "ters":
        kw = {"yontem": g["yontem"]} if not _bos(g.get("yontem")) else {}
        return mo.ters(A, **kw)
    if islem == "coz":
        b = g.get("b", "")
        if _bos(b):
            raise mo.MatrisHatasi("b vektörünü girin (örnek: 3; 5).")
        kw = {}
        if not _bos(g.get("yontem")):
            kw["yontem"] = g["yontem"]
        if not _bos(g.get("bilinmeyen")):
            kw["bilinmeyen"] = str(g["bilinmeyen"]).strip()
        return mo.coz(A, b, **kw)
    if islem == "ozdeger":
        M = g.get("M")
        return mo.ozdeger(A, None if _bos(M) else M, ozvektor=bool(g.get("ozvektor", True)))
    if islem == "cubuk_eleman":
        return mo.cubuk_eleman(g.get("E") or "E", g.get("A") or "A", g.get("L") or "L")
    if islem == "kiris_eleman":
        return mo.kiris_eleman(g.get("E") or "E", g.get("I") or "I", g.get("L") or "L")
    if islem == "kafes_eleman":
        aci = g.get("aci")
        return mo.kafes_eleman(g.get("E") or "E", g.get("A") or "A", g.get("L") or "L",
                               aci_derece=0 if _bos(aci) else _sayi(aci))
    if islem == "birlestir":
        elemanlar = []
        for i, e in enumerate(_liste(g, "elemanlar"), start=1):
            k, dof = (e.get("k"), e.get("dof")) if isinstance(e, dict) else (e[0], e[1])
            if _bos(k):
                continue
            try:
                dof_l = _sayi_listesi(dof)
            except ValueError:
                raise mo.MatrisHatasi(f"Eleman {i}: serbestlik numaraları tam sayı olmalı (örnek: 1 2).") from None
            if not dof_l:
                raise mo.MatrisHatasi(f"Eleman {i}: global serbestlik numaralarını girin (örnek: 1 2).")
            elemanlar.append((k, dof_l))
        if not elemanlar:
            raise mo.MatrisHatasi("En az bir eleman matrisi girin.")
        n = g.get("n")
        if _bos(n):
            raise mo.MatrisHatasi("Toplam serbestlik sayısını girin.")
        try:
            n_int = int(str(n).strip())
        except ValueError:
            raise mo.MatrisHatasi("Toplam serbestlik sayısı tam sayı olmalı.") from None
        return mo.birlestir(elemanlar, n_int)
    if islem == "sinir_kosulu":
        K, F = g.get("K", ""), g.get("F", "")
        if _bos(K) or _bos(F):
            raise mo.MatrisHatasi("K matrisini ve F vektörünü girin.")
        try:
            sabit = _sayi_listesi(g.get("sabit", ""))
        except ValueError:
            raise mo.MatrisHatasi("Tutulu (sabit) serbestlik dereceleri (SD) tam sayı olmalı (örnek: 1 4).") from None
        # Boş bırakılırsa motor mesnetsiz durumu kendisi değerlendirir (K tekilse öğretici hata verir).
        kw = {}
        if not _bos(g.get("bilinmeyen")):
            kw["bilinmeyen"] = str(g["bilinmeyen"]).strip()
        return mo.sinir_kosulu(K, F, sabit, **kw)
    raise mo.MatrisHatasi(f"Bilinmeyen işlem: {islem!r}")


# ---------------------------------------------------------------------------
# ders örneği çalıştırma ("ders_calistir")
# ---------------------------------------------------------------------------
KOD_EN_FAZLA = 6000


def _se_modulu():
    """sonlu_eleman.py varsa (tembel) içe aktarır; yoksa None. Eski kurulumlarda dosya bulunmayabilir."""
    try:
        return importlib.import_module("sonlu_eleman")
    except ImportError:
        return None


def _yapi_modulu():
    """yapi.py (bina analizi) varsa (tembel) içe aktarır; yoksa None. sonlu_eleman.py'ye bağımlıdır."""
    try:
        return importlib.import_module("yapi")
    except ImportError:
        return None


def _tasarim_modulu():
    """tasarim.py (TS 500 / ÇYTHYE kesit tahkikleri) varsa (tembel) içe aktarır; yoksa None."""
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def _rapor_modulu():
    """rapor.py (statik hesap raporu) varsa (tembel) içe aktarır; yoksa None."""
    try:
        return importlib.import_module("rapor")
    except ImportError:
        return None


def _alan_modulu():
    """alan.py (ısı haritası alanları: çubuk boyunca iç kuvvet, gerilme, eğri yer değiştirme; döşeme plakları) varsa; yoksa None."""
    try:
        return importlib.import_module("alan")
    except ImportError:
        return None


def _sonuc_mu(x) -> bool:
    return isinstance(x, mo.Sonuc) or (hasattr(x, "anlatim") and hasattr(x, "deger") and hasattr(x.anlatim, "bloklar"))


def _kod_calistir(kod: str):
    """Ders örneği kodunu çalıştırır; son satırdaki ifadenin değerini döndürür (testler/test_dersler.calistir ile aynı):
    son deyim ayrılır, kalanı exec edilir, son ifade eval edilir. Ad alanı: mo, sp ve varsa se, yapi, tasarim."""
    agac = ast.parse(kod)
    if not agac.body:
        raise mo.MatrisHatasi("Örnek kodu boş.")
    son = agac.body.pop()
    if not isinstance(son, ast.Expr):
        raise mo.MatrisHatasi("Örnek kodunun son satırı bir değer (ifade) olmalı.")
    ad_alani = {"mo": mo, "sp": sp}
    se = _se_modulu()
    if se is not None:
        ad_alani["se"] = se
    yapi = _yapi_modulu()
    if yapi is not None:
        ad_alani["yapi"] = yapi
    tasarim = _tasarim_modulu()
    if tasarim is not None:
        ad_alani["tasarim"] = tasarim
    exec(compile(agac, "<ornek>", "exec"), ad_alani)
    return eval(compile(ast.Expression(son.value), "<ornek>", "eval"), ad_alani)


def _ders_yaniti(deger) -> dict:
    """Örnek kodunun değerini normal işlem yanıtı biçimine çevirir (uygulama aynı çiziciyi kullanır)."""
    if isinstance(deger, (list, tuple)) and deger and all(_sonuc_mu(x) for x in deger):
        bloklar = []
        for i, r in enumerate(deger, start=1):
            bloklar.append({"tur": "md", "icerik": f"#### {i}. adım" + (f": {r.ad}" if r.ad else ""), "etiket": "adim"})
            bloklar += _bloklar(r.anlatim)
        son = deger[-1]
        return {
            "ad": son.ad, "bloklar": bloklar,
            "sonuc_etiket": _etiket("ders", son.ad), "sonuc_latex": _latex("ders", son),
            "sonuc_metin": _metin(son.deger), "zincir": _zincir(son.deger), "hata": None,
        }
    if _sonuc_mu(deger):
        return {
            "ad": deger.ad, "bloklar": _bloklar(deger.anlatim),
            "sonuc_etiket": _etiket("ders", deger.ad), "sonuc_latex": _latex("ders", deger),
            "sonuc_metin": _metin(deger.deger), "zincir": _zincir(deger.deger), "hata": None,
        }
    if deger is None:
        raise mo.MatrisHatasi("Örnek kodu bir değer döndürmedi.")
    if isinstance(deger, str):
        return {"ad": "", "bloklar": [{"tur": "md", "icerik": deger, "etiket": "sonuc"}],
                "sonuc_etiket": "", "sonuc_latex": "", "sonuc_metin": deger, "zincir": False, "hata": None}
    if isinstance(deger, (bool, int, float, complex)):
        deger = sp.sympify(deger)
    tex = sp.latex(deger)
    return {"ad": "", "bloklar": [{"tur": "math", "icerik": tex, "etiket": "sonuc"}],
            "sonuc_etiket": "", "sonuc_latex": tex, "sonuc_metin": _metin(deger), "zincir": _zincir(deger), "hata": None}


def _ders_calistir(girdi: dict) -> dict:
    kod = girdi.get("kod")
    if not isinstance(kod, str) or not kod.strip():
        raise mo.MatrisHatasi("Örnek kodu boş.")
    if len(kod) > KOD_EN_FAZLA:
        raise mo.MatrisHatasi(f"Örnek kodu çok uzun ({len(kod)} karakter; en fazla {KOD_EN_FAZLA}).")
    try:
        deger = _kod_calistir(kod)
    except mo.MatrisHatasi:
        raise
    except Exception as e:  # noqa: BLE001 — sözdizimi, ad ve çalışma hataları öğrenciye okunur biçimde gider
        # Ders kodunun kendi hatası (sözdizimi, NameError…) "girdi" hatası gibi, izsiz bildirilir.
        raise mo.MatrisHatasi(f"Örnek kodu çalışmadı: {type(e).__name__}: {e}") from e
    return _ders_yaniti(deger)


# ---------------------------------------------------------------------------
# sonlu eleman ("se_coz", "se_ornekler", "se_ornek")
# ---------------------------------------------------------------------------
SE_ISLEMLER = {"se_coz", "se_ornekler", "se_ornek"}
SE_MODEL_EN_FAZLA = 200_000   # model JSON metni için üst sınır (karakter)


def _se_zorunlu():
    se = _se_modulu()
    if se is None:
        raise mo.MatrisHatasi("Sonlu eleman modülü (sonlu_eleman.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    return se


def _sonlu_sayilar(v):
    """JSON'a uygun olmayan sayıları (nan, ±inf) None yapar; tarayıcıdaki JSON.parse bunları okuyamaz."""
    if isinstance(v, float):
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    if isinstance(v, dict):
        return {k: _sonlu_sayilar(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_sonlu_sayilar(x) for x in v]
    return v


def _se_coz_yaniti(girdi: dict) -> dict:
    """{"model": {...} ya da JSON metni} → matris işlemleriyle aynı yanıt biçimi + "veri" (yapılı sonuçlar)."""
    se = _se_zorunlu()
    model = girdi.get("model")
    if model is None or (isinstance(model, str) and not model.strip()):
        raise mo.MatrisHatasi("Model boş: düğüm, eleman, mesnet ve yük tanımlayın ya da bir örnek seçin.")
    if isinstance(model, str) and len(model) > SE_MODEL_EN_FAZLA:
        raise mo.MatrisHatasi(f"Model metni çok uzun ({len(model)} karakter; en fazla {SE_MODEL_EN_FAZLA}).")
    r = se.se_coz(model)
    return {
        "ad": r.ad, "bloklar": _bloklar(r.anlatim),
        "sonuc_etiket": _etiket("se_coz", r.ad), "sonuc_latex": _latex("se_coz", r),
        "sonuc_metin": _metin(r.deger), "zincir": False, "hata": None,
        "veri": _sonlu_sayilar(r.veri),
    }


def _se_islem(islem: str, girdi: dict) -> dict:
    if islem == "se_coz":
        return _se_coz_yaniti(girdi)
    se = _se_zorunlu()
    if islem == "se_ornekler":
        return {"ornekler": se.ornek_listesi(), "hata": None}
    ad = str(girdi.get("ad", "")).strip()
    return {"ad": ad, "model": se.ornek_model(ad), "hata": None}


# ---------------------------------------------------------------------------
# bina analizi ("bina_coz", "bina_kutuphane", "bina_sablonlar", "bina_sablon", "bina_yuk_yolu", "bina_deprem",
# "bina_kombinasyon", "bina_eleman_tasarim", "bina_rapor", "bina_tablolar", "bina_alan", "bina_kesit_oner", "bina_eleman_bilgi")
# ---------------------------------------------------------------------------
BINA_ISLEMLER = {"bina_coz", "bina_sablonlar", "bina_sablon", "bina_kutuphane", "bina_yuk_yolu", "bina_deprem", "bina_kombinasyon",
                 "bina_eleman_tasarim", "bina_rapor", "bina_tablolar", "bina_alan", "bina_kesit_oner", "bina_eleman_bilgi"}
BINA_EN_FAZLA = 300_000   # bina JSON metni için üst sınır (karakter)
BINA_ONBELLEK_EN_FAZLA = 3   # tembel kombinasyonlar ve eleman tahkik ayrıntısı için bellekte tutulan son çözüm sayısı
_BINA_ONBELLEK: "OrderedDict[str, dict]" = OrderedDict()


def _onbellege_koy(ic: dict) -> None:
    kimlik = ic.get("kimlik")
    if not kimlik:
        return
    _BINA_ONBELLEK.pop(kimlik, None)
    _BINA_ONBELLEK[kimlik] = ic
    while len(_BINA_ONBELLEK) > BINA_ONBELLEK_EN_FAZLA:
        _BINA_ONBELLEK.popitem(last=False)


def _yapi_zorunlu():
    yapi = _yapi_modulu()
    if yapi is None:
        raise mo.MatrisHatasi("Bina modülü (yapi.py / yapi_veri.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    return yapi


def _bina_girdisi(girdi: dict):
    bina = girdi.get("bina")
    if bina is None or (isinstance(bina, str) and not bina.strip()):
        raise mo.MatrisHatasi("Bina modeli boş: akslar, katlar, kolon/kiriş/döşeme tanımlayın ya da bir şablon seçin.")
    if isinstance(bina, str) and len(bina) > BINA_EN_FAZLA:
        raise mo.MatrisHatasi(f"Bina metni çok uzun ({len(bina)} karakter; en fazla {BINA_EN_FAZLA}).")
    return bina


def _sure_ms(t0: float) -> int:
    """time.perf_counter() başlangıcından bu yana geçen duvar süresi (ms, tam sayı; C19 sure_ms)."""
    return int(round((time.perf_counter() - t0) * 1000.0))


def _anlat_mi(girdi: dict, ayar: dict | None) -> bool:
    """op4 eki (MIMARI §8.6.1): girdi.anlat, yoksa ayarlar.anlat; ikisi de yoksa true (web davranışı)."""
    for kaynak in (girdi, ayar or {}):
        if isinstance(kaynak, dict) and kaynak.get("anlat") is not None:
            return bool(kaynak.get("anlat"))
    return True


def _bina_coz_yaniti(girdi: dict, ayar: dict | None = None) -> dict:
    t0 = time.perf_counter()
    yapi = _yapi_zorunlu()
    bina = _bina_girdisi(girdi)
    anlat = _anlat_mi(girdi, ayar)
    r = yapi.bina_coz(bina, goster="yok") if anlat else yapi.bina_coz(bina, goster="yok", anlat=False)
    veri = _sonlu_sayilar(r.veri)   # ozet.uyarilar: yalnız bu modelde kullanılan doğrulanmamış kayıtlar (motor yazar)
    sure = _sure_ms(t0)
    if isinstance(veri.get("ozet"), dict):
        veri["ozet"]["cozum_sure_ms"] = sure
    ic = getattr(r, "ic", None)
    if isinstance(ic, dict):        # rapor/tablolar yeniden çözmeden üretilsin diye çözüm verisi ve model de saklanır
        if isinstance(bina, str):
            try:
                bina = json.loads(bina)
            except ValueError:
                pass
        ic["veri"], ic["bina"] = veri, bina
        _onbellege_koy(ic)
    return {
        "ad": "bina", "bloklar": _bloklar(r.anlatim) if anlat else [],
        "sonuc_etiket": r"\mathbf{u}_G", "sonuc_latex": "",
        "sonuc_metin": f"{veri['ozet']['sd_sayisi']} SD, {veri['ozet']['kombinasyon_sayisi']} kombinasyon; "
                       f"G = {veri['ozet']['toplam_G']} kN, Q = {veri['ozet']['toplam_Q']} kN",
        "zincir": False, "hata": None, "veri": veri, "sure_ms": sure,
    }


def _bina_kombinasyon_yaniti(girdi: dict) -> dict:
    """Tek kombinasyonun tam KISA'sı: önce önbellekteki çözüm (cozum_kimligi), yoksa girdi.bina anlatımsız yeniden çözülür."""
    yapi = _yapi_zorunlu()
    ad = str(girdi.get("ad") or "").strip()
    if not ad:
        raise mo.MatrisHatasi("Kombinasyon adı (ad) boş; örn. \"1.4G+1.6Q\" ya da \"G+Q+0.2S+EX++0.3EY++0.3EZ\".")
    katsayilar = girdi.get("katsayilar")
    if katsayilar is not None and not isinstance(katsayilar, dict):
        raise mo.MatrisHatasi("katsayilar bir sözlük olmalı: {\"G\": 1.4, \"Q\": 1.6}.")
    ic = _bina_ic(yapi, girdi)
    sonuc = yapi.kombinasyon_kisa(ic, ad, katsayilar)
    return {"ad": ad, "cozum_kimligi": ic.get("kimlik"), "sonuc": _sonlu_sayilar(sonuc), "hata": None}


def _bina_ic(yapi, girdi: dict) -> dict:
    """Önbellekteki çözüm paketi (cozum_kimligi); yoksa girdi.bina anlatımsız yeniden çözülür ve önbelleğe konur."""
    kimlik = girdi.get("cozum_kimligi")
    ic = _BINA_ONBELLEK.get(str(kimlik)) if kimlik else None
    if ic is not None:
        _BINA_ONBELLEK.move_to_end(str(kimlik))
    elif girdi.get("bina") is not None:
        bina = _bina_girdisi(girdi)
        r = yapi.bina_coz(bina, goster="yok", anlat=False)
        ic = r.ic
        ic["veri"], ic["bina"] = _sonlu_sayilar(r.veri), bina
        _onbellege_koy(ic)
    else:
        raise mo.MatrisHatasi("Bu çözüm bellekte yok (sayfa yenilendi ya da son " + str(BINA_ONBELLEK_EN_FAZLA)
                              + " çözümün dışında kaldı). Binayı yeniden çözün; kombinasyonlar ve kesit tahkikleri, çözümde hesaplanan "
                              "G, Q, S, W ve E durumlarının katsayılı toplamından kurulur (yeniden çözüm gerekmez, ama durumların "
                              "bellekte olması gerekir).")
    return ic


def _bina_eleman_tasarim_yaniti(girdi: dict) -> dict:
    """Tek bina elemanının anlatımlı kesit tahkiki (tasarim.py): önbellekteki çözümden, yoksa girdi.bina yeniden çözülür."""
    yapi = _yapi_zorunlu()
    if not hasattr(yapi, "eleman_tasarim"):
        raise mo.MatrisHatasi("Bu kurulumdaki bina modülü kesit tahkiki içermiyor; uygulamayı yenileyin.")
    tur = str(girdi.get("tur") or "").strip().lower()
    if girdi.get("no") is None:
        raise mo.MatrisHatasi("Eleman numarası (no) verilmedi: bina kirişinin ya da kolonunun no'su.")
    ic = _bina_ic(yapi, girdi)
    if tur not in ("kiris", "kolon") and not ic.get("serbest"):
        raise mo.MatrisHatasi("Eleman türü (tur) 'kiris' ya da 'kolon' olmalı.")
    r = yapi.eleman_tasarim(ic, tur, girdi.get("no"), goster="yok")
    return {"ad": r.ad, "bloklar": _bloklar(r.anlatim), "sonuc": _sonlu_sayilar(r.veri), "cozum_kimligi": ic.get("kimlik"),
            "hata": None}


_GENEL_ONBELLEK: "OrderedDict[str, dict]" = OrderedDict()   # aks–kat çözüm kimliği → genel motorla çözüm (kesit önerisi)


def _genel_ic(serbest, ic: dict) -> dict:
    """Aks–kat çözümünün (önbellekteki ``ic``) kesit önerisi için genel motor paketi: ilk istekte çözülür (büyük binada ~1 s),
    sonraki tıklamalarda önbellekten (en çok BINA_ONBELLEK_EN_FAZLA kayıt)."""
    kimlik = str(ic.get("kimlik") or "")
    g = _GENEL_ONBELLEK.get(kimlik) if kimlik else None
    if g is not None:
        _GENEL_ONBELLEK.move_to_end(kimlik)
        return g
    if ic.get("bina") is None:
        raise mo.MatrisHatasi("Bu çözümün bina modeli bellekte yok; binayı yeniden çözün.")
    g = serbest.genel_cozum(ic["bina"])
    if kimlik:
        _GENEL_ONBELLEK[kimlik] = g
        while len(_GENEL_ONBELLEK) > BINA_ONBELLEK_EN_FAZLA:
            _GENEL_ONBELLEK.popitem(last=False)
    return g


def _bina_kesit_oner_yaniti(girdi: dict) -> dict:
    """Kesit önerisi (genel model motoru; aks–kat çözümü genel motorla yeniden çözülür ve önbelleğe alınır, D/C önce görünen
    aks–kat tasarım tablosundan): öneri, gerekçe, D/C önce/sonra, uygula (C4)."""
    t0 = time.perf_counter()
    _yapi_zorunlu()
    try:
        serbest = importlib.import_module("yapi_serbest")
    except ImportError:
        raise mo.MatrisHatasi("Kesit önerisi için yapi_serbest.py gerekir; uygulamayı yenileyin.") from None
    kimlik = girdi.get("cozum_kimligi")
    ic = _BINA_ONBELLEK.get(str(kimlik)) if kimlik else None
    if ic is not None:
        _BINA_ONBELLEK.move_to_end(str(kimlik))
    bina = girdi.get("bina")
    if ic is None and bina is None:
        raise mo.MatrisHatasi("Kesit önerisi için çözüm kimliği (önbellekte) ya da bina gerekir; binayı yeniden çözün.")
    if bina is not None:
        bina = _bina_girdisi(girdi)
    hedef = girdi.get("hedef", "hepsi")
    if hedef not in (None, "hepsi") and not isinstance(hedef, list):
        raise mo.MatrisHatasi('hedef "hepsi" ya da [{"tur": "cubuk", "no": 3}] listesi olmalı.')
    yinele = girdi.get("yinele", 0)
    grup = bool(girdi.get("grup"))
    if ic is not None and not ic.get("serbest"):          # aks–kat çözümü: genel motor paketi önbellekten, D/C önce görünenden
        r = serbest.kesit_oner(None, ic=_genel_ic(serbest, ic), hedef=hedef or "hepsi", yinele=yinele, gorunen=ic, grup=grup)
    elif ic is not None:
        r = serbest.kesit_oner(None, ic=ic, hedef=hedef or "hepsi", yinele=yinele, grup=grup)
    else:
        r = serbest.kesit_oner(bina, hedef=hedef or "hepsi", yinele=yinele, grup=grup)
    return dict(_sonlu_sayilar(r), hata=None, sure_ms=_sure_ms(t0))


def _bina_rapor_yaniti(girdi: dict) -> dict:
    """Statik hesap raporu (rapor.py): önbellekteki çözümün verisinden (yeniden çözmeden); kimlik önbellekte yoksa girdi.bina
    anlatımsız çözülür. Yanıt: {"html", "dosya_adi", "cozum_kimligi", "hata"}."""
    yapi = _yapi_zorunlu()
    rapor = _rapor_modulu()
    if rapor is None:
        raise mo.MatrisHatasi("Rapor modülü (rapor.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    secenek = girdi.get("secenek")
    if secenek is not None and not isinstance(secenek, dict):
        raise mo.MatrisHatasi("secenek bir sözlük olmalı: {\"proje\": {\"ad\": ...}, \"eleman_detay\": \"kritik\"}.")
    if not girdi.get("cozum_kimligi") and girdi.get("bina") is None:
        raise mo.MatrisHatasi("Rapor girdisi boş: önce binayı çözün ve çözüm kimliğini (cozum_kimligi) ya da bina modelini (bina) "
                              "gönderin.")
    ic = _bina_ic(yapi, girdi)
    veri = ic.get("veri")
    if veri is None:                 # önbellekteki eski paket (veri saklanmamış): model verilmişse yeniden çöz
        if girdi.get("bina") is None:
            raise mo.MatrisHatasi("Bu çözümün verisi bellekte yok; binayı yeniden çözün ya da girdide 'bina' modelini de gönderin.")
        r = yapi.bina_coz(_bina_girdisi(girdi), goster="yok", anlat=False)
        ic = r.ic
        ic["veri"], ic["bina"] = _sonlu_sayilar(r.veri), girdi.get("bina")
        _onbellege_koy(ic)
        veri = ic["veri"]
    if ic.get("tas_tam") is not None:        # genel model: yanıtta kısaltılan kontrol satırlarının tamamı raporda
        veri = dict(veri, tasarim=_sonlu_sayilar(ic["tas_tam"]))
    bina = girdi.get("bina") if girdi.get("bina") is not None else ic.get("bina")
    html = rapor.statik_rapor(bina if bina is not None else {}, veri, secenek=secenek)
    return {"html": html, "dosya_adi": rapor.dosya_adi(bina if bina is not None else {}, veri, secenek),
            "cozum_kimligi": ic.get("kimlik"), "hata": None}


def _tablolar_modulu():
    """tablolar.py (tablo editörü ve metraj) varsa (tembel) içe aktarır; yoksa None."""
    try:
        return importlib.import_module("tablolar")
    except ImportError:
        return None


def _bina_tablolar_yaniti(girdi: dict) -> dict:
    """Tablo editörü: önbellekteki çözüm (kimlik eşleşirse) ile bütün tablolar; yoksa çözmeden model/yük/metraj tabloları."""
    yapi = _yapi_zorunlu()
    tb = _tablolar_modulu()
    if tb is None:
        raise mo.MatrisHatasi("Tablo modülü (tablolar.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    kimlik = girdi.get("cozum_kimligi")
    bina = girdi.get("bina")
    if bina is not None:
        bina = _bina_girdisi(girdi)
        if isinstance(bina, str):
            try:
                bina = json.loads(bina)
            except ValueError as e:
                raise mo.MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
        try:   # verilen binanın kimliği: önbellekteki çözüm ancak aynı binaya aitse kullanılır (düzenlenmiş binada eski sonuç yok);
            # genel modelde yapi_serbest okuyucusuyla (yapi.cozum_kimligi: bina_coz ile aynı kimlik)
            kimlik = (yapi.cozum_kimligi(bina) if hasattr(yapi, "cozum_kimligi")
                      else yapi._cozum_kimligi(yapi._bina_oku(bina)))
        except mo.MatrisHatasi:
            kimlik = None
    ic = _BINA_ONBELLEK.get(str(kimlik)) if kimlik else None
    if ic is not None and ic.get("veri") is not None:
        _BINA_ONBELLEK.move_to_end(str(kimlik))
        tablolar = tb.bina_tablolari(bina if bina is not None else ic.get("bina"), ic["veri"])
        return {"tablolar": _sonlu_sayilar(tablolar), "cozum_kimligi": kimlik, "cozumlu": True, "hata": None}
    if bina is None:
        raise mo.MatrisHatasi("Bu çözüm bellekte yok (sayfa yenilendi ya da son " + str(BINA_ONBELLEK_EN_FAZLA)
                              + " çözümün dışında kaldı); tablolar için 'bina' alanını da gönderin ya da binayı yeniden çözün.")
    return {"tablolar": _sonlu_sayilar(tb.bina_tablolari(bina)), "cozum_kimligi": None, "cozumlu": False, "hata": None}


ALAN_ISTASYON = (2, 61)   # bina_alan istasyon sayısı sınırları


def _bina_alan_yaniti(girdi: dict) -> dict:
    """Isı haritası alanı (alan.py §16): önbellekteki çözümden durum / kombinasyon / zarf için eleman ve döşeme alanları."""
    yapi = _yapi_zorunlu()
    alan = _alan_modulu()
    if alan is None:
        raise mo.MatrisHatasi("Isı haritası modülü (alan.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    durum = str(girdi.get("durum") or "").strip()
    if not durum:
        raise mo.MatrisHatasi("Durum (durum) boş: bir yük durumu (G, Q…), kombinasyon adı (örn. \"1.4G+1.6Q\") ya da "
                              "\"zarf+\" / \"zarf-\" verin.")
    istasyon = girdi.get("istasyon")
    try:
        istasyon = alan.ISTASYON if istasyon is None else int(istasyon)
    except (TypeError, ValueError):
        raise mo.MatrisHatasi(f"istasyon bir tamsayı olmalı ({ALAN_ISTASYON[0]}…{ALAN_ISTASYON[1]}).") from None
    if not ALAN_ISTASYON[0] <= istasyon <= ALAN_ISTASYON[1]:
        raise mo.MatrisHatasi(f"istasyon {ALAN_ISTASYON[0]}…{ALAN_ISTASYON[1]} arasında olmalı (verilen {istasyon}).")
    katsayilar = girdi.get("katsayilar")
    if katsayilar is not None and not isinstance(katsayilar, dict):
        raise mo.MatrisHatasi("katsayilar bir sözlük olmalı: {\"G\": 1.4, \"Q\": 1.6}.")
    elemanlar = girdi.get("elemanlar")
    if elemanlar is not None:
        if not isinstance(elemanlar, list):
            raise mo.MatrisHatasi("elemanlar bir FE eleman numarası listesi olmalı: [12, 13].")
        elemanlar = _sayi_listesi(elemanlar)
    ic = _bina_ic(yapi, girdi)
    sonuc = alan.eleman_alanlari(ic, durum, istasyon=istasyon, katsayilar=katsayilar, elemanlar=elemanlar,
                                 paneller=elemanlar is None)
    return {"alan": _sonlu_sayilar(sonuc), "cozum_kimligi": ic.get("kimlik"), "hata": None}


def _sayi_tr(v, n=2) -> str:
    """Bilgi paneli hücresi: n ondalık, virgül ve gerçek eksi işareti (eleman_bilgi.js f() ile aynı biçim); sayı değilse '—'."""
    if not isinstance(v, (int, float)) or v != v or v in (float("inf"), float("-inf")):
        return "—"
    t = f"{float(v):.{n}f}"
    if t.lstrip("-").strip("0.") == "":
        t = t.lstrip("-")
    return t.replace(".", ",").replace("-", "−")


_BILGI_KUVVET = (("N", "kN"), ("Vy", "kN"), ("Vz", "kN"), ("T", "kN·m"), ("My", "kN·m"), ("Mz", "kN·m"))
_BILGI_EK = (("sigma_max", "σ maks", "MPa", 2), ("sigma_min", "σ min", "MPa", 2), ("von_mises", "von Mises", "MPa", 2),
             ("tau_max", "τ maks", "MPa", 2), ("kullanim", "Kullanım", "", 3), ("u", "|u| (eğri yer değiştirme)", "mm", 3))


def _bina_eleman_bilgi_yaniti(girdi: dict) -> dict:
    """Eleman bilgi paneli 'Motor ayrıntısı' paketi (alan.eleman_bilgi_alani; önbellekteki çözümden, yeniden çözmeden):
    ``ic`` sekmesi parça başına istasyon iç kuvvetleri ve en büyük değerler, ``yer`` sekmesi uç yer değiştirmeleri (bina ve yerel
    eksen) ve eğri yer değiştirmenin (sehim) en büyüğü. Bölümler docs/eleman_bilgi.js biçiminde ({baslik, tablo, satirlar, not})."""
    yapi = _yapi_zorunlu()
    alan = _alan_modulu()
    if alan is None:
        raise mo.MatrisHatasi("Isı haritası modülü (alan.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    tur = str(girdi.get("tur") or "").strip().lower()
    if tur not in ("cubuk", "kolon", "kiris", "fe"):
        raise mo.MatrisHatasi("Eleman türü (tur) 'cubuk', 'kolon', 'kiris' ya da 'fe' olmalı.")
    if girdi.get("no") is None:
        raise mo.MatrisHatasi("Eleman numarası (no) verilmedi.")
    durum = str(girdi.get("durum") or "G").strip()
    if durum.lower() == "zarf":
        durum = "zarf+"
    ic = _bina_ic(yapi, girdi)
    p = alan.eleman_bilgi_alani(ic, tur, girdi.get("no"), durum)
    zarf = durum.startswith("zarf")
    coklu = len(p["parcalar"]) > 1
    ic_b, yer_b = [], []
    for kay in p["parcalar"]:
        ek = f" — parça {kay.get('parca')}, FE {kay['no']}" if coklu else f" — FE {kay['no']}"
        sat = []
        for i, x in enumerate(kay["x"]):
            sat.append([_sayi_tr(x, 3)] + [_sayi_tr(kay[a][i], 2) for a, _ in _BILGI_KUVVET])
        ic_b.append({"baslik": f"İstasyon iç kuvvetleri ({p['durum']}){ek}", "acilir": coklu,
                     "tablo": {"basliklar": ["x (m)"] + [f"{a} ({b})" for a, b in _BILGI_KUVVET], "satirlar": sat}})
    en = p.get("en_buyuk") or {}
    sat = []
    for a, b in _BILGI_KUVVET:
        e = en.get(a)
        if e:
            sat.append([f"{a} ({b})", _sayi_tr(e["deger"], 2), _sayi_tr(e["x"], 3), str(e["fe"])])
    for a, ad, b, n in _BILGI_EK:
        e = en.get(a)
        if e:
            v = e["deger"] * 1000.0 if a == "u" else e["deger"]
            sat.append([ad + (f" ({b})" if b else ""), _sayi_tr(v, n), _sayi_tr(e["x"], 3), str(e["fe"])])
    notlar = [p.get("isaret")] + ([p["not"]] if p.get("not") else [])
    if zarf:
        notlar.append("Zarf: her istasyonda uygulanan kombinasyonların en büyüğü (zarf−: en küçüğü); değerler farklı "
                      "kombinasyonlardan gelebilir.")
    ic_b.append({"baslik": "En büyük mutlak değerler (bütün parçalar)", "tablo": {"basliklar": ["Büyüklük", "Değer", "x (m)", "FE"],
                                                                                  "satirlar": sat}, "notlar": [n for n in notlar if n]})
    if p.get("uclar"):
        g, y = [], []
        for u in p["uclar"]:
            for uc in ("i", "j"):
                d = u[uc]
                g.append([f"{uc} ({d['dugum']})"] + [_sayi_tr(v * 1000.0, 3) for v in d["u"]] + [_sayi_tr(v * 1000.0, 4) for v in d["r"]])
                y.append([f"{uc} ({d['dugum']})"] + [_sayi_tr(v * 1000.0, 3) for v in d["u_yerel"]]
                         + [_sayi_tr(v * 1000.0, 4) for v in d["r_yerel"]])
        yer_b.append({"baslik": f"Uç yer değiştirmeleri ({p['durum']}, bina koordinatı)",
                      "tablo": {"basliklar": ["Uç (düğüm)", "uX (mm)", "uY (mm)", "uZ (mm)", "rX (mrad)", "rY (mrad)", "rZ (mrad)"],
                                "satirlar": g}})
        yer_b.append({"baslik": "Uç yer değiştirmeleri (yerel eksen x′, y′, z′)", "acilir": True,
                      "tablo": {"basliklar": ["Uç (düğüm)", "u_x′ (mm)", "u_y′ (mm)", "u_z′ (mm)", "r_x′ (mrad)", "r_y′ (mrad)", "r_z′ (mrad)"],
                                "satirlar": y}})
    else:
        yer_b.append({"not": "Uç yer değiştirmeleri tek bir yük durumu ya da kombinasyon için verilir (zarf değil)."})
    eu = en.get("u")
    if eu:
        yer_b.append({"baslik": "Eğri yer değiştirme (sehim)", "satirlar": [
            ["En büyük |u|", _sayi_tr(eu["deger"] * 1000.0, 3), "mm"], ["Yeri (x)", _sayi_tr(eu["x"], 3), "m"], ["FE eleman", str(eu["fe"]), ""]],
            "not": "Eleman içi biçim M/EI'nin iki kez integraliyle (uç ötelemeleri arasında); düğümler arasındaki sehim dahil."})
    return {"paket": {"sekmeler": {"ic": ic_b, "yer": yer_b}, "sekme_adlari": {"ic": "İç kuvvetler", "yer": "Yer değiştirme"},
                      "uyarilar": [], "durum": p["durum"], "fe": p["fe"]},
            "cozum_kimligi": ic.get("kimlik"), "hata": None}


def _bina_islem(islem: str, girdi: dict, ayar: dict | None = None) -> dict:
    if islem == "bina_eleman_bilgi":
        return _bina_eleman_bilgi_yaniti(girdi)
    if islem == "bina_kesit_oner":
        return _bina_kesit_oner_yaniti(girdi)
    if islem == "bina_rapor":
        return _bina_rapor_yaniti(girdi)
    if islem == "bina_tablolar":
        return _bina_tablolar_yaniti(girdi)
    if islem == "bina_alan":
        return _bina_alan_yaniti(girdi)
    if islem == "bina_coz":
        return _bina_coz_yaniti(girdi, ayar)
    if islem == "bina_kombinasyon":
        return _bina_kombinasyon_yaniti(girdi)
    if islem == "bina_eleman_tasarim":
        return _bina_eleman_tasarim_yaniti(girdi)
    yapi = _yapi_zorunlu()
    if islem == "bina_deprem":
        return {"deprem": _sonlu_sayilar(yapi.deprem_onizleme(_bina_girdisi(girdi))), "hata": None}
    if islem == "bina_kutuphane":
        return dict(_sonlu_sayilar(yapi.kutuphane()), hata=None)
    if islem == "bina_sablonlar":
        return {"sablonlar": yapi.bina_sablonlar(), "hata": None}
    if islem == "bina_sablon":
        ad = str(girdi.get("ad", "")).strip()
        return {"ad": ad, "bina": yapi.bina_sablon(ad), "hata": None}
    veri = girdi.get("veri")
    if not isinstance(veri, dict):
        raise mo.MatrisHatasi("Yük yolu için önce binayı çözün; 'veri' alanı bina_coz yanıtının 'veri' sözlüğü olmalı.")
    yol = yapi.yuk_yolu(_bina_girdisi(girdi), veri, girdi.get("hedef") or {})
    return dict(_sonlu_sayilar(yol), hata=None)


# ---------------------------------------------------------------------------
# op4 (yerel program) eklemeleri — MIMARI §8.6; web arayüzü bunları kullanmaz, varsayılanlar web davranışını korur
# ---------------------------------------------------------------------------
OP4_ISLEMLER = {"bina_kimlik"}
IPTAL_ILETISI = "İşlem iptal edildi."
SD_SINIRI_EN_AZ, SD_SINIRI_EN_FAZLA = 100, 200_000
# ayarlar.sd_siniri verildiğinde motorun "tarayıcı sınırı" iletileri yerel programın sınırını anlatır.
_SINIR_ILETILERI = (
    ("tarayıcıda çözüm için en fazla", "bellek ve süre sınırı nedeniyle en fazla"),
    ("tarayıcıda en fazla", "bellek ve süre sınırı nedeniyle en fazla"),
    ("tarayıcı sınırını", "bellek ve süre sınırını"),
)


def _bina_kimlik_yaniti(girdi: dict) -> dict:
    """op4: modelin çözüm kimliği (çözmeden). .op4'te saklı sonuçlar bu kimlikle modele bağlanır (MIMARI §8.6.2)."""
    yapi = _yapi_zorunlu()
    kimlik = yapi.cozum_kimligi(_bina_girdisi(girdi))
    return {"cozum_kimligi": kimlik, "onbellekte": kimlik in _BINA_ONBELLEK, "hata": None}


def _sd_siniri(ayar: dict):
    """ayarlar.sd_siniri → tamsayı (aralığa çekilmiş) ya da None (verilmemiş)."""
    v = ayar.get("sd_siniri") if isinstance(ayar, dict) else None
    if v is None or isinstance(v, bool):
        return None
    try:
        sd = int(v)
    except (TypeError, ValueError):
        raise mo.MatrisHatasi(f"ayarlar.sd_siniri bir tamsayı olmalı (ör. 6000); verilen: {v!r}.") from None
    return max(SD_SINIRI_EN_AZ, min(SD_SINIRI_EN_FAZLA, sd))


def _sinirlari_kur(sd) -> list:
    """İstek süresince serbestlik derecesi sınırlarını değiştirir; geri yükleme listesini döndürür (sd None → [])."""
    eski: list = []
    if sd is None:
        return eski
    for ad in ("yapi", "yapi_serbest"):
        try:
            m = importlib.import_module(ad)
        except ImportError:
            continue
        if hasattr(m, "EN_FAZLA_SD"):
            eski.append((m, "EN_FAZLA_SD", m.EN_FAZLA_SD))
            m.EN_FAZLA_SD = sd
    if sd > 1500:
        try:
            tm = importlib.import_module("temel")
        except ImportError:
            tm = None
        if tm is not None and hasattr(tm, "EN_KUCUK_AG"):
            eski.append((tm, "EN_KUCUK_AG", tm.EN_KUCUK_AG))
            tm.EN_KUCUK_AG = round(max(0.02, min(tm.EN_KUCUK_AG, 0.10 * math.sqrt(1500 / sd))), 4)
    return eski


def _sinirlari_geri_yukle(eski: list) -> None:
    for m, ad, deger in reversed(eski):   # tekrar çağrılabilir (iptal geri yüklemenin ortasına düşerse)
        setattr(m, ad, deger)


def _sinir_iletileri(metin: str) -> str:
    for eski, yeni in _SINIR_ILETILERI:
        metin = metin.replace(eski, yeni)
    return metin


def calistir(istek_json: str) -> str:
    """İsteği çalıştırır (yukarıdaki biçimler). ayarlar.sd_siniri verilmişse sınırlar istek süresince değişir (op4)."""
    sd, eski = None, []
    try:
        if isinstance(istek_json, str) and '"sd_siniri"' in istek_json:   # web istekleri ikinci kez ayrıştırılmaz
            try:
                ayar = json.loads(istek_json).get("ayarlar") or {}
                sd = _sd_siniri(ayar) if isinstance(ayar, dict) else None
            except (ValueError, AttributeError, mo.MatrisHatasi):
                sd = None   # bozuk istek / değer: _calistir_ic olağan (öğretici) hatasını verir
        eski = _sinirlari_kur(sd)
        try:
            yanit = _calistir_ic(istek_json)
        finally:
            _sinirlari_geri_yukle(eski)
    except KeyboardInterrupt:   # op4 motor sunucusu çalışan isteği _thread.interrupt_main ile keser (MIMARI §8.4)
        _sinirlari_geri_yukle(eski)
        return json.dumps({"hata": IPTAL_ILETISI, "hata_turu": "iptal"}, ensure_ascii=False)
    return _sinir_iletileri(yanit) if sd is not None else yanit


def _calistir_ic(istek_json: str) -> str:
    try:
        istek = json.loads(istek_json)
        ayar = istek.get("ayarlar") or {}
        motor_ayari = dict(
            goster="yok",
            ondalik=bool(ayar.get("ondalik", False)),
            basamak=max(1, min(12, int(ayar.get("basamak", 4) or 4))),
            en_fazla_eleman=max(0, int(ayar.get("en_fazla_eleman", 36) or 36)),
        )
        # Ok şemaları (adım adım SVG). Eski bir motor kopyası "sema" ayarını tanımıyorsa hata verme, atla.
        if hasattr(mo.ayarlar, "sema"):
            motor_ayari["sema"] = bool(ayar.get("sema", True))
        mo.ayarla(**motor_ayari)
        islem = str(istek.get("islem", ""))
        if islem == "ders_calistir":
            return json.dumps(_ders_calistir(istek.get("girdi") or {}), ensure_ascii=False)
        if islem in SE_ISLEMLER:
            return json.dumps(_se_islem(islem, istek.get("girdi") or {}), ensure_ascii=False)
        if islem in BINA_ISLEMLER or islem in OP4_ISLEMLER:
            _sd_siniri(ayar)   # op4: geçersiz ayarlar.sd_siniri öğretici hata verir
        if islem in BINA_ISLEMLER:
            return json.dumps(_bina_islem(islem, istek.get("girdi") or {}, ayar), ensure_ascii=False)
        if islem in OP4_ISLEMLER:
            return json.dumps(_bina_kimlik_yaniti(istek.get("girdi") or {}), ensure_ascii=False)
        if islem not in ISLEMLER:
            raise mo.MatrisHatasi(f"Bilinmeyen işlem: {islem!r}")
        if islem == "yardim":
            return json.dumps({
                "ad": "yardim",
                "bloklar": [{"tur": "md", "icerik": mo.YARDIM_METNI, "etiket": "adim"}],
                "sonuc_etiket": "", "sonuc_latex": "", "sonuc_metin": "", "zincir": False, "hata": None,
            }, ensure_ascii=False)
        g = istek.get("girdi") or {}
        r = _calistir(islem, g)
        return json.dumps({
            "ad": r.ad,
            "bloklar": _bloklar(r.anlatim),
            "sonuc_etiket": _etiket(islem, r.ad),
            "sonuc_latex": _latex(islem, r),
            "sonuc_metin": _metin(r.deger),
            "zincir": _zincir(r.deger),
            "hata": None,
        }, ensure_ascii=False)
    except mo.MatrisHatasi as e:
        return json.dumps({"hata": str(e), "hata_turu": "girdi"}, ensure_ascii=False)
    except MemoryError:
        return json.dumps({
            "hata": "Hesap için bellek yetmedi: model bu bilgisayarın (ya da hesap motoruna ayrılan) belleğine sığmıyor. "
                    "Serbestlik derecesini azaltın (aks / kat sayısı, bölme düğümleri, temel ağ aralığı) ya da bellek "
                    "tavanını yükseltin.",
            "hata_turu": "ic",
        }, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001 — tarayıcıya her hatayı okunur biçimde geri ver
        return json.dumps({
            "hata": f"{type(e).__name__}: {e}",
            "hata_turu": "ic",
            "iz": traceback.format_exc()[-1500:],
        }, ensure_ascii=False)
