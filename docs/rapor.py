# -*- coding: utf-8 -*-
"""Statik hesap raporu (tasarım belgesi §14.1): bina çözümünden (``yapi.bina_coz(...).veri``) kendi içinde tam bir HTML5
belgesi üretir — gömülü CSS, A4 yazdırma düzeni (sayfa sonları, sayfa numarası), bağlantılı içindekiler, satır içi SVG
spektrum grafiği. Dış kaynak yoktur (çevrimdışı PWA); formüller düz HTML (alt/üst simge, Unicode) ile yazılır.

    import yapi, rapor
    bina = yapi.bina_sablon("betonarme-3kat-3x3")
    veri = yapi.bina_coz(bina, anlat=False).veri
    html = rapor.statik_rapor(bina, veri, secenek={"proje": {"ad": "Örnek konut", "hazirlayan": "…"}})

``secenek`` (hepsi isteğe bağlı):
  * ``proje``: {ad, yer, il, ilce, ada, parsel, malik, hazirlayan, kontrol, tarih} — kapak künyesi;
  * ``bolumler``: dahil edilecek bölümler (1–14 numaraları ve/veya "A", "B", "C", "metraj"; varsayılan hepsi; kapak her zaman);
  * ``eleman_detay``: "kritik" (varsayılan: her eleman türünde D/C en büyük 5 + D/C > 1 olanların tamamı) | "hepsi" | "yok";
  * ``ek_tablolar``: önceden hesaplanmış TABLO listesi (§15.1) → "Ek C — Seçilen tablolar";
  * ``tablolar``: tablo adları — ``tablolar.bina_tablolari(bina, veri)`` çağrılıp adlarla süzülür (modül yoksa not düşülür);
    ``tablo_filtre``: {ad: {"satirlar": [indeks, …]}} satır seçimi; "metraj" grubundan tablo seçilirse "Metraj özeti" bölümü;
  * ``program_surumu``: kapakta yazılacak sürüm metni (yoksa matris_ogren sürümü).

Bütün alanlar ``.get`` ile okunur: veri şeması büyüdükçe (``veri.temel`` §13, ``surum: 3`` çubuk/panel/kren §12) rapor kırılmaz;
veri olmayan bölüm atlanmaz, "Bu modelde uygulanmadı" notuyla kalır. Sayı biçimi ``yapi._f`` ile aynıdır (ondalık nokta).

Genel model çözümü (``veri.model == "genel"``, yapi_serbest): §3 çubuk/panel sayıları türe göre; §5 basit çelik kesitler (boru, kutu,
korniyer, U) ve vute ayrı, betonarme tablosunda yalnız beton dikdörtgen kesitler; §6.2 panel yükleri ve kenar payları, §6.3 çubuk
yük dökümü, §6.5 panel rüzgârı (c_p, q(z), yön başına toplam kuvvet); §10 panel rüzgârında beklenen tepki −ΣF ve taban kesmesi;
§12.3 çubuk türlerine göre ayrıntı (K = [güçlü, zayıf]); §13 açık mesnetler ayrı, N_temel yoksa γ·B·L·h.
"""
from __future__ import annotations

import datetime as _dt
import html as _html
import json
import math
import re

try:  # malzeme / kesit / yönetmelik kütüphanesi (salt veri)
    import yapi_veri as yv
except ImportError:  # pragma: no cover
    yv = None

__all__ = ["statik_rapor", "tablo_html", "BOLUM_BASLIKLARI"]

G_YER = 9.81   # m/s² (yapi.py ile aynı: V_tE = m_t·S_aR·g)

BOLUM_BASLIKLARI = {
    1: "Kapak ve künye",
    2: "Kullanılan yönetmelikler",
    3: "Yapı genel bilgileri",
    4: "Malzemeler",
    5: "Kesitler",
    6: "Yükler",
    7: "Deprem parametreleri (TBDY 2018)",
    8: "Analiz yöntemi",
    9: "Yük birleşimleri",
    10: "Analiz sonuçları",
    11: "Betonarme kesit hesapları",
    12: "Çelik eleman kontrolleri",
    13: "Temel hesabı",
    14: "Sonuç ve öneriler",
}
_EK_BASLIKLARI = {"metraj": "Metraj özeti", "A": "Ek A — Düğüm koordinatları", "B": "Ek B — Çubuk bağlantı tablosu",
                  "C": "Ek C — Seçilen tablolar"}
UYGULANMADI = "Bu modelde uygulanmadı."
# genel model (surum 3) çubuk türlerinin Türkçe adı (sözleşme C18: yapi_serbest.TUR_ADI ve tablolar.TUR_ADI ile aynı; motor adresi
# "Ç{no} ({TUR_ADI[tur]})"); sıra: rapor tablolarındaki sıra
TUR_ADI = {"kolon": "kolon", "kiris": "kiriş", "capraz": "çapraz", "makas-ust": "makas üst başlık", "makas-alt": "makas alt başlık",
           "makas-dikme": "makas dikmesi", "makas-diyagonal": "makas diyagonali", "asik": "aşık", "kren": "kren kirişi", "bag": "bağ",
           "diger": "diğer"}
_CUBUK_TURU = TUR_ADI
# FE eleman türleri (Ek B, §12.3 başlıkları, temel elemanları): çubuk türleri + temel ağı elemanları (temel.py)
_ELEMAN_TURU = {**TUR_ADI, "temel-kirisi": "temel kirişi", "radye-serit": "radye şeridi"}
# yay kayıtları (yaylar[]: motor eksenleri) → bina eksenleri (sözleşme C12): Fx→FX, Fz→−FY, Fy→FZ, Mx→MX, Mz→−MY, My→MZ
_YAY_BINA = {"Fx": ("FX", 1.0), "Fz": ("FY", -1.0), "Fy": ("FZ", 1.0), "Mx": ("MX", 1.0), "Mz": ("MY", -1.0), "My": ("MZ", 1.0)}
# yay bileşeninin bina eksenli rijitlik adı (C13: kx → kx, ky → kz, kz → ky, krx → krx, kry → krz, krz → kry)
_YAY_ANAHTAR = {"Fx": "kx", "Fz": "ky", "Fy": "kz", "Mx": "krx", "Mz": "kry", "My": "krz"}
_YAY_ETIKET = {"kx": ("k_x", "kN/m"), "ky": ("k_y", "kN/m"), "kz": ("k_z", "kN/m"), "krx": ("k_rx", "kN·m/rad"),
               "kry": ("k_ry", "kN·m/rad"), "krz": ("k_rz", "kN·m/rad")}
# tepki satırı türleri: açık yaylı mesnet (C13), rijit diyaframlı seviyedeki mesnedin ceza yayı (C14), türsüz yay = elastik temel
_YAY_TURU = {"yay-mesnet": "yaylı mesnet", "diyafram-mesnet": "mesnet (diyafram bağıyla)", None: "elastik mesnet (zemin yayı)"}
ESKI_TEMEL_NOTU = ("Bu çözümde mütemadi/radye temel sonucu yok (çözüm eski ya da temel tipi değişti); binayı yeniden çözün.")
_PANEL_TURU = {"doseme": "döşeme", "cati": "çatı", "cephe": "cephe"}
_SEKIL = {"ucgen": "üçgen", "trapez": "trapez", "duzgun": "düzgün", "dogrusal": "doğrusal", "yok": "—"}
_DAGITIM = {"iki": "iki doğrultulu", "tek-13": "tek doğr. (1–3)", "tek-24": "tek doğr. (2–4)", "yok": "yok (köşelere)"}


# ============================================================================
# Biçim yardımcıları
# ============================================================================
def _e(x) -> str:
    """HTML kaçışı (None → boş)."""
    return "" if x is None else _html.escape(str(x), quote=True)


def _sayi_mi(x) -> bool:
    if isinstance(x, bool):
        return False
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _f(x, b=2) -> str:
    """yapi._f ile aynı: en çok b ondalık, sondaki sıfırlar atılır (ondalık nokta). Sayı değilse "–"."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "–"
    if x != x:
        return "–"
    if math.isinf(x):
        return "∞" if x > 0 else "−∞"
    s = f"{x:.{b}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _s(x, n=4) -> str:
    """n anlamlı basamak; çok küçük/büyük sayılar a×10ⁿ (HTML üst simge)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "–"
    if x == 0 or x != x or math.isinf(x):
        return _f(x)
    us = math.floor(math.log10(abs(x)))
    if -3 <= us < 7:
        return _f(x, max(0, n - 1 - us))
    m = x / 10 ** us
    return f"{_f(m, n - 1)}×10<sup>{'−' if us < 0 else ''}{abs(us)}</sup>"


def _b(x, birim="", b=2) -> str:
    """Sayı + birim (bölünmez boşluk)."""
    s = _f(x, b)
    return f"{s}&nbsp;{_e(birim)}" if birim and s != "–" else s


def _g(d, *yol, vars=None):
    """İç içe güvenli okuma: _g(veri, "deprem", "X", "Tp")."""
    for k in yol:
        if isinstance(d, dict):
            d = d.get(k)
        elif isinstance(d, (list, tuple)) and isinstance(k, int) and -len(d) <= k < len(d):
            d = d[k]
        else:
            return vars
        if d is None:
            return vars
    return d


def _liste(x) -> list:
    return x if isinstance(x, list) else []


def _sozluk(x) -> dict:
    return x if isinstance(x, dict) else {}


def _v(ad, alt="", ust="") -> str:
    """Formül simgesi: italik ad + alt/üst simge."""
    s = f"<i>{ad}</i>"
    if alt:
        s += f"<sub>{alt}</sub>"
    if ust:
        s += f"<sup>{ust}</sup>"
    return s


_SIMGE = {   # kontrol adlarındaki düz simgeler → HTML (tasarim.py adları "Md ≤ Mr" biçiminde)
    "Md": _v("M", "d"), "Mr": _v("M", "r"), "Vd": _v("V", "d"), "Vc": _v("V", "c"), "Vw": _v("V", "w"), "Vr": _v("V", "r"),
    "Nd": _v("N", "d"), "Ndm": _v("N", "dm"), "Mx": _v("M", "x"), "My": _v("M", "y"), "Mrx": _v("M", "rx"),
    "Mry": _v("M", "ry"), "Mcx": _v("M", "cx"), "Mcy": _v("M", "cy"), "Pr": _v("P", "r"), "Pc": _v("P", "c"),
    "fcd": _v("f", "cd"), "fck": _v("f", "ck"), "fctd": _v("f", "ctd"), "fyd": _v("f", "yd"), "fyk": _v("f", "yk"),
    "bw": _v("b", "w"), "Ac": _v("A", "c"), "As": _v("A", "s"), "Lb": _v("L", "b"), "Lp": _v("L", "p"), "Lr": _v("L", "r"),
    "Cb": _v("C", "b"), "ρmin": _v("ρ", "min"), "ρb": _v("ρ", "b"), "e_min": _v("e", "min"), "L_b": _v("L", "b"),
    "C_b": _v("C", "b"), "L_c": _v("L", "c"), "KL": "<i>KL</i>",
}
_SIMGE_RE = re.compile(r"(?<![\w&;])(" + "|".join(sorted(map(re.escape, _SIMGE), key=len, reverse=True)) + r")(?![\w])")


def _formul(metin) -> str:
    """Düz kontrol adını kaçışlı HTML'e çevirir; bilinen simgeler alt simgeli yazılır."""
    return _SIMGE_RE.sub(lambda m: _SIMGE[m.group(1)], _e(metin))


def _dc_hucre(dc, saglandi=None) -> str:
    if not _sayi_mi(dc):
        return "–"
    ok = (float(dc) <= 1.0 + 1e-9) if saglandi is None else bool(saglandi)
    return f'<span class="{"ok" if ok else "no"}">{_f(dc, 3)}&nbsp;{"✔" if ok else "✘"}</span>'


def _isaret(ok) -> str:
    return '<span class="ok">✔</span>' if ok else '<span class="no">✘</span>'


def _temel_aks(t) -> str:
    """Temel kaydının aks adı ('B2'; genel modelde ek aks sistemindeyse 'KANAT:K1a')."""
    on = f"{t['sistem']}:" if t.get("sistem") not in (None, "GLOBAL") else ""
    return on + "".join(map(str, _liste(t.get("aks"))))


def _temel_tipi(x) -> str:
    """Temel tipinin okunuşu (temel.tip_oku ile aynı eş anlamlılar): sürekli / mutemadi / mütemadi → 'surekli'; boş → 'tekil'."""
    t = str(x or "tekil").strip().lower()
    return "surekli" if t in ("surekli", "sürekli", "mutemadi", "mütemadi") else t


def _rijitlik_sayisi(x) -> str:
    """Yay rijitliği: binlik boşluklu tam sayı (10 000), çok büyük ceza rijitliklerinde üstel (1.2e+10)."""
    x = float(x)
    if abs(x) >= 1e8:
        return f"{x:.3g}"
    return f"{x:,.0f}".replace(",", " ") if abs(x) >= 100 else _f(x, 3)


def _yay_metni(yay) -> str:
    """{kx, …, krz} (bina eksenleri) → 'k_z = 10 000 kN/m; k_rx = 500 kN·m/rad' (düz metin)."""
    yay = _sozluk(yay)
    return "; ".join(f"{_YAY_ETIKET[a][0]} = {_rijitlik_sayisi(yay[a])} {_YAY_ETIKET[a][1]}" for a in _YAY_ETIKET if _sayi_mi(yay.get(a)))


def _tepki_kayitlari(kisa):
    """Durum / birleşim kaydının düğüm başına destek kuvvetleri (bina eksenleri): mesnet tepkisi + yazılmış yay kuvvetleri (yaylar[]:
    motor eksenleri → bina, C12). Dönüş: ([{dugum, FX…MZ, tip, yay}], yay_ozet ya da None). ``tip``: 'mesnet', 'yaylı mesnet',
    'mesnet (diyafram bağıyla)' ya da 'elastik mesnet (zemin yayı)'; ``yay``: yay rijitlikleri {kx…krz} (bina eksenleri).
    ``yay_ozet``: yanıta yazılmayan (mütemadi/radye temel ağı) yayların toplamı {FX…MZ}."""
    alan = ("FX", "FY", "FZ", "MX", "MY", "MZ")
    kayit = {}
    for t in _liste(_g(kisa, "tepkiler")):
        if isinstance(t, dict):
            r = kayit.setdefault(t.get("dugum"), {"dugum": t.get("dugum"), **{a: 0.0 for a in alan}, "tip": "mesnet", "yay": {}})
            for a in alan:
                r[a] += float(t.get(a) or 0)
    for y in _liste(_g(kisa, "yaylar")):
        if not isinstance(y, dict) or y.get("bilesen") not in _YAY_BINA:
            continue
        a, isaret = _YAY_BINA[y["bilesen"]]
        r = kayit.setdefault(y.get("dugum"), {"dugum": y.get("dugum"), **{b: 0.0 for b in alan}, "tip": "mesnet", "yay": {}})
        r[a] += isaret * float(y.get("kuvvet") or 0)
        r["tip"] = _YAY_TURU.get(y.get("tur"), _YAY_TURU[None])
        if _sayi_mi(y.get("k")):
            r["yay"][_YAY_ANAHTAR[y["bilesen"]]] = float(y["k"])
    oz = _g(kisa, "yay_ozet")
    oz = {a: float(oz.get(a) or 0) for a in alan} if isinstance(oz, dict) else None
    return list(kayit.values()), oz


def _tablo(basliklar, satirlar, *, sinif="", baslik=None, sayisal=None, alt=None) -> str:
    """Hücreleri hazır HTML olan tablo. ``sayisal``: sağa yaslanacak sütun indeksleri (varsayılan: ilk sütun hariç hepsi)."""
    if not satirlar:
        return '<p class="not">Kayıt yok.</p>'
    n = len(basliklar)
    sag = set(range(1, n)) if sayisal is None else set(sayisal)
    h = [f'<table class="{_e(sinif)}">' if sinif else "<table>"]
    if baslik:
        h.append(f"<caption>{baslik}</caption>")
    h.append("<thead><tr>" + "".join(f"<th>{b}</th>" for b in basliklar) + "</tr></thead><tbody>")
    for s in satirlar:
        if isinstance(s, str):          # hazır satır (colspan vb.)
            h.append(s)
            continue
        h.append("<tr>" + "".join(f'<td class="s">{c}</td>' if i in sag else f"<td>{c}</td>" for i, c in enumerate(s)) + "</tr>")
    h.append("</tbody>")
    if alt:
        h.append("<tfoot><tr>" + "".join(f'<td class="s">{c}</td>' if i in sag else f"<td>{c}</td>" for i, c in enumerate(alt))
                 + "</tr></tfoot>")
    h.append("</table>")
    return "".join(h)


def _anahtar_deger(satirlar, sinif="kv") -> str:
    """İki/üç sütunlu parametre tablosu: [(ad, değer[, açıklama])]."""
    govde = []
    for s in satirlar:
        govde.append("<tr>" + "".join(f"<td>{c}</td>" for c in s) + "</tr>")
    return f'<table class="{sinif}"><tbody>{"".join(govde)}</tbody></table>'


def _not(metin) -> str:
    return f'<p class="not">{metin}</p>'


def _p(metin) -> str:
    return f"<p>{metin}</p>"


def _h3(metin, kimlik=None) -> str:
    kimlik_html = f' id="{_e(kimlik)}"' if kimlik else ""
    return f"<h3{kimlik_html}>{metin}</h3>"


def _ul(maddeler) -> str:
    return "<ul>" + "".join(f"<li>{m}</li>" for m in maddeler) + "</ul>" if maddeler else ""


# ============================================================================
# Genel tablo biçimi (§15.1 TABLO) — tablo editörü ile ortak
# ============================================================================
SUTUN_EN_FAZLA = 9   # bir tabloda yan yana en çok veri sütunu; fazlası ilk sütun yinelenerek bölünür (A4 dikey sayfa)


def _tablo_deger(sutun, deger) -> str:
    if deger is None or deger == "":
        return ""
    tur = sutun.get("tur")
    if isinstance(deger, bool) or tur == "bool":
        return "✔" if deger else "—"
    if isinstance(deger, (int, float)) and not isinstance(deger, bool):
        od = sutun.get("ondalik")
        try:
            od = int(od) if od is not None else None
        except (TypeError, ValueError):
            od = None
        if od is None:
            return _f(deger, 3) if abs(float(deger)) >= 1e-3 or deger == 0 else _s(deger, 4)
        return _f(deger, od)
    if isinstance(deger, (list, tuple)):
        return _e(", ".join(str(x) for x in deger))
    if isinstance(deger, dict):
        return _e(json.dumps(deger, ensure_ascii=False))
    return _e(deger)


def tablo_html(tablo, *, satirlar=None, kimlik=None) -> str:
    """§15.1 TABLO sözlüğü → HTML (başlık, açıklama, birimli sütun başlıkları, toplam satırı, kaynak).

    TABLO = {"ad", "baslik", "grup"?, "sutunlar": [{"ad", "baslik", "birim"?, "tur"?, "ondalik"?}],
             "satirlar": [{"degerler": {...}}], "toplam"?: {...}, "aciklama"?, "kaynak"?}.
    ``satirlar``: gösterilecek satır indeksleri (tablo editörü filtresi). Sütun sayısı ``SUTUN_EN_FAZLA``'yı aşarsa tablo
    ilk sütun yinelenerek yatay parçalara bölünür (yazdırmada sayfaya sığar). D/C sütunlarında 1'i aşan değer kırmızıdır."""
    t = _sozluk(tablo)
    sutunlar = [s for s in _liste(t.get("sutunlar")) if isinstance(s, dict) and s.get("ad") is not None]
    tum = [s for s in _liste(t.get("satirlar")) if isinstance(s, dict)]
    if satirlar is not None:
        tum = [tum[i] for i in satirlar if isinstance(i, int) and 0 <= i < len(tum)]
    baslik = t.get("baslik") or t.get("ad") or "Tablo"
    kimlik_html = f' id="{_e(kimlik)}"' if kimlik else ""
    grup_html = f' <span class="grup">({_e(t.get("grup"))})</span>' if t.get("grup") else ""
    h = [f'<div class="tablo-kutu"{kimlik_html}>', f"<h4>{_e(baslik)}{grup_html}</h4>"]
    if t.get("aciklama"):
        h.append(f'<p class="aciklama">{_e(t["aciklama"])}</p>')
    if not sutunlar:
        h.append('<p class="not">Tabloda sütun yok.</p></div>')
        return "".join(h)
    if not tum:
        h.append('<p class="not">Tabloda satır yok.</p>')
    toplam = _sozluk(t.get("toplam"))
    ilk, digerleri = sutunlar[0], sutunlar[1:]
    parcalar = [digerleri[i:i + SUTUN_EN_FAZLA - 1] for i in range(0, len(digerleri), SUTUN_EN_FAZLA - 1)] or [[]]

    def th(s):
        birim = s.get("birim")
        return f"{_e(s.get('baslik') or s.get('ad'))}" + (f'<br><span class="birim">[{_e(birim)}]</span>' if birim else "")

    def td(s, deger):
        hucre = _tablo_deger(s, deger)
        sinif = "s" if isinstance(deger, (int, float)) and not isinstance(deger, bool) else ""
        ad = str(s.get("ad", "")).lower()
        if sinif and ("dc" in ad or "d/c" in str(s.get("baslik", "")).lower()) and float(deger) > 1.0 + 1e-9:
            sinif += " asim"
        return f'<td class="{sinif}">{hucre}</td>' if sinif else f"<td>{hucre}</td>"

    for pi, parca in enumerate(parcalar):
        cols = [ilk] + parca
        if len(parcalar) > 1:
            h.append(f'<p class="parca">Sütunlar {pi + 1}/{len(parcalar)}</p>')
        h.append('<table class="veri kucuk">' if len(cols) > 6 else '<table class="veri">')
        h.append("<thead><tr>" + "".join(f"<th>{th(s)}</th>" for s in cols) + "</tr></thead><tbody>")
        for r in tum:
            d = _sozluk(r.get("degerler"))
            h.append("<tr>" + "".join(td(s, d.get(s.get("ad"))) for s in cols) + "</tr>")
        h.append("</tbody>")
        if toplam:
            h.append("<tfoot><tr>" + "".join(
                td(s, toplam.get(s.get("ad"))) if i else f'<td>{_e(toplam.get(s.get("ad"), "Toplam"))}</td>'
                for i, s in enumerate(cols)) + "</tr></tfoot>")
        h.append("</table>")
    if t.get("kaynak"):
        h.append(f'<p class="kaynak">Kaynak: {_e(t["kaynak"])}</p>')
    h.append("</div>")
    return "".join(h)


# ============================================================================
# CSS
# ============================================================================
_CSS = """
:root{--ink:#111;--ink2:#444;--ink3:#6b6b6b;--line:#c9c9c9;--line2:#e4e4e4;--bg:#e9e8e4;--page:#fff;--acc:#1c5cab;
--ok:#0a7a32;--no:#c0262d;--warn:#8a5a00;--tint:#f4f6f9;--s1:#2a78d6;--s2:#eb6834}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:10pt/1.45 "Segoe UI","Noto Sans","DejaVu Sans",Arial,sans-serif}
.rapor{max-width:210mm;margin:16px auto;background:var(--page);padding:14mm 14mm 18mm;box-shadow:0 1px 6px rgba(0,0,0,.18)}
h1{font-size:20pt;margin:0 0 4mm;letter-spacing:.02em}
h2{font-size:14pt;margin:0 0 3mm;padding-bottom:1.5mm;border-bottom:1.5pt solid var(--acc);color:var(--acc)}
h2 .no{display:inline-block;min-width:9mm}
h3{font-size:11.5pt;margin:5mm 0 2mm;color:var(--ink)}
h4{font-size:10.5pt;margin:4mm 0 1.5mm}
p{margin:1.5mm 0}
.not{color:var(--ink2);font-style:italic}
.kaynak,.aciklama{color:var(--ink3);font-size:8.5pt}
.grup{font-weight:normal;color:var(--ink3);font-size:9pt}
.birim{font-weight:normal;color:var(--ink3);font-size:7.5pt}
.ok{color:var(--ok);font-weight:600;white-space:nowrap}
.no{color:var(--no);font-weight:700;white-space:nowrap}
table{border-collapse:collapse;width:100%;margin:2mm 0 3mm;font-size:8.6pt}
caption{caption-side:top;text-align:left;font-weight:600;padding:1mm 0}
th,td{border:.5pt solid var(--line);padding:1mm 1.5mm;vertical-align:top;text-align:left}
thead th{background:var(--tint);font-weight:600;vertical-align:bottom}
tfoot td{font-weight:600;background:var(--tint)}
td.s{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.asim{color:var(--no);font-weight:700}
table.kucuk{font-size:7.6pt}
table.kucuk th,table.kucuk td{padding:.6mm 1mm}
table.kv{width:auto;min-width:60%}
table.kv td:first-child{color:var(--ink2);white-space:nowrap}
table.kontrol td:nth-child(2){font-size:8.4pt}
table.kontrol .adim{display:block;margin:.3mm 0}
.tablo-kutu{margin:3mm 0}
.parca{font-size:8pt;color:var(--ink3);margin:1mm 0 0}
.kutu{border:1pt solid var(--line);background:var(--tint);padding:3mm 4mm;margin:3mm 0;border-radius:2mm}
.uyari{border-color:#e0b04a;background:#fff8e6}
.uyari strong{color:var(--warn)}
.kapak{min-height:250mm;display:flex;flex-direction:column}
.kapak .ust{border-bottom:2pt solid var(--acc);padding-bottom:4mm;margin-bottom:6mm}
.kapak .ust .alt{color:var(--ink2);font-size:12pt}
.kapak table.kv{min-width:100%}
.kapak .bos{flex:1}
nav.icindekiler ol{padding-left:0;list-style:none;columns:1}
nav.icindekiler li{display:flex;gap:2mm;padding:.8mm 0;border-bottom:.5pt dotted var(--line)}
nav.icindekiler a{color:var(--ink);text-decoration:none}
nav.icindekiler .no{min-width:12mm;color:var(--acc);font-weight:600}
a{color:var(--acc)}
.eleman{border-top:.75pt solid var(--line);margin-top:4mm;padding-top:1mm}
.eleman h4{margin-top:1mm}
.ozet-sayi{display:flex;flex-wrap:wrap;gap:3mm;margin:3mm 0}
.ozet-sayi div{flex:1 1 30mm;border:.75pt solid var(--line);border-radius:1.5mm;padding:2mm 3mm}
.ozet-sayi b{display:block;font-size:13pt}
.ozet-sayi div>span{display:block;color:var(--ink2);font-size:8pt}
svg{max-width:100%;height:auto}
.grafik{margin:2mm 0 4mm}
.lejant{font-size:8.5pt;color:var(--ink2)}
.lejant i.c{display:inline-block;width:18px;height:0;border-top:2px solid var(--s1);vertical-align:middle;margin:0 4px 0 10px}
.lejant i.c2{border-top:2px dashed var(--s2)}
footer.son{margin-top:8mm;padding-top:2mm;border-top:.5pt solid var(--line);color:var(--ink3);font-size:8pt}
code{font-family:"DejaVu Sans Mono",Consolas,monospace;font-size:.92em;background:var(--tint);padding:0 .6mm;border-radius:.6mm}
table.birlesim td:nth-child(2){width:62%}
.ifade{white-space:nowrap}
.maddeler ul{margin:1mm 0 2mm;padding-left:5mm;font-size:8.4pt}
.maddeler li{margin:.3mm 0}
.ekbilgi{color:var(--ink3);font-size:8pt}
@media (max-width:760px){
 body{font-size:9.5pt}
 .rapor{margin:0;padding:16px;box-shadow:none;max-width:none}
 table{display:block;overflow-x:auto}
 .kapak{min-height:0}
}
@page{size:A4;margin:16mm 12mm 16mm 14mm;
 @bottom-center{content:"Sayfa " counter(page) " / " counter(pages);font:8pt sans-serif;color:#666}
 @top-right{content:"Statik hesap raporu — eğitim amaçlıdır";font:7.5pt sans-serif;color:#888}}
@page:first{@top-right{content:none}}
@media print{
 body{background:#fff;font-size:9.2pt}
 .rapor{max-width:none;margin:0;padding:0;box-shadow:none}
 section.bolum,nav.icindekiler{break-before:page}
 section.bolum.kisa{break-before:auto;margin-top:10mm}
 h2,h3,h4,.eleman-bas{break-after:avoid}
 tr,.ozet-sayi,.kutu,svg,.grafik,.eleman{break-inside:avoid}
 thead{display:table-header-group}
 table{font-size:7.8pt}
 table.kucuk{font-size:6.8pt}
 th,td{padding:.5mm 1mm}
 a{color:inherit;text-decoration:none}
 .kapak{min-height:0}
}
"""


# ============================================================================
# Rapor kurucusu
# ============================================================================
def _yukle(x) -> dict:
    """Sözlük ya da JSON metni → sözlük (başka her şey boş sözlük)."""
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except ValueError:
            return {}
    return x if isinstance(x, dict) else {}


def _tasarim_modulu():
    try:
        import tasarim
        return tasarim
    except Exception:   # noqa: BLE001 — rapor tasarim.py olmadan da üretilir
        return None


def _durum_adi(ad):
    adlar = getattr(yv, "YUK_DURUMU_ADLARI", {}) if yv else {}
    if ad in adlar:
        return adlar[ad]
    if str(ad).startswith("W"):
        return f"rüzgâr ({str(ad)[1:]} doğrultusu)"
    if str(ad).startswith("EX") or str(ad).startswith("EY"):
        return f"yatay deprem {str(ad)[:2]} (dışmerkezlik {'+' if str(ad).endswith('+') else '−'}%5)"
    if ad == "EZ":
        return "düşey deprem Ed(Z)"
    if str(ad).startswith("K"):
        return "kren (tekerlek yükleri, konum zarfı)"
    return ""


def _ifade(katsayilar) -> str:
    """{G: 1.4, Q: 1.6} → "1.4·G + 1.6·Q" (HTML)."""
    parcalar = []
    for d, g in _sozluk(katsayilar).items():
        try:
            g = float(g)
        except (TypeError, ValueError):
            continue
        isaret = "−" if g < 0 else "+"
        kat = "" if abs(abs(g) - 1.0) < 1e-12 else f"{_f(abs(g), 3)}·"
        ad = _e(d)
        if "+" in str(d) or "-" in str(d):     # W+X, EX− gibi işaretli durum adları parantezle
            ad = f"({ad.replace('-', '−')})"
        parcalar.append((isaret, f"{kat}{ad}"))
    if not parcalar:
        return "–"
    s = ("−" if parcalar[0][0] == "−" else "") + parcalar[0][1]
    for isaret, p in parcalar[1:]:
        s += f" {isaret} {p}"
    return s


def _slug(metin) -> str:
    tablo = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
    s = re.sub(r"[^A-Za-z0-9]+", "_", str(metin).translate(tablo)).strip("_").lower()
    return s[:60] or "bina"


class _Rapor:
    def __init__(self, bina, veri, secenek):
        self.ham = _yukle(bina)
        self.v = _yukle(veri)
        self.sec = _sozluk(secenek)
        self.B = _sozluk(self.v.get("bina")) or self.ham
        # temel ayarı: normalize edilmiş kayıt (B: varsayılanlar, tekil temel listesi) + kullanıcı modeli (ham: tip, zemin); mütemadi /
        # radye boyutları önce çözümün normalize kaydından (veri.bina.temeller.surekli / .radye: çözülen değerler), yoksa modelden
        tb_v, tb_h = _sozluk(self.B.get("temeller")), _sozluk(self.ham.get("temeller"))
        self.temeller = {**tb_v, **tb_h}
        for a in ("surekli", "radye"):
            if isinstance(tb_v.get(a), dict):
                self.temeller[a] = {**_sozluk(tb_h.get(a)), **tb_v[a]}
        self.temeller["tip"] = _temel_tipi(self.temeller.get("tip"))
        self.proje = _sozluk(self.sec.get("proje"))
        self.ts = _tasarim_modulu()
        self.kaynaklar = set()
        bol = self.sec.get("bolumler")
        self.secili = None if not isinstance(bol, (list, tuple, set)) else {str(b).strip() for b in bol}
        detay = str(self.sec.get("eleman_detay") or "kritik").strip().lower()
        self.detay = detay if detay in ("hepsi", "kritik", "yok") else "kritik"
        self.genel = self.v.get("model") == "genel"     # genel model (surum 3, yapi_serbest): çubuk/panel alanları
        self.el = {e.get("no"): e for e in _liste(_g(self.v, "ag", "elemanlar")) if isinstance(e, dict)}
        self.dug = {d.get("no"): d for d in _liste(_g(self.v, "ag", "dugumler")) if isinstance(d, dict)}
        self.tablolar, self.tablo_notu = self._tablolari_topla()

    # ---------------------------------------------------------------- yardımcılar
    def dahil(self, anahtar) -> bool:
        return self.secili is None or str(anahtar) in self.secili

    def kaynak(self, *metinler):
        for m in metinler:
            if isinstance(m, str) and m.strip():
                self.kaynaklar.add(m.strip())
        return "; ".join(_e(m) for m in metinler if isinstance(m, str) and m.strip())

    @staticmethod
    def tepki_toplami(kisa):
        """Σ destek kuvveti (bina eksenleri; sözleşme C12) = Σ mesnet tepkisi + Σ yazılmış yay kuvveti (yaylı mesnet, diyafram bağı,
        elastik temel; motor → bina: Fx→FX, Fz→−FY, Fy→FZ, Mx→MX, Mz→−MY, My→MZ) + ``yay_ozet`` (yanıta yazılmayan mütemadi/radye
        temel yayları)."""
        kayit, oz = _tepki_kayitlari(kisa)
        return {a: sum(t[a] for t in kayit) + (oz[a] if oz else 0.0) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}

    def beklenen_tepki(self, ad):
        """Yük durumunun uygulanan toplam yükünden beklenen mesnet tepkisi toplamı → ({FX, FY, FZ}, açıklama HTML) ya da None.
        Düşey durumlar (G, Q, S): Σ R_Z = Σ yük; rüzgâr W±X/Y: Σ R = ∓ toplam kat kuvveti; deprem EX±/EY±: Σ R = −V_tE
        (dışmerkezlik yalnız burulma momenti ekler); EZ: Σ R_Z = k_z·ΣG."""
        ad = str(ad)
        top = _sozluk(_g(self.v, "yukler", "toplam"))
        sifir = {"FX": 0.0, "FY": 0.0, "FZ": 0.0}
        if _sayi_mi(top.get(ad)):
            return dict(sifir, FZ=float(top[ad])), f"{_b(top[ad], 'kN', 2)} (düşey, aşağı)"
        m = re.fullmatch(r"W([+-])([XY])", ad)
        rz = _sozluk(self.v.get("ruzgar"))
        F = _liste(_sozluk(rz.get("toplam")).get(ad)) if rz.get("yontem") == "panel" else []
        if m and len(F) >= 3 and all(_sayi_mi(x) for x in F[:3]):      # panel rüzgârı: Σ R = −Σ F (üç bileşen; çatı emmesi düşey)
            Fx, Fy, Fz = (float(x) for x in F[:3])
            return ({"FX": -Fx, "FY": -Fy, "FZ": -Fz},
                    f"Σ<i>F</i> = ({_f(Fx, 2)}; {_f(Fy, 2)}; {_f(Fz, 2)}) kN (panel basınçları)")
        if m and _sayi_mi(rz.get("toplam_" + m.group(2).lower())):
            T = float(rz["toplam_" + m.group(2).lower()])
            yon = 1.0 if m.group(1) == "+" else -1.0
            return dict(sifir, **{"F" + m.group(2): -yon * T}), f"{_b(T, 'kN', 2)} ({m.group(1).replace('-', '−')}{m.group(2)} yönünde)"
        d = _sozluk(self.v.get("deprem"))
        m = re.fullmatch(r"E([XY])([+-])", ad)
        if m and _sayi_mi(_g(d, m.group(1), "VtE")):
            V = float(_g(d, m.group(1), "VtE"))
            return dict(sifir, **{"F" + m.group(1): -V}), f"{_v('V', 'tE')} = {_b(V, 'kN', 2)} (+{m.group(1)} yönünde)"
        if ad == "EZ" and _sayi_mi(d.get("EZ_katsayi")) and _sayi_mi(top.get("G")):
            kz, G = float(d["EZ_katsayi"]), float(top["G"])
            return dict(sifir, FZ=kz * G), f"{_f(kz, 4)}·ΣG = {_b(kz * G, 'kN', 2)} (düşey)"
        return None

    def malzeme(self, ad):
        return _sozluk(_g(self.v, "kutuphane_ozeti", "malzemeler", ad))

    def kesit_ham(self, ad):
        return _sozluk(_g(self.ham, "kesitler", ad))

    def baslik(self):
        return self.proje.get("ad") or self.v.get("baslik") or self.ham.get("baslik") or "Bina"

    def _tablolari_topla(self):
        """secenek.ek_tablolar (hazır) + secenek.tablolar (adlar → tablolar.bina_tablolari) → [(TABLO, satır süzgeci)]."""
        sonuc, notlar = [], []
        filtre = _sozluk(self.sec.get("tablo_filtre"))

        def ekle(t):
            if isinstance(t, dict):
                f = _sozluk(filtre.get(t.get("ad"))).get("satirlar")
                sonuc.append((t, f if isinstance(f, list) else None))

        for t in _liste(self.sec.get("ek_tablolar")):
            ekle(t)
        adlar = self.sec.get("tablolar")
        if isinstance(adlar, (list, tuple)) and adlar:
            try:
                import tablolar as _tm
                hepsi = _tm.bina_tablolari(self.ham or self.B, self.v)
            except ImportError:
                notlar.append("Seçilen tablolar eklenemedi: tablo modülü (tablolar.py) bu kurulumda yok.")
                hepsi = None
            except Exception as hata:   # noqa: BLE001 — rapor tablolar olmadan da üretilir
                notlar.append(f"Seçilen tablolar üretilemedi: {type(hata).__name__}: {hata}")
                hepsi = None
            if hepsi is not None:
                adlar_s = [str(a) for a in adlar]
                sozluk = {str(t.get("ad")): t for t in _liste(hepsi) if isinstance(t, dict)}
                for a in adlar_s:
                    if a in sozluk:
                        ekle(sozluk[a])
                    else:
                        notlar.append(f"Tablo bulunamadı: {a}")
        return sonuc, notlar

    def metraj_tablolari(self):
        return [(t, f) for t, f in self.tablolar if str(t.get("ad", "")).lower().startswith("metraj")
                or str(t.get("grup", "")).lower() == "metraj"]

    # ---------------------------------------------------------------- belge
    def uret(self) -> str:
        bolumler = []   # (anahtar, id, numara metni, başlık, html)
        uretici = {1: self.b1, 2: self.b2, 3: self.b3, 4: self.b4, 5: self.b5, 6: self.b6, 7: self.b7, 8: self.b8,
                   9: self.b9, 10: self.b10, 11: self.b11, 12: self.b12, 13: self.b13, 14: self.b14}
        for no in range(1, 15):
            if no == 1 or self.dahil(no):
                bolumler.append((str(no), f"b{no}", f"{no}.", BOLUM_BASLIKLARI[no], uretici[no]()))
        if self.metraj_tablolari() and self.dahil("metraj"):
            bolumler.append(("metraj", "metraj", "", _EK_BASLIKLARI["metraj"], self.metraj()))
        for ek, f in (("A", self.ekA), ("B", self.ekB)):
            if self.dahil(ek):
                bolumler.append((ek, f"ek{ek}", "", _EK_BASLIKLARI[ek], f()))
        if (self.tablolar or self.tablo_notu) and self.dahil("C"):
            bolumler.append(("C", "ekC", "", _EK_BASLIKLARI["C"], self.ekC()))
        icerik = []
        for anahtar, kimlik, no, baslik, govde in bolumler:
            if anahtar == "1":
                icerik.append(f'<section class="kapak" id="{kimlik}">{govde}</section>')
                icerik.append(self.icindekiler(bolumler))
                continue
            sinif = "bolum kisa" if len(govde) < 700 else "bolum"     # yalnız not içeren bölüm yeni sayfa açmaz
            icerik.append(f'<section class="{sinif}" id="{kimlik}"><h2><span class="no">{_e(no)}</span>{_e(baslik)}</h2>{govde}</section>')
        tarih = _e(self.proje.get("tarih") or _dt.date.today().strftime("%d.%m.%Y"))
        son = (f'<footer class="son">Matris Öğren — statik hesap raporu · {_e(self.baslik())} · {tarih} · çözüm kimliği '
               f'{_e(self.v.get("cozum_kimligi") or "–")}. Bu belge eğitim amaçlıdır; resmî proje yerine geçmez.</footer>')
        return ("<!DOCTYPE html>\n<html lang=\"tr\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
                f"<title>Statik Hesap Raporu — {_e(self.baslik())}</title>"
                "<meta name=\"generator\" content=\"Matris Öğren rapor.py\">"
                f"<style>{_CSS}</style></head><body><main class=\"rapor\">{''.join(icerik)}{son}</main></body></html>\n")

    def icindekiler(self, bolumler):
        li = []
        for anahtar, kimlik, no, baslik, _ in bolumler:
            if anahtar == "1":
                continue
            li.append(f'<li><span class="no">{_e(no) or "—"}</span><a href="#{kimlik}">{_e(baslik)}</a></li>')
        return f'<nav class="icindekiler" id="icindekiler"><h2>İçindekiler</h2><ol>{"".join(li)}</ol></nav>'

    # ================================================================ 1. Kapak
    def b1(self):
        p, v, oz = self.proje, self.v, _sozluk(self.v.get("ozet"))
        il_ilce = " / ".join(x for x in (p.get("il"), p.get("ilce")) if x) or p.get("il_ilce")
        ada_parsel = " / ".join(x for x in (str(p.get("ada") or ""), str(p.get("parsel") or "")) if x) or p.get("ada_parsel")
        surum = self.sec.get("program_surumu")
        if not surum:
            try:
                import matris_ogren as _mo
                surum = f"Matris Öğren motoru {getattr(_mo, '__version__', '?')}"
            except Exception:   # noqa: BLE001
                surum = "Matris Öğren"
        sistem = {"betonarme": "Betonarme", "celik": "Çelik"}.get(v.get("sistem") or self.B.get("sistem"), v.get("sistem") or "–")
        satirlar = [("Proje adı", _e(p.get("ad") or v.get("baslik") or "–")),
                    ("Yapı", _e(v.get("baslik") or self.ham.get("baslik") or "–")),
                    ("Yapı yeri", _e(p.get("yer") or "–")), ("İl / ilçe", _e(il_ilce or "–")),
                    ("Ada / parsel", _e(ada_parsel or "–")), ("Yapı sahibi", _e(p.get("malik") or "–")),
                    ("Hazırlayan", _e(p.get("hazirlayan") or "–"))]
        if p.get("kontrol"):
            satirlar.append(("Kontrol eden", _e(p["kontrol"])))
        satirlar += [("Tarih", _e(p.get("tarih") or _dt.date.today().strftime("%d.%m.%Y"))),
                     ("Taşıyıcı sistem", _e(sistem)), ("Program", _e(surum)),
                     ("Çözüm kimliği", _e(v.get("cozum_kimligi") or "–"))]
        dc = oz.get("en_buyuk_dc")
        kutular = [(_f(oz.get("sd_sayisi"), 0), "serbestlik derecesi"),
                   (_f(oz.get("kombinasyon_sayisi"), 0), "uygulanan yük birleşimi"),
                   (_dc_hucre(dc) if _sayi_mi(dc) else "–", "en büyük eleman D/C"),
                   (_dc_hucre(oz.get("en_buyuk_temel_DC")) if _sayi_mi(oz.get("en_buyuk_temel_DC")) else "–", "en büyük temel D/C")]
        return (f'<div class="ust"><h1>STATİK HESAP RAPORU</h1><div class="alt">{_e(v.get("baslik") or self.ham.get("baslik") or "")}</div></div>'
                + _anahtar_deger(satirlar)
                + '<div class="ozet-sayi">' + "".join(f"<div><b>{a}</b><span>{_e(b)}</span></div>" for a, b in kutular) + "</div>"
                + '<div class="kutu uyari"><strong>Önemli not:</strong> Bu rapor <b>eğitim amaçlıdır, resmî proje yerine geçmez.</b> '
                  "Matris Öğren uygulamasının öğretici hesap hattıyla (TS 498, TS 500, ÇYTHYE, TBDY 2018 esaslarına göre ön boyutlandırma) "
                  "üretilmiştir; kapasite tasarımı, ikinci mertebe etkileri, birleşim/detay hesapları ve yerel zemin etüdü gibi resmî "
                  "projede zorunlu kısımlar kapsam dışıdır. Uygulama projesi yetkili inşaat mühendisince hazırlanmalı ve "
                  "denetlenmelidir.</div><div class=\"bos\"></div>")

    # ================================================================ 2. Yönetmelikler
    def b2(self):
        v = self.v
        dep, kar, rz = bool(v.get("deprem")), bool(v.get("kar")), bool(v.get("ruzgar"))
        sistem = v.get("sistem") or self.B.get("sistem")
        celik = sistem == "celik" or any(_g(m, "tur") == "celik" for m in _sozluk(_g(v, "kutuphane_ozeti", "malzemeler")).values())
        beton = any(_g(m, "tur") == "beton" for m in _sozluk(_g(v, "kutuphane_ozeti", "malzemeler")).values())
        liste = [
            ("TS 498:2021", "Yapı Elemanlarının Boyutlandırılmasında Alınacak Yüklerin Hesap Değerleri (TSE, 2021)",
             "sabit ve hareketli yükler, kar (md. 11), rüzgâr (md. 14), hareketli yük çizelgesi (Çizelge 6)", True),
            ("TS 500:2000", "Betonarme Yapıların Tasarım ve Yapım Kuralları (TSE, Şubat 2000; T1, T2, T3 değişiklikleri dahil)",
             "malzeme (Çizelge 3.2), yük birleşimleri (md. 6.2.6), eğilme (md. 7.1), kolon (md. 7.4), kesme (md. 8.1), döşeme aktarımı (md. 11.4.3)", beton),
            ("ÇYTHYE 2016/2018", "Çelik Yapıların Tasarım, Hesap ve Yapımına Dair Yönetmelik (RG 04.02.2016/29614) ve Esaslar "
             "(RG 15.02.2018/30333 Mük.)", "YDKT/GKT yük birleşimleri (5.3), kesit sınıfı (5.4), basınç (8), eğilme (9), kesme (10), "
             "bileşik etki (11.1)", celik),
            ("TBDY 2018", "Türkiye Bina Deprem Yönetmeliği (RG 18.03.2018/30364 Mük.)",
             "tasarım spektrumu (Bölüm 2), DTS/BYS (Bölüm 3), eşdeğer deprem yükü yöntemi (4.7), öteleme sınırları (4.9), "
             "deprem birleşimleri (4.4.4), betonarme boyut/eksenel sınırlar (Bölüm 7)", dep or beton),
            ("TS EN 1991-1-3", "Eurocode 1 — Yapılar üzerindeki etkiler: Kar yükleri", "kar yükü şekil katsayısı μ₁ (Tablo 5.2)", kar),
            ("TS EN 10025-2", "Sıcak haddelenmiş yapı çelikleri — alaşımsız yapı çelikleri teknik teslim şartları",
             "S235 / S275 / S355 akma ve çekme dayanımları", celik),
            ("TS EN 10365", "Sıcak haddelenmiş I ve H kesitli çelik profiller — boyutlar ve kesit özellikleri", "IPE / HEA / HEB profil tabloları", celik),
            ("TS 708:2016", "Çelik — Beton için donatı çeliği", "B420C / B500C donatı sınıfları", beton),
            ("TS ISO 9194", "Yapıların projelendirme esasları — yapı malzemelerinin ve depolanan malzemelerin yoğunlukları",
             "birim hacim ağırlıklar (TS 498:2021 md. 5 atfı)", True),
        ]
        h = _tablo(["Kısaltma", "Tam künye", "Kullanıldığı yer", "Bu modelde"],
                   [[f"<b>{_e(a)}</b>", _e(b), _e(c), _isaret(True) if d else "—"] for a, b, c, d in liste], sayisal=())
        # Hesaplarda adı geçen maddeler: veri içindeki bütün kaynak metinleri
        maddeler = set()
        for yol in (("kombinasyonlar",),):
            for k in _liste(_g(v, *yol)):
                if isinstance(k, dict) and k.get("uygulandi") and k.get("kaynak"):
                    maddeler.add(str(k["kaynak"]))
        for x in _sozluk(_g(v, "deprem", "kaynaklar")).values():
            if isinstance(x, str):
                maddeler.add(x)
        for d in _liste(_g(v, "yukler", "dosemeler")):
            if isinstance(d, dict) and d.get("q_kaynak"):
                maddeler.add(str(d["q_kaynak"]))
        for d in _liste(_g(v, "yukler", "paneller")):        # genel model: panel yük kaynakları (kullanıcı değerleri hariç)
            for a in ("q_kaynak", "g_kaynak"):
                if isinstance(d, dict) and d.get(a) and str(d[a]) not in ("kullanıcı değeri", "verilmedi (0)"):
                    maddeler.add(str(d[a]))
        for anahtar in ("kar", "ruzgar"):
            for a in ("kaynak", "Sk_kaynak", "mu_kaynak", "C_kaynak", "q_kaynak"):
                if _g(v, anahtar, a):
                    maddeler.add(str(_g(v, anahtar, a)))
        for e in _liste(_g(v, "tasarim", "elemanlar")):
            for k in _liste(_g(e, "kontroller")):
                if isinstance(k, dict) and k.get("kaynak"):
                    maddeler.add(str(k["kaynak"]))
        if yv is not None:
            for m in _sozluk(_g(v, "kutuphane_ozeti", "malzemeler")).values():
                kut = _g(m, "kutuphane")
                for tablo in ("BETONLAR", "DONATILAR", "CELIKLER"):
                    kayit = _sozluk(getattr(yv, tablo, {}).get(kut))
                    if kayit.get("kaynak"):
                        maddeler.add(str(kayit["kaynak"]))
        gruplar = {}
        for m in sorted(maddeler):
            on = next((k for k in ("TS 498", "TS 500", "TBDY", "ÇYTHYE", "TS EN", "TS ISO", "TS 708") if m.startswith(k)), "Diğer")
            gruplar.setdefault(on, []).append(m)
        h += _h3("Hesaplarda başvurulan maddeler")
        h += _not("Aşağıdaki liste, bu modelin hesabında fiilen kullanılan yönetmelik madde, çizelge ve denklem atıflarıdır "
                  "(çözüm verisindeki kaynak alanlarından derlenmiştir).")
        h += '<div class="maddeler">'
        for on in ("TS 498", "TS 500", "TBDY", "ÇYTHYE", "TS EN", "TS ISO", "TS 708", "Diğer"):
            if on in gruplar:
                h += f"<h4>{_e(on)}</h4>" + _ul([_e(m) for m in gruplar[on]])
        return h + "</div>"

    # ================================================================ 3. Genel bilgiler
    def b3(self):
        v, B, oz, ag = self.v, self.B, _sozluk(self.v.get("ozet")), _sozluk(self.v.get("ag"))
        katlar = [k for k in _liste(B.get("katlar")) if isinstance(k, dict)]
        ax = [a for a in _liste(_g(B, "akslar", "x")) if isinstance(a, dict)]
        ay = [a for a in _liste(_g(B, "akslar", "y")) if isinstance(a, dict)]
        kotlar = [float(k.get("kot", 0) or 0) for k in katlar]
        HN = _g(v, "deprem", "HN", vars=(max(kotlar) - min(kotlar)) if kotlar else None)
        dos = _liste(_g(v, "yukler", "dosemeler"))
        alan = sum(float(d.get("alan") or 0) for d in dos if isinstance(d, dict))
        if self.genel:      # genel model: döşeme alanı 'doseme' türü panellerden
            alan = sum(float(p.get("alan") or 0) for p in _liste(_g(v, "yukler", "paneller")) if isinstance(p, dict) and p.get("tur") == "doseme")

        def aralik(akslar):
            k = [float(a.get("konum", 0) or 0) for a in akslar]
            return [k[i + 1] - k[i] for i in range(len(k) - 1)]

        BX = (float(ax[-1].get("konum", 0)) - float(ax[0].get("konum", 0))) if ax else None
        BY = (float(ay[-1].get("konum", 0)) - float(ay[0].get("konum", 0))) if ay else None
        sistem = {"betonarme": "Betonarme (TS 500)", "celik": "Çelik (ÇYTHYE)"}.get(v.get("sistem") or B.get("sistem"), v.get("sistem") or "–")
        cub, pan = _liste(self.ham.get("cubuklar")), _liste(self.ham.get("paneller"))
        satir = [
            ("Taşıyıcı sistem", _e(sistem)),
            ("Bina modeli sürümü", _e(f"surum {self.ham.get('surum', v.get('surum', '–'))}"
                                      + (" (aks sistemi tabanlı serbest çubuk/panel modeli)" if self.genel else ""))),
            ("Kat sayısı (temel üstü)", _f(max(len(katlar) - 1, 0), 0)),
            ("Bina yüksekliği " + _v("H", "N"), _b(HN, "m")),
            ("Plan boyutları " + _v("B", "X") + " × " + _v("B", "Y"), f"{_b(BX, 'm')} × {_b(BY, 'm')}" if BX is not None and BY is not None else "–"),
            ("X aksları ve aralıkları", _e(", ".join(str(a.get("ad")) for a in ax)) + " — " + _e(" + ".join(_f(x) for x in aralik(ax))) + " m"),
            ("Y aksları ve aralıkları", _e(", ".join(str(a.get("ad")) for a in ay)) + " — " + _e(" + ".join(_f(x) for x in aralik(ay))) + " m"),
            ("Toplam döşeme alanı" + (" (döşeme panelleri)" if self.genel else ""), _b(alan, "m²")),
        ] + (self._genel_sayilar() if self.genel else [
            ("Kolon / kiriş / döşeme sayısı", f"{len(_liste(B.get('kolonlar')))} / {len(_liste(B.get('kirisler')))} / {len(_liste(B.get('dosemeler')))}"),
            ("Serbest çubuk / panel / kren sayısı (surum 3)", f"{len(cub)} / {len(pan)} / {len(_liste(self.ham.get('kren')))}"
             if (cub or pan or self.ham.get("kren")) else "yok"),
        ]) + [
            ("Sonlu eleman ağı: düğüm / çubuk eleman", f"{_f(oz.get('dugum', len(_liste(ag.get('dugumler')))), 0)} / {_f(oz.get('eleman', len(_liste(ag.get('elemanlar')))), 0)}"),
            ("Serbestlik derecesi sayısı", _f(oz.get("sd_sayisi", ag.get("sd_sayisi")), 0)),
            ("Mesnet sayısı", _f(len(_liste(ag.get("mesnetler"))), 0)),
            ("Yük durumu / uygulanan birleşim sayısı", f"{_f(oz.get('durum_sayisi'), 0)} / {_f(oz.get('kombinasyon_sayisi'), 0)}"),
            ("Kat diyaframı", _e({"rijit": "rijit (efendi–köle)", "esnek": "esnek (diyafram kısıtı yok)"}.get(ag.get("diyafram") or oz.get("diyafram"), ag.get("diyafram") or "–"))),
            ("Deprem / rüzgâr / kar", " / ".join("açık" if oz.get(a) else "kapalı" for a in ("deprem_etkin", "ruzgar_etkin", "kar_etkin"))),
        ]
        h = _anahtar_deger(satir)
        rows = []
        for k in katlar:
            kd = next((x for x in _liste(_g(v, "yukler", "katlar")) if isinstance(x, dict) and x.get("kat") == k.get("no")), {})
            rows.append([_e(k.get("no")), _e(k.get("ad")), _b(k.get("kot"), "m"), _b(k.get("h"), "m"),
                         _b(kd.get("G"), "kN", 1), _b(kd.get("Q"), "kN", 1)])
        h += _h3("Kat tablosu") + _tablo(["Kat", "Ad", "Kot", "Kat yüksekliği <i>h</i>", "G (kat)", "Q (kat)"], rows, sayisal=(2, 3, 4, 5))
        h += self._aks_sistemi()
        return h

    def _genel_sayilar(self):
        """Genel model: çubuk ve panel sayıları türe göre, kren köprüleri (§3)."""
        cub = [c for c in _liste(_g(self.v, "ag", "cubuklar")) if isinstance(c, dict)] or \
              [c for c in _liste(self.ham.get("cubuklar")) if isinstance(c, dict)]
        pan = [p for p in _liste(_g(self.v, "ag", "paneller")) if isinstance(p, dict)] or \
              [p for p in _liste(self.ham.get("paneller")) if isinstance(p, dict)]

        def say(liste, adlar):
            n = {}
            for x in liste:
                n[x.get("tur") or "diger"] = n.get(x.get("tur") or "diger", 0) + 1
            sira = [t for t in adlar if t in n] + sorted(t for t in n if t not in adlar)
            return f"{len(liste)}" + (": " + ", ".join(f"{adlar.get(t, t)} {n[t]}" for t in sira) if n else "")

        sat = [("Çubuk sayısı (türe göre)", _e(say(cub, _CUBUK_TURU))), ("Panel sayısı (türe göre)", _e(say(pan, _PANEL_TURU)))]
        kren = [k for k in _liste(self.ham.get("kren")) if isinstance(k, dict)]
        if kren:
            kopru = _liste(_g(self.v, "kren", "kopruler"))
            sat.append(("Kren", _e(f"{len(kren)} kren yolu" + (f", {len(kopru)} köprü" if kopru else ""))))
        return sat

    def _aks_sistemi(self):
        """Aks sistemi (§19): X/Y/Z aks tabloları (konum + aralık) ve ek (döndürülmüş / silindirik) aks sistemleri."""
        akslar = _sozluk(self.ham.get("akslar")) or _sozluk(self.B.get("akslar"))
        h = ""
        rows = []
        for yon, ad in (("x", "X"), ("y", "Y"), ("z", "Z")):
            liste = [a for a in _liste(akslar.get(yon)) if isinstance(a, dict)]
            onceki = None
            for a in liste:
                k = a.get("konum")
                aralik = _f(float(k) - float(onceki), 3) if _sayi_mi(k) and _sayi_mi(onceki) else "–"
                ek = []
                if a.get("tur") and a.get("tur") != "ana":
                    ek.append(str(a["tur"]))
                if a.get("kat") is not None:
                    ek.append(f"kat {a['kat']}")
                rows.append([_e(ad), f"<b>{_e(a.get('ad'))}</b>", _f(k, 3), aralik, _e(", ".join(ek))])
                onceki = k
        if rows:
            h += _h3("Aks sistemi (GLOBAL)") + _tablo(["Yön", "Aks", "Konum [m]", "Aralık [m]", "Not"], rows, sinif="kucuk", sayisal=(2, 3))
            if not _liste(akslar.get("z")):
                h += _not("Z aksları tanımlanmamış: kat kotları Z seviyeleri olarak kullanılır (kat tablosu).")
        ek = [s for s in _liste(self.ham.get("aks_sistemleri")) if isinstance(s, dict)]
        if ek:
            rows = []
            for s in ek:
                eksen = []
                for anahtar in ("x", "y", "r", "teta"):
                    liste = [a for a in _liste(s.get(anahtar)) if isinstance(a, dict)]
                    if liste:
                        eksen.append(f"{anahtar}: " + ", ".join(f"{a.get('ad')} = {_f(a.get('konum'), 3)}" for a in liste))
                rows.append([f"<b>{_e(s.get('ad'))}</b>", _e(s.get("tur") or "kartezyen"),
                             _e("(" + ", ".join(_f(x, 3) for x in _liste(s.get("orijin"))) + ")") if _liste(s.get("orijin")) else "–",
                             _b(s.get("aci"), "°", 2), _e("; ".join(eksen)), _e("GLOBAL" if s.get("z") is None else "kendi Z aksları")])
            h += _h4_tablo("Ek aks sistemleri", ["Sistem", "Tür", "Orijin [m]", "Dönme açısı", "Akslar", "Z"], rows, sinif="kucuk", sayisal=())
        return h

    # ================================================================ 4. Malzemeler
    def b4(self):
        mal = _sozluk(_g(self.v, "kutuphane_ozeti", "malzemeler"))
        if not mal:
            return _not(UYGULANMADI)
        gmc = getattr(self.ts, "GAMMA_MC", 1.5) if self.ts else 1.5
        gms = getattr(self.ts, "GAMMA_MS", 1.15) if self.ts else 1.15
        h = ""
        for ad, m in mal.items():
            tur, kut = m.get("tur"), m.get("kutuphane") or ad
            satir = []
            if tur == "beton":
                k = _sozluk(getattr(yv, "BETONLAR", {}).get(kut)) if yv else {}
                fck = float(k.get("fck", m.get("fck", 0)) or 0)
                fctk = float(k.get("fctk", 0.35 * math.sqrt(fck) if fck else 0))
                Ec = float(k.get("Ec", (m.get("E_kNm2") or 0) / 1000.0))
                satir = [
                    ("Karakteristik basınç dayanımı", _v("f", "ck"), "", _b(fck, "MPa")),
                    ("Malzeme katsayısı", _v("γ", "mc"), "TS 500 md. 6.2.5 (yerinde döküm)", _f(gmc)),
                    ("Tasarım basınç dayanımı", _v("f", "cd"), f"{_v('f', 'ck')}/{_v('γ', 'mc')} = {_f(fck)}/{_f(gmc)}", _b(fck / gmc, "MPa", 3)),
                    ("Karakteristik çekme dayanımı", _v("f", "ctk"), "TS 500 Çizelge 3.2", _b(fctk, "MPa", 3)),
                    ("Tasarım çekme dayanımı", _v("f", "ctd"), f"{_v('f', 'ctk')}/{_v('γ', 'mc')} = {_f(fctk, 3)}/{_f(gmc)}", _b(fctk / gmc, "MPa", 3)),
                    ("Elastisite modülü", _v("E", "c"), "TS 500 Çizelge 3.2 (≈ 3250√" + _v("f", "ck") + " + 14000)", _b(Ec, "MPa", 0)),
                    ("Kayma modülü", _v("G", "c"), "0.40·" + _v("E", "c"), _b(float(m.get("G_kNm2") or 0.4 * Ec * 1000) / 1000.0, "MPa", 0)),
                    ("Poisson oranı", "<i>ν</i>", "TS 500 md. 3.3.3", _f(k.get("nu", 0.2))),
                    ("Eşdeğer blok katsayısı", _v("k", "1"), "TS 500 Çizelge 7.1", _f(k.get("k1"), 3)),
                    ("Birim hacim ağırlık", "<i>γ</i>", "TS ISO 9194 (betonarme)", _b(m.get("gamma"), "kN/m³")),
                ]
                kayn = k.get("kaynak")
                baslik = f"Beton {_e(kut)} <span class=grup>(modelde: {_e(ad)})</span>"
            elif tur == "donati":
                k = _sozluk(getattr(yv, "DONATILAR", {}).get(kut)) if yv else {}
                fyk = float(k.get("fyk", m.get("fyk", 420)) or 420)
                Es = float(k.get("Es", 200000))
                satir = [
                    ("Karakteristik akma dayanımı", _v("f", "yk"), "", _b(fyk, "MPa")),
                    ("Malzeme katsayısı", _v("γ", "ms"), "TS 500 md. 6.2.5", _f(gms)),
                    ("Tasarım akma dayanımı", _v("f", "yd"), f"{_v('f', 'yk')}/{_v('γ', 'ms')} = {_f(fyk)}/{_f(gms)}", _b(fyk / gms, "MPa", 2)),
                    ("Kopma dayanımı", _v("f", "su"), "TS 500 Çizelge 3.1", _b(k.get("fsu"), "MPa")),
                    ("Elastisite modülü", _v("E", "s"), "TS 500 md. 7.1", _b(Es, "MPa", 0)),
                    ("Akma birim şekil değiştirmesi", _v("ε", "yd"), f"{_v('f', 'yd')}/{_v('E', 's')}", _f(fyk / gms / Es, 5)),
                ]
                kayn = k.get("kaynak")
                baslik = f"Donatı çeliği {_e(kut)} <span class=grup>(modelde: {_e(ad)})</span>"
            elif tur == "celik":
                k = _sozluk(getattr(yv, "CELIKLER", {}).get(kut)) if yv else {}
                satir = [
                    ("Akma dayanımı (t ≤ 40 mm)", _v("F", "y"), "ÇYTHYE Tablo 2.1A", _b(k.get("Fy", m.get("Fy")), "MPa")),
                    ("Çekme dayanımı (t ≤ 40 mm)", _v("F", "u"), "ÇYTHYE Tablo 2.1A", _b(k.get("Fu"), "MPa")),
                    ("Akma dayanımı (40 < t ≤ 80 mm)", _v("F", "y"), "ÇYTHYE Tablo 2.1A", _b(k.get("Fy_40_80"), "MPa")),
                    ("Çekme dayanımı (40 < t ≤ 80 mm)", _v("F", "u"), "ÇYTHYE Tablo 2.1A", _b(k.get("Fu_40_80"), "MPa")),
                    ("Elastisite modülü", "<i>E</i>", "ÇYTHYE simgeler listesi", _b(k.get("E", (m.get("E_kNm2") or 0) / 1000), "MPa", 0)),
                    ("Kayma modülü", "<i>G</i>", "ÇYTHYE md. 8.2.2", _b(k.get("G", (m.get("G_kNm2") or 0) / 1000), "MPa", 0)),
                    ("Poisson oranı", "<i>ν</i>", "", _f(k.get("nu", 0.3))),
                    ("Birim hacim ağırlık", "<i>γ</i>", "TS ISO 9194", _b(m.get("gamma", k.get("gamma")), "kN/m³")),
                ]
                kayn = k.get("kaynak")
                baslik = f"Yapı çeliği {_e(kut)} <span class=grup>(modelde: {_e(ad)})</span>"
            else:
                satir = [("Elastisite modülü", "<i>E</i>", "", _b((m.get("E_kNm2") or 0) / 1000, "MPa", 0)),
                         ("Birim hacim ağırlık", "<i>γ</i>", "", _b(m.get("gamma"), "kN/m³"))]
                kayn = None
                baslik = _e(ad)
            h += _h3(baslik) + _tablo(["Büyüklük", "Simge", "Formül / kaynak", "Değer"],
                                      [[_e(a), b, c, d] for a, b, c, d in satir], sayisal=(3,))
            if kayn:
                h += f'<p class="kaynak">Kaynak: {self.kaynak(kayn)}</p>'
        return h

    # ================================================================ 5. Kesitler
    def kesit_sinifi(self, profil, Fy):
        if not self.ts:
            return None
        try:
            return self.ts.kesit_sinifi(profil, float(Fy))
        except Exception:   # noqa: BLE001
            return None

    def b5(self):
        kes = _sozluk(_g(self.v, "kutuphane_ozeti", "kesitler"))
        if not kes:
            return _not(UYGULANMADI)
        dik, prof, sinif, basit = [], [], [], []
        for ad, k in kes.items():
            tip = k.get("tip")
            m = self.malzeme(k.get("malzeme"))
            if tip == "profil" or (tip == "vute" and k.get("profil")):      # vute: temel I profil + doğrusal artan gövde (değişken kesit)
                p = _sozluk(getattr(yv, "PROFILLER", {}).get(k.get("profil"))) if yv else {}
                prof.append((ad, k, p, m))
            elif tip == "basit" or m.get("tur") == "celik":      # basit çelik kesit ya da çelik dikdörtgen (lama): betonarme değil
                basit.append((ad, k, m))
            else:
                dik.append((ad, k))
        h = ""
        if dik:
            rows = []
            for ad, k in dik:
                b, hh = float(k.get("b") or 0), float(k.get("h") or 0)
                ham = self.kesit_ham(ad)
                olcu = f"{_f(b * 100, 1)} × {_f(hh * 100, 1)}"
                if k.get("tip") == "vute":      # betonarme vute: temel dikdörtgen kesit + derin uçta ek yükseklik
                    olcu += (f' <span class="birim">+ vute: ek yükseklik {_f(float(k.get("ek_yukseklik") or 0) * 100, 1)} cm, '
                             f'boy {_b(k.get("boy"), "m") if k.get("boy") is not None else "çubuk boyu"}; temel {_e(k.get("temel"))}</span>')
                rows.append([f"<b>{_e(ad)}</b>", _e(k.get("malzeme")), olcu,
                             _f(k.get("A", b * hh) * 1e4, 1), _s(float(k.get("Iy") or b * hh ** 3 / 12) * 1e8, 5),
                             _s(float(k.get("Iz") or hh * b ** 3 / 12) * 1e8, 5), _s(float(k.get("J") or 0) * 1e8, 5),
                             _s(b * hh ** 2 / 6 * 1e6, 5), _s(float(k.get("Wpl") or b * hh ** 2 / 4) * 1e6, 5),
                             _f(hh / math.sqrt(12) * 100, 2), _f(b / math.sqrt(12) * 100, 2),
                             _f((ham.get("pas") if ham.get("pas") is not None else 0.03) * 1000, 0)])
            h += _h3("Dikdörtgen (betonarme) kesitler")
            h += _tablo(["Kesit", "Malzeme", "<i>b</i> × <i>h</i><br><span class=birim>[cm]</span>", "<i>A</i><br><span class=birim>[cm²]</span>",
                         _v("I", "y") + "<br><span class=birim>[cm⁴]</span>", _v("I", "z") + "<br><span class=birim>[cm⁴]</span>",
                         "<i>J</i><br><span class=birim>[cm⁴]</span>", _v("W", "el,y") + "<br><span class=birim>[cm³]</span>",
                         _v("W", "pl,y") + "<br><span class=birim>[cm³]</span>", _v("i", "y") + "<br><span class=birim>[cm]</span>",
                         _v("i", "z") + "<br><span class=birim>[cm]</span>", "pas<br><span class=birim>[mm]</span>"],
                        rows, sinif="kucuk", sayisal=range(2, 12))
            h += _p(f"{_v('I', 'y')} = <i>b h</i><sup>3</sup>/12 (güçlü eksen, <i>h</i> eğilme düzleminde), {_v('I', 'z')} = <i>h b</i><sup>3</sup>/12, "
                    f"<i>J</i> ≈ <i>β b</i><sup>3</sup><i>h</i> (β = 1/3 − 0.21(b/h)(1 − b<sup>4</sup>/(12h<sup>4</sup>)), <i>b</i> ≤ <i>h</i>), "
                    f"{_v('W', 'el,y')} = <i>b h</i><sup>2</sup>/6, {_v('W', 'pl,y')} = <i>b h</i><sup>2</sup>/4, <i>i</i> = √(<i>I</i>/<i>A</i>) = <i>h</i>/√12. "
                    "Pas: boyuna donatı ağırlık merkezi tasarımda paspayı + 20 mm alınır (bkz. Bölüm 11).")
            if any(k.get("tip") == "vute" for _, k in dik):
                h += _p("Vute (değişken kesit): değerler temel kesitindir; kesit yüksekliği derin uçta ek yükseklik kadar artar ve "
                        + _v("L", "vute") + " boyunca doğrusal azalır. Motor çubuğu parçalara böler ve her parçayı ortalama yüksekliğindeki "
                        "dikdörtgen kesitle modeller.")
        if prof:
            rows, rows2 = [], []
            for ad, k, p, m in prof:
                pad = _e(k.get("profil"))
                if k.get("tip") == "vute":
                    pad += (f' <span class="birim">+ vute: ek yükseklik {_f(float(k.get("ek_yukseklik") or 0) * 1000, 0)} mm, '
                            f'boy {_b(k.get("boy"), "m") if k.get("boy") is not None else "çubuk boyu"}; temel {_e(k.get("temel"))}</span>')
                rows.append([f"<b>{_e(ad)}</b>", pad, _e(k.get("malzeme")), _f(p.get("h"), 1), _f(p.get("b"), 1),
                             _f(p.get("tw"), 1), _f(p.get("tf"), 1), _f(p.get("r"), 1), _f(p.get("A", (k.get("A") or 0) * 1e4), 2),
                             _f(p.get("g"), 1)])
                rows2.append([f"<b>{_e(ad)}</b>", _s(p.get("Iy", (k.get("Iy") or 0) * 1e8), 5), _s(p.get("Wely"), 4), _s(p.get("Wply"), 4),
                              _f(p.get("iy"), 2), _s(p.get("Iz", (k.get("Iz") or 0) * 1e8), 4), _s(p.get("Welz"), 4), _s(p.get("Wplz"), 4),
                              _f(p.get("iz"), 2), _s(p.get("It", (k.get("J") or 0) * 1e8), 4), _s(p.get("Iw"), 4), _f(p.get("Avz"), 2)])
                ks = self.kesit_sinifi(k.get("profil"), m.get("Fy") or 275)
                if ks:
                    bs, gv = _sozluk(ks.get("baslik")), _sozluk(ks.get("govde"))
                    sinif.append([f"<b>{_e(ad)}</b>", _e(k.get("profil")), _b(m.get("Fy"), "MPa"),
                                  _f(bs.get("oran"), 2), _f(bs.get("lambda_p"), 2), _f(bs.get("lambda_r"), 2),
                                  _f(gv.get("oran"), 2), _f(gv.get("lambda_p"), 2), _f(gv.get("lambda_r"), 2),
                                  _e(ks.get("egilme")), _e(ks.get("basinc"))])
                    self.kaynak(ks.get("kaynak"))
            h += _h3("Çelik profiller — boyutlar")
            h += _tablo(["Kesit", "Profil", "Malzeme", "<i>h</i> [mm]", "<i>b</i> [mm]", _v("t", "w") + " [mm]", _v("t", "f") + " [mm]",
                         "<i>r</i> [mm]", "<i>A</i> [cm²]", "<i>g</i> [kg/m]"], rows, sayisal=range(3, 10))
            h += _h3("Çelik profiller — kesit özellikleri")
            h += _tablo(["Kesit", _v("I", "y") + " [cm⁴]", _v("W", "el,y") + " [cm³]", _v("W", "pl,y") + " [cm³]", _v("i", "y") + " [cm]",
                         _v("I", "z") + " [cm⁴]", _v("W", "el,z") + " [cm³]", _v("W", "pl,z") + " [cm³]", _v("i", "z") + " [cm]",
                         _v("I", "t") + " [cm⁴]", _v("I", "w") + " [×10³ cm⁶]", _v("A", "vz") + " [cm²]"], rows2, sinif="kucuk", sayisal=range(1, 12))
            h += _p("Profil tablosunda <i>y</i> güçlü eksendir (Avrupa kuralı); motorda kirişin güçlü eksen ataleti "
                    + _v("I", "z,m") + " = " + _v("I", "y,profil") + " olarak kullanılır. Kaynak: "
                    + self.kaynak(getattr(yv, "_PROFIL_KAYNAK", "") if yv else "") + ".")
            if any(k.get("tip") == "vute" for _, k, _, _ in prof):
                h += _p("Vute (değişken kesit): temel I profilinin başlıkları sabit; gövde derin uçta ek yükseklik kadar uzar ve "
                        + _v("L", "vute") + " boyunca doğrusal azalarak temel profil yüksekliğine iner (kaynaklı I yaklaşımı). "
                        "Tablodaki değerler temel profilindir; "
                        "motor çubuğu parçalara böler ve her parçayı ortalama yüksekliğindeki eşdeğer kesitle modeller, tahkikte moment "
                        "M·" + _v("h", "0") + "/<i>h</i> ile ölçeklenir.")
            if sinif:
                h += _h3("Kesit sınıfı (ÇYTHYE md. 5.4.1, Tablo 5.1A/5.1B)")
                h += _tablo(["Kesit", "Profil", _v("F", "y"), "Başlık <i>b</i>/2" + _v("t", "f"), _v("λ", "p"), _v("λ", "r"),
                             "Gövde <i>h</i>/" + _v("t", "w"), _v("λ", "p"), _v("λ", "r"), "Eğilmede", "Basınçta"], sinif, sinif="kucuk",
                            sayisal=range(2, 9))
                h += _p(f"Başlık: {_v('λ', 'p')} = 0.38√(<i>E</i>/{_v('F', 'y')}), {_v('λ', 'r')} = 1.0√(<i>E</i>/{_v('F', 'y')}); "
                        f"gövde (eğilme): {_v('λ', 'p')} = 3.76√(<i>E</i>/{_v('F', 'y')}), {_v('λ', 'r')} = 5.70√(<i>E</i>/{_v('F', 'y')}). "
                        "λ ≤ λ<sub>p</sub> kompakt, λ<sub>p</sub> < λ ≤ λ<sub>r</sub> kompakt olmayan, λ > λ<sub>r</sub> narin.")
        if basit:
            h += self._basit_kesitler(basit)
        rc = _sozluk(_g(self.v, "ag", "rijitlik_carpani"))
        h += _h3("Çatlamış kesit (etkin) rijitlikleri")
        if rc and (_g(self.v, "ozet", "catlamis_rijitlik") or _g(self.B, "analiz", "catlamis_rijitlik")):
            h += _tablo(["Eleman", "Eğilme rijitliği çarpanı", "Kaynak"],
                        [["Kolon", _f(rc.get("kolon"), 2), "TBDY 2018 Tablo 4.2"], ["Kiriş", _f(rc.get("kiris"), 2), "TBDY 2018 Tablo 4.2"]],
                        sayisal=(1,))
            h += _not("Etkin rijitlik yalnız deprem etkili birleşimlerde ve bu birleşimlere giren düşey yük durumlarında kullanılır "
                      "(TBDY 2018 md. 4.5.8); deprem dışı birleşimler brüt kesit rijitliğiyle çözülür.")
        else:
            h += _not("Çatlamış kesit rijitliği kullanılmadı (brüt kesit rijitliği).")
        return h

    def _basit_kesitler(self, basit):
        """Çelik basit kesitler (kutu, boru, korniyer, çift korniyer, U; çelik dikdörtgen): özellikler tasarim.kesit_ozellik ya da
        çözümdeki kesit kartından (A, I, J, W_pl); W_el = I/(h/2), i = √(I/A)."""
        rows, sinif = [], []
        for ad, k, m in basit:
            p = {}
            if self.ts is not None and k.get("profil"):
                try:
                    p = _sozluk(self.ts.kesit_ozellik(k.get("profil")))
                except Exception:   # noqa: BLE001 — kartla devam
                    p = {}
            A = p.get("A", float(k.get("A") or 0) * 1e4)
            Iy = p.get("Iy", float(k.get("Iy") or 0) * 1e8)
            Iz = p.get("Iz", float(k.get("Iz") or 0) * 1e8)
            hh, bb = float(k.get("h") or 0) * 100, float(k.get("b") or 0) * 100
            Wely = p.get("Wely", Iy / (hh / 2) if hh else None)
            Welz = p.get("Welz", Iz / (bb / 2) if bb else None)
            iy = p.get("iy", math.sqrt(Iy / A) if A and Iy else None)
            iz = p.get("iz", math.sqrt(Iz / A) if A and Iz else None)
            g = p.get("g", A * 0.785 if A else None)
            rows.append([f"<b>{_e(ad)}</b>", _e(k.get("profil") or f"{_f(bb * 10, 0)}×{_f(hh * 10, 0)} mm"), _e(k.get("malzeme")),
                         _f(A, 2), _f(g, 2), _s(Iy, 5), _s(Iz, 5), _s(p.get("It", float(k.get("J") or 0) * 1e8), 5), _s(Wely, 4), _s(Welz, 4),
                         _s(p.get("Wply", float(k.get("Wpl") or 0) * 1e6), 4), _f(iy, 2), _f(iz, 2), _f(p.get("i_min", min(x for x in (iy, iz) if x) if (iy or iz) else None), 2)])
            # sınıf: tasarim.kesit_sinifi basit kesit adını (KUTU/BORU/L/2L/UPN…) da çözer (C20); profilsiz çelik dikdörtgende ad yok
            ks = self.kesit_sinifi(k.get("profil"), m.get("Fy") or 275) if k.get("profil") else None
            if ks:
                pad = str(k.get("profil"))
                sinif.append(((f"<b>{_e(ad)}</b> — " if str(ad) != pad else "") + f"{_e(pad)}: basınçta {_e(ks.get('basinc') or '–')}, "
                              + (f"eğilmede {_e(ks['egilme'])}" if ks.get("egilme") else "eğilme sınıfı tanımlı değil (eksenel çubuk)"),
                              [(ad, pad, x) for x in _liste(ks.get("parcalar")) if isinstance(x, dict)]))
                self.kaynak(ks.get("kaynak"))
        h = _h3("Çelik basit kesitler (kutu/boru/korniyer/U)")
        h += _tablo(["Kesit", "Kesit adı", "Malzeme", "<i>A</i> [cm²]", "<i>g</i> [kg/m]", _v("I", "y") + " [cm⁴]", _v("I", "z") + " [cm⁴]",
                     _v("I", "t") + " [cm⁴]", _v("W", "el,y") + " [cm³]", _v("W", "el,z") + " [cm³]", _v("W", "pl,y") + " [cm³]",
                     _v("i", "y") + " [cm]", _v("i", "z") + " [cm]", _v("i", "min") + " [cm]"], rows, sinif="kucuk", sayisal=range(3, 14))
        h += _p("Kesit özellikleri kapalı formdan (köşe yarıçaplarıyla; boru: <i>A</i> = π(<i>D</i>² − (<i>D</i> − 2<i>t</i>)²)/4, "
                "<i>I</i> = π(<i>D</i>⁴ − (<i>D</i> − 2<i>t</i>)⁴)/64, " + _v("W", "el") + " = <i>I</i>/(<i>D</i>/2)); "
                "<i>i</i> = √(<i>I</i>/<i>A</i>). Korniyerde " + _v("i", "min") + " asal eksen <i>v</i> yarıçapıdır. Bu kesitler "
                "eksenel çubuk olarak (ÇYTHYE Bölüm 7–8) tahkik edilir.")
        if sinif:
            h += "<h4>Kesit sınıfı (ÇYTHYE md. 5.4.1, Tablo 5.1A/5.1B)</h4>" + _ul([x for x, _ in sinif])
            rows = [[f"<b>{_e(ad)}</b>", _e(pad), _e(x.get("ad") or ""), _f(x.get("oran"), 2), _f(x.get("lambda_r_basinc"), 2),
                     _e(x.get("basinc") or "–"), _f(x.get("lambda_p"), 2), _f(x.get("lambda_r"), 2), _e(x.get("egilme") or "–")]
                    for _, parcalar in sinif for ad, pad, x in parcalar]
            if rows:
                h += _tablo(["Kesit", "Kesit adı", "Parça (genişlik/kalınlık)", "Oran", _v("λ", "r") + " (basınç)", "Basınçta",
                             _v("λ", "p") + " (eğilme)", _v("λ", "r") + " (eğilme)", "Eğilmede"], rows, sinif="kucuk", sayisal=(3, 4, 6, 7))
            h += _not("Parça oranı sınırla karşılaştırılır: basınçta λ ≤ " + _v("λ", "r") + " narin olmayan (Tablo 5.1A); eğilmede "
                      "λ ≤ " + _v("λ", "p") + " kompakt, " + _v("λ", "p") + " < λ ≤ " + _v("λ", "r") + " kompakt olmayan, üstü narin "
                      "(Tablo 5.1B). En elverişsiz parça kesitin sınıfını belirler.")
        return h

    # ================================================================ 6. Yükler
    def b6(self):
        B = self.B
        h = ""
        # 6.1 birim ağırlıklar
        rows = []
        if yv is not None:
            for a in ("betonarme", "celik"):
                k = _sozluk(getattr(yv, "TS498_BIRIM_AGIRLIK", {}).get(a))
                if k:
                    rows.append([_e(k.get("ad", a)), _b(k.get("deger"), "kN/m³"), self.kaynak(k.get("kaynak"))])
        h += _h3("6.1 Sabit yük (G): birim hacim ağırlıklar ve öz ağırlık")
        h += _tablo(["Malzeme", "<i>γ</i>", "Kaynak"], rows, sayisal=(1,))
        kiris_oz = _g(B, "analiz", "kiris_oz") or "brut"
        if self.genel:
            beton = any(isinstance(k, dict) and k.get("tip") in ("dikdortgen", "vute") and self.malzeme(k.get("malzeme")).get("tur") == "beton"
                        for k in _sozluk(_g(self.v, "kutuphane_ozeti", "kesitler")).values())      # betonarme çubuk var mı
            h += _p("Panel: <i>g</i> = " + _v("γ", "b") + "·<i>t</i> + " + _v("g", "ek") + " (kaplama, sac, tesisat; yüzey alanına); "
                    "çubuk öz ağırlığı <i>γ</i>·<i>A</i> kN/m çubuk boyunca yayılı (vute çubuklarında parça başına ortalama kesitle"
                    + ("; betonarme kirişte döşeme kalınlığı düşülür: <i>γ</i>·<i>b</i>·(<i>h</i> − <i>t</i>)" if kiris_oz == "net" and beton else "")
                    + "); duvar: " + _v("g", "d") + " = " + _v("w", "duvar") + "·" + _v("h", "duvar") + " kN/m (çubuğa verilen duvar).")
        else:
            h += self._b6_aks_kat_metni(kiris_oz)
        duv = _sozluk(B.get("duvarlar"))
        if duv:
            h += _h4_tablo("Duvar tipleri", ["Ad", "Kütüphane", "Açıklama", "<i>w</i>"],
                           [[_e(a), _e(d.get("kutuphane")), _e(d.get("aciklama")), _b(d.get("deger"), "kN/m²")] for a, d in duv.items()
                            if isinstance(d, dict)], sayisal=(3,))
        if self.genel:
            h += self._b6_genel_paneller()
            h += self._b6_genel_cubuklar()
        else:
            h += self._b6_aks_kat_dosemeler()
        h += self._b6_kar_ruzgar_kren_ek()
        h += self._b6_azaltma()
        return h

    def _b6_azaltma(self):
        """TS 498:2021 md. 16 hareketli yük azaltması (yalnız yuk_durumlari.Q.azaltma açıksa)."""
        az = _sozluk(self.v.get("hareketli_azaltma"))
        if not az:
            return ""
        el = [e for e in _liste(az.get("elemanlar")) if isinstance(e, dict)]
        bet = {}
        for e in el:
            bet.setdefault(e.get("beta"), []).append(e)
        t = _sozluk(az.get("temel"))
        ozet = "; ".join(f"β = {_f(b_, 3)}: {len(es)} kolon ({_e(', '.join(str(x.get('adres') or x.get('no')) for x in es[:4]))}"
                         f"{' …' if len(es) > 4 else ''})" for b_, es in sorted(bet.items(), key=lambda kv: kv[0] if kv[0] is not None else 1))
        h = _h3("6.9 Hareketli yük azaltması (TS 498:2021 md. 16, Çizelge 7)")
        h += _p("Üç tam kattan fazla kat taşıyan düşey elemanlarda (kolon) ve temellerde hareketli yük, taşınan tam kat sayısına göre "
                "Çizelge 7'deki <i>β</i> (alınacak Q / toplam Q) ile azaltıldı; kiriş ve döşemede azaltma yapılmadı. " + _e(ozet)
                + f". Temel: β = {_f(t.get('beta'), 3)} ({_e(t.get('kural') or '')}). Deprem birleşimlerinde Q azaltılmadı (motor kuralı).")
        h += f'<p class="kaynak">{self.kaynak(az.get("kaynak"))}</p>'
        return h

    def _b6_aks_kat_metni(self, kiris_oz):
        return _p("Döşeme: <i>g</i> = " + _v("γ", "b") + "·<i>h</i> + " + _v("g", "ek") + " (kaplama, sıva vb.); kiriş öz ağırlığı: "
                + ("<i>γ</i>·<i>b</i>·(<i>h</i> − <i>t</i>) (net: döşeme kalınlığı döşemede sayılır)" if kiris_oz == "net"
                   else "<i>γ</i>·<i>b</i>·<i>h</i> (brüt)")
                + "; kolon öz ağırlığı <i>γ</i>·<i>A</i>·<i>L</i> üst düğüme tekil yük; duvar: " + _v("g", "d") + " = "
                + _v("w", "duvar") + "·(" + _v("h", "kat") + " − " + _v("h", "kiriş") + ") kN/m.")

    def _b6_aks_kat_dosemeler(self):
        """6.2 döşeme yükleri, (ham) paneller ve 6.3 kiriş yük dökümü — aks–kat modeli."""
        B, Y = self.B, _sozluk(self.v.get("yukler"))
        h = ""
        # 6.2 döşeme yükleri
        dos = [d for d in _liste(Y.get("dosemeler")) if isinstance(d, dict)]
        h += _h3("6.2 Döşeme yükleri (G, Q) ve kirişlere aktarım (TS 500 md. 11.4.3)")
        if dos:
            badr = {d.get("no"): d for d in _liste(B.get("dosemeler")) if isinstance(d, dict)}
            rows = []
            for d in dos:
                b0 = badr.get(d.get("no"), {})
                rows.append([_e(d.get("no")), _e(b0.get("adres", "")), _e(d.get("kat")), f"{_f(d.get('lx'))} × {_f(d.get('ly'))}",
                             _f(d.get("m"), 3), _e({"cift": "çift doğr.", "tek": "tek doğr."}.get(d.get("tip"), d.get("tip"))),
                             _f((b0.get("h") or 0) * 100, 1), _f(d.get("g_plak"), 3), _f(d.get("g_ek"), 3), _f(d.get("g"), 3),
                             _e(b0.get("kullanim", "")), _f(d.get("q"), 3), _f(d.get("alan"), 2), _f(d.get("G_toplam"), 1), _f(d.get("Q_toplam"), 1)])
            h += _tablo(["No", "Adres", "Kat", _v("l", "x") + " × " + _v("l", "y") + " [m]", "<i>m</i>", "Tip", "<i>h</i> [cm]",
                         _v("g", "plak") + " [kN/m²]", _v("g", "ek") + " [kN/m²]", "<i>g</i> [kN/m²]", "Kullanım", "<i>q</i> [kN/m²]",
                         "Alan [m²]", "ΣG [kN]", "ΣQ [kN]"], rows, sinif="kucuk", sayisal=(3, 4, 6, 7, 8, 9, 11, 12, 13, 14))
            qk = sorted({str(d.get("q_kaynak")) for d in dos if d.get("q_kaynak")})
            if qk:
                h += f'<p class="kaynak">Hareketli yük kaynakları: {self.kaynak(*qk)}</p>'
            h += _p("<i>m</i> = " + _v("l", "u") + "/" + _v("l", "k") + " ≤ 2: çift doğrultulu (kısa kenar kirişine üçgen, uzun kenar kirişine "
                    "trapez yük; tepe <i>p</i>·" + _v("l", "k") + "/2); <i>m</i> > 2: tek doğrultulu (uzun kenarlara <i>p</i>·" + _v("l", "k")
                    + "/2 düzgün). Eşdeğer düzgün yükler (yalnız el hesabı için; FE çözümüne gerçek yük şekli gider): üçgen "
                    + _v("q", "eM") + " = <i>p</i>" + _v("l", "k") + "/3, " + _v("q", "eV") + " = <i>p</i>" + _v("l", "k") + "/4; trapez "
                    + _v("q", "eM") + " = (<i>p</i>" + _v("l", "k") + "/2)(1 − 1/(3<i>m</i><sup>2</sup>)), " + _v("q", "eV")
                    + " = (<i>p</i>" + _v("l", "k") + "/2)(1 − 1/(2<i>m</i>)).")
            rows = []
            for d in dos:
                for p in _liste(d.get("paylar")):
                    if not isinstance(p, dict):
                        continue
                    rows.append([_e(d.get("no")), _e(p.get("kiris_no")), _e(p.get("kenar", "")), _e(p.get("sekil", "")), _f(p.get("L")),
                                 _f(p.get("tepe_g"), 3), _f(p.get("tepe_q"), 3), _f(p.get("q_eM_g"), 3), _f(p.get("q_eV_g"), 3),
                                 _f(p.get("q_eM_q"), 3), _f(p.get("q_eV_q"), 3), _f(p.get("toplam_G"), 2), _f(p.get("toplam_Q"), 2)])
            if rows:
                h += _h4_tablo("Döşeme payları (kirişlere giden yük)",
                               ["Döşeme", "Kiriş", "Kenar", "Şekil", "<i>L</i> [m]", "tepe <i>g</i>", "tepe <i>q</i>", _v("q", "eM,g"),
                                _v("q", "eV,g"), _v("q", "eM,q"), _v("q", "eV,q"), "ΣG [kN]", "ΣQ [kN]"], rows, sinif="kucuk",
                               sayisal=range(4, 13), dip="Çizgisel yükler kN/m.")
        else:
            h += _not("Modelde aks–kat döşemesi yok.")
        pan = [p for p in _liste(self.ham.get("paneller")) if isinstance(p, dict)]
        if pan:
            h += _h4_tablo("Paneller (surum 3)", ["No", "Tür", "Kalınlık [m]", "<i>g</i> [kN/m²]", "<i>q</i> [kN/m²]", "Kullanım", "Kar", "Dağıtım"],
                           [[_e(p.get("no")), _e(p.get("tur")), _f(p.get("kalinlik"), 3), _f(p.get("g"), 3), _f(p.get("q"), 3),
                             _e(p.get("kullanim", "")), "✔" if p.get("kar") else "—", _e(p.get("dagitim", ""))] for p in pan], sayisal=(2, 3, 4))
        # 6.3 kiriş yük dökümü
        kir = [k for k in _liste(Y.get("kirisler")) if isinstance(k, dict)]
        h += _h3("6.3 Kiriş yük dökümü")
        if kir:
            badr = {k.get("no"): k for k in _liste(B.get("kirisler")) if isinstance(k, dict)}
            rows = []
            for k in kir:
                G, Q, kn, el = _sozluk(k.get("G")), _sozluk(k.get("Q")), _sozluk(k.get("kN_m")), _sozluk(k.get("el_hesabi"))
                rows.append([_e(k.get("no")), _e(_g(badr, k.get("no"), "adres", vars="")), _f(k.get("L")),
                             _f(G.get("doseme"), 2), _f(G.get("duvar"), 2), _f(G.get("oz"), 2), _f(G.get("ek"), 2), _f(G.get("toplam_kN"), 2),
                             _f(Q.get("doseme"), 2), _f(Q.get("ek"), 2), _f(Q.get("toplam_kN"), 2),
                             _f(kn.get("duvar"), 3), _f(kn.get("q_eM_G"), 3), _f(kn.get("q_eM_Q"), 3),
                             _f(el.get("M_G"), 2), _f(el.get("M_Q"), 2)])
            h += _tablo(["No", "Adres", "<i>L</i> [m]", "G döşeme", "G duvar", "G öz", "G ek", "ΣG [kN]", "Q döşeme", "Q ek", "ΣQ [kN]",
                         _v("g", "duvar") + " [kN/m]", _v("q", "eM,G") + " [kN/m]", _v("q", "eM,Q") + " [kN/m]",
                         _v("M", "G") + " el [kN·m]", _v("M", "Q") + " el [kN·m]"], rows, sinif="kucuk", sayisal=range(2, 16))
            h += _not("Toplam yükler kN; el hesabı momentleri basit kiriş varsayımıyla " + _v("q", "eM") + "<i>L</i><sup>2</sup>/8 (FE sonucuyla "
                      "karşılaştırma için).")
        else:
            h += _not("Aks–kat kirişi yok.")
        return h

    def _b6_kar_ruzgar_kren_ek(self):
        """6.4 kar, 6.5 rüzgâr, 6.6 kren, 6.7 ek yükler, 6.8 kat yük toplamları."""
        v, Y = self.v, _sozluk(self.v.get("yukler"))
        h = ""
        # 6.4 kar
        kar = _sozluk(v.get("kar"))
        h += _h3("6.4 Kar yükü (S) — TS 498:2021 md. 11, TS EN 1991-1-3")
        if kar:
            mu, Ce, Ct, Sk = (kar.get(a) for a in ("mu", "Ce", "Ct", "Sk"))
            h += _anahtar_deger([
                ("Kar bölgesi / rakım", f"{_e(kar.get('bolge'))} / {_b(kar.get('rakim'), 'm', 0)}"),
                ("Zemin kar yükü " + _v("S", "k"), _b(Sk, "kN/m²", 3) + f' <span class="kaynak">({self.kaynak(kar.get("Sk_kaynak"))})</span>'),
                ("Çatı eğimi <i>α</i> / şekil katsayısı " + _v("μ", "1"), f"{_b(kar.get('alpha'), '°', 1)} / {_f(mu, 3)}"
                 + f' <span class="kaynak">({self.kaynak(kar.get("mu_kaynak"))})</span>'),
                (_v("C", "e") + ", " + _v("C", "t"), f"{_f(Ce, 2)}, {_f(Ct, 2)}"),
                ("Çatı kar yükü <i>s</i>", f"<i>s</i> = {_v('μ', '1')}·{_v('C', 'e')}·{_v('C', 't')}·{_v('S', 'k')} = {_f(mu, 3)}·{_f(Ce)}·{_f(Ct)}·{_f(Sk, 3)} = <b>{_b(kar.get('s'), 'kN/m²', 3)}</b>"),
                ("Çatı alanı / toplam kar yükü", f"{_b(kar.get('cati_alani'), 'm²')} / {_b(kar.get('S_toplam'), 'kN')}"),
            ])
            self.kaynak(kar.get("kaynak"))
        else:
            h += _not("Kar yükü bu modelde tanımlanmadı (S durumu kapalı).")
        # 6.5 rüzgâr
        rz = _sozluk(v.get("ruzgar"))
        h += _h3("6.5 Rüzgâr yükü (W) — TS 498:2021 md. 14")
        if rz and rz.get("yontem") == "panel":
            h += self._ruzgar_paneli(rz)
        elif rz:
            h += _p(f"<i>W</i> = <i>C</i>·<i>q</i>(<i>z</i>)·<i>A</i>; <i>C</i> = {_f(rz.get('C'), 2)} "
                    f'<span class="kaynak">({self.kaynak(rz.get("C_kaynak"))})</span>; <i>q</i>(<i>z</i>): '
                    f'<span class="kaynak">{self.kaynak(rz.get("q_kaynak"))}</span>.')
            rows = [[_e(k.get("kat")), _b(k.get("z"), "m"), _b(k.get("q"), "kN/m²", 3), _b(k.get("h_pay"), "m"),
                     _b(k.get("cephe_x"), "m²"), _b(k.get("F_x"), "kN", 2), _b(k.get("cephe_y"), "m²"), _b(k.get("F_y"), "kN", 2)]
                    for k in _liste(rz.get("katlar")) if isinstance(k, dict)]
            h += _tablo(["Kat", "<i>z</i>", "<i>q</i>(<i>z</i>)", "yük yüksekliği", "cephe (X yükü için)", _v("F", "X"),
                         "cephe (Y yükü için)", _v("F", "Y")], rows,
                        alt=["Toplam", "", "", "", "", _b(rz.get("toplam_x"), "kN", 2), "", _b(rz.get("toplam_y"), "kN", 2)])
        else:
            h += _not("Rüzgâr yükü bu modelde tanımlanmadı (W durumu kapalı).")
        # 6.6 kren
        h += _h3("6.6 Kren yükleri")
        kren = [k for k in _liste(self.ham.get("kren")) if isinstance(k, dict)]
        if kren:
            rows = []
            for k in kren:
                t = _sozluk(k.get("tekerlek"))
                rows.append([_e(k.get("no")), _e(", ".join(map(str, _liste(k.get("yol"))))), _b(t.get("P_maks"), "kN"), _b(t.get("P_min"), "kN"),
                             _b(t.get("H_yanal"), "kN"), _b(t.get("H_fren"), "kN"), _b(t.get("aralik"), "m"), _e(t.get("adet")),
                             _f(k.get("dinamik"), 2), _e(k.get("konum_sayisi"))])
            h += _tablo(["No", "Yol çubukları", _v("P", "maks"), _v("P", "min"), _v("H", "yanal"), _v("H", "fren"), "Aralık", "Adet",
                         "Dinamik katsayı", "Konum"], rows, sinif="kucuk")
            h += _p("Düşey tekerlek yükü tasarımda dinamik katsayıyla büyütülür: " + _v("P", "d") + " = φ·" + _v("P", "maks")
                    + "; kren yolu boyunca her konum ayrı alt yük durumu (K) olarak çözülür, iç kuvvetler konumların zarfıdır. "
                    "Yatay yanal (" + _v("H", "yanal") + ") ve fren (" + _v("H", "fren") + ") kuvvetleri ray seviyesinde etkir.")
            kv = self.v.get("kren")
            if isinstance(kv, dict) and kv:
                h += "<h4>Kren çözüm özeti</h4>" + self._kren_ozeti(kv)
            elif isinstance(kv, list) and kv:
                h += "<h4>Kren çözüm özeti</h4>" + self._genel_kayit({"kren": kv})
        else:
            h += _not("Bu modelde kren yükü yok.")
        # 6.7 ek yükler
        h += _h3("6.7 Ek yükler")
        ek = [e for e in _liste(self.ham.get("ek_yukler")) if isinstance(e, dict)]
        if ek:
            rows = []
            for e in ek:
                hedef = {k: e[k] for k in ("kiris", "cubuk", "doseme", "panel", "aks", "kat", "dugum") if k in e}
                deg = {k: e[k] for k in ("q", "q1", "q2", "x1", "x2", "g", "p", "P", "x", "FX", "FY", "FZ", "MX", "MY", "MZ", "yon") if k in e}
                rows.append([_e(e.get("tur")), _e(json.dumps(hedef, ensure_ascii=False)), _e(e.get("durum")),
                             _e(", ".join(f"{a} = {b}" for a, b in deg.items()))])
            h += _tablo(["Tür", "Hedef", "Durum", "Değerler (kN, kN/m, kN/m², kN·m)"], rows, sayisal=())
        else:
            h += _not("Ek (kullanıcı tanımlı) yük yok.")
        # 6.8 kat ağırlıkları
        kat = [k for k in _liste(Y.get("katlar")) if isinstance(k, dict)]
        h += _h3("6.8 Kat yük toplamları")
        if kat:
            top = _sozluk(Y.get("toplam"))
            h += _tablo(["Kat", "Kot", "<i>h</i>", "G [kN]", "Q [kN]", "S [kN]"],
                        [[_e(k.get("kat")), _b(k.get("kot"), "m"), _b(k.get("h"), "m"), _f(k.get("G"), 2), _f(k.get("Q"), 2), _f(k.get("S"), 2)]
                         for k in kat], alt=["Toplam", "", "", _f(top.get("G"), 2), _f(top.get("Q"), 2), _f(top.get("S"), 2)])
        return h

    def _b6_genel_paneller(self):
        """6.2 Panel yükleri ve çubuklara dağıtım (genel model): motorun hesapladığı g, q, s (kaynaklarıyla), dağıtım ve kenar payları."""
        pan = [p for p in _liste(_g(self.v, "yukler", "paneller")) if isinstance(p, dict)]
        h = _h3("6.2 Panel yükleri ve çubuklara dağıtım (TS 498, TS 500 md. 11.4.3)")
        if not pan:
            return h + _not("Modelde panel yok: yükler çubuklara doğrudan (öz ağırlık, duvar, ek yük) verilir.")
        h += _p("Panel yükleri: <i>g</i> = " + _v("γ", "b") + "·<i>t</i> + " + _v("g", "ek") + " yüzey alanına; hareketli <i>q</i> ve kar "
                "<i>s</i> = " + _v("μ", "1") + "·" + _v("C", "e") + "·" + _v("C", "t") + "·" + _v("S", "k") + " yatay izdüşüme (eğik panelde "
                "yüzey yükü <i>q</i>·cos α). Dağıtım: iki doğrultulu panelde her nokta en yakın kenara gider (açıortay bölgeleri; dikdörtgende "
                "45° kuralı: kısa kenara üçgen, uzun kenara trapez), tek doğrultulu panel yükünü iki karşı kenara yarı yarıya verir, "
                "'yok' köşe düğümlerine eşit pay. Pay: kenarın aldığı yük alanı (m²); kenar yükü = pay × birim yük.")
        rows = []
        for p in pan:
            rows.append([_e(p.get("no")), _e(_PANEL_TURU.get(p.get("tur"), p.get("tur") or "")), _f(p.get("alan"), 2), _f(p.get("egim"), 1),
                         _e(_DAGITIM.get(p.get("dagitim"), p.get("dagitim") or "")), _f(p.get("g"), 3), _f(p.get("q"), 3), _f(p.get("s"), 3),
                         _f(p.get("G_toplam"), 2), _f(p.get("Q_toplam"), 2), _f(p.get("S_toplam"), 2)])
        top = lambda a: sum(float(p.get(a) or 0) for p in pan)   # noqa: E731
        h += _h4_tablo(f"Panel yükleri ({len(pan)} panel)", ["Panel", "Tür", "Alan [m²]", "Eğim [°]", "Dağıtım", "<i>g</i> [kN/m²]",
                       "<i>q</i> [kN/m²]", "<i>s</i> [kN/m²]", "ΣG [kN]", "ΣQ [kN]", "ΣS [kN]"], rows, sinif="kucuk",
                       sayisal=(2, 3, 5, 6, 7, 8, 9, 10),
                       alt=["Σ", "", _f(top("alan"), 2), "", "", "", "", "", _f(top("G_toplam"), 2), _f(top("Q_toplam"), 2), _f(top("S_toplam"), 2)])
        gk = sorted({str(p.get("g_kaynak")) for p in pan if p.get("g_kaynak")})
        qk = sorted({str(p.get("q_kaynak")) for p in pan if p.get("q_kaynak")})
        if gk or qk:
            h += (f'<p class="kaynak">Sabit yük (g) kaynakları: {self.kaynak(*gk) or "–"}. Hareketli yük (q) kaynakları: '
                  f'{self.kaynak(*qk) or "–"}.</p>')
        rows = []
        for p in pan:
            A = float(p.get("alan") or 0)
            birim = {d: float(p.get(d + "_toplam") or 0) / A if A else 0.0 for d in ("G", "Q", "S")}
            for k in _liste(p.get("kenarlar")):
                if not isinstance(k, dict) or not float(k.get("pay") or 0) > 0:
                    continue
                pay = float(k["pay"])
                rows.append([_e(p.get("no")), _e(k.get("kenar")), _e(", ".join(f"Ç{n}" for n in _liste(k.get("cubuklar")))),
                             _e(_SEKIL.get(k.get("sekil"), k.get("sekil") or "")), _f(pay, 3), _f(pay * birim["G"], 2),
                             _f(pay * birim["Q"], 2), _f(pay * birim["S"], 2)])
            if p.get("dagitim") == "yok" and A:
                rows.append([_e(p.get("no")), "–", "köşe düğümleri", "tekil (eşit)", _f(A, 3), _f(p.get("G_toplam"), 2),
                             _f(p.get("Q_toplam"), 2), _f(p.get("S_toplam"), 2)])
        h += _h4_tablo("Kenar payları (panel → çubuk)", ["Panel", "Kenar", "Çubuklar", "Yük şekli", "Pay [m²]", "G [kN]", "Q [kN]", "S [kN]"],
                       rows, sinif="kucuk", sayisal=(4, 5, 6, 7),
                       dip="Kenar boyunca yük, kenar zincirindeki çubuklara sırasıyla verilir (FE'ye gerçek üçgen/trapez/parçalı doğrusal yük gider); "
                           "Σ kenar payları = panel toplamı.")
        return h

    _CUBUK_SINIR = 30          # büyük modelde 6.3'te gösterilen en yüklü çubuk sayısı

    def _b6_genel_cubuklar(self):
        """6.3 Çubuk yük dökümü (genel model): G/Q/S için öz ağırlık, panel, duvar, ek; büyük modelde en yüklü 30 çubuk."""
        cub = [c for c in _liste(_g(self.v, "yukler", "cubuklar")) if isinstance(c, dict)]
        tur = {c.get("no"): c.get("tur") for c in _liste(_g(self.v, "ag", "cubuklar")) if isinstance(c, dict)}
        h = _h3("6.3 Çubuk yük dökümü")
        if not cub:
            return h + _not("Çubuk yük dökümü bu çözümde yok.")

        def top(c):
            return sum(float(_sozluk(c.get(d)).get("toplam_kN") or 0) for d in ("G", "Q", "S"))
        secilen = cub
        if len(cub) > 2 * self._CUBUK_SINIR:
            secilen = sorted(cub, key=lambda c: -top(c))[:self._CUBUK_SINIR]
            secilen.sort(key=lambda c: c.get("no") if isinstance(c.get("no"), (int, float)) else 0)
        rows = []
        for c in secilen:
            G, Q, S_ = _sozluk(c.get("G")), _sozluk(c.get("Q")), _sozluk(c.get("S"))
            rows.append([_e(c.get("no")), _e(_CUBUK_TURU.get(tur.get(c.get("no")), tur.get(c.get("no")) or "")), _f(c.get("L"), 2),
                         _f(G.get("oz"), 2), _f(G.get("panel"), 2), _f(G.get("duvar"), 2), _f(G.get("ek"), 2), _f(G.get("toplam_kN"), 2),
                         _f(Q.get("panel"), 2), _f(Q.get("ek"), 2), _f(Q.get("toplam_kN"), 2), _f(S_.get("panel"), 2), _f(S_.get("toplam_kN"), 2)])
        h += _tablo(["Çubuk", "Tür", "<i>L</i> [m]", "G öz", "G panel", "G duvar", "G ek", "ΣG [kN]", "Q panel", "Q ek", "ΣQ [kN]",
                     "S panel", "ΣS [kN]"], rows, sinif="kucuk", sayisal=range(2, 13))
        if len(secilen) < len(cub):
            h += _not(f"Büyük model: {len(cub)} çubuktan G + Q + S toplamı en büyük {len(secilen)} çubuk gösterildi; bütün çubuklar "
                      "Tablolar › Yükler › 'Eleman Yük Ataması (Çubuk Başına)' tablosundadır.")
        h += _not("Değerler kN (düşey bileşen): öz ağırlık çubuk boyunca yayılı, panel payları kenar yük şekliyle (üçgen/trapez/düzgün), "
                  "duvar ve ek yükler verildiği gibi; FE çözümüne gerçek yayılı yük gider.")
        return h

    def _ruzgar_paneli(self, rz):
        """6.5 rüzgâr — panel yöntemi (genel model): panel başına z, q(z), dört yön için c_p; yön başına toplam kuvvet vektörü."""
        h = _p("Panel yöntemi: her rüzgâr panelinde basınç normal doğrultusunda <i>p</i> = " + _v("c", "p") + "·<i>q</i>(<i>z</i>) "
               "(<i>z</i>: panelin en üst noktasının taban üstü yüksekliği; " + _v("c", "p") + " &gt; 0 basınç, &lt; 0 emme) ve panel dağıtımıyla "
               "kenar çubuklarına aktarılır; dört yön (W+X, W−X, W+Y, W−Y) ayrı yük durumudur. "
               f'<span class="kaynak">({self.kaynak(rz.get("kaynak"))})</span>')
        rows = []
        for p in _liste(rz.get("paneller")):
            if not isinstance(p, dict):
                continue
            cp = _sozluk(p.get("cp"))
            rows.append([_e(p.get("panel")), _e(_PANEL_TURU.get(p.get("tur"), p.get("tur") or "")), _f(p.get("z"), 2), _f(p.get("q"), 3)]
                        + [_f(cp.get(y), 3) for y in ("W+X", "W-X", "W+Y", "W-Y")])
        h += _h4_tablo(f"Panel basınç katsayıları ({len(rows)} panel)", ["Panel", "Tür", "<i>z</i> [m]", "<i>q</i>(<i>z</i>) [kN/m²]",
                       _v("c", "p") + " W+X", _v("c", "p") + " W−X", _v("c", "p") + " W+Y", _v("c", "p") + " W−Y"], rows, sinif="kucuk",
                       sayisal=range(2, 8))
        rows = []
        for y, F in _sozluk(rz.get("toplam")).items():
            F = list(_liste(F)) + [None, None, None]
            rows.append([f"<b>{_e(str(y).replace('-', '−'))}</b>", _f(F[0], 2), _f(F[1], 2), _f(F[2], 2)])
        h += _h4_tablo("Yön başına toplam rüzgâr kuvveti (panel basınçlarının vektörel toplamı)",
                       ["Durum", "Σ" + _v("F", "X") + " [kN]", "Σ" + _v("F", "Y") + " [kN]", "Σ" + _v("F", "Z") + " [kN]"], rows,
                       dip="Σ" + _v("F", "Z") + " çatı emmesinin düşey bileşenidir (yukarı +). Mesnet tepkileri bu vektörün tersidir (Bölüm 10.1).")
        if rz.get("not"):
            h += _not(_e(rz.get("not")))
        return h

    def _kren_ozeti(self, kv):
        """6.6 Kren çözüm özeti: köprüler, alt yük durumları (virgülle), kren yolu zarfı (ilk 30 eleman), kaynak."""
        h = ""
        rows = []
        for k in _liste(kv.get("kopruler")):
            if not isinstance(k, dict):
                continue
            t = _sozluk(k.get("tekerlek"))
            rows.append([_e(k.get("kopru")), _e(", ".join(map(str, _liste(k.get("kren"))))), _e(k.get("konum_sayisi")),
                         _b(t.get("P_maks"), "kN"), _b(t.get("P_min"), "kN"), _b(t.get("H_yanal"), "kN"), _b(t.get("H_fren"), "kN"),
                         _f(k.get("dinamik"), 2), _b(k.get("yol_uzunlugu"), "m")])
        if rows:
            h += _tablo(["Köprü", "Kren yolları", "Konum sayısı", _v("P", "maks"), _v("P", "min"), _v("H", "yanal"), _v("H", "fren"),
                         "Dinamik katsayı", "Yol uzunluğu"], rows, sinif="kucuk")
        dur = [str(d) for d in _liste(kv.get("durumlar"))]
        if dur:
            h += _p(f"<b>Kren alt yük durumları ({len(dur)}):</b> " + _e(", ".join(dur)) + ".")
        if kv.get("aciklama"):
            h += _p(_e(kv["aciklama"]))
        z = [x for x in _liste(kv.get("zarf")) if isinstance(x, dict)]
        if z:
            rows = [[_e(x.get("no")), f"{_f(x.get('N_min'), 2)} / {_f(x.get('N_max'), 2)}", f"{_f(x.get('V_min'), 2)} / {_f(x.get('V_max'), 2)}",
                     f"{_f(x.get('M_min'), 2)} / {_f(x.get('M_max'), 2)}", f"{_f(x.get('My_min'), 2)} / {_f(x.get('My_max'), 2)}"]
                    for x in z[:30]]
            h += _h4_tablo("Kren yolu elemanları — yalnız kren durumlarının zarfı" + (f" (ilk 30 / {len(z)})" if len(z) > 30 else ""),
                           ["Eleman", "<i>N</i> min / maks [kN]", _v("V", "y") + " min / maks [kN]", _v("M", "z") + " min / maks [kN·m]",
                            _v("M", "y") + " min / maks [kN·m]"], rows, sinif="kucuk")
        if kv.get("kaynak"):
            h += f'<p class="kaynak">Kaynak: {self.kaynak(kv["kaynak"])}</p>'
        return h or self._genel_kayit(kv)

    # ================================================================ 7. Deprem
    def spektrum_svg(self, d):
        nok = [p for p in _liste(d.get("spektrum")) if isinstance(p, (list, tuple)) and len(p) >= 2 and all(_sayi_mi(x) for x in p[:3])]
        if len(nok) < 2:
            return ""
        G, Hh, sol, alt, ust, sag = 640.0, 300.0, 52.0, 40.0, 16.0, 16.0
        Tm = max(p[0] for p in nok) or 4.0
        Sm = max(max(p[1] for p in nok), 1e-9) * 1.12
        X = lambda T: sol + (G - sol - sag) * T / Tm   # noqa: E731
        Yp = lambda S: Hh - alt - (Hh - alt - ust) * S / Sm   # noqa: E731
        s = [f'<svg viewBox="0 0 {int(G)} {int(Hh)}" role="img" aria-label="Yatay elastik tasarım spektrumu ve azaltılmış spektrum" '
             'xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="11">']
        s.append(f'<rect x="0" y="0" width="{int(G)}" height="{int(Hh)}" fill="#fff"/>')
        adim = 0.5 if Tm > 2 else 0.25
        t = 0.0
        while t <= Tm + 1e-9:
            s.append(f'<line x1="{X(t):.1f}" y1="{ust}" x2="{X(t):.1f}" y2="{Hh - alt}" stroke="#e4e4e4" stroke-width="1"/>'
                     f'<text x="{X(t):.1f}" y="{Hh - alt + 14}" text-anchor="middle" fill="#52514e">{_f(t)}</text>')
            t += adim
        ys = 0.2 if Sm <= 1.5 else 0.5
        y = 0.0
        while y <= Sm + 1e-9:
            s.append(f'<line x1="{sol}" y1="{Yp(y):.1f}" x2="{G - sag}" y2="{Yp(y):.1f}" stroke="#e4e4e4" stroke-width="1"/>'
                     f'<text x="{sol - 6}" y="{Yp(y) + 4:.1f}" text-anchor="end" fill="#52514e">{_f(y, 2)}</text>')
            y += ys
        s.append(f'<line x1="{sol}" y1="{Hh - alt}" x2="{G - sag}" y2="{Hh - alt}" stroke="#52514e" stroke-width="1"/>'
                 f'<line x1="{sol}" y1="{ust}" x2="{sol}" y2="{Hh - alt}" stroke="#52514e" stroke-width="1"/>')
        s.append(f'<text x="{(G + sol) / 2:.1f}" y="{Hh - 6}" text-anchor="middle" fill="#0b0b0b">Periyot T [s]</text>'
                 f'<text x="14" y="{(Hh - alt + ust) / 2:.1f}" text-anchor="middle" fill="#0b0b0b" transform="rotate(-90 14 {(Hh - alt + ust) / 2:.1f})">Spektral ivme [g]</text>')
        for ad, T in (("T_A", d.get("TA")), ("T_B", d.get("TB"))):
            if _sayi_mi(T) and 0 < float(T) <= Tm:
                s.append(f'<line x1="{X(float(T)):.1f}" y1="{ust}" x2="{X(float(T)):.1f}" y2="{Hh - alt}" stroke="#9a9993" stroke-dasharray="2 3"/>'
                         f'<text x="{X(float(T)) + 3:.1f}" y="{ust + 10}" fill="#52514e">{ad.replace("_", "")}</text>')
        pa = " ".join(f"{X(p[0]):.1f},{Yp(p[1]):.1f}" for p in nok)
        s.append(f'<polyline points="{pa}" fill="none" stroke="#2a78d6" stroke-width="2" stroke-linejoin="round"/>')
        if all(len(p) >= 3 for p in nok):
            pr = " ".join(f"{X(p[0]):.1f},{Yp(p[2]):.1f}" for p in nok)
            s.append(f'<polyline points="{pr}" fill="none" stroke="#eb6834" stroke-width="2" stroke-dasharray="6 4"/>')
        Tp = d.get("Tp")
        if _sayi_mi(Tp) and 0 < float(Tp) <= Tm:
            Sa = d.get("Sae_Tp")
            s.append(f'<line x1="{X(float(Tp)):.1f}" y1="{ust}" x2="{X(float(Tp)):.1f}" y2="{Hh - alt}" stroke="#0b0b0b" stroke-width="1"/>'
                     f'<text x="{X(float(Tp)) + 4:.1f}" y="{ust + 24}" fill="#0b0b0b">Tp = {_f(Tp, 3)} s</text>')
            if _sayi_mi(Sa):
                s.append(f'<circle cx="{X(float(Tp)):.1f}" cy="{Yp(float(Sa)):.1f}" r="4" fill="#2a78d6" stroke="#fff" stroke-width="2">'
                         f'<title>Sae(Tp) = {_f(Sa, 4)} g</title></circle>'
                         f'<text x="{X(float(Tp)) + 7:.1f}" y="{Yp(float(Sa)) - 6:.1f}" fill="#0b0b0b">Sae(Tp) = {_f(Sa, 3)}</text>')
            Sr = d.get("SaR")
            if _sayi_mi(Sr):
                s.append(f'<circle cx="{X(float(Tp)):.1f}" cy="{Yp(float(Sr)):.1f}" r="4" fill="#eb6834" stroke="#fff" stroke-width="2">'
                         f'<title>SaR(Tp) = {_f(Sr, 4)} g</title></circle>'
                         f'<text x="{X(float(Tp)) + 7:.1f}" y="{Yp(float(Sr)) - 6:.1f}" fill="#0b0b0b">SaR(Tp) = {_f(Sr, 4)}</text>')
        s.append("</svg>")
        return ('<div class="grafik">' + "".join(s) + '<div class="lejant"><i class="c"></i>' + _v("S", "ae") + "(<i>T</i>) yatay elastik "
                "tasarım spektrumu (TBDY Denk. 2.2)<i class=\"c c2\"></i>" + _v("S", "aR") + "(<i>T</i>) = " + _v("S", "ae") + "/" + _v("R", "a")
                + " azaltılmış spektrum (Denk. 4.8)</div></div>")

    def b7(self):
        d = _sozluk(self.v.get("deprem"))
        if not d:
            return _not("Bu modelde deprem yükü (E) tanımlanmadı; TBDY 2018 eşdeğer deprem yükü hesabı uygulanmadı. "
                        + UYGULANMADI)
        kay = _sozluk(d.get("kaynaklar"))

        def k(a):
            return f'<span class="kaynak">{self.kaynak(kay.get(a))}</span>' if kay.get(a) else ""

        SS, S1, FS, F1, SDS, SD1 = (d.get(a) for a in ("SS", "S1", "FS", "F1", "SDS", "SD1"))
        HN, Ct = d.get("HN"), d.get("Ct")
        satir = [
            ("Yer / koordinat", _e(self.proje.get("yer") or "–") + " " + _e(" / ".join(x for x in (self.proje.get("il"), self.proje.get("ilce")) if x))),
            ("Deprem yer hareketi düzeyi", _e(_g(self.B, "deprem", "DD") or "DD-2"), ""),
            (_v("S", "S") + ", " + _v("S", "1") + " (DD-2)", f"{_f(SS, 3)}, {_f(S1, 3)}", k("SS")),
            ("Yerel zemin sınıfı", _e(d.get("zemin_sinifi")), k("zemin_sinifi")),
            (_v("F", "S") + ", " + _v("F", "1"), f"{_f(FS, 3)}, {_f(F1, 3)}", k("FS")),
            (_v("S", "DS"), f"{_v('S', 'S')}·{_v('F', 'S')} = {_f(SS, 3)}·{_f(FS, 3)} = <b>{_f(SDS, 4)}</b>", k("SDS")),
            (_v("S", "D1"), f"{_v('S', '1')}·{_v('F', '1')} = {_f(S1, 3)}·{_f(F1, 3)} = <b>{_f(SD1, 4)}</b>", k("SD1")),
            (_v("T", "A"), f"0.2·{_v('S', 'D1')}/{_v('S', 'DS')} = 0.2·{_f(SD1, 4)}/{_f(SDS, 4)} = <b>{_b(d.get('TA'), 's', 4)}</b>", k("TA")),
            (_v("T", "B"), f"{_v('S', 'D1')}/{_v('S', 'DS')} = {_f(SD1, 4)}/{_f(SDS, 4)} = <b>{_b(d.get('TB'), 's', 4)}</b>", k("TB")),
            (_v("T", "L"), _b(d.get("TL"), "s"), k("TL")),
            ("Bina kullanım sınıfı BKS / önem katsayısı <i>I</i>", f"{_e(d.get('BKS'))} / {_f(d.get('I'), 2)}", k("I")),
            ("Deprem tasarım sınıfı DTS", _e(d.get("DTS")), k("DTS")),
            ("Bina yükseklik sınıfı BYS (" + _v("H", "N") + " = " + _b(HN, "m") + ")", _e(d.get("BYS")), k("BYS")),
            ("Taşıyıcı sistem", _e(f"{d.get('tasiyici_kod') or ''} — {d.get('tasiyici_tanim') or d.get('tasiyici') or ''}"), ""),
            ("Taşıyıcı sistem davranış katsayısı <i>R</i> / dayanım fazlalığı <i>D</i>", f"{_f(d.get('R'), 2)} / {_f(d.get('D'), 2)}", k("R")),
            ("Hareketli yük kütle katılım katsayısı <i>n</i>", _f(d.get("n"), 2), k("n")),
            ("Ampirik periyot " + _v("T", "pA"), f"{_v('C', 't')}·{_v('H', 'N')}<sup>3/4</sup> = {_f(Ct, 3)}·{_f(HN, 3)}<sup>0.75</sup> = <b>{_b(d.get('TpA'), 's', 4)}</b>", k("TpA")),
            ("Toplam kütle " + _v("m", "t") + " / ağırlık " + _v("W", "t"), f"{_b(d.get('m_t'), 't', 3)} / {_b(d.get('W_t'), 'kN', 2)}", k("m_t")),
            ("Kat sayısı <i>N</i>", _f(d.get("N"), 0), ""),
            ("Diyafram / çatlamış rijitlik", _e(f"{d.get('diyafram') or '–'} / {'evet' if d.get('catlamis_rijitlik') else 'hayır'}"), ""),
            ("Ek dışmerkezlik", f"± {_f((d.get('e_oran') or 0.05) * 100, 1)}%·<i>B</i>", k("e")),
            ("DD-3 spektral ivmeleri (öteleme için)", f"{_v('S', 'DS')} = {_f(d.get('SDS_DD3'), 4)}, {_v('S', 'D1')} = {_f(d.get('SD1_DD3'), 4)}", k("lambda")),
        ]
        oz = _sozluk(d.get("ozel_spektrum"))
        if oz:
            a = _sozluk(oz.get("asgari"))
            satir.append(("Sahaya özel spektrum (TBDY md. 2.4)",
                          _e(f"{len(_liste(oz.get('noktalar')))} noktalı T–S_ae tablosu; kaynak: {oz.get('kaynak') or '–'}; "
                             f"S_DS {oz.get('SDS_kaynak')}, S_D1 {oz.get('SD1_kaynak')}; md. 2.4.1.2 %90 tabanı "
                             + (("sağlandı" if a.get("saglandi") else "sağlanmadı, tabanın altında kalan aralıklarda %90 tabanı kullanıldı")
                                + f" (en küçük oran {_f(a.get('en_kucuk_oran'), 3)})" if a else "denetlenemedi")), k("ozel_spektrum")))
        km = _sozluk(d.get("karma"))
        if km:
            kx, ky = _sozluk(km.get("X")), _sozluk(km.get("Y"))
            bol = "; ".join(f"{z.get('ad')}: {z.get('X')}/{z.get('Y')}" for z in _liste(km.get("bolgeler")) if isinstance(z, dict))
            satir.append(("Karma taşıyıcı sistem (TBDY md. 4.3.4.2)",
                          _e(f"X: {kx.get('kod')} (R = {_f(kx.get('R'), 2)}, D = {_f(kx.get('D'), 2)}); Y: {ky.get('kod')} "
                             f"(R = {_f(ky.get('R'), 2)}, D = {_f(ky.get('D'), 2)})" + (f"; bölgeler — {bol} (en küçük R bütün binaya)" if bol else "")),
                          k("karma")))
        h = _anahtar_deger([s if len(s) == 3 else (s[0], s[1], "") for s in satir])
        h += _h3("7.1 Yatay elastik tasarım spektrumu") + self.spektrum_svg(d)
        h += _p(f"{_v('S', 'ae')}(<i>T</i>) = (0.4 + 0.6<i>T</i>/{_v('T', 'A')}){_v('S', 'DS')} (0 ≤ <i>T</i> ≤ {_v('T', 'A')}); "
                f"{_v('S', 'DS')} ({_v('T', 'A')} ≤ <i>T</i> ≤ {_v('T', 'B')}); {_v('S', 'D1')}/<i>T</i> ({_v('T', 'B')} ≤ <i>T</i> ≤ {_v('T', 'L')}); "
                f"{_v('S', 'D1')}{_v('T', 'L')}/<i>T</i><sup>2</sup> (<i>T</i> ≥ {_v('T', 'L')}) — {k('Sae_Tp') or 'TBDY 2018 Denk. (2.2)'}")
        # doğrultu tablosu
        h += _h3("7.2 Doğrultu başına eşdeğer deprem yükü")
        rows = []
        tanim = [
            ("Ampirik periyot " + _v("T", "pA"), lambda x: _b(d.get("TpA"), "s", 4)),
            ("Rayleigh periyodu " + _v("T", "R"), lambda x: _b(x.get("Tp_rayleigh"), "s", 4)),
            ("Kullanılan periyot " + _v("T", "p") + " (yöntem)", lambda x: f"{_b(x.get('Tp'), 's', 4)} ({_e(x.get('Tp_yontem') or d.get('Tp_yontem') or '–')})"),
            (_v("S", "ae") + "(" + _v("T", "p") + ")", lambda x: _b(x.get("Sae_Tp"), "g", 4)),
            (_v("R", "a") + "(" + _v("T", "p") + ")", lambda x: _f(x.get("Ra"), 3)),
            (_v("S", "aR") + " = " + _v("S", "ae") + "/" + _v("R", "a"), lambda x: f"{_f(x.get('Sae_Tp'), 4)}/{_f(x.get('Ra'), 3)} = <b>{_b(x.get('SaR'), 'g', 5)}</b>"),
            (_v("V", "tE") + " = " + _v("m", "t") + "·" + _v("S", "aR") + "·<i>g</i>",
             lambda x: f"{_f(d.get('m_t'), 2)}·{_f(x.get('SaR'), 5)}·{_f(G_YER)} = {_b(x.get('VtE_hesap', x.get('VtE')), 'kN', 2)}"),
            (_v("V", "tE,min") + " = 0.04·" + _v("m", "t") + "·<i>I</i>·" + _v("S", "DS") + "·<i>g</i>",
             lambda x: f"0.04·{_f(d.get('m_t'), 2)}·{_f(d.get('I'), 2)}·{_f(SDS, 4)}·{_f(G_YER)} = {_b(x.get('VtE_min'), 'kN', 2)}"),
            ("Tasarım taban kesme kuvveti " + _v("V", "tE"), lambda x: f"<b>{_b(x.get('VtE'), 'kN', 2)}</b>" + (" (alt sınır belirleyici)" if x.get("alt_sinir_etkin") else "")),
            ("Tepe ek kuvveti Δ" + _v("F", "NE") + " = 0.0075·<i>N</i>·" + _v("V", "tE"),
             lambda x: f"0.0075·{_f(d.get('N'), 0)}·{_f(x.get('VtE'), 2)} = {_b(x.get('dFN'), 'kN', 3)}"),
            ("Devrilme momenti " + _v("M", "o") + " = Σ" + _v("F", "iE") + _v("H", "i"), lambda x: _b(x.get("Mo"), "kN·m", 1)),
            ("En büyük burulma düzensizliği katsayısı " + _v("η", "bi"), lambda x: _f(x.get("eta_max"), 3)),
            ("Ötelemede " + _v("T", "p") + " / taban kesmesi", lambda x: f"{_b(x.get('Tp_drift'), 's', 4)} / {_b(x.get('V_drift'), 'kN', 2)}"),
            ("En büyük " + _v("θ", "II") + " / sınır", lambda x: f"{_f(x.get('theta_max'), 4)} / {_f(x.get('theta_sinir'), 3)}"),
        ]
        X, Yd = _sozluk(d.get("X")), _sozluk(d.get("Y"))
        for ad, fn in tanim:
            rows.append([ad, fn(X) if X else "–", fn(Yd) if Yd else "–"])
        h += _tablo(["Büyüklük", "X doğrultusu", "Y doğrultusu"], rows)
        h += _p(f"{_v('R', 'a')}(<i>T</i>) = <i>R</i>/<i>I</i> (<i>T</i> > {_v('T', 'B')}); <i>D</i> + (<i>R</i>/<i>I</i> − <i>D</i>)<i>T</i>/{_v('T', 'B')} "
                f"(<i>T</i> ≤ {_v('T', 'B')}) {k('Ra')}. {_v('T', 'p')}: {k('Tp')}")
        # kat tablosu
        katlar = [x for x in _liste(d.get("katlar")) if isinstance(x, dict)]
        if katlar:
            h += _h3("7.3 Kat kütleleri ve eşdeğer deprem kuvvetleri")
            h += _p(f"{_v('F', 'iE')} = ({_v('V', 'tE')} − Δ{_v('F', 'NE')})·{_v('m', 'i')}{_v('H', 'i')}/Σ{_v('m', 'j')}{_v('H', 'j')} {k('F')}; "
                    f"{_v('m', 'i')} = ({_v('w', 'G')} + <i>n</i>·{_v('w', 'Q')})/<i>g</i> {k('n')}")
            rows = [[_e(x.get("kat")), _f(x.get("H"), 2), _f(x.get("h"), 2), _f(x.get("w_i"), 2), _f(x.get("m_i"), 3),
                     _f(x.get("F_x"), 2), _f(x.get("V_x"), 2), _f(x.get("F_y"), 2), _f(x.get("V_y"), 2)] for x in katlar]
            h += _tablo(["Kat", _v("H", "i") + " [m]", _v("h", "i") + " [m]", _v("w", "i") + " [kN]", _v("m", "i") + " [t]",
                         _v("F", "iE,X") + " [kN]", _v("V", "i,X") + " [kN]", _v("F", "iE,Y") + " [kN]", _v("V", "i,Y") + " [kN]"], rows,
                        alt=["Σ", "", "", _f(sum(float(x.get("w_i") or 0) for x in katlar), 2), _f(sum(float(x.get("m_i") or 0) for x in katlar), 3),
                             _f(sum(float(x.get("F_x") or 0) for x in katlar), 2), "", _f(sum(float(x.get("F_y") or 0) for x in katlar), 2), ""])
            h += _h3("7.4 Ek dışmerkezlik ve burulma düzensizliği")
            h += _p(f"<i>e</i> = ±{_f((d.get('e_oran') or 0.05), 2)}·<i>B</i> (deprem doğrultusuna dik kat boyutu); {_v('M', 'ib')} = {_v('F', 'iE')}·<i>e</i> {k('e')}. "
                    f"{_v('η', 'bi')} = (Δ<sub>i</sub>)<sub>max</sub>/(Δ<sub>i</sub>)<sub>ort</sub>; {_v('η', 'bi')} > 1.2 → A1 düzensizliği, "
                    f"≤ 2.0 eşdeğer deprem yükü yöntemi için sınır {k('eta_b')}")
            rows = []
            for x in katlar:
                ex, ey = x.get("eta_bx"), x.get("eta_by")
                rows.append([_e(x.get("kat")), _f(x.get("B_dik_x"), 2), _f(x.get("e_x"), 3), _f(x.get("Mb_x"), 2), _f(ex, 3),
                             _f(x.get("B_dik_y"), 2), _f(x.get("e_y"), 3), _f(x.get("Mb_y"), 2), _f(ey, 3), _f(x.get("D_b"), 2),
                             _isaret(all(not _sayi_mi(e) or float(e) <= 2.0 for e in (ex, ey)))
                             + (" A1" if any(_sayi_mi(e) and float(e) > 1.2 for e in (ex, ey)) else "")])
            h += _tablo(["Kat", _v("B", "⊥") + " (X yükü) [m]", _v("e", "X") + " [m]", _v("M", "b,X") + " [kN·m]", _v("η", "bX"),
                         _v("B", "⊥") + " (Y yükü) [m]", _v("e", "Y") + " [m]", _v("M", "b,Y") + " [kN·m]", _v("η", "bY"), _v("D", "bi"),
                         "η ≤ 2.0"], rows, sinif="kucuk")
            h += _h3("7.5 Göreli kat ötelemeleri (TBDY 2018 md. 4.9)")
            sin = d.get("sinir_oran")
            h += _p(f"Δ<sub>i</sub> = <i>u</i><sub>i</sub> − <i>u</i><sub>i−1</sub>; δ<sub>i</sub> = (<i>R</i>/<i>I</i>)·Δ<sub>i</sub>; "
                    f"<i>λ</i>·δ<sub>i,max</sub>/<i>h</i><sub>i</sub> ≤ {_f(sin, 4)} (κ = {_f(d.get('kappa'), 2)}, <i>λ</i> = {_f(d.get('lambda'), 3)}, "
                    f"dolgu: {_e(d.get('dolgu') or '–')}) {k('delta')}")
            rows = []
            for x in katlar:
                rows.append([_e(x.get("kat")), _f(x.get("h"), 2), _f(float(x.get("delta_x") or 0) * 1000, 3), _f(float(x.get("delta_etkin_x") or 0) * 1000, 2),
                             _f(x.get("oran_x"), 5), _f(float(x.get("delta_y") or 0) * 1000, 3), _f(float(x.get("delta_etkin_y") or 0) * 1000, 2),
                             _f(x.get("oran_y"), 5),
                             (_f(x.get("sinir_x"), 4) + " / " + _f(x.get("sinir_y"), 4) + f" (κ {_f(x.get('kappa_x'), 2)} / {_f(x.get('kappa_y'), 2)})")
                             if "sinir_x" in x else _f(x.get("sinir", sin), 4),
                             _dc_hucre(max(float(x.get("oran_x") or 0) / float(x["sinir_x"] or 1), float(x.get("oran_y") or 0) / float(x["sinir_y"] or 1))
                                       if "sinir_x" in x else
                                       max(float(x.get("oran_x") or 0), float(x.get("oran_y") or 0)) / float(x.get("sinir", sin) or 1),
                                       x.get("uygun"))])
            h += _tablo(["Kat", _v("h", "i") + " [m]", "Δ<sub>X,max</sub> [mm]", "δ<sub>X,max</sub> [mm]", "λδ<sub>X</sub>/h",
                         "Δ<sub>Y,max</sub> [mm]", "δ<sub>Y,max</sub> [mm]", "λδ<sub>Y</sub>/h", "Sınır", "D/C"], rows, sinif="kucuk")
            h += _h3("7.6 İkinci mertebe göstergesi " + _v("θ", "II"))
            h += _p(f"{_v('θ', 'II,i')} = (Δ<sub>i</sub>)<sub>ort</sub>·Σ<sub>k≥i</sub> <i>w</i><sub>k</sub>/({_v('V', 'i')}·{_v('h', 'i')}) ≤ "
                    f"0.12·<i>D</i>/({_v('C', 'h')}·<i>R</i>) = 0.12·{_f(d.get('D'), 2)}/({_f(d.get('Ch'), 2)}·{_f(d.get('R'), 2)}) = "
                    f"{_f(d.get('theta_sinir'), 4)} {k('theta')}")
            rows = [[_e(x.get("kat")), _f(x.get("theta_x"), 5), _f(x.get("theta_y"), 5),
                     (_f(x.get("theta_sinir_x"), 4) + " / " + _f(x.get("theta_sinir_y"), 4)) if "theta_sinir_x" in x else _f(d.get("theta_sinir"), 4),
                     _dc_hucre(max(float(x.get("theta_x") or 0) / float(x["theta_sinir_x"] or 1), float(x.get("theta_y") or 0) / float(x["theta_sinir_y"] or 1))
                               if "theta_sinir_x" in x else
                               max(float(x.get("theta_x") or 0), float(x.get("theta_y") or 0)) / float(d.get("theta_sinir") or 1))] for x in katlar]
            if any("kappa_x" in x for x in katlar):
                h += _p("Karma bina: κ (md. 4.9.1.3) ve " + _v("C", "h") + " (Denk. 4.36) kat ve doğrultu başına katın sisteminden — betonarme "
                        "κ = 1, " + _v("C", "h") + " = 0.5; çelik κ = 0.5, " + _v("C", "h") + " = 1; aynı katta ikisi birden çelik değerleri "
                        "(sınır sütununda X / Y).")
            h += _tablo(["Kat", _v("θ", "II,X"), _v("θ", "II,Y"), "Sınır", "D/C"], rows)
        uy = _sozluk(d.get("uygulanabilirlik"))
        if uy:
            h += _h3("7.7 Eşdeğer deprem yükü yönteminin uygulanabilirliği")
            h += _p(f"DTS = {_e(uy.get('DTS'))}, BYS = {_e(uy.get('BYS'))}, eşik BYS ≥ {_e(uy.get('esik'))} — "
                    f"{_e(uy.get('kosul_duzenli') or '')}. Sonuç: <b>{'uygulanabilir' if d.get('uygulanabilir') else 'uygulanamaz'}</b>. "
                    f'<span class="kaynak">{self.kaynak(uy.get("kaynak"))}</span>' + (f" {_e(uy.get('not'))}" if uy.get("not") else ""))
        if _liste(d.get("uyarilar")):
            h += _h3("Deprem uyarıları") + _ul([_e(u) for u in d["uyarilar"]])
        return h

    # ================================================================ 8. Analiz yöntemi
    def b8(self):
        v, ag, oz = self.v, _sozluk(self.v.get("ag")), _sozluk(self.v.get("ozet"))
        mes = _liste(ag.get("mesnetler"))
        tipler = {}
        for m in mes:
            if isinstance(m, dict):
                tipler[m.get("tip")] = tipler.get(m.get("tip"), 0) + 1
        n_dug = len(_liste(ag.get("dugumler")))
        h = _p("Yapı, üç boyutlu çubuk (uzay çerçeve) sonlu eleman modeliyle çözülmüştür: her düğümde 6 serbestlik derecesi "
               "(3 öteleme + 3 dönme), her çubuk 12×12 eleman rijitlik matrisli Euler–Bernoulli elemanıdır (Kassimali yerel eksen kuralı: "
               "<i>x</i>′ eleman ekseni, kirişte <i>y</i>′ yukarı). Yayılı yükler (üçgen/trapez/parçalı) eşdeğer düğüm yüklerine 3 noktalı "
               "Gauss–Legendre integrasyonuyla çevrilir; sistem doğrusal elastik çözülür ve birleşimler süperpozisyonla kurulur "
               "(<b>u</b><sub>komb</sub> = Σ<i>γ</i><sub>i</sub><b>u</b><sub>i</sub>).")
        sat = [("Düğüm / çubuk eleman sayısı", f"{_f(oz.get('dugum', n_dug), 0)} / {_f(oz.get('eleman', len(_liste(ag.get('elemanlar')))), 0)}"),
               ("Serbestlik derecesi (çözülen)", _f(oz.get("sd_sayisi", ag.get("sd_sayisi")), 0)),
               ("Rijitlik matrisi <b>K</b> boyutu (6 × düğüm)", f"{6 * n_dug} × {6 * n_dug}" if n_dug else "–"),
               ("Çözüm yolu", _e(ag.get("cozum_yolu") or ag.get("mod") or "–")),
               ("Mesnetler", _e(", ".join(f"{n} {t}" for t, n in tipler.items()) or "–")),
               ("Temel mesnet modeli", _e(self.temeller.get("mesnet") or "–")),
               ("Kat diyaframı", _e(ag.get("diyafram") or oz.get("diyafram") or "–")),
               ("Çatlamış kesit rijitliği", "evet (TBDY Tablo 4.2)" if oz.get("catlamis_rijitlik") else "hayır"),
               ("Kiriş öz ağırlığı", _e(_g(self.B, "analiz", "kiris_oz") or "–")),
               ("Diyagram istasyon sayısı", _f(_g(self.B, "analiz", "diyagram_nokta"), 0))]
        h += _anahtar_deger(sat)
        dy = [x for x in _liste(ag.get("diyaframlar")) if isinstance(x, dict)]
        if dy:
            h += _h3("Rijit diyaframlar (efendi–köle)")
            h += _p("Her kat döşemesi düzlem içinde rijit kabul edilir: kat düğümlerinin " + _v("u", "X") + ", " + _v("u", "Y") + ", "
                    + _v("θ", "Z") + " serbestlikleri, kütle merkezindeki ana (efendi) düğümün serbestliklerine bağlanır.")
            h += _tablo(["Diyafram", "Ana düğüm", "<i>X</i> [m]", "<i>Y</i> [m]", "<i>Z</i> [m]", "Bağlı düğüm"],
                        [[_e(x.get("ad")), _e(x.get("ana")), _f(x.get("X"), 3), _f(x.get("Y"), 3), _f(x.get("Z"), 3),
                          _f(len(_liste(x.get("dugumler"))), 0)] for x in dy])
        h += _h3("Uç serbestlikleri ve doğrusal olmayan elemanlar")
        cub = [c for c in _liste(self.ham.get("cubuklar")) if isinstance(c, dict)]
        serbest = [c for c in cub if c.get("serbest")]
        ycek = [c for c in cub if c.get("yalniz_cekme")]
        if serbest:
            h += _tablo(["Çubuk", "Tür", "<i>i</i> ucu", "<i>j</i> ucu"],
                        [[_e(c.get("no")), _e(_CUBUK_TURU.get(c.get("tur"), c.get("tur")) if self.genel else c.get("tur")),
                          _e(", ".join(_liste(_g(c, "serbest", "i")))) or "—",
                          _e(", ".join(_liste(_g(c, "serbest", "j")))) or "—"] for c in serbest], sayisal=())
        else:
            h += _not("Bütün çubuk uçları rijit (uç serbestliği tanımlanmadı).")
        if ycek:
            h += _p(f"{len(ycek)} çubuk yalnız çekme elemanıdır: dayanım birleşimleri süperpozisyonla değil, birleşim başına yinelemeli "
                    "(basınca düşen çubuk çıkarılarak) çözülür.")
        else:
            h += _not("Yalnız çekme (doğrusal olmayan) eleman yok; bütün birleşimler süperpozisyonla kurulur.")
        h += _h3("Yük durumları")
        rows = []
        for ad, k in _sozluk(v.get("durumlar")).items():
            S = self.tepki_toplami(k)
            bek = self.beklenen_tepki(ad)
            rows.append([f"<b>{_e(ad)}</b>", _e(_durum_adi(ad)), bek[1] if bek else "–",
                         _f(S["FX"], 2), _f(S["FY"], 2), _f(S["FZ"], 2)])
        h += _tablo(["Durum", "Açıklama", "Uygulanan toplam yük", "Σ" + _v("R", "X") + " [kN]", "Σ" + _v("R", "Y") + " [kN]",
                     "Σ" + _v("R", "Z") + " [kN]"], rows, sayisal=(3, 4, 5))
        h += _not("Her yük durumu aynı rijitlik matrisiyle ayrı sağ taraf olarak çözülür; "
                  "deprem birim durumları ve çatlamış kesit kopyaları yalnız birleşimlerde kullanılır.")
        return h

    # ================================================================ 9. Birleşimler
    def b9(self):
        v = self.v
        kume = _g(self.B, "kombinasyon_kumesi") or _g(self.ham, "kombinasyon_kumesi")
        kk = _sozluk(getattr(yv, "KOMBINASYONLAR", {}).get(kume)) if yv else {}
        h = _p(f"Kullanılan küme: <b>{_e(kk.get('ad') or kume or '–')}</b>"
               + (f' <span class="kaynak">({self.kaynak(kk.get("kaynak"))})</span>' if kk.get("kaynak") else ""))
        kmk = _sozluk(_g(self.v, "tasarim", "kombinasyon_kumeleri"))
        if kmk:      # karma yapı: kesit malzemesine göre küme
            h += _p("Karma yapı — eleman tahkikinde malzemeye göre küme: " + "; ".join(
                f"{_e(m)}: <b>{_e(_sozluk(x).get('ad') or _sozluk(x).get('kume'))}</b> ({_e(_sozluk(x).get('kombinasyon_sayisi'))} birleşim)"
                for m, x in kmk.items()) + ". Tablolarda ve zarfta ana küme gösterilir; aynı yük durumlarından kurulur.")
        kom = [k for k in _liste(v.get("kombinasyonlar")) if isinstance(k, dict)]
        if not kom:
            return h + _not(UYGULANMADI)
        uy = [k for k in kom if k.get("uygulandi")]
        h += _p(f"Uygulanan birleşim sayısı: <b>{len(uy)}</b> (tanımlı satır {len(kom)}; uygulanmayanlar ilgili yük durumu modelde "
                "olmadığı için listelenmiş ama hesaba girmemiştir).")
        tur_ad = {"dayanim": "dayanım", "servis": "servis", "deprem": "deprem", "drift": "öteleme"}
        # 9.1 aileler: yönetmelik satırı başına bir satır (kaynak, not, varyant sayısı)
        aileler = {}
        for k in kom:
            a = str(k.get("aile") or k.get("ad") or "")
            aileler.setdefault(a, []).append(k)
        rows = []
        for i, (a, ks) in enumerate(aileler.items(), 1):
            k0 = ks[0]
            n_uy = sum(1 for k in ks if k.get("uygulandi"))
            notlar = []
            for k in ks:
                n = str(k.get("not") or "").strip()
                if n and n not in notlar:
                    notlar.append(n)
            neden = next((str(k.get("neden")) for k in ks if not k.get("uygulandi") and k.get("neden")), "")
            rows.append([_e(i), f"<b>{_e(a)}</b>", _e(tur_ad.get(k0.get("tur"), k0.get("tur") or "")), _e(k0.get("kaynak") or ""),
                         f"{_isaret(True)} {n_uy}" if n_uy else "— " + _e(neden),
                         _e(len(ks)), "<br>".join(_e(n) for n in notlar)])
        h += _h3("9.1 Birleşim aileleri (yönetmelik satırları)")
        h += _tablo(["#", "Aile", "Tür", "Kaynak", "Uygulanan", "Varyant", "Not"], rows, sinif="kucuk", sayisal=(0, 5))
        # 9.2 her birleşimin tam katsayılı ifadesi (tek satır)
        rows = []
        for i, k in enumerate(kom, 1):
            tur = tur_ad.get(k.get("tur"), k.get("tur") or "")
            if k.get("catlamis"):
                tur += " (etkin rijitlik)"
            rows.append([_e(i), f'<span class="ifade">{_ifade(k.get("katsayilar"))}</span>', _e(tur),
                         _isaret(True) if k.get("uygulandi") else '<span class="birim">— uygulanmadı</span>'])
        h += _h3("9.2 Bütün birleşimlerin katsayılı ifadeleri")
        h += _p("Ad kuralı (sonuç tablolarında belirleyen birleşim bu adla yazılır): katsayılar sırasıyla, 1 yazılmaz; ör. "
                "<code>G+Q+0.2S+EX++0.3EY++0.3EZ</code> = G + Q + 0.2·S + (EX+) + 0.3·(EY+) + 0.3·EZ.")
        h += _tablo(["#", "Katsayılı ifade", "Tür", "Uygulandı"], rows, sinif="kucuk birlesim", sayisal=(0,))
        h += _not("EX±, EY±: ±%5 ek dışmerkezlikli yatay deprem durumları; EZ: düşey deprem etkisi; W±X, W±Y: rüzgâr doğrultuları; "
                  "TBDY 2018 md. 4.4.4: Ed(H) = ±Ed(X) ± 0.3Ed(Y) ve ±0.3Ed(X) ± Ed(Y). \"Etkin rijitlik\": TBDY 2018 md. 4.5.8 "
                  "çatlamış kesit rijitliğiyle çözülen birleşim.")
        return h

    # ================================================================ 10. Analiz sonuçları
    def b10(self):
        v = self.v
        h = ""
        durumlar = _sozluk(v.get("durumlar"))
        dadr = {d.get("no"): d for d in _liste(_g(v, "ag", "dugumler")) if isinstance(d, dict)}
        top = _sozluk(_g(v, "yukler", "toplam"))
        h += _h3("10.1 Mesnet tepkileri")
        ozet = []
        for ad, k in durumlar.items():
            S = self.tepki_toplami(k)
            bek = self.beklenen_tepki(ad)
            if bek:
                R = bek[0]
                buyukluk = max(abs(R[a]) for a in ("FX", "FY", "FZ"))
                fark = max(abs(S[a] - R[a]) for a in ("FX", "FY", "FZ")) / max(buyukluk, 1e-9) * 100
                ozet.append([f"<b>{_e(ad)}</b>", _f(S["FX"], 3), _f(S["FY"], 3), _f(S["FZ"], 3),
                             f"({_f(R['FX'], 3)}; {_f(R['FY'], 3)}; {_f(R['FZ'], 3)})", _f(fark, 4) + "&nbsp;%", _isaret(fark < 0.01)])
            else:
                ozet.append([f"<b>{_e(ad)}</b>", _f(S["FX"], 3), _f(S["FY"], 3), _f(S["FZ"], 3), "–", "–", "–"])
            if ad in ("G", "Q"):
                h += self._tepki_tablosu(f"Durum {ad} ({_e(_durum_adi(ad))})", k, dadr)
        for ad, k in _sozluk(v.get("sonuclar")).items():
            h += self._tepki_tablosu(f"Birleşim {_e(ad)}", k, dadr)
        h += _h4_tablo("Korunum denetimi: Σ tepki = − Σ uygulanan yük (durum başına)",
                       ["Durum", "Σ" + _v("R", "X") + " [kN]", "Σ" + _v("R", "Y") + " [kN]", "Σ" + _v("R", "Z") + " [kN]",
                        "Beklenen (" + _v("R", "X") + "; " + _v("R", "Y") + "; " + _v("R", "Z") + ") [kN]", "Fark", "ΣR = −ΣP"], ozet,
                       sinif="kucuk", dip="Beklenen tepki uygulanan yükün tersidir: düşey durumlarda Σ" + _v("R", "Z") + " = ΣG (ΣQ, ΣS); "
                       + ("panel rüzgârında Σ<b>R</b> = −Σ<b>F</b> (panel basınçlarının üç bileşeni)" if _g(v, "ruzgar", "yontem") == "panel"
                          else "rüzgârda Σ" + _v("R", "X") + " = ∓ΣF (TS 498 kat kuvvetleri)")
                       + ", depremde Σ" + _v("R", "X") + " = −" + _v("V", "tE")
                       + " (eşdeğer deprem yükü), EZ'de Σ" + _v("R", "Z") + " = " + _v("k", "z") + "·ΣG. Fark % = en büyük bileşen farkı / "
                       "beklenen büyüklük.")
        kor = _sozluk(_g(v, "akis", "korunum"))
        if kor:
            alan = [("dosemeler", "döşemeler"), ("paneller", "paneller"), ("duvarlar", "duvarlar"), ("kiris_oz", "kiriş öz ağırlığı"),
                    ("kolon_oz", "kolon öz ağırlığı"), ("cubuk_oz", "çubuk öz ağırlığı"), ("ek", "ek yükler"), ("temel_oz", "temel öz ağırlığı"),
                    ("toplam", "toplam yük"),
                    ("kolon_taban", "tabanlar ΣN (mesnet + yay)" if self.genel else "kolon tabanları ΣN"), ("tepki", "mesnet tepkisi ΣR"),
                    ("yay", "zemin yayları"), ("temel", "mesnet tepkileri ΣR" if self.genel else "temellere giden"),
                    ("yuk_alani", "yük alanı (el hesabı)"), ("dagitilamayan", "dağıtılamayan")]
            durum_ad = [d for d in kor if isinstance(kor[d], dict)]
            rows = [[_e(b)] + [_f(_g(kor, d, a), 3) for d in durum_ad] for a, b in alan if any(_g(kor, d, a) is not None for d in durum_ad)]
            h += _h4_tablo("Yük akışı korunumu (panel → çubuk → mesnet / temel) [kN]" if self.genel else
                           "Yük akışı korunumu (döşeme → kiriş → kolon → temel) [kN]", ["Kalem"] + [_e(d) for d in durum_ad], rows)
        # 10.2 kat kesmeleri
        h += _h3("10.2 Kat kesme kuvvetleri")
        rows = []
        dk = {x.get("kat"): x for x in _liste(_g(v, "deprem", "katlar")) if isinstance(x, dict)}
        rk = [x for x in _liste(_g(v, "ruzgar", "katlar")) if isinstance(x, dict)]
        rkum = {}
        tx = ty = 0.0
        for x in sorted(rk, key=lambda x: -float(x.get("kat") or 0)):
            tx += float(x.get("F_x") or 0)
            ty += float(x.get("F_y") or 0)
            rkum[x.get("kat")] = (tx, ty)
        for kat in sorted(set(dk) | set(rkum), key=lambda x: -float(x or 0)):
            rows.append([_e(kat), _f(_g(dk, kat, "V_x"), 2), _f(_g(dk, kat, "V_y"), 2),
                         _f(rkum[kat][0], 2) if kat in rkum else "–", _f(rkum[kat][1], 2) if kat in rkum else "–"])
        if _g(v, "ruzgar", "yontem") == "panel":
            h += self._panel_ruzgar_kesmesi(dk, durumlar)
        else:
            h += _tablo(["Kat", "Deprem " + _v("V", "i,X") + " [kN]", "Deprem " + _v("V", "i,Y") + " [kN]", "Rüzgâr " + _v("V", "i,X") + " [kN]",
                         "Rüzgâr " + _v("V", "i,Y") + " [kN]"], rows) if rows else _not("Yatay yük (deprem, rüzgâr) tanımlanmadı.")
        # 10.3 yer değiştirmeler
        h += _h3("10.3 Yer değiştirme en büyükleri")
        rows = []
        for ad, k in durumlar.items():
            dg = [x for x in _liste(_g(k, "dugumler")) if isinstance(x, dict)]
            if not dg:
                continue
            hucre = []
            for a in ("uX", "uY", "uZ"):
                x = max(dg, key=lambda d: abs(float(d.get(a) or 0)))
                hucre.append(f"{_f(float(x.get(a) or 0) * 1000, 3)} <span class=birim>({_e(_g(dadr, x.get('no'), 'adres', vars=x.get('no')))})</span>")
            rows.append([f"<b>{_e(ad)}</b>"] + hucre)
        if rows:
            h += _h4_tablo("Yük durumları", ["Durum", "|" + _v("u", "X") + "|<sub>max</sub> [mm]", "|" + _v("u", "Y") + "|<sub>max</sub> [mm]",
                           "|" + _v("u", "Z") + "|<sub>max</sub> [mm]"], rows)
        ko = _sozluk(v.get("kombinasyon_ozet"))
        if ko:
            rows = []
            for ad, o in ko.items():
                if not isinstance(o, dict):
                    continue
                u, en = _sozluk(o.get("u_enb")), _sozluk(o.get("enb"))
                rows.append([_e(ad), _f(float(u.get("X") or 0) * 1000, 3), _f(float(u.get("Y") or 0) * 1000, 3), _f(float(u.get("Z") or 0) * 1000, 3),
                             _f(en.get("N"), 2), _f(en.get("V"), 2), _f(en.get("Vz"), 2), _f(en.get("M"), 2), _f(en.get("My"), 2), _f(en.get("T"), 3),
                             _f(o.get("FZ_tepki"), 2)])
            h += _h4_tablo("Birleşimler (en büyük mutlak değerler)", ["Birleşim", "|" + _v("u", "X") + "| [mm]", "|" + _v("u", "Y") + "| [mm]",
                           "|" + _v("u", "Z") + "| [mm]", "|N| [kN]", "|" + _v("V", "y") + "| [kN]", "|" + _v("V", "z") + "| [kN]",
                           "|" + _v("M", "z") + "| [kN·m]", "|" + _v("M", "y") + "| [kN·m]", "|T| [kN·m]", "Σ" + _v("R", "Z") + " [kN]"],
                           rows, sinif="kucuk")
        # 10.4 zarf
        h += _h3("10.4 Eleman iç kuvvet zarfı")
        z = [x for x in _liste(_g(v, "zarf", "elemanlar")) if isinstance(x, dict)]
        if z:
            h += _p(f"Zarf {_f(_g(v, 'zarf', 'kombinasyon_sayisi', vars=len(_liste(_g(v, 'zarf', 'kombinasyonlar')))), 0)} birleşim üzerinden "
                    "(her istasyon, en küçük / en büyük). Yerel eksenler: <i>N</i> eksenel (çekme +), " + _v("V", "y") + " ve " + _v("M", "z")
                    + " güçlü eksen düzleminde (kirişte düşey), " + _v("V", "z") + " ve " + _v("M", "y") + " zayıf eksen, <i>T</i> burulma. "
                    "Birimler kN ve kN·m.")
            rows = []
            for x in z:
                e = self.el.get(x.get("no"), {})
                bel = _sozluk(x.get("belirleyen"))

                def mm(a):
                    return f"{_f(x.get(a + '_min'), 2)}<br>{_f(x.get(a + '_max'), 2)}"

                rows.append([f"{_e(x.get('no'))}<br><span class=birim>{_e(e.get('adres', ''))}</span>", mm("N"), mm("V"), mm("Vz"), mm("T"),
                             mm("My"), mm("M"),
                             f"<span class=birim>{_e(bel.get('M_min', ''))}<br>{_e(bel.get('M_max', ''))}</span>"])
            h += _tablo(["Eleman", "<i>N</i> min/maks", _v("V", "y") + " min/maks", _v("V", "z") + " min/maks", "<i>T</i> min/maks",
                         _v("M", "y") + " min/maks", _v("M", "z") + " min/maks", "Belirleyen (" + _v("M", "z") + " min / maks)"], rows,
                        sinif="kucuk", sayisal=range(1, 7))
        else:
            h += _not(UYGULANMADI)
        return h

    def _panel_ruzgar_kesmesi(self, dk, durumlar):
        """10.2 — panel rüzgârı: deprem kat kesmeleri ve rüzgâr taban kesmesi (W durumlarının mesnet tepkilerinden)."""
        h = ""
        if dk:
            rows = [[_e(kat), _f(_g(dk, kat, "V_x"), 2), _f(_g(dk, kat, "V_y"), 2)] for kat in sorted(dk, key=lambda x: -float(x or 0))]
            h += _tablo(["Kat", "Deprem " + _v("V", "i,X") + " [kN]", "Deprem " + _v("V", "i,Y") + " [kN]"], rows)
        rows = []
        for ad in ("W+X", "W-X", "W+Y", "W-Y"):
            k = durumlar.get(ad)
            if not isinstance(k, dict):
                continue
            S = self.tepki_toplami(k)
            rows.append([f"<b>{_e(ad.replace('-', '−'))}</b>", _f(S["FX"], 2), _f(S["FY"], 2), _f(S["FZ"], 2)])
        if rows:
            h += _h4_tablo("Rüzgâr taban kesmesi (W durumlarının mesnet tepkileri)",
                           ["Durum", "Σ" + _v("R", "X") + " [kN]", "Σ" + _v("R", "Y") + " [kN]", "Σ" + _v("R", "Z") + " [kN]"], rows)
        h += _not("Panel rüzgârı: kat kesmesi uygulanmaz — rüzgâr basıncı kat seviyelerine değil panellere (normal doğrultusunda) etkir; "
                  "yalnız taban kesmesi (Σ mesnet tepkisi) verilir. Σ" + _v("R", "Z") + " çatı emmesinin tepkisidir.")
        return h

    def _tepki_tablosu(self, baslik, kisa, dadr):
        """Bir durumun / birleşimin düğüm başına destek kuvvetleri (mesnet tepkisi + yay kuvveti, bina eksenleri) ve Σ satırı (= tepki
        toplamı, §10.1 korunum). Yay varsa 'Tür' ve 'Yay rijitliği' sütunları; yanıta yazılmayan temel ağı yayları tek satırda (Σ)."""
        kayit, oz = _tepki_kayitlari(kisa)
        if not kayit and not oz:
            return ""
        alan = ("FX", "FY", "FZ", "MX", "MY", "MZ")
        S = self.tepki_toplami(kisa)
        turlu = oz is not None or any(t["tip"] != "mesnet" for t in kayit)
        akis_yay = {m.get("dugum"): _sozluk(m.get("yay")) for m in _liste(_g(self.v, "akis", "mesnetler")) if isinstance(m, dict)}
        # mütemadi / radye temel ağının düğümleri: sabit tepkileri yalnız yatay tutulmadır (düşey kuvvet zemin yaylarında, yay_ozet)
        ag = {d.get("no") for d in _liste(_g(self.v, "temel", "dugumler")) if isinstance(d, dict)} \
            if _g(self.v, "temel", "tip") in ("surekli", "radye") else set()
        rows = []
        for t in kayit:
            r = [_e(t["dugum"]), _e(_g(dadr, t["dugum"], "adres", vars=""))]
            if turlu:
                yay = akis_yay.get(t["dugum"]) if t["tip"] == "yaylı mesnet" and akis_yay.get(t["dugum"]) else t["yay"]
                tip = "temel ağı (yatay tutulu)" if t["tip"] == "mesnet" and t["dugum"] in ag else t["tip"]
                r += [_e(tip), _e(_yay_metni(yay) if t["tip"] != "mesnet" else "") or "–"]
            rows.append(r + [_f(t[a], 3) for a in alan])
        if oz:
            rows.append(["–", "temel ağı (Σ)", "zemin yayları (Winkler)", "k<sub>z</sub> = k<sub>0</sub>·A<sub>etki</sub> (§13)"]
                        + [_f(oz[a], 3) for a in alan])
        bas = ["Düğüm", "Adres"] + (["Tür", "Yay rijitliği"] if turlu else []) + [
            _v("R", "X") + " [kN]", _v("R", "Y") + " [kN]", _v("R", "Z") + " [kN]", _v("M", "X") + " [kN·m]", _v("M", "Y") + " [kN·m]",
            _v("M", "Z") + " [kN·m]"]
        dip = ("Yaylı mesnet ve zemin yayı satırları yay kuvvetidir (yayın yapıya uyguladığı, mesnet tepkisi gibi); Σ satırı mesnet tepkileri "
               "ile yay kuvvetlerinin toplamıdır." if turlu else None)
        return _h4_tablo(baslik, bas, rows, alt=["Σ", ""] + (["", ""] if turlu else []) + [_f(S[a], 3) for a in alan], dip=dip)

    # ================================================================ 11. Betonarme
    def _tasarim_elemanlari(self, sistem):
        return [e for e in _liste(_g(self.v, "tasarim", "elemanlar")) if isinstance(e, dict) and e.get("sistem") == sistem]

    def _detay_secimi(self, elemanlar):
        if self.detay == "yok":
            return []
        if self.detay == "hepsi":
            return elemanlar
        sec, gor = [], set()
        turler = ["kiris", "kolon"]
        if self.genel:      # genel model: çapraz, aşık, kren kirişi, makas … da türüne göre
            turler += [t for t in _CUBUK_TURU if t not in turler and any(e.get("tur") == t for e in elemanlar)]
            turler += sorted({str(e.get("tur")) for e in elemanlar if e.get("tur") not in turler})
        for tur in turler:
            t = sorted((e for e in elemanlar if e.get("tur") == tur), key=lambda e: -float(e.get("dc") or 0))
            for e in t[:5] + [e for e in t[5:] if float(e.get("dc") or 0) > 1.0 + 1e-9]:
                if (tur, e.get("no")) not in gor:
                    gor.add((tur, e.get("no")))
                    sec.append(e)
        return sec

    def _kontrol_listesi(self, elemanlar):
        """Bütün elemanların bütün kontrol satırları: kontrol (formül) → talep ≤ kapasite → D/C ✔/✘."""
        rows = []
        for e in elemanlar:
            kon = [k for k in _liste(e.get("kontroller")) if isinstance(k, dict)]
            for i, k in enumerate(kon):
                birim = k.get("birim") or ""
                ilk = f"<b>{_e(e.get('adres'))}</b><br><span class=birim>{_e(e.get('kesit'))}</span>" if i == 0 else ""
                rows.append([ilk, _formul(k.get("ad")), f"{_s(k.get('talep'), 4)} ≤ {_s(k.get('kapasite'), 4)}{('&nbsp;' + _e(birim)) if birim else ''}",
                             f"<span class=birim>{_e(k.get('kombinasyon') or '—')}</span>", _dc_hucre(k.get("dc"), k.get("saglandi"))])
        return _tablo(["Eleman", "Kontrol (formül)", "Yerine konmuş: talep ≤ kapasite", "Birleşim", "D/C"], rows, sinif="kucuk", sayisal=(2, 4))

    def _kontrol_tablosu(self, satirlar):
        """Ayrıntılı kontrol tablosu: [(ad, formül, [adımlar], sonuç, dc, sağlandı, kaynak, birleşim)]."""
        rows = []
        for ad, formul, adimlar, sonuc, dc, ok, kayn, komb in satirlar:
            ilk = f"<b>{ad}</b>" + (f"<br><span class=kaynak>{self.kaynak(kayn)}</span>" if kayn else "") \
                  + (f"<br><span class=birim>Birleşim: {_e(komb)}</span>" if komb else "")
            orta = (f'<span class="adim">{formul}</span>' if formul else "") + "".join(f'<span class="adim">{a}</span>' for a in adimlar)
            rows.append([ilk, orta, sonuc, _dc_hucre(dc, ok) if dc is not None else (_isaret(ok) if ok is not None else "–")])
        return _tablo(["Kontrol", "Formül → yerine konmuş değerler", "Sonuç", "D/C"], rows, sinif="kontrol", sayisal=(3,))

    def _ba_malzeme(self, e):
        mal = self.malzeme(e.get("malzeme"))
        beton = mal.get("kutuphane") or "C30/37"
        don = self.kesit_ham(e.get("kesit")).get("donati")
        dm = self.malzeme(don) if don else {}
        donati = dm.get("kutuphane") or (don if don and yv and don in getattr(yv, "DONATILAR", {}) else "B420C")
        return beton, donati

    def _kiris_detay(self, e):
        oz, ts = _sozluk(e.get("ozet")), self.ts
        beton, donati = self._ba_malzeme(e)
        kon = {str(k.get("ad")): k for k in _liste(e.get("kontroller")) if isinstance(k, dict)}
        # genel model (yapi_serbest) satır adları tasarim.py'nin adlarıdır ("Mesnet (üst donatı): …Eğilme taşıma gücü…",
        # "Kesme (<kombinasyon>): …Kesme dayanımı…"): aks–kat adıyla bulunamayan satır desenle eşlenir
        for anahtar, bas, icerik in (("Eğilme (mesnet, üst) Md ≤ Mr", "Mesnet", "Eğilme taşıma gücü"),
                                     ("Eğilme (açıklık, alt) Md ≤ Mr", "Açıklık", "Eğilme taşıma gücü"),
                                     ("Kesme Vd ≤ Vc + Vw", "Kesme (", "Kesme dayanımı"),
                                     ("Kesme üst sınırı Vd ≤ 0,22 fcd bw d", "Kesme (", "Kesme üst sınırı")):
            if anahtar not in kon:
                k_ = next((k for a, k in kon.items() if a.startswith(bas) and icerik in a), None)
                if k_ is not None:
                    kon[anahtar] = k_
        b, h, d = oz.get("b"), oz.get("h"), oz.get("d_m")
        satir = []
        if ts is None or not all(_sayi_mi(x) for x in (b, h, d)):
            return None
        dp = float(h) - float(d)
        try:
            bm, dm = ts.beton_malzeme(beton), ts.donati_malzeme(donati)
            em = ts.kiris_egilme(float(oz.get("Md_mesnet") or 0), b, h, dp, bm, dm)
            ea = ts.kiris_egilme(float(oz.get("Md_aciklik") or 0), b, h, dp, bm, dm)
            kk = ts.kiris_kesme(float(oz.get("Vd") or 0), b, h, dp, bm, dm)
        except Exception:   # noqa: BLE001 — tasarım API'si değişirse özet satırlarına düşülür
            return None
        fcd, fyd, fctd, k1 = bm["fcd"], dm["fyd"], bm["fctd"], bm["k1"]
        bmm, dmm = float(b) * 1000, float(d) * 1000
        genel = [f"<i>b</i> = {_f(bmm, 0)} mm, <i>h</i> = {_f(float(h) * 1000, 0)} mm, <i>d</i> = <i>h</i> − <i>d</i>′ = {_f(float(h) * 1000, 0)} − "
                 f"{_f(dp * 1000, 0)} = {_f(dmm, 0)} mm; {_v('f', 'cd')} = {_f(fcd, 2)} MPa, {_v('f', 'yd')} = {_f(fyd, 2)} MPa, "
                 f"{_v('f', 'ctd')} = {_f(fctd, 3)} MPa, {_v('k', '1')} = {_f(k1, 2)}"]
        for etiket, r, anahtar, ust in (("mesnet, üst donatı", em, "Eğilme (mesnet, üst) Md ≤ Mr", True),
                                        ("açıklık, alt donatı", ea, "Eğilme (açıklık, alt) Md ≤ Mr", False)):
            k = kon.get(anahtar, {})
            As_g, As_s = r.get("As_gerekli_cm2"), r.get("As_saglanan_cm2")
            oneri = _g(r, "oneri", "metin") or "–"
            Md = r.get("Md_kNm")
            adim = [f"{_v('ρ', 'min')} = 0.8{_v('f', 'ctd')}/{_v('f', 'yd')} = 0.8·{_f(fctd, 3)}/{_f(fyd, 2)} = {_f(r.get('rho_min'), 5)}; "
                    f"{_v('A', 's,min')} = {_v('ρ', 'min')}<i>bd</i> = {_f(float(r.get('rho_min') or 0) * bmm * dmm / 100, 2)} cm²",
                    f"{_v('M', 'd')} = {_f(Md, 2)} kN·m → {_v('A', 's,gerekli')} = <b>{_f(As_g, 2)} cm²</b>"
                    + (" (çift donatılı: " + _v("A", "s′") + f" = {_f(r.get('As_ust_gerekli_cm2'), 2)} cm²)" if (r.get("As_ust_gerekli_cm2") or 0) > 0 else "")
                    + f"; seçilen <b>{_e(oneri)}</b> = {_f(As_s, 2)} cm²",
                    f"<i>a</i> = {_v('A', 's')}{_v('f', 'yd')}/(0.85{_v('f', 'cd')}<i>b</i>) = {_f(float(As_s or 0) * 100, 1)}·{_f(fyd, 2)}/(0.85·{_f(fcd, 2)}·{_f(bmm, 0)}) "
                    f"= {_f(r.get('a_r_mm'), 2)} mm (<i>c</i> = <i>a</i>/{_v('k', '1')} = {_f(r.get('c_r_mm'), 2)} mm, {_v('ε', 's')} = {_f(r.get('eps_s_r'), 5)})",
                    f"{_v('M', 'r')} = {_v('A', 's')}{_v('f', 'yd')}(<i>d</i> − <i>a</i>/2) = {_f(float(As_s or 0) * 100, 1)}·{_f(fyd, 2)}·({_f(dmm, 0)} − "
                    f"{_f(float(r.get('a_r_mm') or 0) / 2, 2)})·10<sup>−6</sup> = {_f(r.get('Mr_kNm'), 2)} kN·m"]
            satir.append((f"Eğilme ({_e(etiket)})", f"{_v('M', 'd')} ≤ {_v('M', 'r')}", adim,
                          f"{_b(Md, 'kN·m')} ≤ {_b(r.get('Mr_kNm'), 'kN·m')}", k.get("dc", r.get("Mr_kNm") and float(Md or 0) / float(r["Mr_kNm"])),
                          k.get("saglandi"), "TS 500 md. 7.1, Çizelge 7.1", k.get("kombinasyon")))
            rho = r.get("rho_saglanan")
            satir.append((f"Donatı oranı ({_e(etiket)})", f"{_v('ρ', 'min')} ≤ ρ ≤ {_v('ρ', 'max')} = min(0.85{_v('ρ', 'b')}; 0.02)",
                          [f"ρ = {_v('A', 's')}/(<i>bd</i>) = {_f(float(As_s or 0) * 100, 1)}/({_f(bmm, 0)}·{_f(dmm, 0)}) = {_f(rho, 5)}; "
                           f"{_v('ρ', 'b')} = {_f(r.get('rho_b'), 5)}, 0.85{_v('ρ', 'b')} = {_f(r.get('rho_085b'), 5)}"],
                          f"{_f(r.get('rho_min'), 5)} ≤ {_f(rho, 5)} ≤ {_f(r.get('rho_max'), 4)}",
                          float(rho or 0) / float(r.get("rho_max") or 1), float(r.get("rho_min") or 0) <= float(rho or 0) + 1e-12 <= float(r.get("rho_max") or 1) + 2e-12,
                          "TS 500 md. 7.3, Denk. 7.3–7.5", None))
        k = kon.get("Kesme Vd ≤ Vc + Vw", {})
        o = _sozluk(kk.get("oneri"))
        satir.append(("Kesme dayanımı", f"{_v('V', 'd')} ≤ {_v('V', 'r')} = {_v('V', 'c')} + {_v('V', 'w')}",
                      [f"{_v('V', 'cr')} = 0.65{_v('f', 'ctd')}<i>b</i><sub>w</sub><i>d</i> = 0.65·{_f(fctd, 3)}·{_f(bmm, 0)}·{_f(dmm, 0)}·10<sup>−3</sup> = {_f(kk.get('V_cr_kN'), 2)} kN; "
                       f"{_v('V', 'c')} = 0.8{_v('V', 'cr')} = {_f(kk.get('V_c_kN'), 2)} kN",
                       f"{_v('A', 'sw')}/<i>s</i> (min) = 0.3({_v('f', 'ctd')}/{_v('f', 'ywd')})<i>b</i><sub>w</sub> = 0.3·({_f(fctd, 3)}/{_f(kk.get('fywd'), 2)})·{_f(bmm, 0)} = "
                       f"{_f(kk.get('Asw_s_min'), 4)} mm²/mm; seçilen etriye <b>{_e(o.get('metin') or oz.get('etriye') or '–')}</b> "
                       f"({_v('A', 'sw')}/<i>s</i> = {_f(o.get('Asw_s'), 4)} mm²/mm, {_v('s', 'max')} = {_f(kk.get('s_max_mm'), 0)} mm)",
                       f"{_v('V', 'w')} = ({_v('A', 'sw')}/<i>s</i>){_v('f', 'ywd')}<i>d</i> = {_f(o.get('Asw_s'), 4)}·{_f(kk.get('fywd'), 2)}·{_f(dmm, 0)}·10<sup>−3</sup> = "
                       f"{_f(kk.get('V_w_kN'), 2)} kN; {_v('V', 'r')} = {_f(kk.get('V_c_kN'), 2)} + {_f(kk.get('V_w_kN'), 2)} = {_f(kk.get('V_r_kN'), 2)} kN"],
                      f"{_b(oz.get('Vd'), 'kN')} ≤ {_b(kk.get('V_r_kN'), 'kN')}", k.get("dc"), k.get("saglandi"), "TS 500 md. 8.1.4, Denk. 8.4–8.5",
                      k.get("kombinasyon")))
        k = kon.get("Kesme üst sınırı Vd ≤ 0,22 fcd bw d", {})
        satir.append(("Kesme üst sınırı (gövde ezilmesi)", f"{_v('V', 'd')} ≤ 0.22{_v('f', 'cd')}<i>b</i><sub>w</sub><i>d</i>",
                      [f"0.22·{_f(fcd, 2)}·{_f(bmm, 0)}·{_f(dmm, 0)}·10<sup>−3</sup> = {_f(kk.get('V_max_kN'), 2)} kN"],
                      f"{_b(oz.get('Vd'), 'kN')} ≤ {_b(kk.get('V_max_kN'), 'kN')}", k.get("dc"), k.get("saglandi"), "TS 500 md. 8.1.5b, Denk. 8.7",
                      k.get("kombinasyon")))
        for k in _liste(e.get("kontroller")):   # boyut koşulları ve diğerleri (özet satırları)
            if isinstance(k, dict) and (k.get("kosul") or str(k.get("ad", "")).startswith(("mesnet:", "açıklık:", "kesme:", "TBDY"))):
                satir.append((_formul(k.get("ad")), "", [], f"{_s(k.get('talep'), 4)} / {_s(k.get('kapasite'), 4)} {_e(k.get('birim') or '')}",
                              k.get("dc"), k.get("saglandi"), k.get("kaynak"), k.get("kombinasyon")))
        return "<p>" + "; ".join(genel) + "</p>" + self._kontrol_tablosu(satir)

    def _kolon_detay(self, e):
        oz = _sozluk(e.get("ozet"))
        beton, donati = self._ba_malzeme(e)
        bm = None
        if self.ts:
            try:
                bm = self.ts.beton_malzeme(beton)
            except Exception:   # noqa: BLE001
                bm = None
        fck = float(bm["fck"]) if bm else float(self.malzeme(e.get("malzeme")).get("fck") or 0)
        fcd = float(bm["fcd"]) if bm else fck / 1.5
        bX, bY = float(oz.get("bX") or 0), float(oz.get("bY") or 0)
        Ac = bX * bY * 1e6
        kon = [k for k in _liste(e.get("kontroller")) if isinstance(k, dict)]
        Nd = next((k.get("talep") for k in kon if "0,9 fcd" in str(k.get("ad"))), None)
        satir = []
        genel = (f"<i>b</i><sub>X</sub> × <i>b</i><sub>Y</sub> = {_f(bX * 1000, 0)} × {_f(bY * 1000, 0)} mm, {_v('A', 'c')} = {_f(Ac, 0)} mm²; "
                 f"{_v('f', 'ck')} = {_f(fck, 1)} MPa, {_v('f', 'cd')} = {_f(fcd, 2)} MPa; ρ = {_f(oz.get('rho'), 4)}"
                 + (" (varsayım)" if oz.get("rho_varsayim") else "") + f", {_v('A', 's')} = {_f(oz.get('As_toplam_cm2'), 2)} cm²"
                 + (f"; D/C ≤ 1 için gereken ρ = {_f(oz.get('rho_gerekli'), 4)}" if oz.get("rho_gerekli") is not None else "; gereken ρ ≤ 0.04 bulunamadı"))
        for k in kon:
            ad = str(k.get("ad") or "")
            komb, kayn = k.get("kombinasyon"), k.get("kaynak")
            tam = ad
            if ad.startswith("N–M: "):          # genel model satırı "N–M: <kombinasyon> (uç): N–Mx etkileşimi …": kuyruğuyla eşlenir
                ad = ad.rsplit(": ", 1)[-1]
            if ad.startswith("N–Mx") or ad.startswith("N–My"):
                x = ad.startswith("N–Mx")
                derinlik = bY if x else bX
                emin = 15 + 0.03 * derinlik * 1000
                eks = "x" if x else "y"
                adim = [f"{_v('e', 'min')} = 15 mm + 0.03<i>h</i> = 15 + 0.03·{_f(derinlik * 1000, 0)} = {_f(emin, 1)} mm"]
                if _sayi_mi(Nd):
                    adim.append(f"{_v('N', 'd')} = {_f(Nd, 2)} kN; {_v('N', 'd')}·{_v('e', 'min')} = {_f(float(Nd) * emin / 1000, 2)} kN·m; "
                                f"{_v('M', 'd' + eks)} = max(|{_v('M', eks)}|, {_v('N', 'd')}{_v('e', 'min')}) = {_f(k.get('talep'), 2)} kN·m")
                adim.append(f"{_v('M', 'r' + eks)}({_v('N', 'd')}): TS 500 eşdeğer dikdörtgen blokla kurulan N–M etkileşim eğrisi üzerinde, "
                            "orijinden geçen ışın boyunca (radyal) kapasite = " + _b(k.get("kapasite"), "kN·m"))
                satir.append((_formul(tam), f"{_v('M', 'd' + eks)} ≤ {_v('M', 'r' + eks)}({_v('N', 'd')})", adim,
                              f"{_b(k.get('talep'), 'kN·m')} ≤ {_b(k.get('kapasite'), 'kN·m')}", k.get("dc"), k.get("saglandi"), kayn, komb))
            elif ad.startswith("İki eksenli"):
                kuyruk = lambda q: str(q.get("ad", "")).rsplit(": ", 1)[-1] if str(q.get("ad", "")).startswith("N–M: ") else str(q.get("ad", ""))  # noqa: E731
                mx = next((q for q in kon if kuyruk(q).startswith("N–Mx") and (q.get("kombinasyon") == komb or not komb)), None) \
                    or next((q for q in kon if kuyruk(q).startswith("N–Mx")), {})
                my = next((q for q in kon if kuyruk(q).startswith("N–My") and (q.get("kombinasyon") == komb or not komb)), None) \
                    or next((q for q in kon if kuyruk(q).startswith("N–My")), {})
                adim = [f"{_v('M', 'dx')}/{_v('M', 'rx')} = {_f(mx.get('talep'), 2)}/{_f(mx.get('kapasite'), 2)} = {_f(mx.get('dc'), 3)}; "
                        f"{_v('M', 'dy')}/{_v('M', 'ry')} = {_f(my.get('talep'), 2)}/{_f(my.get('kapasite'), 2)} = {_f(my.get('dc'), 3)}",
                        "Bresler ters yük (1/" + _v("N", "r") + " = 1/" + _v("N", "rx") + " + 1/" + _v("N", "ry") + " − 1/" + _v("N", "0")
                        + ", " + _v("N", "d") + " ≥ 0.1" + _v("f", "ck") + _v("A", "c") + ") ya da doğrusal toplam (öğretici yaklaşım)"]
                satir.append(("İki eksenli eğilme", f"{_v('M', 'dx')}/{_v('M', 'rx')} + {_v('M', 'dy')}/{_v('M', 'ry')} ≤ 1 (ya da {_v('N', 'd')}/{_v('N', 'r')} ≤ 1)",
                              adim, f"η = {_f(k.get('talep'), 3)} ≤ 1", k.get("dc"), k.get("saglandi"), kayn, komb))
            elif "0,9 fcd" in ad:
                satir.append(("Eksenel kuvvet üst sınırı (TS 500)", f"{_v('N', 'd')} ≤ 0.9{_v('f', 'cd')}{_v('A', 'c')}",
                              [f"0.9·{_f(fcd, 2)}·{_f(Ac, 0)}·10<sup>−3</sup> = {_f(0.9 * fcd * Ac / 1000, 1)} kN"],
                              f"{_b(k.get('talep'), 'kN')} ≤ {_b(k.get('kapasite'), 'kN')}", k.get("dc"), k.get("saglandi"), kayn, komb))
            elif "0,40 fck" in ad:
                satir.append(("Eksenel kuvvet sınırı (TBDY)", f"{_v('N', 'dm')} ≤ 0.40{_v('f', 'ck')}{_v('A', 'c')}",
                              [f"0.40·{_f(fck, 1)}·{_f(Ac, 0)}·10<sup>−3</sup> = {_f(0.40 * fck * Ac / 1000, 1)} kN"],
                              f"{_b(k.get('talep'), 'kN')} ≤ {_b(k.get('kapasite'), 'kN')}", k.get("dc"), k.get("saglandi"), kayn, komb))
            elif "ρ" in ad:
                satir.append((_formul(tam), f"ρ = {_v('A', 's')}/{_v('A', 'c')} ≥ 0.01",
                              [f"ρ = {_f(oz.get('As_toplam_cm2'), 2)}/{_f(Ac / 100, 1)} = {_f(oz.get('rho'), 4)}"],
                              f"{_f(k.get('kapasite'), 4)} ≥ {_f(k.get('talep'), 4)}", k.get("dc"), k.get("saglandi"), kayn, komb))
            else:
                satir.append((_formul(tam), "", [], f"{_s(k.get('talep'), 4)} / {_s(k.get('kapasite'), 4)} {_e(k.get('birim') or '')}",
                              k.get("dc"), k.get("saglandi"), kayn, komb))
        return f"<p>{genel}</p>" + self._kontrol_tablosu(satir)

    def _eleman_basligi(self, e):
        tur = _ELEMAN_TURU.get(e.get("tur"), e.get("tur"))
        bel = _sozluk(e.get("belirleyen"))
        return (f"<h4>{_e(e.get('adres'))} — {_e(tur)} {_e(e.get('no'))}, {_e(e.get('kesit'))} ({_e(e.get('malzeme'))}) "
                f"· D/C {_dc_hucre(e.get('dc'))}</h4><p class=kaynak>Belirleyen: {_e(bel.get('kontrol') or '–')} — "
                f"{_e(bel.get('kombinasyon') or '–')}; durum: {_e(e.get('durum') or '–')}; FE elemanları: "
                f"{_e(', '.join(map(str, _liste(e.get('fe_elemanlar')))))}</p>")

    @staticmethod
    def _varsayimlar(tas, sistem):
        """§11.1 / §12.1 varsayım satırları: genel model (``varsayim_gruplari``) yalnız bu sistemin ve ortak satırları — betonarme
        bölümünde ÇYTHYE / kren satırı, çelik bölümünde TS 500 satırı yazılmaz; aks–kat modeli (gruplar yok) bütün liste."""
        gr = _sozluk(tas.get("varsayim_gruplari"))
        if gr:
            return _liste(gr.get(sistem)) + _liste(gr.get("ortak"))
        return _liste(tas.get("varsayimlar"))

    def b11(self):
        tas = _sozluk(self.v.get("tasarim"))
        el = self._tasarim_elemanlari("betonarme")
        if not tas:
            return _not("Kesit tahkikleri bu çözümde yok (tasarım modülü yüklenmedi). " + UYGULANMADI)
        if not el:
            return _not("Modelde betonarme eleman yok. " + UYGULANMADI)
        h = _p(f"Yöntem: <b>{_e(_g(tas, 'yontem', 'betonarme') or 'TS 500:2000')}</b>; tahkik birleşim sayısı "
               f"{_f(tas.get('kombinasyon_sayisi'), 0)}.") + _h3("11.1 Varsayımlar") + _ul([_e(x) for x in self._varsayimlar(tas, "betonarme")])
        kir = [e for e in el if e.get("tur") == "kiris"]
        kol = [e for e in el if e.get("tur") == "kolon"]
        if kir:
            rows = []
            for e in kir:
                o = _sozluk(e.get("ozet"))
                rows.append([f"{_e(e.get('adres'))}", _e(e.get("kesit")), _f(o.get("Md_mesnet"), 2), _f(o.get("As_ust_cm2"), 2), _e(o.get("oneri_ust") or "–"),
                             _f(o.get("Md_aciklik"), 2), _f(o.get("As_alt_cm2"), 2), _e(o.get("oneri_alt") or "–"), _f(o.get("Vd"), 2),
                             _e(o.get("etriye") or "–"), _dc_hucre(e.get("dc"))])
            h += _h3("11.2 Kirişler — özet")
            h += _tablo(["Kiriş", "Kesit", _v("M", "d,mesnet") + " [kN·m]", _v("A", "s,üst") + " [cm²]", "Üst donatı",
                         _v("M", "d,açıklık") + " [kN·m]", _v("A", "s,alt") + " [cm²]", "Alt donatı", _v("V", "d") + " [kN]", "Etriye", "D/C"],
                        rows, sinif="kucuk", sayisal=(2, 3, 5, 6, 8, 10))
        if kol:
            rows = []
            for e in kol:
                o = _sozluk(e.get("ozet"))
                n04 = float(o.get("Ndm_kN") or 0) / float(o.get("N_sinir_TBDY_kN") or 1)
                eksik = self.genel and "N_sinir_TBDY_kN" not in o        # genel model kaydında olmayan alanlar "–"
                rows.append([_e(e.get("adres")), _e(e.get("kesit")), _e(o.get("yon") or ""), _f(o.get("N_max_kN"), 1), _f(o.get("N_min_kN"), 1),
                             _f(o.get("rho"), 4), _f(o.get("As_toplam_cm2"), 2), _f(o.get("rho_gerekli"), 4) if o.get("rho_gerekli") is not None else
                             ("–" if self.genel and "rho_gerekli" not in o else "> 0.04"),
                             "–" if eksik else _f(n04, 3), _e(_g(e, "belirleyen", "kontrol") or ""), _dc_hucre(e.get("dc"))])
            h += _h3("11.3 Kolonlar — özet")
            h += _tablo(["Kolon", "Kesit", "Yön", _v("N", "maks") + " [kN]", _v("N", "min") + " [kN]", "ρ", _v("A", "s") + " [cm²]", "ρ gerekli",
                         _v("N", "dm") + "/(0.40" + _v("f", "ck") + _v("A", "c") + ")", "Belirleyen", "D/C"], rows, sinif="kucuk",
                        sayisal=(3, 4, 5, 6, 7, 8, 10))
            h += _not("N basınç pozitif. Kolon noktaları her birleşimin alt ve üst ucundaki eş zamanlı (N, M<sub>x</sub>, M<sub>y</sub>) "
                      "değerleridir (zarf değil).")
        h += _h3("11.4 Döşemeler")
        h += _not("Döşeme eğilme/donatı tahkiki bu modelde uygulanmadı; döşemeler yük aktarımı (TS 500 md. 11.4.3) için modellenmiştir.")
        sec = self._detay_secimi(el)
        h += _h3("11.5 Ayrıntılı kesit hesapları"
                 + {"kritik": " (her türde D/C en büyük 5 eleman + D/C &gt; 1 olanlar)", "hepsi": " (bütün elemanlar)", "yok": ""}[self.detay])
        if not sec:
            h += _not("Ayrıntılı hesap seçilmedi (eleman_detay = \"yok\").")
        for e in sec:
            govde = self._kiris_detay(e) if e.get("tur") == "kiris" else self._kolon_detay(e)
            if govde is None:
                govde = self._kontrol_listesi([e])
            h += f'<div class="eleman">{self._eleman_basligi(e)}{govde}</div>'
        h += _h3("11.6 Bütün betonarme elemanların kontrol satırları") + self._kontrol_listesi(el)
        return h

    # ================================================================ 12. Çelik
    def _celik_detay(self, e):
        oz, ts = _sozluk(e.get("ozet")), self.ts
        kes = _sozluk(_g(self.v, "kutuphane_ozeti", "kesitler", e.get("kesit")))
        profil = kes.get("profil")
        mal = self.malzeme(e.get("malzeme"))
        if ts is None or not profil:
            return None
        if kes.get("tip") == "basit" or str(oz.get("kontrol") or "").startswith("çubuk"):
            return None        # basit kesit / eksenel çubuk (ÇYTHYE 7–8): I profil eğilme ayrıntısı yok, kontrol satırları gösterilir
        Kh = oz.get("K")
        if isinstance(Kh, (list, tuple)) and Kh:      # genel model: [K_güçlü, K_zayıf]
            K = tuple(float(x) for x in (list(Kh) + list(Kh))[:2])
            K_metin = f"{_f(K[0], 2)} / {_f(K[1], 2)} (güçlü / zayıf eksen)"
        else:
            K = float(Kh or 1)
            K_metin = _f(oz.get("K"), 2)
        bolge = oz.get("bolge")
        if bolge == "negatif":
            Lb, Cb = oz.get("Lb_neg_m"), oz.get("Cb_neg")
        elif bolge == "pozitif":
            Lb, Cb = 0.0, 1.0
        else:
            Lb, Cb = oz.get("Lb_m"), 1.0
        try:
            r = ts.celik_eleman_kontrol(profil, mal.get("kutuphane") or "S275", L=float(oz.get("L_m") or 1), Lb=float(Lb or 0),
                                        K=K, Cb=float(Cb or 1), yontem=oz.get("yontem") or "YDKT",
                                        **({"kren": True} if self.genel and e.get("tur") == "kren" else {}),
                                        kuvvetler=[{"ad": "belirleyen", "N": float(oz.get("N_kN") or 0), "Mx": float(oz.get("Mx_kNm") or 0),
                                                    "My": float(oz.get("My_kNm") or 0), "V": float(oz.get("V_kN") or 0)}])
        except Exception:   # noqa: BLE001
            return None
        p = _sozluk(getattr(yv, "PROFILLER", {}).get(profil)) if yv else {}
        m, sn, eg, bs, ks, ck = (_sozluk(r.get(a)) for a in ("malzeme", "sinif", "egilme", "basinc", "kesme", "cekme"))
        Fy, E = float(m.get("Fy") or 275), float(m.get("E") or 200000)
        y = r.get("yontem") or "YDKT"
        kat_ad = lambda kk, alt: (f"{_v('φ', alt)} = {_f(kk.get('phi_' + alt[0]), 2)}" if y == "YDKT"   # noqa: E731
                                  else f"1/{_v('Ω', alt)} = 1/{_f(kk.get('Omega_' + alt[0]), 2)}")
        kmb = _sozluk(_liste(r.get("kombinasyonlar"))[0]) if _liste(r.get("kombinasyonlar")) else {}
        et = _sozluk(kmb.get("etkilesim"))
        bel = _g(e, "belirleyen", "kombinasyon")
        satir = []
        bsl, gv = _sozluk(sn.get("baslik")), _sozluk(sn.get("govde"))
        satir.append(("Kesit sınıfı", f"λ = <i>b</i>/2{_v('t', 'f')} (başlık), <i>h</i>/{_v('t', 'w')} (gövde)",
                      [f"başlık: λ = {_f(bsl.get('oran'), 2)}; {_v('λ', 'p')} = 0.38√(<i>E</i>/{_v('F', 'y')}) = {_f(bsl.get('lambda_p'), 2)}; "
                       f"{_v('λ', 'r')} = {_f(bsl.get('lambda_r'), 2)}",
                       f"gövde: λ = {_f(gv.get('oran'), 2)}; {_v('λ', 'p')} = 3.76√(<i>E</i>/{_v('F', 'y')}) = {_f(gv.get('lambda_p'), 2)}; "
                       f"{_v('λ', 'r')} = {_f(gv.get('lambda_r'), 2)}"],
                      f"eğilme: {_e(sn.get('egilme'))}; basınç: {_e(sn.get('basinc'))}", None, sn.get("egilme") != "narin", sn.get("kaynak"), None))
        iz = float(p.get("iz") or 0) * 10
        Lp, Lr, Lbm = eg.get("Lp_m"), eg.get("Lr_m"), eg.get("Lb_m")
        adim = [f"{_v('M', 'p')} = {_v('F', 'y')}{_v('W', 'pl,y')} = {_f(Fy, 0)}·{_f(float(p.get('Wply') or 0) * 1000, 0)}·10<sup>−6</sup> = {_f(eg.get('Mp_kNm'), 2)} kN·m",
                f"{_v('L', 'p')} = 1.76{_v('i', 'z')}√(<i>E</i>/{_v('F', 'y')}) = 1.76·{_f(iz, 1)}·√({_f(E, 0)}/{_f(Fy, 0)}) = {_f(float(Lp or 0) * 1000, 0)} mm; "
                f"{_v('L', 'r')} = {_f(float(Lr or 0) * 1000, 0)} mm (Denk. 9.8b, {_v('i', 'ts')} = {_f(eg.get('its_mm'), 2)} mm, {_v('h', 'o')} = {_f(eg.get('ho_mm'), 1)} mm)",
                f"{_v('L', 'b')} = {_f(float(Lbm or 0) * 1000, 0)} mm, {_v('C', 'b')} = {_f(eg.get('Cb'), 3)} → bölge: {_e(eg.get('bolge'))}"
                + (f"; {_v('F', 'cr')} = {_f(eg.get('Fcr_MPa'), 2)} MPa" if eg.get("Fcr_MPa") is not None and float(Lbm or 0) > float(Lr or 0) else ""),
                f"{_v('M', 'n')} = {_f(eg.get('Mn_kNm'), 2)} kN·m; {_v('M', 'c')} = {kat_ad(eg, 'b')}·{_v('M', 'n')} = {_f(eg.get('Mc_kNm'), 2)} kN·m"]
        satir.append(("Güçlü eksen eğilmesi", f"{_v('M', 'rx')} ≤ {_v('M', 'cx')}", adim,
                      f"{_b(oz.get('Mx_kNm'), 'kN·m')} ≤ {_b(eg.get('Mc_kNm'), 'kN·m')}", et.get("oran_Mx"), (et.get("oran_Mx") or 0) <= 1 + 1e-9,
                      "ÇYTHYE 2018 md. 9.2 (Denk. 9.3–9.8)", bel))
        satir.append(("Zayıf eksen eğilmesi", f"{_v('M', 'ry')} ≤ {_v('M', 'cy')}",
                      [f"{_v('M', 'ny')} = min({_v('F', 'y')}{_v('W', 'pl,z')}; 1.6{_v('F', 'y')}{_v('W', 'el,z')}) = {_f(eg.get('Mny_kNm'), 2)} kN·m; "
                       f"{_v('M', 'cy')} = {_f(eg.get('Mcy_kNm'), 2)} kN·m"],
                      f"{_b(oz.get('My_kNm'), 'kN·m')} ≤ {_b(eg.get('Mcy_kNm'), 'kN·m')}", et.get("oran_My"), (et.get("oran_My") or 0) <= 1 + 1e-9,
                      "ÇYTHYE 2018 md. 9.6.1, Denk. 9.39", bel))
        N = float(oz.get("N_kN") or 0)
        if N >= 0:
            adim = [f"<i>KL</i>/<i>i</i> = max({_f(bs.get('KLr_x'), 1)}; {_f(bs.get('KLr_y'), 1)}) = {_f(bs.get('KLr'), 1)}; 4.71√(<i>E</i>/{_v('F', 'y')}) = {_f(bs.get('sinir_471'), 1)}",
                    f"{_v('F', 'e')} = π<sup>2</sup><i>E</i>/(<i>KL</i>/<i>i</i>)<sup>2</sup> = π<sup>2</sup>·{_f(E, 0)}/{_f(bs.get('KLr'), 1)}<sup>2</sup> = {_f(bs.get('Fe_MPa'), 2)} MPa"
                    + (f" (burulmalı: {_f(bs.get('Fe_z_MPa'), 1)} MPa)" if bs.get("Fe_z_MPa") is not None else ""),
                    f"{_v('F', 'cr')} = " + ("0.658<sup>" + _v("F", "y") + "/" + _v("F", "e") + "</sup>" + _v("F", "y") if "inelastik" in str(bs.get("bolge"))
                                             else "0.877" + _v("F", "e")) + f" = {_f(bs.get('Fcr_MPa'), 2)} MPa ({_e(bs.get('bolge'))})",
                    f"{_v('P', 'n')} = {_v('F', 'cr')}{_v('A', 'g')} = {_f(bs.get('Fcr_MPa'), 2)}·{_f(bs.get('A_mm2'), 0)}·10<sup>−3</sup> = {_f(bs.get('Pn_kN'), 2)} kN; "
                    f"{_v('P', 'c')} = {kat_ad(bs, 'c')}·{_v('P', 'n')} = {_f(bs.get('Pc_kN'), 2)} kN"]
            satir.append(("Eksenel basınç", f"{_v('P', 'r')} ≤ {_v('P', 'c')}", adim, f"{_b(N, 'kN')} ≤ {_b(bs.get('Pc_kN'), 'kN')}",
                          et.get("oran_P"), (et.get("oran_P") or 0) <= 1 + 1e-9, "ÇYTHYE 2018 md. 8.2, Denk. 8.1–8.4", bel))
        else:
            adim = [f"akma: {_v('T', 'n')} = {_v('F', 'y')}{_v('A', 'g')} = {_f(ck.get('Tn_akma_kN'), 1)} kN; kırılma: {_v('T', 'n')} = {_v('F', 'u')}{_v('A', 'e')} = {_f(ck.get('Tn_kirilma_kN'), 1)} kN",
                    f"{_v('T', 'c')} = {_f(ck.get('Tc_kN'), 2)} kN ({_e(ck.get('belirleyici'))})"]
            satir.append(("Eksenel çekme", f"{_v('T', 'r')} ≤ {_v('T', 'c')}", adim, f"{_b(-N, 'kN')} ≤ {_b(ck.get('Tc_kN'), 'kN')}",
                          et.get("oran_P"), (et.get("oran_P") or 0) <= 1 + 1e-9, "ÇYTHYE 2018 md. 7.2", bel))
        satir.append(("Kesme (güçlü eksen)", f"{_v('V', 'r')} ≤ {_v('V', 'c')}",
                      [f"<i>h</i>/{_v('t', 'w')} = {_f(ks.get('h_tw'), 2)} ≤ 2.24√(<i>E</i>/{_v('F', 'y')}) = {_f(ks.get('sinir_224'), 2)} → {_v('C', 'v1')} = {_f(ks.get('Cv1'), 3)} ({_e(ks.get('dal'))})",
                       f"{_v('V', 'n')} = 0.6{_v('F', 'y')}{_v('A', 'w')}{_v('C', 'v1')} = 0.6·{_f(Fy, 0)}·{_f(ks.get('Aw_mm2'), 0)}·{_f(ks.get('Cv1'), 3)}·10<sup>−3</sup> = {_f(ks.get('Vn_kN'), 2)} kN; "
                       f"{_v('V', 'c')} = {_f(ks.get('Vc_kN'), 2)} kN"],
                      f"{_b(oz.get('V_kN'), 'kN')} ≤ {_b(ks.get('Vc_kN'), 'kN')}", kmb.get("dc_kesme"), (kmb.get("dc_kesme") or 0) <= 1 + 1e-9,
                      "ÇYTHYE 2018 md. 10.2.1, Denk. 10.1–10.3", bel))
        oP, ox, oy = (float(et.get(a) or 0) for a in ("oran_P", "oran_Mx", "oran_My"))
        if et.get("dal") == "11.1a":
            form = f"{_v('P', 'r')}/{_v('P', 'c')} + 8/9({_v('M', 'rx')}/{_v('M', 'cx')} + {_v('M', 'ry')}/{_v('M', 'cy')}) ≤ 1 ({_v('P', 'r')}/{_v('P', 'c')} ≥ 0.2)"
            yer = f"{_f(oP, 4)} + 8/9·({_f(ox, 4)} + {_f(oy, 4)}) = {_f(et.get('dc'), 4)}"
        else:
            form = f"{_v('P', 'r')}/(2{_v('P', 'c')}) + {_v('M', 'rx')}/{_v('M', 'cx')} + {_v('M', 'ry')}/{_v('M', 'cy')} ≤ 1 ({_v('P', 'r')}/{_v('P', 'c')} < 0.2)"
            yer = f"{_f(oP, 4)}/2 + {_f(ox, 4)} + {_f(oy, 4)} = {_f(et.get('dc'), 4)}"
        satir.append((f"Bileşik etki (Denk. {_e(et.get('dal') or '11.1')})", form, [yer], f"{_f(et.get('dc'), 4)} ≤ 1", et.get("dc"),
                      (et.get("dc") or 0) <= 1 + 1e-9, et.get("kaynak") or "ÇYTHYE 2018 md. 11.1.1", bel))
        for k in _liste(e.get("kontroller")):
            if isinstance(k, dict) and k.get("kosul"):
                satir.append((_formul(k.get("ad")), "<i>KL</i>/<i>i</i> ≤ 200 (basınç), <i>L</i>/<i>i</i> ≤ 300 (çekme)" if "Narinlik" in str(k.get("ad")) else "",
                              [], f"{_f(k.get('talep'), 2)} ≤ {_f(k.get('kapasite'), 0)}", k.get("dc"), k.get("saglandi"), k.get("kaynak"), None))
        ek = ""
        if bolge in ("pozitif", "negatif"):
            ek = (f"<p class=kaynak>Döşemeli kiriş: pozitif moment bölgesinde {_v('L', 'b')} = 0 (D/C = {_f(oz.get('dc_pozitif'), 3)}), negatif moment "
                  f"bölgesinde {_v('L', 'b')} = {_f(oz.get('Lb_neg_m'), 2)} m, {_v('C', 'b')} = {_f(oz.get('Cb_neg'), 3)} (D/C = {_f(oz.get('dc_negatif'), 3)}); "
                  f"belirleyen bölge: {_e(bolge)}. Aşağıdaki satırlar belirleyen bölgenin kuvvetleriyle yeniden hesaplanmıştır.</p>")
        return (f"<p>{_e(profil)}, {_e(m.get('sinif'))}: {_v('F', 'y')} = {_f(Fy, 0)} MPa, <i>E</i> = {_f(E, 0)} MPa; <i>L</i> = {_b(oz.get('L_m'), 'm')}, "
                f"<i>K</i> = {K_metin}; yöntem {_e(y)}; belirleyen kuvvetler: <i>N</i> = {_b(N, 'kN')} (basınç +), {_v('M', 'x')} = "
                f"{_b(oz.get('Mx_kNm'), 'kN·m')}, {_v('M', 'y')} = {_b(oz.get('My_kNm'), 'kN·m')}, <i>V</i> = {_b(oz.get('V_kN'), 'kN')}</p>"
                + ek + self._kontrol_tablosu(satir))

    def b12(self):
        tas = _sozluk(self.v.get("tasarim"))
        el = self._tasarim_elemanlari("celik")
        if not tas:
            return _not("Kesit tahkikleri bu çözümde yok (tasarım modülü yüklenmedi). " + UYGULANMADI)
        if not el:
            return _not("Modelde çelik eleman yok. " + UYGULANMADI)
        h = _p(f"Yöntem: <b>{_e(_g(tas, 'yontem', 'celik') or 'ÇYTHYE 2018')}</b>; tahkik birleşim sayısı {_f(tas.get('kombinasyon_sayisi'), 0)}. "
               "YDKT: φ<sub>b</sub> = φ<sub>c</sub> = 0.90, φ<sub>v</sub> = 1.00 (haddelenmiş I, 10.2.1(a)); GKT: Ω<sub>b</sub> = Ω<sub>c</sub> = 1.67, Ω<sub>v</sub> = 1.50.")
        h += _h3("12.1 Varsayımlar") + _ul([_e(x) for x in self._varsayimlar(tas, "celik")])
        rows = []
        for e in el:
            o = _sozluk(e.get("ozet"))
            rows.append([_e(e.get("adres")), _e(e.get("kesit")), _e(o.get("sinif") or ""), _f(o.get("L_m"), 2), _f(o.get("Lb_m"), 2),
                         _f(o.get("N_kN"), 2), _f(o.get("Pc_kN"), 1), _f(o.get("Mx_kNm"), 2), _f(o.get("Mc_kNm"), 1), _f(o.get("V_kN"), 2),
                         _f(o.get("Vc_kN"), 1), _e(_g(e, "belirleyen", "kontrol") or ""), _dc_hucre(e.get("dc"))])
        h += _h3("12.2 Özet")
        h += _tablo(["Eleman", "Kesit", "Sınıf", "<i>L</i> [m]", _v("L", "b") + " [m]", _v("P", "r") + " [kN]", _v("P", "c") + " [kN]",
                     _v("M", "rx") + " [kN·m]", _v("M", "cx") + " [kN·m]", _v("V", "r") + " [kN]", _v("V", "c") + " [kN]", "Belirleyen", "D/C"],
                    rows, sinif="kucuk", sayisal=range(3, 13))
        cub = [c for c in _liste(self.ham.get("cubuklar")) if isinstance(c, dict) and c.get("tur") not in ("kolon", "kiris", None)]
        if cub:
            h += _not(f"Modelde {len(cub)} çapraz/makas/aşık/kren çubuğu var; tahkikleri çözüm verisinde yer aldığı ölçüde yukarıdaki tablolardadır.")
        sec = self._detay_secimi(el)
        h += _h3("12.3 Ayrıntılı eleman kontrolleri"
                 + {"kritik": " (her türde D/C en büyük 5 eleman + D/C &gt; 1 olanlar)", "hepsi": " (bütün elemanlar)", "yok": ""}[self.detay])
        if not sec:
            h += _not("Ayrıntılı hesap seçilmedi (eleman_detay = \"yok\").")
        for e in sec:
            govde = self._celik_detay(e) or self._kontrol_listesi([e])
            h += f'<div class="eleman">{self._eleman_basligi(e)}{govde}</div>'
        h += _h3("12.4 Bütün çelik elemanların kontrol satırları") + self._kontrol_listesi(el)
        return h

    # ================================================================ 13. Temel
    def _genel_kayit(self, d, derinlik=0):
        """Bilinmeyen (gelecekteki) temel verisi için genel gösterim: düz alanlar anahtar–değer, listeler tablo."""
        duz = [(k, x) for k, x in d.items() if not isinstance(x, (dict, list))]
        h = _anahtar_deger([(_e(k), _e(x) if not _sayi_mi(x) else _s(x, 5)) for k, x in duz]) if duz else ""
        for k, x in d.items():
            if isinstance(x, list) and x and all(isinstance(r, dict) for r in x):
                anah = []
                for r in x[:200]:
                    for a, b in r.items():
                        if not isinstance(b, (dict, list)) and a not in anah:
                            anah.append(a)
                anah = anah[:12]
                rows = [[_s(r.get(a), 5) if _sayi_mi(r.get(a)) else _e(r.get(a, "")) for a in anah] for r in x[:200]]
                h += _h4_tablo(_e(k) + (f" (ilk 200 / {len(x)})" if len(x) > 200 else ""), [_e(a) for a in anah], rows, sinif="kucuk")
            elif isinstance(x, list) and x:
                h += f"<h4>{_e(k)}</h4>" + _ul([_e(r) for r in x[:50]])
            elif isinstance(x, dict) and derinlik < 1:
                h += f"<h4>{_e(k)}</h4>" + self._genel_kayit(x, derinlik + 1)
        return h

    def _temel_geometri(self, tm):
        """Mütemadi / radye temel boyutları (bina.temeller.surekli / .radye, §13)."""
        tip = tm.get("tip")
        if tip == "surekli":
            g = _sozluk(tm.get("surekli"))
            akslar = g.get("akslar")
            sat = [("Temel kirişi doğrultusu", _e({"x": "X aksları boyunca", "y": "Y aksları boyunca", "xy": "iki doğrultuda (ızgara)"}
                                                    .get(g.get("yon"), g.get("yon") or "–"))),
                   ("Aks çizgileri", _e("tümü" if akslar in (None, "tum") else ", ".join(map(str, _liste(akslar))))),
                   ("Tabla genişliği <i>B</i>", _b(g.get("B"), "m")), ("Tabla kalınlığı " + _v("h", "tabla"), _b(g.get("h_tabla"), "m")),
                   ("Gövde " + _v("b", "gövde") + " × " + _v("h", "gövde"), f"{_b(g.get('b_govde'), 'm')} × {_b(g.get('h_govde'), 'm')}"),
                   ("Uç taşma (konsol)", _b(g.get("tasma"), "m")), ("Eleman bölme aralığı", _b(g.get("ag"), "m"))]
            return (_h3("Mütemadi (sürekli) temel boyutları") + _anahtar_deger(sat)
                    + _p("Ters T kesitli temel kirişleri temel seviyesinde çubuk eleman olarak modellenir; zemin ayrık Winkler yaylarıdır: "
                         + _v("k", "z") + " = " + _v("k", "0") + "·<i>B</i>·<i>l</i> (<i>l</i> düğüm etki boyu)."))
        if tip == "radye":
            g = _sozluk(tm.get("radye"))
            kir = _sozluk(g.get("kiris"))
            sat = [("Plak kalınlığı <i>h</i>", _b(g.get("h"), "m")), ("Aks dışına taşma", _b(g.get("tasma"), "m")),
                   ("Izgara aralığı <i>a</i>", _b(g.get("ag"), "m")),
                   ("Temel kirişleri", f"{_b(kir.get('b'), 'm')} × {_b(kir.get('h'), 'm')}" if kir else "yok (kirişsiz radye)")]
            return (_h3("Radye temel boyutları") + _anahtar_deger(sat)
                    + _p("Plak iki doğrultulu ızgara (şerit çubuklar) ile modellenir: şerit genişliği <i>a</i> (kenarda <i>a</i>/2), "
                         "<i>I</i> = <i>a h</i><sup>3</sup>/12, <i>J</i> ≈ <i>a h</i><sup>3</sup>/6; zemin yayı " + _v("k", "z") + " = "
                         + _v("k", "0") + "·(etki alanı)."))
        return ""

    def _temel_analizi(self, temel):
        """veri.temel (§13: tekil/mütemadi/radye temel analizi) → özet, taban basınçları, elemanlar, kontroller, uyarılar."""
        h = _h3("13.1 Temel analizi sonuçları")
        if temel.get("tip"):
            h += _p("Çözülen temel tipi: <b>" + _e({"tekil": "tekil (münferit)", "surekli": "mütemadi (sürekli)", "radye": "radye"}
                                                    .get(temel.get("tip"), temel.get("tip"))) + "</b>.")
        ozet = [("p_maks", "En büyük taban basıncı " + _v("p", "maks"), "kN/m²"), ("p_min", "En küçük taban basıncı " + _v("p", "min"), "kN/m²"),
                ("q_em", "Zemin emniyet gerilmesi " + _v("q", "em"), "kN/m²"),
                ("DC_zemin", "Zemin D/C = " + _v("p", "maks") + "/" + _v("q", "em") + " (servis G+Q)", ""),
                ("oturma_maks_mm", "En büyük oturma", "mm"), ("farkli_oturma", "Farklı oturma (komşu fark / açıklık)", "")]
        sat = []
        for a, ad, br in ozet:
            if temel.get(a) is not None:
                if a == "DC_zemin":
                    deger = (f"{_f(temel.get('p_maks'), 2)}/{_f(temel.get('q_em'), 2)} = " if _sayi_mi(temel.get("p_maks"))
                             and _sayi_mi(temel.get("q_em")) else "") + _dc_hucre(temel[a])
                else:
                    deger = _b(temel[a], br, 4)
                sat.append((ad, deger))
        if sat:
            h += _anahtar_deger(sat)
        dug = [d for d in _liste(temel.get("dugumler")) if isinstance(d, dict)]
        if dug:
            sinir = 300
            rows = [[_e(d.get("no")), _f(d.get("X"), 3), _f(d.get("Y"), 3), _f(d.get("w_mm"), 3), _f(d.get("p_kNm2"), 2)] for d in dug[:sinir]]
            h += _h4_tablo("Taban basıncı ve oturma (düğüm başına, servis G+Q)"
                           + (f" — ilk {sinir} / {len(dug)} düğüm" if len(dug) > sinir else ""),
                           ["Düğüm", "<i>X</i> [m]", "<i>Y</i> [m]", "<i>w</i> [mm]", "<i>p</i> [kN/m²]"], rows, sinif="kucuk")
        el = [e for e in _liste(temel.get("elemanlar")) if isinstance(e, dict)]
        if el:
            rows = []
            for e in el[:300]:
                enb = _sozluk(e.get("enb"))
                kay = e.get("kaynak")
                rows.append([_e(e.get("no")), _e(_ELEMAN_TURU.get(e.get("tur"), e.get("tur") or "")),
                             _e(json.dumps(kay, ensure_ascii=False) if isinstance(kay, (dict, list)) else (kay or "")),
                             _f(enb.get("N"), 2), _f(enb.get("V"), 2), _f(enb.get("M"), 2), _f(enb.get("T"), 2)])
            h += _h4_tablo("Temel elemanları — en büyük mutlak iç kuvvetler", ["Eleman", "Tür", "Kaynak", "|N| [kN]", "|V| [kN]",
                           "|M| [kN·m]", "|T| [kN·m]"], rows, sinif="kucuk", sayisal=(3, 4, 5, 6))
        tas = [t for t in _liste(temel.get("tasarim")) if isinstance(t, dict)]
        if tas:
            h += _h3("13.2 Temel tasarım kontrolleri (TS 500, TBDY 2018 Bölüm 16)")
            satir = []
            for t in tas:
                eleman = _e(t.get("ad") or t.get("adres") or t.get("no") or "")
                for k in _liste(t.get("kontroller")) or [t]:
                    if not (isinstance(k, dict) and ("talep" in k or "dc" in k)):
                        continue
                    adim = [_e(a) for a in _liste(k.get("adimlar"))] or ([_e(k["yerine"])] if k.get("yerine") else [])
                    birim = _e(k.get("birim") or "")
                    satir.append((f"{eleman} — {_formul(k.get('ad') or '')}", _formul(k.get("formul") or ""), adim,
                                  f"{_s(k.get('talep'), 4)} ≤ {_s(k.get('kapasite'), 4)} {birim}", k.get("dc"), k.get("saglandi"),
                                  k.get("kaynak"), k.get("kombinasyon")))
            h += self._kontrol_tablosu(satir) if satir else _not("Kontrol satırı yok.")
        bilinen = {o[0] for o in ozet} | {"tasarim", "dugumler", "elemanlar", "uyarilar", "tip"}
        kalan = {a: b for a, b in temel.items() if a not in bilinen}
        if kalan:
            h += _h3("13.3 Diğer temel verileri") + self._genel_kayit(kalan)
        if _liste(temel.get("uyarilar")):
            h += _h3("Temel uyarıları") + _ul([_e(u) for u in temel["uyarilar"]])
        return h

    def b13(self):
        v, B = self.v, self.B
        tm = self.temeller
        zemin = _sozluk(tm.get("zemin"))
        h = _anahtar_deger([
            ("Temel tipi", _e({"tekil": "tekil (münferit)", "surekli": "mütemadi (sürekli)", "radye": "radye"}.get(tm.get("tip"), tm.get("tip") or "–"))),
            ("Mesnet modeli (üst yapı analizi)", "temel ağı (Winkler zemin yayları; sabit mesnet yok)" if tm.get("tip") in ("surekli", "radye")
             else _e(tm.get("mesnet") or "–")),
            ("Zemin emniyet gerilmesi " + _v("q", "em"), _b(zemin.get("q_em"), "kN/m²")),
            ("Yatak katsayısı " + _v("k", "0"), _b(zemin.get("k0"), "kN/m³", 0)),
            ("Zemin birim hacim ağırlığı", _b(zemin.get("gamma"), "kN/m³") if zemin.get("gamma") is not None else "–"),
        ])
        temel = v.get("temel")
        cozulen = temel.get("tip") if isinstance(temel, dict) else None
        if tm.get("tip") in ("surekli", "radye") and cozulen not in ("surekli", "radye"):
            # model mütemadi/radye, çözümde o temelin sonucu yok (temel tipi çözümden sonra değişti ya da eski çözüm): iki motorda da
            h += _not(ESKI_TEMEL_NOTU)
        else:
            h += self._temel_geometri(tm)
        if cozulen in ("surekli", "radye"):
            acik = [m for m in _liste(_g(v, "akis", "mesnetler")) if isinstance(m, dict)]
            return h + self._temel_analizi(temel) + (self._acik_mesnetler(acik) if acik else "")
        tum = [t for t in _liste(_g(v, "akis", "temeller")) if isinstance(t, dict)]
        gamma = float(_g(getattr(yv, "TS498_BIRIM_AGIRLIK", {}) if yv else {}, "betonarme", "deger", vars=25.0))
        h_v = _g(self.temeller, "varsayilan", "h")
        tem = []
        for t in tum:        # temel kaydı: B/L'li satırlar (açık mesnetler ayrı); N_temel yoksa γ·B·L·h
            if t.get("B") is None or t.get("L") is None:
                continue
            if t.get("N_temel") is None:
                hh = t.get("h") if t.get("h") is not None else h_v
                if _sayi_mi(hh):
                    t = dict(t, N_temel=gamma * float(t["B"]) * float(t["L"]) * float(hh), h=hh)
            tem.append(t)
        acik = [m for m in _liste(_g(v, "akis", "mesnetler")) if isinstance(m, dict)] or \
               [t for t in tum if t.get("B") is None or t.get("L") is None]
        acik_html = self._acik_mesnetler(acik) if acik else ""
        if not tem:
            return h + acik_html + _not("Temel sonuçları yok. " + UYGULANMADI)
        h += _h3("13.1 Tekil temeller — servis yükleri (G + Q) altında zemin gerilmeleri")
        h += _p(f"<i>N</i> = {_v('N', 'G')} + {_v('N', 'Q')} + {_v('N', 'temel')} ({_v('N', 'temel')} = <i>γ</i>·<i>B</i>·<i>L</i>·<i>h</i>, <i>γ</i> = 25 kN/m³); "
                f"σ<sub>maks,min</sub> = <i>N</i>/(<i>BL</i>) ± 6{_v('M', 'X')}/(<i>BL</i><sup>2</sup>) ± 6{_v('M', 'Y')}/(<i>LB</i><sup>2</sup>); "
                f"{_v('e', 'X')} = |{_v('M', 'Y')}|/<i>N</i>, {_v('e', 'Y')} = |{_v('M', 'X')}|/<i>N</i>; çekirdek koşulu <i>e</i> ≤ <i>B</i>/6; "
                f"D/C = σ<sub>maks</sub>/{_v('q', 'em')}.")
        rows = []
        for t in tem:
            rows.append([_e(_temel_aks(t)), f"{_f(t.get('B'))} × {_f(t.get('L'))} × {_f(t.get('h'))}", _f(t.get("N_G"), 1),
                         _f(t.get("N_Q"), 1), _f(t.get("N_temel"), 1), _f(t.get("N_servis"), 1), _f(t.get("MX"), 2), _f(t.get("MY"), 2),
                         _f(float(t.get("e_X") or 0) * 1000, 1), _f(float(t.get("e_Y") or 0) * 1000, 1), _f(t.get("sigma_max"), 1), _f(t.get("sigma_min"), 1),
                         _isaret(t.get("cekirdek_icinde")), _dc_hucre(t.get("DC"))])
        h += _tablo(["Aks", "<i>B</i>×<i>L</i>×<i>h</i> [m]", _v("N", "G") + " [kN]", _v("N", "Q") + " [kN]", _v("N", "temel") + " [kN]",
                     "<i>N</i> [kN]", _v("M", "X") + " [kN·m]", _v("M", "Y") + " [kN·m]", _v("e", "X") + " [mm]", _v("e", "Y") + " [mm]",
                     "σ<sub>maks</sub> [kN/m²]", "σ<sub>min</sub> [kN/m²]", "Çekirdek", "D/C"], tem and rows, sinif="kucuk", sayisal=range(2, 14))
        t = max(tem, key=lambda x: float(x.get("DC") or 0))
        B_, L_, N_, MX, MY = (float(t.get(a) or 0) for a in ("B", "L", "N_servis", "MX", "MY"))
        if B_ > 0 and L_ > 0:
            s1, s2, s3 = N_ / (B_ * L_), 6 * abs(MX) / (B_ * L_ ** 2), 6 * abs(MY) / (L_ * B_ ** 2)
            h += _h3("13.2 Belirleyici temel: aks " + _e(_temel_aks(t)))
            h += self._kontrol_tablosu([
                ("Zemin gerilmesi", f"σ<sub>maks</sub> = <i>N</i>/(<i>BL</i>) + 6|{_v('M', 'X')}|/(<i>BL</i><sup>2</sup>) + 6|{_v('M', 'Y')}|/(<i>LB</i><sup>2</sup>) ≤ {_v('q', 'em')}",
                 [f"<i>N</i> = {_f(t.get('N_G'), 2)} + {_f(t.get('N_Q'), 2)} + {_f(t.get('N_temel'), 2)} = {_f(N_, 2)} kN",
                  f"σ<sub>maks</sub> = {_f(N_, 2)}/({_f(B_)}·{_f(L_)}) + 6·{_f(abs(MX), 3)}/({_f(B_)}·{_f(L_)}<sup>2</sup>) + 6·{_f(abs(MY), 3)}/({_f(L_)}·{_f(B_)}<sup>2</sup>) "
                  f"= {_f(s1, 2)} + {_f(s2, 2)} + {_f(s3, 2)} = {_f(t.get('sigma_max'), 2)} kN/m²"],
                 f"{_b(t.get('sigma_max'), 'kN/m²')} ≤ {_b(t.get('q_em'), 'kN/m²')}", t.get("DC"), float(t.get("DC") or 0) <= 1 + 1e-9,
                 "TS 500 / zemin emniyet gerilmesi (servis yükleri)", "G+Q"),
                ("Çekirdek (dışmerkezlik)", f"{_v('e', 'X')}/<i>B</i> + {_v('e', 'Y')}/<i>L</i> ≤ 1/6",
                 [f"{_f(float(t.get('e_X') or 0) * 1000, 1)}/{_f(B_ * 1000, 0)} + {_f(float(t.get('e_Y') or 0) * 1000, 1)}/{_f(L_ * 1000, 0)} = "
                  f"{_f(float(t.get('e_X') or 0) / B_ + float(t.get('e_Y') or 0) / L_, 4)}"],
                 "taban basıncı her yerde basınç" if t.get("cekirdek_icinde") else "temel tabanında çekme (kalkma) var",
                 (float(t.get("e_X") or 0) / B_ + float(t.get("e_Y") or 0) / L_) * 6, bool(t.get("cekirdek_icinde")), None, "G+Q")])
        h += acik_html
        h += _h3("13.3 Zımbalama ve temel donatısı")
        if self.genel:
            h += _not("Tekil temel zımbalama (TS 500 md. 8.3) ve eğilme donatısı hesabı bu çözümde yok; genel modelde kolon tabanları tekil "
                      "temel mesnetidir. " + UYGULANMADI)
        else:
            h += _not("Tekil temel zımbalama (TS 500 md. 8.3) ve eğilme donatısı hesabı bu çözümde yok; mütemadi ve radye temel analizi "
                      "(Winkler zeminli temel kirişi / ızgara) bu modelde seçilmedi. " + UYGULANMADI)
        return h

    def _acik_mesnetler(self, acik):
        """Açık (temelsiz) mesnetlerin servis tepkileri (akis.mesnetler; eski çözümlerde B'siz akis.temeller satırları)."""
        rows = []
        # rijit diyaframlı seviyedeki mesnet: ux/uy/rz ceza yayıyla (yaylar[].tur 'diyafram-mesnet', C14)
        diyafram = {y.get("dugum") for y in _liste(_g(self.v, "durumlar", "G", "yaylar"))
                    if isinstance(y, dict) and y.get("tur") == "diyafram-mesnet"}
        ek = any(m.get("yay") or m.get("tip") == "yay" or m.get("dugum") in diyafram for m in acik)
        for m in acik:
            d = m.get("dugum")
            adres = m.get("adres") or _g(self.dug, d, "adres", vars="") or (
                "".join(map(str, _liste(m.get("aks")))) if m.get("aks") else "")
            tip = m.get("tip") or ""
            if tip == "yay" or m.get("yay"):
                tip, aciklama = "yaylı mesnet", _yay_metni(m.get("yay"))
            elif d in diyafram:
                tip, aciklama = "mesnet (diyafram bağıyla)", "ux/uy/rz ceza rijitliğiyle"
            else:
                aciklama = ""
            rows.append([_e(d), _e(adres), _e(tip)] + ([_e(aciklama) or "–"] if ek else [])
                        + [_f(m.get("N_G"), 2), _f(m.get("N_Q"), 2), _f(m.get("MX"), 2), _f(m.get("MY"), 2)])
        return _h4_tablo("Açık mesnet tepkileri (temel kaydı yok)", ["Düğüm", "Adres", "Tip"] + (["Yay rijitliği / bağ"] if ek else [])
                         + [_v("N", "G") + " [kN]", _v("N", "Q") + " [kN]", _v("M", "X") + " [kN·m]", _v("M", "Y") + " [kN·m]"], rows,
                         sinif="kucuk",
                         dip="'mesnetler' listesiyle verilen (temel boyutu olmayan) mesnetler: zemin gerilmesi hesaplanmaz; "
                             "tepkiler bağlandıkları yapıya ya da temele ayrıca aktarılmalıdır."
                             + (" Yaylı mesnette tepki yay kuvvetini de içerir (k_x, k_y, k_z kN/m; k_rx, k_ry, k_rz kN·m/rad; bina "
                                "eksenleri)." if any(r[2] == "yaylı mesnet" for r in rows) else "")
                             + (" Diyafram bağı: rijit diyaframlı seviyedeki mesnedin yatay (ux, uy) ve rz tutulması ceza yayıdır; bu "
                                "nokta bütün katın yatay hareketini tutar." if any(r[2] == "mesnet (diyafram bağıyla)" for r in rows) else ""))

    # ================================================================ 14. Sonuç
    def b14(self):
        v, oz, tas = self.v, _sozluk(self.v.get("ozet")), _sozluk(self.v.get("tasarim"))
        el = [e for e in _liste(tas.get("elemanlar")) if isinstance(e, dict)]
        asan = sorted((e for e in el if float(e.get("dc") or 0) > 1.0 + 1e-9), key=lambda e: -float(e.get("dc") or 0))
        h = ""
        dag = _sozluk(tas.get("dc_dagilimi"))
        if dag:
            h += _h3("14.1 D/C dağılımı") + _tablo(["Aralık", "Eleman sayısı"], [[_e(a), _f(b, 0)] for a, b in dag.items()])
        h += _h3("14.2 Yetersiz elemanlar (D/C &gt; 1)")
        if asan:
            rows = []
            for e in asan:
                o = _sozluk(e.get("ozet"))
                oneri = e.get("oneri")
                if not oneri:
                    if e.get("sistem") == "celik":
                        oneri = "Daha büyük profil seçin (aynı aileden bir üst profil) ya da yanal tutulmasız boyu (L_b) kısaltın."
                    elif e.get("tur") == "kolon":
                        oneri = (f"Boyuna donatıyı ρ = {_f(o.get('rho_gerekli'), 4)} değerine çıkarın." if o.get("rho_gerekli") is not None
                                 else "Kolon kesitini büyütün (ρ ≤ 0.04 ile sağlanamıyor).")
                    else:
                        oneri = ("Donatıyı artırın." if e.get("durum") == "donatı artır" else "Kiriş kesitini (h ya da b) büyütün.")
                rows.append([_e(e.get("adres")), _e(e.get("kesit")), _e(_g(e, "belirleyen", "kontrol") or ""), _e(_g(e, "belirleyen", "kombinasyon") or ""),
                             _dc_hucre(e.get("dc")), _e(oneri if isinstance(oneri, str) else json.dumps(oneri, ensure_ascii=False))])
            h += _tablo(["Eleman", "Kesit", "Belirleyen kontrol", "Birleşim", "D/C", "Öneri"], rows, sinif="kucuk", sayisal=(4,))
        else:
            h += _p(_isaret(True) + " D/C &gt; 1 olan eleman yok." if el else "Kesit tahkiki yapılmadı.")
        uy = []
        for kaynak, liste in (("Genel", _liste(oz.get("uyarilar"))), ("Tasarım", _liste(tas.get("uyarilar"))),
                              ("Deprem", _liste(_g(v, "deprem", "uyarilar"))), ("Temel", _liste(_g(v, "temel", "uyarilar")))):
            uy += [f"<b>{_e(kaynak)}:</b> {_e(u)}" for u in liste]
        h += _h3("14.3 Uyarılar") + (_ul(uy) if uy else _p("Uyarı yok."))
        # genel değerlendirme
        cumle = []
        if el:
            en = max(el, key=lambda e: float(e.get("dc") or 0))
            cumle.append(f"Modelde {len(el)} " + ("çubuk" if self.genel else "eleman (kiriş ve kolon)")
                         + " kesit tahkikinden geçirilmiştir; en büyük talep/kapasite oranı "
                         f"<b>{_f(en.get('dc'), 3)}</b> ({_e(en.get('adres'))}, {_e(_g(en, 'belirleyen', 'kontrol') or '')}, "
                         f"{_e(_g(en, 'belirleyen', 'kombinasyon') or '')}).")
            cumle.append("Bütün elemanlar seçilen kesit ve donatılarla yeterlidir." if not asan else
                         f"{len(asan)} eleman yetersizdir; yukarıdaki öneriler uygulanıp model yeniden çözülmelidir.")
        dt = oz.get("en_buyuk_temel_DC")
        if _sayi_mi(dt):
            cumle.append(f"Servis yükleri altında en büyük zemin gerilmesi oranı σ<sub>maks</sub>/{_v('q', 'em')} = <b>{_f(dt, 3)}</b> "
                         + ("(uygun)." if float(dt) <= 1 else "(<span class=no>aşılıyor</span>: temel boyutları büyütülmelidir)."))
        dep = _sozluk(v.get("deprem"))
        if dep:
            kat = [x for x in _liste(dep.get("katlar")) if isinstance(x, dict)]
            if kat:
                en_oran = max(max(float(x.get("oran_x") or 0), float(x.get("oran_y") or 0)) for x in kat)
                uygun = all(x.get("uygun", True) for x in kat)
                cumle.append(f"Göreli kat ötelemesi en büyük λδ/h = {_f(en_oran, 5)} (sınır {_f(dep.get('sinir_oran'), 4)}): "
                             + ("sağlanır." if uygun else "<span class=no>sağlanmaz</span>."))
            cumle.append(f"Eşdeğer deprem yükü yöntemi bu bina için {'uygulanabilir' if dep.get('uygulanabilir') else 'uygulanamaz'} "
                         f"(DTS {_e(dep.get('DTS'))}, BYS {_e(dep.get('BYS'))}).")
        cumle.append("Bu rapor eğitim amaçlı ön boyutlandırmadır; TBDY 2018 kapasite tasarımı (güçlü kolon–zayıf kiriş, kapasite kesmesi, "
                     "birleşim bölgeleri), ikinci mertebe etkileri, birleşim/bağlantı hesapları, döşeme ve temel donatı detayları resmî projede "
                     "ayrıca yapılmalıdır.")
        h += _h3("14.4 Genel değerlendirme") + "".join(_p(c) for c in cumle)
        return h

    # ================================================================ Ekler
    def metraj(self):
        h = _p("Seçilen metraj tabloları (yaklaşık keşif; birim fiyat içermez):")
        for t, f in self.metraj_tablolari():
            h += tablo_html(t, satirlar=f)
        return h

    def ekA(self):
        dg = [d for d in _liste(_g(self.v, "ag", "dugumler")) if isinstance(d, dict)]
        if not dg:
            return _not(UYGULANMADI)
        mes = {m.get("dugum"): m.get("tip") for m in _liste(_g(self.v, "ag", "mesnetler")) if isinstance(m, dict)}
        rows = [[_e(d.get("no")), _e(d.get("adres", "")), _f(d.get("X"), 3), _f(d.get("Y"), 3), _f(d.get("Z"), 3), _e(d.get("kat", "")),
                 _e(mes.get(d.get("no"), "")) + (" (ana düğüm)" if d.get("efendi") else "")] for d in dg]
        return _p("Bina koordinat sistemi: <i>X</i> sağa (harfli akslar), <i>Y</i> plan derinliği (sayılı akslar), <i>Z</i> yukarı (kot).") + \
            _tablo(["Düğüm", "Adres", "<i>X</i> [m]", "<i>Y</i> [m]", "<i>Z</i> [m]", "Kat", "Mesnet"], rows, sinif="kucuk", sayisal=(2, 3, 4))

    def ekB(self):
        el = [e for e in _liste(_g(self.v, "ag", "elemanlar")) if isinstance(e, dict)]
        if not el:
            return _not(UYGULANMADI)
        kes = _sozluk(_g(self.v, "kutuphane_ozeti", "kesitler"))
        cub = {c.get("no"): c for c in _liste(self.ham.get("cubuklar")) if isinstance(c, dict)}
        rows = []
        for e in el:
            d = _liste(e.get("dugumler"))
            ser = e.get("serbest") or _g(cub.get(_g(e, "kaynak", "no")), "serbest") if isinstance(e.get("kaynak"), dict) else e.get("serbest")
            if self.genel and ser is None and e.get("cubuk") in cub:          # genel model: FE parçası → çubuk uç serbestlikleri
                ser = cub[e.get("cubuk")].get("serbest") or None
            ser_m = ("i: " + ",".join(_liste(_g(ser, "i"))) + " / j: " + ",".join(_liste(_g(ser, "j")))) if isinstance(ser, dict) else "rijit"
            rows.append([_e(e.get("no")), _e(_ELEMAN_TURU.get(e.get("tur"), e.get("tur") or "")), _e(d[0] if d else ""),
                         _e(d[1] if len(d) > 1 else ""), _e(e.get("adres", "")),
                         _e(e.get("kesit", "")), _e(_g(kes, e.get("kesit"), "malzeme", vars="")), _f(e.get("L"), 3),
                         _f(e.get("rijitlik_carpani"), 2) if e.get("rijitlik_carpani") is not None else "1", _e(ser_m)])
        return _tablo(["Eleman", "Tür", "<i>i</i>", "<i>j</i>", "Adres", "Kesit", "Malzeme", "<i>L</i> [m]", "Rijitlik çarpanı", "Uç serbestliği"],
                      rows, sinif="kucuk", sayisal=(2, 3, 7, 8))

    def ekC(self):
        h = ""
        if self.tablo_notu:
            h += _ul([_e(n) for n in self.tablo_notu])
        diger = [(t, f) for t, f in self.tablolar if (t, f) not in self.metraj_tablolari()] if self.dahil("metraj") else self.tablolar
        if not diger and not self.tablo_notu:
            return _not("Tablo seçilmedi.")
        for i, (t, f) in enumerate(diger, 1):
            h += tablo_html(t, satirlar=f, kimlik=f"ekC-{i}")
        if self.metraj_tablolari() and self.dahil("metraj"):
            h += _not("Metraj tabloları 'Metraj özeti' bölümündedir.")
        return h


def _h4_tablo(baslik, basliklar, satirlar, *, sinif="", sayisal=None, alt=None, dip=None) -> str:
    return f"<h4>{baslik}</h4>" + _tablo(basliklar, satirlar, sinif=sinif, sayisal=sayisal, alt=alt) + (_not(dip) if dip else "")


# ============================================================================
# Genel giriş
# ============================================================================
def statik_rapor(bina, veri, *, secenek=None) -> str:
    """Bina modeli (sözlük ya da JSON metni) ve ``yapi.bina_coz(...).veri`` → tam HTML statik hesap raporu (metin).

    Bölümler (§14.1, sıra sabit): 1 kapak/künye, 2 yönetmelikler, 3 genel bilgiler, 4 malzemeler, 5 kesitler, 6 yükler,
    7 deprem, 8 analiz yöntemi, 9 yük birleşimleri, 10 analiz sonuçları, 11 betonarme, 12 çelik, 13 temel, 14 sonuç;
    [Metraj özeti], Ek A düğümler, Ek B çubuklar, [Ek C seçilen tablolar]. Veri olmayan bölüm "Bu modelde uygulanmadı"
    notuyla yer alır. ``secenek`` için modül belgesine bakın."""
    if secenek is not None and not isinstance(secenek, dict):
        raise TypeError("secenek bir sözlük olmalı: {\"proje\": {...}, \"eleman_detay\": \"kritik\", ...}")
    return _Rapor(bina, veri, secenek).uret()


def dosya_adi(bina, veri, secenek=None) -> str:
    """İndirme için dosya adı: statik_rapor_<ad>.html (Türkçe karakterler sadeleştirilir)."""
    p = _sozluk(_sozluk(secenek).get("proje"))
    ad = p.get("ad") or _sozluk(_yukle(veri)).get("baslik") or _yukle(bina).get("baslik") or "bina"
    return f"statik_rapor_{_slug(ad)}.html"
