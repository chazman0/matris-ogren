# -*- coding: utf-8 -*-
"""Isı haritası alanları: çubuk boyunca iç kuvvet, gerilme, kullanım ve EĞRİ yer değiştirme; döşeme plak alanları.

Girdi, köprünün önbelleğindeki çözüm paketidir (``yapi.bina_coz(...).ic``): ``paket`` (durum başına düğüm yer
değiştirmeleri ve eleman diyagramları, bina koordinatında), ``alan`` (normalize bina ``B``, ağ ``ag``, motor modeli,
yükler ``Y``, tasarım sonucu). Hiçbir şey yeniden çözülmez: kombinasyon = durum alanlarının doğrusal birleşimi, zarf =
istasyon bazında en büyük / en küçük.

Eksen ve işaret kuralları (motorla birebir; testle kilitli)
-----------------------------------------------------------
* Bina sistemi X sağa, Y derinlik, Z yukarı. Yerel eksenler x′ (eleman ekseni, i → j), y′, z′; ``lam`` satırları bina
  koordinatında birim vektörlerdir (kirişte y′ yukarı; kolonda y′ = −X, z′ = −Y).
* N çekme +. Vy = dMz/dx, Vz = dMy/dx. Mz (motorun M'si) "alt lif" (−y′) çekmede +; My, −z′ lifi çekmede +.
* Lif gerilmesi (doğrusal elastik, çekme +):  σ(y, z) = N/A − Mz·y/Iz − My·z/Iy   (y, z yerel; MPa = kN/m² / 1000).
* Eğrilik: EIz·v″ = Mz, EIy·w″ = My (v: y′ yönünde, w: z′ yönünde sehim), EA·u′ = N.

Eğri yer değiştirme (her istasyonda)
------------------------------------
Uç ötelemeleri yerel eksene çevrilir; eleman içi biçim, M/EI'nin iki kez integralidir:
``v(x) = v_i (1 − ξ) + v_j ξ + [ψ(x) − ξ ψ(L)] / EI``,  ``ψ(x) = ∫₀ˣ∫₀^s M dt ds``.
M, istasyonlarda (M, V = dM/dx) kübik Hermite ile kurulur (düzgün ve doğrusal değişen yayılı yükte kesin), integraller
kapalı formdur. Yalnız uç ÖTELEMELERİ kullanıldığından uç serbestlikli (mafsallı) elemanda düğüm dönmesi elemana
taşınmaz: mafsallı uçta eğim kendiliğinden doğru çıkar. Kesin eğrilik, uçlarda düğüm dönmesini de verir (testte sağlanır).
Doğrulamalar (testler/test_alan.py): basit kiriş orta sehim 5qL⁴/384EI, konsol uç PL³/3EI ve tüm eğri, iki ucu ankastre
kiriş qL⁴/384EI, bir ucu mafsallı kiriş, eğilme düzlemi dışı (z′) yükte w ve lif işareti.

Gerilmeler (en dış lif, yaklaşık): σ_maks/min = N/A ± |My|/Wy ± |Mz|/Wz (boru: ± √(My² + Mz²)/W);
τ_maks ≈ |Vy|/A_vy + |Vz|/A_vz + |T|/W_t; von Mises ≈ √(σ² + 3τ²) (σ = en büyük mutlak lif gerilmesi; güvenli yanda).
Kullanım: çelikte von Mises / F_y; betonarmede tasarım kapasiteleriyle |M|/M_r (açıklık/mesnet) ve |V|/V_r (kiriş),
|Mx|/M_rx + |My|/M_ry (kolon, kapasiteler belirleyici kombinasyonun N'inde) — tasarım yoksa None.

Döşemeler (sonlu eleman değildir): 45° yük payı poligonları (TS 500 md. 11.4.3 dağıtımıyla aynı) ve dört kenarı basit
mesnetli dikdörtgen plak için çift Fourier (Navier) serisi: w, m_x, m_y (ν = 0,2; sürekli kenar etkisi yok sayılır).

Radye / mütemadi temel (temel modülü çözüm paketine taban basıncı metası koyduysa): Winkler düğüm oturması w = −u_Z ve
taban basıncı p = k0·w, düğümler ızgaraya dizilerek (``radye_alani``).

Dışa açık yardımcılar (köprü ``bina_alan`` ve eleman bilgi paneli ``bina_eleman_bilgi`` için):
``eleman_alanlari``, ``panel_alanlari``, ``radye_alani``, ``alan_paketi``, ``durum_katsayilari``, ``durum_listesi``,
``fe_elemanlari``, ``eleman_kaydi``, ``istasyon_kuvvetleri``, ``uc_yer_degistirmeleri``, ``eleman_bilgi_alani``,
``kesit_geometrisi``, ``lif_gerilmesi``, ``navier_plak``, ``yuk_payi_poligonlari``, ``poligon_alani``;
çekirdek: ``cubuk_alani``, ``sehim_egrisi``, ``eksenel_yer_degistirme``, ``hermite_ara_deger``, ``istasyon_izgarasi``.
"""
from __future__ import annotations

import math

import numpy as np

from matris_ogren import MatrisHatasi

ISTASYON = 21
NAVIER_TERIM = 31          # m, n ≤ 31 tek terimler (merkez momenti %0,1 içinde; sehim çok daha hızlı yakınsar)
PLAK_IZGARA = 21
PLAK_NU = 0.2              # betonarme plak Poisson oranı (TS 500 md. 3.3.3)
_DIY = ("N", "V", "M", "Vz", "My", "T")                    # paket diyagram sırası
ALANLAR = ("N", "Vy", "Vz", "T", "My", "Mz")               # çıktı adları (Vy = motor V, Mz = motor M)
BUYUKLUKLER = ("u", "uX", "uY", "uZ", "N", "Vy", "Vz", "T", "My", "Mz", "sigma_max", "sigma_min", "von_mises", "tau_max",
               "kullanim")
BIRIMLER = {"u": "m", "uX": "m", "uY": "m", "uZ": "m", "N": "kN", "Vy": "kN", "Vz": "kN", "T": "kN·m", "My": "kN·m",
            "Mz": "kN·m", "sigma_max": "MPa", "sigma_min": "MPa", "von_mises": "MPa", "tau_max": "MPa", "kullanim": "",
            "x": "m", "w": "m", "mx": "kN·m/m", "my": "kN·m/m", "q": "kN/m²"}
_NEGATIF_OLMAYAN = ("u", "von_mises", "tau_max", "kullanim")
_CATLAMIS_EK = "~c"
_DEPREM_DURUM = ("EX+", "EX-", "EY+", "EY-")
BETONARME_NOT = ("Betonarme: çatlamış kesitte gerçek gerilme farklıdır; doğrusal elastik σ yalnız gösterim içindir, "
                 "'kullanım' haritasını esas alın.")
ISARET = "σ(y, z) = N/A − Mz·y/Iz − My·z/Iy (y, z yerel eksen; çekme +; MPa)"


# ============================================================================
# Çekirdek: istasyon ara değeri, M/EI'nin iki kez integrali, sehim ve eksenel yer değiştirme (durum ekseni boyunca vektörel)
# ============================================================================
def _artan(xs):
    """Kesin artan istasyonlar ve tutulacak indeksler (yinelenen x atılır)."""
    xs = np.asarray(xs, dtype=float)
    tut = [0]
    for i in range(1, len(xs)):
        if xs[i] - xs[tut[-1]] > 1e-12:
            tut.append(i)
    return xs[tut], np.array(tut)


def _parca(xs, xe):
    idx = np.clip(np.searchsorted(xs, xe, side="right") - 1, 0, len(xs) - 2)
    return idx, xe - xs[idx], xs[idx + 1] - xs[idx]


def _hermite_katsayi(f, df, h):
    """Parça başına kübik f(s) = c0 + c1 s + c2 s² + c3 s³ (f, df uçlarda)."""
    f0, f1, d0, d1 = f[..., :-1], f[..., 1:], df[..., :-1], df[..., 1:]
    c2 = (3.0 * (f1 - f0) / h - 2.0 * d0 - d1) / h
    c3 = (2.0 * (f0 - f1) / h + d0 + d1) / (h * h)
    return f0, d0, c2, c3


def hermite_ara_deger(xs, f, df, xe):
    """İstasyon değerleri f ve türevleri df (son eksen istasyon; öndeki eksenler serbest) ile kübik Hermite ara değer:
    (f(xe), f′(xe)). Kübik f için kesindir (düzgün/doğrusal yayılı yükte M)."""
    xs = np.asarray(xs, dtype=float)
    f, df, xe = np.asarray(f, dtype=float), np.asarray(df, dtype=float), np.asarray(xe, dtype=float)
    if len(xs) < 2:
        return np.broadcast_to(f[..., :1], f.shape[:-1] + xe.shape).copy(), np.zeros(f.shape[:-1] + xe.shape)
    c0, c1, c2, c3 = _hermite_katsayi(f, df, np.diff(xs))
    i, s, _ = _parca(xs, xe)
    a0, a1, a2, a3 = c0[..., i], c1[..., i], c2[..., i], c3[..., i]
    return a0 + s * (a1 + s * (a2 + s * a3)), a1 + s * (2.0 * a2 + 3.0 * s * a3)


def _cift_integral(xs, f, df, xe):
    """φ(x) = ∫₀ˣ f, ψ(x) = ∫₀ˣ φ (f: kübik Hermite parçalar, kapalı form). Dönüş φ(xe), ψ(xe), φ(L), ψ(L)."""
    h = np.diff(xs)
    c0, c1, c2, c3 = _hermite_katsayi(f, df, h)
    Iphi = h * (c0 + h * (c1 / 2.0 + h * (c2 / 3.0 + h * c3 / 4.0)))
    Ipsi = h * h * (c0 / 2.0 + h * (c1 / 6.0 + h * (c2 / 12.0 + h * c3 / 20.0)))
    sifir = np.zeros(f.shape[:-1] + (1,))
    phi0 = np.concatenate([sifir, np.cumsum(Iphi, axis=-1)], axis=-1)            # parça başlarında φ (son: φ(L))
    psi0 = np.concatenate([sifir, np.cumsum(phi0[..., :-1] * h + Ipsi, axis=-1)], axis=-1)
    i, s, _ = _parca(xs, xe)
    a0, a1, a2, a3 = c0[..., i], c1[..., i], c2[..., i], c3[..., i]
    phi = phi0[..., i] + s * (a0 + s * (a1 / 2.0 + s * (a2 / 3.0 + s * a3 / 4.0)))
    psi = psi0[..., i] + phi0[..., i] * s + s * s * (a0 / 2.0 + s * (a1 / 6.0 + s * (a2 / 12.0 + s * a3 / 20.0)))
    return phi, psi, phi0[..., -1], psi0[..., -1]


def sehim_egrisi(xs, M, V, EI, v_i, v_j, xe):
    """Eğilme sehimi v(xe) ve eğimi v′(xe): EI·v″ = M, v(0) = v_i, v(L) = v_j (yalnız uç ötelemeleri; uç dönmesi
    gerekmez — mafsallı uçta da doğru). M, V istasyon değerleri (son eksen), V = dM/dx. Öndeki eksenler (durumlar)
    yayınlanır; EI skaler ya da öndeki eksenle uyumlu dizi."""
    xs, keep = _artan(xs)
    M, V = np.asarray(M, dtype=float)[..., keep], np.asarray(V, dtype=float)[..., keep]
    xe = np.asarray(xe, dtype=float)
    L = xs[-1] - xs[0]
    xe0 = xe - xs[0]
    xi = xe0 / L
    EI = np.asarray(EI, dtype=float)[..., None] if np.ndim(EI) else float(EI)
    v_i, v_j = np.asarray(v_i, dtype=float)[..., None], np.asarray(v_j, dtype=float)[..., None]
    phi, psi, _, psiL = _cift_integral(xs - xs[0], M, V, xe0)
    v = v_i * (1.0 - xi) + v_j * xi + (psi - xi * psiL[..., None]) / EI
    dv = (v_j - v_i) / L + (phi - psiL[..., None] / L) / EI
    return v, dv


def eksenel_yer_degistirme(xs, N, EA, u_i, u_j, xe):
    """Eksenel yer değiştirme: EA·u′ = N, u(0) = u_i, u(L) = u_j; N istasyonlar arasında doğrusal (yayılı eksenel yükte
    kesin). Uçlarda tutarlılık hatası (yuvarlama) doğrusal dağıtılır."""
    xs, keep = _artan(xs)
    N = np.asarray(N, dtype=float)[..., keep]
    xe = np.asarray(xe, dtype=float)
    L = xs[-1] - xs[0]
    h = np.diff(xs)
    I = np.concatenate([np.zeros(N.shape[:-1] + (1,)), np.cumsum(h * (N[..., :-1] + N[..., 1:]) / 2.0, axis=-1)], axis=-1)
    i, s, hh = _parca(xs, xe)
    Ni = N[..., i] + (N[..., i + 1] - N[..., i]) * s / hh
    Ix = I[..., i] + s * (N[..., i] + Ni) / 2.0
    xi = (xe - xs[0]) / L
    EA = np.asarray(EA, dtype=float)[..., None] if np.ndim(EA) else float(EA)
    u_i, u_j = np.asarray(u_i, dtype=float)[..., None], np.asarray(u_j, dtype=float)[..., None]
    return u_i * (1.0 - xi) + u_j * xi + (Ix - xi * I[..., -1:]) / EA


def _dogrusal(xs, f, xe):
    xs, keep = _artan(xs)
    f = np.asarray(f, dtype=float)[..., keep]
    i, s, h = _parca(xs, np.asarray(xe, dtype=float))
    return f[..., i] + (f[..., i + 1] - f[..., i]) * s / h


def istasyon_izgarasi(xs, istasyon=ISTASYON):
    """Çıktı istasyonları: [0, L]'de eşit aralıklı ``istasyon`` nokta ∪ motor istasyonları (yük parça sınırları dahil)."""
    xs = np.asarray(xs, dtype=float)
    L = float(xs[-1])
    n = max(2, int(istasyon))
    tum = np.concatenate([np.linspace(0.0, L, n), xs])
    tum.sort()
    out = [tum[0]]
    for x in tum[1:]:
        if x - out[-1] > 1e-9 * max(L, 1.0):
            out.append(x)
    out[-1] = L
    return np.array(out)


def cubuk_alani(xs, diy, lam, d_i, d_j, EA, EIy, EIz, xe):
    """Tek çubuk, k durum: istasyonlarda (k, 9, ne) = N, Vy, Vz, T, My, Mz, uX, uY, uZ (bina global öteleme).
    diy (k, 6, ns): paket sırası N, V, M, Vz, My, T; d_i/d_j (k, 3) uç ötelemeleri (bina global); EIy/EIz (k,) ya da skaler."""
    lam = np.asarray(lam, dtype=float)
    diy = np.asarray(diy, dtype=float)
    N, V, M, Vz, My, T = (diy[:, a, :] for a in range(6))
    Mz_e, Vy_e = hermite_ara_deger(xs, M, V, xe)
    My_e, Vz_e = hermite_ara_deger(xs, My, Vz, xe)
    N_e, T_e = _dogrusal(xs, N, xe), _dogrusal(xs, T, xe)
    yi, yj = np.asarray(d_i, dtype=float) @ lam.T, np.asarray(d_j, dtype=float) @ lam.T      # (k, 3) yerel
    u_ax = eksenel_yer_degistirme(xs, N, EA, yi[:, 0], yj[:, 0], xe)
    v, _ = sehim_egrisi(xs, M, V, EIz, yi[:, 1], yj[:, 1], xe)
    w, _ = sehim_egrisi(xs, My, Vz, EIy, yi[:, 2], yj[:, 2], xe)
    yerel = np.stack([u_ax, v, w], axis=1)                       # (k, 3, ne)
    glob = np.einsum("ab,kan->kbn", lam, yerel)                  # Σ_a lam[a, b]·yerel_a
    return np.concatenate([np.stack([N_e, Vy_e, Vz_e, T_e, My_e, Mz_e], axis=1), glob], axis=1)


# ============================================================================
# Kesit geometrisi (yerel eksenlerde) ve gerilme sabitleri
# ============================================================================
def _yv():
    try:
        import yapi_veri as yv
        return yv
    except ImportError:      # pragma: no cover
        return None


def _profil_kaydi(ad):
    yv = _yv()
    if yv is None or not ad:
        return None
    ad_n = str(ad).strip().upper().replace("  ", " ")
    if ad_n in yv.PROFILLER:
        return ad_n, yv.PROFILLER[ad_n]
    for on in ("IPE", "HEA", "HEB"):
        if ad_n.startswith(on) and " " not in ad_n and ad_n[len(on):] and (on + " " + ad_n[len(on):]) in yv.PROFILLER:
            return on + " " + ad_n[len(on):], yv.PROFILLER[on + " " + ad_n[len(on):]]
    return None


def _basit_profil(ad):
    """'KUTU 200x100x6', 'BORU 168.3x6.3', 'L 100x10', '2L 100x10 s=10', 'UPN 200' → (tip, boyutlar mm); tasarim.py varsa."""
    try:
        import tasarim
        coz = getattr(tasarim, "_ad_coz", None)
        return coz(str(ad)) if coz else None
    except Exception:       # noqa: BLE001 — bilinmeyen ad: dikdörtgen eşdeğeri
        return None


def _mm(d, *anahtarlar):
    for a in anahtarlar:
        v = d.get(a)
        if isinstance(v, (int, float)) and v > 0:
            return float(v) / 1000.0
    return None


def kesit_geometrisi(ks, me, mal=None):
    """Kesit kartı (bina normalize kaydı ``ks``) + motor elemanı ``me`` (A, Iy, Iz, J, E, G yerel) → yerel eksenli kesit:
    {sekil, h (derinlik), b, tw, tf, t, D, eksen ('y': derinlik y′ boyunca | 'z'), dy, dz (y′/z′ boyunca dış ölçü),
    A, Iy, Iz, J, Wy, Wz, Wply, Wplz, Avy, Avz, Wt, not}. Bilinmeyen şekil → aynı A ve güçlü I'lı dikdörtgen eşdeğeri."""
    ks = ks or {}
    A, Iy, Iz, J = (float(me.get(a) or 0.0) for a in ("A", "Iy", "Iz", "J"))
    tip = str(ks.get("tip") or "dikdortgen").lower()
    I_g = float(ks.get("I_guclu") or max(Iy, Iz))
    eksen = "y" if abs(Iz - I_g) <= abs(Iy - I_g) else "z"
    k = {"sekil": "dikdortgen", "eksen": eksen, "A": A, "Iy": Iy, "Iz": Iz, "J": J, "not": None}
    prof = _profil_kaydi(ks.get("profil")) if tip == "profil" else None
    basit = None
    if tip == "profil" and prof is None and ks.get("profil"):
        basit = _basit_profil(ks.get("profil"))
    elif tip in ("kutu", "boru", "l", "2l", "u"):
        basit = ({"l": "L", "2l": "2L", "u": "U"}.get(tip, tip), ks)
    if prof is not None:
        ad, p = prof
        h, b, tw, tf = p["h"] / 1000.0, p["b"] / 1000.0, p["tw"] / 1000.0, p["tf"] / 1000.0
        k.update({"sekil": "I", "profil": ad, "h": h, "b": b, "tw": tw, "tf": tf, "r": p.get("r", 0.0) / 1000.0})
        W_g, W_z = p["Wely"] * 1e-6, p["Welz"] * 1e-6
        Wp_g, Wp_z = p["Wply"] * 1e-6, p["Wplz"] * 1e-6
        Av_g = (p.get("Avz") or p["h"] * p["tw"] / 100.0) * 1e-4
        Av_z = 2.0 * b * tf / 1.5
        Wt = J / max(tf, tw) if J > 0 else None
        derin, gen = h, b
    elif basit is not None and isinstance(basit, tuple) and isinstance(basit[1], dict):
        tipb, bt = basit
        k["sekil"] = tipb
        if tipb == "kutu":
            H, Bk, t = _mm(bt, "H", "h"), _mm(bt, "B", "b"), _mm(bt, "t")
            H, Bk, t = H or 0.2, Bk or H or 0.2, t or 0.006
            k.update({"h": H, "b": Bk, "t": t})
            derin, gen = H, Bk
            Av_g, Av_z = 2.0 * H * t, 2.0 * Bk * t
            Wt = 2.0 * t * (H - t) * (Bk - t)
        elif tipb == "boru":
            D, t = _mm(bt, "D"), _mm(bt, "t")
            D, t = D or 0.2, t or 0.006
            k.update({"D": D, "t": t, "h": D, "b": D})
            derin = gen = D
            Av_g = Av_z = A / 2.0 if A > 0 else math.pi * D * t / 2.0
            Wt = 2.0 * (math.pi * (D ** 4 - (D - 2 * t) ** 4) / 64.0) / D * 2.0
        elif tipb in ("L", "2L"):
            bb, t = _mm(bt, "b"), _mm(bt, "t")
            bb, t = bb or 0.1, t or 0.01
            k.update({"b": bb, "h": bb, "t": t, "s": (_mm(bt, "s") or 0.01) if tipb == "2L" else None,
                      "not": "Korniyer: asal eksenler yerine geometrik eksenlerle yaklaşık lif gerilmesi."})
            derin, gen = bb, (2 * bb + (k["s"] or 0.0)) if tipb == "2L" else bb
            Av_g = Av_z = bb * t * (2 if tipb == "2L" else 1)
            Wt = J / t if J > 0 else None
        else:   # U
            H, Bk, tw, tf = _mm(bt, "h"), _mm(bt, "b"), _mm(bt, "tw"), _mm(bt, "tf")
            H, Bk, tw, tf = H or 0.2, Bk or 0.075, tw or 0.0085, tf or 0.0115
            k.update({"h": H, "b": Bk, "tw": tw, "tf": tf})
            derin, gen = H, Bk
            Av_g, Av_z = H * tw, 2.0 * Bk * tf / 1.5
            Wt = J / max(tw, tf) if J > 0 else None
        W_g = Wp_g = W_z = Wp_z = None
    elif tip == "dikdortgen" and ks.get("b") and ks.get("h"):
        b, h = float(ks["b"]), float(ks["h"])
        k.update({"h": h, "b": b})
        derin, gen = h, b
        W_g, W_z, Wp_g, Wp_z = b * h * h / 6.0, h * b * b / 6.0, b * h * h / 4.0, h * b * b / 4.0
        Av_g = Av_z = b * h / 1.5
        Wt = J / min(b, h) if J > 0 else None
    else:
        I_z = min(Iy, Iz)
        h = math.sqrt(12.0 * I_g / A) if A > 0 and I_g > 0 else 0.3
        b = A / h if A > 0 else 0.3
        if I_z > 0 and A > 0:
            b = math.sqrt(12.0 * I_z / A)
        k.update({"h": h, "b": b, "not": f"Kesit şekli ({tip}) tanınmadı: aynı A ve I'lı dikdörtgen eşdeğeri çizildi."})
        derin, gen = h, b
        W_g, W_z, Wp_g, Wp_z = None, None, None, None
        Av_g = Av_z = A / 1.5 if A > 0 else None
        Wt = J / min(b, h) if J > 0 else None
    # yerel eksenlere: derinlik y′ boyunca ise güçlü eğilme z′ etrafında (Iz)
    if eksen == "y":
        dy, dz = derin, gen
        Wz, Wy, Wplz, Wply, Avy, Avz = W_g, W_z, Wp_g, Wp_z, Av_g, Av_z
    else:
        dy, dz = gen, derin
        Wy, Wz, Wply, Wplz, Avz, Avy = W_g, W_z, Wp_g, Wp_z, Av_g, Av_z
    if k["sekil"] in ("L", "2L", "U"):
        Wy = Wz = None
    if not Wz:
        Wz = Iz / (dy / 2.0) if dy > 0 else None
    if not Wy:
        Wy = Iy / (dz / 2.0) if dz > 0 else None
    k.update({"dy": dy, "dz": dz, "Wy": Wy, "Wz": Wz, "Wply": Wply, "Wplz": Wplz, "Avy": Avy or A, "Avz": Avz or A,
              "Wt": Wt})
    if mal:
        k["malzeme"] = mal
    return k


def _malzeme_ozeti(B, ks):
    m = (getattr(B, "malzemeler", {}) or {}).get((ks or {}).get("malzeme")) or {}
    out = {"ad": m.get("kutuphane") or (ks or {}).get("malzeme"), "tur": m.get("tur"), "E": m.get("E_MPa")}
    if m.get("tur") == "celik":
        out["fy"] = m.get("Fy")
    elif m.get("tur") == "beton":
        out["fck"] = m.get("fck")
    return out


# ============================================================================
# Paket: bina çözümünden durum başına istasyon alanları (bir kez; önbellekte)
# ============================================================================
def _ic_kontrol(ic):
    if not isinstance(ic, dict) or "paket" not in ic:
        raise MatrisHatasi("Önce bina çözülmeli (önbellekte çözüm yok ya da süresi doldu); binayı yeniden çözün.")
    if not isinstance(ic.get("alan"), dict):
        raise MatrisHatasi("Bu çözüm paketi ısı haritası bilgisi taşımıyor (eski bina modülü); binayı yeniden çözün.")


def _catlamis_mi(ad, paket, model_c):
    if model_c is None:
        return False
    if ad.endswith(_CATLAMIS_EK) or ad in _DEPREM_DURUM:
        return True
    return ad == "EZ" and ("G" + _CATLAMIS_EK) in paket.durum


def alan_paketi(ic, istasyon=ISTASYON):
    """Durum başına eleman istasyon alanları (k, 9, ne) ve sabit eleman bilgileri; ``ic["_alan"]``da önbelleklenir."""
    _ic_kontrol(ic)
    on = ic.get("_alan")
    if on is not None and on["istasyon"] == int(istasyon):
        return on
    A = ic["alan"]
    paket, ag, model = ic["paket"], A["ag"], A["model"]
    B = A["B"]
    model_c = ag.get("model_c")
    adlar = list(paket.durum)
    catl = np.array([_catlamis_mi(a, paket, model_c) for a in adlar])
    me_b = {me["no"]: me for me in model["elemanlar"]}
    me_c = {me["no"]: me for me in model_c["elemanlar"]} if model_c else me_b
    ag_el = {e["no"]: e for e in ag["elemanlar"]}
    dno = {dg["no"]: dg for dg in ag["dugumler"]}
    d_idx = {no: i for i, no in enumerate(paket.dugum_no)}
    DUG = np.array([paket.durum[a]["dug"] for a in adlar])          # (k, nd, 6)
    tas = A.get("tasarim") or {}
    tas_fe = {}
    for kay in tas.get("elemanlar") or []:
        for fe in kay.get("fe_elemanlar") or []:
            tas_fe[fe] = kay
    elemanlar, alanlar = [], []
    for j, no in enumerate(paket.el_no):
        e = ag_el[no]
        xs = np.array(paket.el_x[j], dtype=float)
        xe = istasyon_izgarasi(xs, istasyon)
        blok = np.array([paket.durum[a]["diy"][paket.ofs[j]:paket.ofs[j] + 6 * paket.ns[j]] for a in adlar])
        blok = blok.reshape(len(adlar), 6, paket.ns[j])
        mb, mc = me_b[no], me_c[no]
        E = float(mb["E"])
        EIy = np.where(catl, E * float(mc["Iy"]), E * float(mb["Iy"]))
        EIz = np.where(catl, E * float(mc["Iz"]), E * float(mb["Iz"]))
        i_no, j_no = e["dugumler"]
        d_i, d_j = DUG[:, d_idx[i_no], :3], DUG[:, d_idx[j_no], :3]
        alanlar.append(cubuk_alani(xs, blok, e["lam"], d_i, d_j, E * float(mb["A"]), EIy, EIz, xe))
        ks = (getattr(B, "kesitler", {}) or {}).get(e.get("kesit")) or {}
        mal = _malzeme_ozeti(B, ks)
        kes = kesit_geometrisi(ks, mb, mal)
        kes["ad"] = e.get("kesit")
        a, b = dno[i_no], dno[j_no]
        elemanlar.append({"no": no, "tur": e.get("tur"), "bina_no": e.get("kaynak_no"), "parca": e.get("parca"),
                          "kat": e.get("kat"), "adres": e.get("adres"), "dugumler": [i_no, j_no],
                          "i": [a["X"], a["Y"], a["Z"]], "j": [b["X"], b["Y"], b["Z"]], "L": float(xs[-1]),
                          "yerel": {"x": list(e["lam"][0]), "y": list(e["lam"][1]), "z": list(e["lam"][2])},
                          "kesit": kes, "x": xe, "tasarim": tas_fe.get(no), "lam": np.asarray(e["lam"], dtype=float)})
    on = {"istasyon": int(istasyon), "adlar": adlar, "idx": {a: i for i, a in enumerate(adlar)}, "elemanlar": elemanlar,
          "alanlar": alanlar, "fe_idx": {e["no"]: i for i, e in enumerate(elemanlar)}, "DUG": DUG}
    ic["_alan"] = on
    return on


def durum_listesi(ic):
    """Arayüz seçicisi için: yük durumları (çatlamış kopyalar hariç), uygulanan kombinasyonlar (tür), zarf."""
    _ic_kontrol(ic)
    komb_tur = ic["alan"].get("komb_tur") or {}
    return {"durumlar": [a for a in ic["paket"].durum if not a.endswith(_CATLAMIS_EK)],
            "kombinasyonlar": [{"ad": a, "tur": komb_tur.get(a)} for a in ic.get("kombinasyonlar", {})],
            "zarf": ["zarf+", "zarf-"]}


def durum_katsayilari(ic, durum, katsayilar=None):
    """Durum adı → [(ad, {paket durumu: γ})]: tek durum, uygulanan kombinasyon (hesap katsayıları; deprem birleşiminde
    çatlamış kopyalar), serbest birleşim (``katsayilar``) ya da "zarf+"/"zarf-" (uygulanan dayanım/deprem/servis
    kombinasyonlarının hepsi; öteleme satırları hariç)."""
    _ic_kontrol(ic)
    paket = ic["paket"]
    durum = str(durum or "").strip()
    komb = ic.get("kombinasyonlar") or {}
    if durum in ("zarf+", "zarf-", "zarf"):
        tur = ic["alan"].get("komb_tur") or {}
        liste = [(a, k) for a, k in komb.items() if tur.get(a) != "drift"]
        if not liste:
            liste = [(a, {a: 1.0}) for a in paket.durum if not a.endswith(_CATLAMIS_EK)]
        return liste
    if durum in komb:
        return [(durum, dict(komb[durum]))]
    if durum in paket.durum:
        return [(durum, {durum: 1.0})]
    if isinstance(katsayilar, dict) and katsayilar:
        kat = {}
        for d, g in katsayilar.items():
            if str(d) not in paket.durum:
                raise MatrisHatasi(f"{d!r} yük durumu bu çözümde yok. Mevcut durumlar: {', '.join(paket.durum)}.")
            kat[str(d)] = float(g)
        return [(durum or "birleşim", kat)]
    if not durum:
        raise MatrisHatasi("Durum adı (durum) boş: bir yük durumu (G, Q…), kombinasyon adı ya da \"zarf+\" / \"zarf-\" verin.")
    raise MatrisHatasi(f"Durum ya da kombinasyon bulunamadı: {durum!r}. Durumlar: {', '.join(a for a in paket.durum if not a.endswith(_CATLAMIS_EK))}; "
                       f"kombinasyonlardan bazıları: {', '.join(list(komb)[:6])}…; ya da \"zarf+\" / \"zarf-\".")


def _gamma_matrisi(pa, liste):
    G = np.zeros((len(liste), len(pa["adlar"])))
    for i, (_, kat) in enumerate(liste):
        for d, g in kat.items():
            if d in pa["idx"]:
                G[i, pa["idx"][d]] = g
    return G


# ============================================================================
# Türetilmiş büyüklükler: gerilme, kesme, von Mises, kullanım
# ============================================================================
def _kapasite(kay, bas, uc=None):
    """Tasarım kontrol satırından kapasite (ad ``bas`` ile başlar; ``uc`` verilirse adında o uç geçen satır)."""
    for k in (kay or {}).get("kontroller") or []:
        ad = str(k.get("ad", ""))
        if ad.startswith(bas) and k.get("kapasite") and (uc is None or ad.endswith(uc)):
            return float(k["kapasite"])
    return None


def _kolon_kapasitesi(kay, bas, x):
    """Kolon M_r(x): alt (x = 0) ve üst (x = L) uç kapasiteleri arasında doğrusal (her biri o ucun belirleyici
    kombinasyonundaki N ile); tek uç biliniyorsa sabit."""
    alt, ust = _kapasite(kay, bas, "alt uç"), _kapasite(kay, bas, "üst uç")
    if alt is None and ust is None:
        tek = _kapasite(kay, bas)
        return None if tek is None else np.full_like(x, tek)
    alt, ust = alt if alt is not None else ust, ust if ust is not None else alt
    L = float(x[-1]) if len(x) and x[-1] > 0 else 1.0
    return alt + (ust - alt) * (np.asarray(x, dtype=float) / L)


def _turet(F, el):
    """F (c, 9, n) → {σ_maks, σ_min, τ_maks, von Mises, kullanım} (c, n) MPa / oran."""
    k = el["kesit"]
    N, Vy, Vz, T, My, Mz = (F[:, a, :] for a in range(6))
    A = k["A"] or 1.0
    if k["sekil"] == "boru":
        W = k.get("Wz") or k.get("Wy") or 1.0
        eg = np.hypot(My, Mz) / W
    else:
        eg = (np.abs(My) / k["Wy"] if k.get("Wy") else 0.0) + (np.abs(Mz) / k["Wz"] if k.get("Wz") else 0.0)
    smax = (N / A + eg) / 1000.0
    smin = (N / A - eg) / 1000.0
    tau = (np.abs(Vy) / k["Avy"] + np.abs(Vz) / k["Avz"] + (np.abs(T) / k["Wt"] if k.get("Wt") else 0.0)) / 1000.0
    sabs = np.maximum(np.abs(smax), np.abs(smin))
    vm = np.sqrt(sabs * sabs + 3.0 * tau * tau)
    mal = k.get("malzeme") or {}
    kul = None
    if mal.get("tur") == "celik" and mal.get("fy"):
        kul = vm / float(mal["fy"])
    elif el.get("tasarim"):
        kay = el["tasarim"]
        if el.get("tur") == "kiris":
            Mn, Mp, Vr = _kapasite(kay, "Eğilme (mesnet"), _kapasite(kay, "Eğilme (açıklık"), _kapasite(kay, "Kesme Vd")
            if Mn or Mp:
                kul = np.where(Mz >= 0, Mz / (Mp or Mn), -Mz / (Mn or Mp))
                if Vr:
                    kul = np.maximum(kul, np.abs(Vy) / Vr)
        elif el.get("tur") == "kolon":
            Mrx, Mry = _kolon_kapasitesi(kay, "N–Mx", el["x"]), _kolon_kapasitesi(kay, "N–My", el["x"])
            if Mrx is not None and Mry is not None and np.all(Mrx > 0) and np.all(Mry > 0):
                lam = el["lam"]
                MX = My * lam[1][0] + Mz * lam[2][0]      # bina X / Y eksenleri etrafında (yon takası lam ile kendiliğinden)
                MY = My * lam[1][1] + Mz * lam[2][1]
                kul = np.abs(MX) / Mrx + np.abs(MY) / Mry
    return smax, smin, tau, vm, kul


def _yuvarla(a, b=5):
    a = np.asarray(a, dtype=float)
    out = []
    for v in a.ravel().tolist():
        if v != v or v in (math.inf, -math.inf):
            out.append(None)
        elif v == 0.0:
            out.append(0.0)
        else:
            out.append(float(f"{v:.{b}g}"))
    return np.array(out, dtype=object).reshape(a.shape).tolist() if a.ndim > 1 else out


def _ekstremum(seri, x):
    """{deger, x} = en büyük mutlak değer ve yeri; ayrıca "max" / "min" {deger, x} (işaretli büyüklükler için)."""
    if seri is None:
        return None
    a = np.asarray(seri, dtype=float)
    if not a.size or not np.all(np.isfinite(a)):
        return None

    def kay(i):
        return {"deger": float(f"{a[i]:.5g}"), "x": float(f"{x[i]:.5g}")}
    out = kay(int(np.argmax(np.abs(a))))
    out["max"], out["min"] = kay(int(np.argmax(a))), kay(int(np.argmin(a)))
    return out


# ============================================================================
# Ana işlevler
# ============================================================================
def eleman_alanlari(ic, durum, *, istasyon=ISTASYON, katsayilar=None, elemanlar=None, paneller=True):
    """§16.1: {"durum", "birim", "elemanlar": [...], "dugumler": [...], "paneller": [...], "aralik", "not", "isaret",
    "secenekler"}. ``elemanlar`` (FE no listesi) verilirse yalnız onlar yazılır (eleman bilgi paneli)."""
    pa = alan_paketi(ic, istasyon)
    liste = durum_katsayilari(ic, durum, katsayilar)
    zarf = str(durum).startswith("zarf")
    eksi = str(durum) == "zarf-"
    G = _gamma_matrisi(pa, liste)
    istenen = set(elemanlar) if elemanlar is not None else None
    cikti, aralik = [], {}
    betonarme = False

    def araliga(ad, dizi):
        if dizi is None:
            return
        a = np.asarray(dizi, dtype=float)
        a = a[np.isfinite(a)]
        if not a.size:
            return
        lo, hi = float(a.min()), float(a.max())
        if ad in aralik:
            lo, hi = min(lo, aralik[ad][0]), max(hi, aralik[ad][1])
        aralik[ad] = [lo, hi]

    for el, F_d in zip(pa["elemanlar"], pa["alanlar"]):
        if istenen is not None and el["no"] not in istenen:
            continue
        F = np.tensordot(G, F_d, axes=(1, 0))                    # (c, 9, n)
        smax, smin, tau, vm, kul = _turet(F, el)
        U = np.linalg.norm(F[:, 6:9, :], axis=1)
        bel = None
        if zarf:
            sec = np.min if eksi else np.max
            Fz = sec(F, axis=0)
            smax_z, smin_z = (np.min(smax, axis=0), np.min(smin, axis=0)) if eksi else (np.max(smax, axis=0), np.max(smin, axis=0))
            tau_z, vm_z, U_z = tau.max(axis=0), vm.max(axis=0), U.max(axis=0)
            kul_z = kul.max(axis=0) if kul is not None else None
            hedef = kul if kul is not None else vm
            ic_ = np.unravel_index(int(np.argmax(hedef)), hedef.shape)
            bel = {"kombinasyon": liste[ic_[0]][0], "buyukluk": "kullanim" if kul is not None else "von_mises"}
            F1, smax1, smin1, tau1, vm1, U1, kul1 = Fz, smax_z, smin_z, tau_z, vm_z, U_z, kul_z
        else:
            F1, smax1, smin1, tau1, vm1, U1 = F[0], smax[0], smin[0], tau[0], vm[0], U[0]
            kul1 = kul[0] if kul is not None else None
        x = el["x"]
        k = el["kesit"]
        if (k.get("malzeme") or {}).get("tur") == "beton":
            betonarme = True
        kay = {"no": el["no"], "tur": el["tur"], "bina_no": el["bina_no"], "parca": el["parca"], "kat": el["kat"],
               "adres": el["adres"], "dugumler": el["dugumler"], "i": el["i"], "j": el["j"], "L": el["L"], "yerel": el["yerel"],
               "kesit": {a: (float(f"{v:.6g}") if isinstance(v, float) else v) for a, v in k.items()},
               "x": _yuvarla(x, 6), "u": _yuvarla(F1[6:9].T)}
        for a_i, ad in enumerate(ALANLAR):
            kay[ad] = _yuvarla(F1[a_i])
        kay["sigma_max"], kay["sigma_min"] = _yuvarla(smax1), _yuvarla(smin1)
        kay["tau_max"], kay["von_mises"] = _yuvarla(tau1), _yuvarla(vm1)
        kay["kullanim"] = _yuvarla(kul1) if kul1 is not None else None
        kay["u_abs"] = _yuvarla(U1)
        tas = el.get("tasarim")
        kay["tasarim"] = ({"dc": tas.get("dc"), "durum": tas.get("durum"), "belirleyen": tas.get("belirleyen"),
                           "bina_no": tas.get("no")} if tas else None)
        if bel:
            kay["belirleyen"] = bel
        ekst = {"u": _ekstremum(U1, x)}
        for a_i, ad in enumerate(ALANLAR):
            ekst[ad] = _ekstremum(F1[a_i], x)
        ekst.update({"sigma_max": _ekstremum(smax1, x), "sigma_min": _ekstremum(smin1, x), "von_mises": _ekstremum(vm1, x),
                     "tau_max": _ekstremum(tau1, x), "kullanim": _ekstremum(kul1, x)})
        kay["ekstremum"] = ekst
        cikti.append(kay)
        araliga("u", U1)
        for a_i, ad in enumerate(("uX", "uY", "uZ")):
            araliga(ad, F1[6 + a_i])
        for a_i, ad in enumerate(ALANLAR):
            araliga(ad, F1[a_i])
        for ad, d in (("sigma_max", smax1), ("sigma_min", smin1), ("von_mises", vm1), ("tau_max", tau1), ("kullanim", kul1)):
            araliga(ad, d)
    # düğümler
    paket = ic["paket"]
    D = np.tensordot(G, pa["DUG"], axes=(1, 0))                # (c, nd, 6)
    if zarf:
        D = D.min(axis=0) if eksi else D.max(axis=0)
    else:
        D = D[0]
    dno = {dg["no"]: dg for dg in ic["alan"]["ag"]["dugumler"]}
    dugumler = []
    if istenen is None:
        for i, no in enumerate(paket.dugum_no):
            dg = dno.get(no)
            if dg is None or dg.get("efendi"):
                continue
            dugumler.append({"no": no, "X": dg["X"], "Y": dg["Y"], "Z": dg["Z"], "kat": dg.get("kat"), "adres": dg.get("adres"),
                             "u": _yuvarla(D[i, :3]), "r": _yuvarla(D[i, 3:])})
    out = {"durum": str(durum), "zarf": zarf, "kombinasyon_sayisi": len(liste) if zarf else None,
           "katsayilar": None if zarf else liste[0][1], "birim": dict(BIRIMLER), "isaret": ISARET,
           "elemanlar": cikti, "dugumler": dugumler, "aralik": aralik, "istasyon": pa["istasyon"],
           "not": BETONARME_NOT if betonarme else None, "secenekler": durum_listesi(ic)}
    if zarf:
        out["zarf_not"] = ("Zarf: her istasyonda her büyüklüğün " + ("en küçüğü" if eksi else "en büyüğü")
                           + " ayrı ayrı alınır (farklı kombinasyonlardan gelebilir); |u|, τ, von Mises ve kullanımda her zaman en büyük.")
    if paneller and istenen is None:
        out["paneller"] = panel_alanlari(ic, durum, katsayilar=katsayilar)
        out["radye"] = radye_alani(ic, durum, katsayilar=katsayilar)
    return out


# ============================================================================
# Döşemeler: 45° yük payı poligonları ve Navier plak çözümü
# ============================================================================
def navier_plak(a, b, q, D, *, nu=PLAK_NU, nx=PLAK_IZGARA, ny=PLAK_IZGARA, terim=NAVIER_TERIM):
    """Dört kenarı basit mesnetli dikdörtgen plak (a × b, düzgün q, D = E t³/12(1 − ν²)) — çift Fourier (Navier) serisi,
    m, n ≤ terim tek terimler. Dönüş {"x", "y", "w" [ny][nx], "mx", "my"} (w aşağı +, m alt lif çekme +)."""
    x = np.linspace(0.0, a, nx)
    y = np.linspace(0.0, b, ny)
    ms = np.arange(1, terim + 1, 2, dtype=float)
    sx = np.sin(np.outer(ms, x) * math.pi / a)          # (m, nx)
    sy = np.sin(np.outer(ms, y) * math.pi / b)          # (n, ny)
    M, Nn = np.meshgrid(ms, ms, indexing="ij")          # (m, n)
    paydas = M * Nn * (M * M / a ** 2 + Nn * Nn / b ** 2) ** 2
    cw = 16.0 * q / (math.pi ** 6 * D) / paydas
    cm = 16.0 * q / math.pi ** 4 / paydas
    w = np.einsum("mn,mx,ny->yx", cw, sx, sy)
    mx = np.einsum("mn,mx,ny->yx", cm * (M * M / a ** 2 + nu * Nn * Nn / b ** 2), sx, sy)
    my = np.einsum("mn,mx,ny->yx", cm * (nu * M * M / a ** 2 + Nn * Nn / b ** 2), sx, sy)
    return {"x": x, "y": y, "w": w, "mx": mx, "my": my}


def yuk_payi_poligonlari(x0, y0, x1, y1, tip, tasiyan=None):
    """Dikdörtgen panelin kenarlara yük payı bölgeleri (45° kuralı): {kenar_ad: [[X, Y], ...]} (alt, ust, sol, sag).
    tip 'cift': kısa kenara üçgen, uzun kenara trapez (açıortaylar); 'tek': ``tasiyan`` kenarlar (varsayılan uzun
    kenarlar) yarı yarıya dikdörtgen; taşımayan kenar boş liste."""
    dx, dy = x1 - x0, y1 - y0
    xm, ym = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def temiz(p):
        out = []
        for q in p:
            if not out or abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) > 1e-12:
                out.append([float(q[0]), float(q[1])])
        if len(out) > 1 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) <= 1e-12:
            out.pop()
        return out

    if tip == "tek":
        if tasiyan is None:
            tasiyan = ("alt", "ust") if dx >= dy else ("sol", "sag")
        bolge = {"alt": [(x0, y0), (x1, y0), (x1, ym), (x0, ym)], "ust": [(x0, ym), (x1, ym), (x1, y1), (x0, y1)],
                 "sol": [(x0, y0), (xm, y0), (xm, y1), (x0, y1)], "sag": [(xm, y0), (x1, y0), (x1, y1), (xm, y1)]}
        return {k: (temiz(v) if k in tasiyan else []) for k, v in bolge.items()}
    if dx >= dy:
        h = dy / 2.0
        return {"alt": temiz([(x0, y0), (x1, y0), (x1 - h, ym), (x0 + h, ym)]),
                "ust": temiz([(x1, y1), (x0, y1), (x0 + h, ym), (x1 - h, ym)]),
                "sol": temiz([(x0, y1), (x0, y0), (x0 + h, ym)]),
                "sag": temiz([(x1, y0), (x1, y1), (x1 - h, ym)])}
    h = dx / 2.0
    return {"sol": temiz([(x0, y1), (x0, y0), (xm, y0 + h), (xm, y1 - h)]),
            "sag": temiz([(x1, y0), (x1, y1), (xm, y1 - h), (xm, y0 + h)]),
            "alt": temiz([(x0, y0), (x1, y0), (xm, y0 + h)]),
            "ust": temiz([(x1, y1), (x0, y1), (xm, y1 - h)])}


def poligon_alani(p):
    return 0.5 * abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))))


def _plak_yuk_katsayilari(ic):
    """Durum → döşeme alan yükü: G→g, Q→q, S→s (çatlamış kopyalar aynı), EZ → k_z·g (k_z = EZ/G oranı paketten)."""
    paket = ic["paket"]
    kz = 0.0
    if "EZ" in paket.durum:
        Gd = paket.durum.get("G" + _CATLAMIS_EK) or paket.durum.get("G")
        if Gd is not None:
            g, e = Gd["dug"].ravel(), paket.durum["EZ"]["dug"].ravel()
            nn = float(g @ g)
            kz = float(e @ g) / nn if nn > 0 else 0.0
    return kz


def panel_alanlari(ic, durum, *, katsayilar=None, nx=PLAK_IZGARA, ny=PLAK_IZGARA):
    """§16.2: [{"no", "kat", "adres", "kose": [[X, Y, Z] × 4], "izgara": {nx, ny, x, y, w, mx, my, q, D, t, E},
    "yuk_payi": [{"kiris", "eleman", "kenar", "sekil", "poligon": [[X, Y], ...], "alan"}], "tip", "not"}]."""
    _ic_kontrol(ic)
    A = ic["alan"]
    B, Y = A["B"], A.get("Y")
    dosemeler = list(getattr(Y, "dosemeler", None) or getattr(B, "dosemeler", None) or [])
    if not dosemeler:
        return []
    liste = durum_katsayilari(ic, durum, katsayilar)
    kz = _plak_yuk_katsayilari(ic)
    eksi = str(durum) == "zarf-"
    kir = {k["no"]: k for k in getattr(B, "kirisler", [])}
    kp = getattr(B, "kiris_parca", {}) or {}
    out = []
    for d in dosemeler:
        try:
            x0, x1 = B.xk[d["ix0"]], B.xk[d["ix1"]]
            y0, y1 = B.yk[d["iy0"]], B.yk[d["iy1"]]
            z = B.kat[d["kat"]]["kot"]
        except (KeyError, IndexError, AttributeError, TypeError):
            continue
        yk = {"G": d.get("g", 0.0), "Q": d.get("q_top", d.get("q", 0.0)) or 0.0, "S": d.get("s", 0.0) or 0.0}
        def p_durum(ad):
            temel = ad[:-len(_CATLAMIS_EK)] if ad.endswith(_CATLAMIS_EK) else ad
            if temel in yk:
                return float(yk[temel])
            if ad == "EZ":
                return kz * float(yk["G"])
            return 0.0
        qs = [sum(g * p_durum(a) for a, g in kat.items()) for _, kat in liste]
        q = (min(qs) if eksi else max(qs)) if len(qs) > 1 else qs[0]
        # plak rijitliği: kenar kirişlerinden birinin betonu (yoksa C30)
        E = None
        for p in d.get("paylar", []):
            k = kir.get(p.get("kiris_no"))
            m = (getattr(B, "malzemeler", {}) or {}).get((k or {}).get("malzeme")) if k else None
            if m and m.get("tur") == "beton":
                E = float(m["E"])
                break
        E = E or 32.0e6
        t = float(d.get("h") or 0.12)
        Dp = E * t ** 3 / (12.0 * (1.0 - PLAK_NU ** 2))
        pl = navier_plak(x1 - x0, y1 - y0, q, Dp, nx=nx, ny=ny)
        pol = yuk_payi_poligonlari(x0, y0, x1, y1, d.get("tip", "cift"),
                                   tasiyan=tuple(p["kenar_ad"] for p in d.get("paylar", []) if p.get("sekil") not in ("yok", None))
                                   if d.get("tip") == "tek" else None)
        paylar = []
        for p in d.get("paylar", []):
            fe = None
            par = kp.get(p.get("key"))
            if par is not None:
                fe = par[1].get("eleman")
            poli = pol.get(p.get("kenar_ad"), [])
            paylar.append({"kiris": p.get("kiris_no"), "eleman": fe, "kenar": p.get("kenar_ad"), "sekil": p.get("sekil"),
                           "poligon": [[round(a, 6), round(b, 6)] for a, b in poli], "alan": round(poligon_alani(poli), 6) if poli else 0.0})
        ls = min(x1 - x0, y1 - y0)
        mx_e, my_e, w_e = float(np.max(np.abs(pl["mx"]))), float(np.max(np.abs(pl["my"]))), float(np.max(np.abs(pl["w"])))
        qls2 = abs(q) * ls * ls
        out.append({"no": d["no"], "kat": d["kat"], "adres": d.get("adres"), "z": z, "tip": d.get("tip"),
                    "kose": [[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]],
                    "izgara": {"nx": nx, "ny": ny, "x": _yuvarla(pl["x"] + x0, 6), "y": _yuvarla(pl["y"] + y0, 6),
                               "w": _yuvarla(pl["w"]), "mx": _yuvarla(pl["mx"]), "my": _yuvarla(pl["my"]), "q": q, "D": Dp,
                               "t": t, "E": E, "nu": PLAK_NU},
                    "en_buyuk": {"w": float(f"{w_e:.5g}"), "mx": float(f"{mx_e:.5g}"), "my": float(f"{my_e:.5g}")},
                    # karşılaştırma için basit mesnetli plak katsayıları α = m / (q·l_s²) (TS 500 Denk. 11.3 biçimi m_d = α p_d l_sn²)
                    "alfa": ({"ls": ls, "x": float(f"{mx_e / qls2:.4g}"), "y": float(f"{my_e / qls2:.4g}")} if qls2 > 0 else None),
                    "yuk_payi": paylar,
                    "not": "Yaklaşık plak çözümü: dört kenar basit mesnetli (Navier serisi, ν = 0,2); sürekli kenar etkisi yok "
                           "sayılır. TS 500 md. 11.4.3 (Denk. 11.3, m_d = α·p_d·l_sn², α Çizelge 11.1) sürekli kenarlarda mesnet "
                           "momenti ve daha küçük açıklık momenti verir; buradaki α = m/(q·l_s²) dört kenarı basit mesnetli üst "
                           "sınır karşılaştırmasıdır. Kirişlere aktarım 45° yük payı bölgeleriyle (renkli poligonlar) yapılır."})
    return out


def _radye_meta(ic):
    """Temel modülü (mütemadi/radye) çözüm paketine taban basıncı metası koyduysa: (tip, k0, [(no, X, Y)], q_em)."""
    A = ic.get("alan") or {}
    B = A.get("B")
    tem = getattr(B, "temeller", None) or {}
    tip = tem.get("tip") if isinstance(tem, dict) else None
    meta = ic.get("temel")
    k0 = dug = None
    if isinstance(meta, dict) and meta.get("dugumler"):
        k0, dug = meta.get("k0"), meta["dugumler"]
    else:
        ti = (A.get("ag") or {}).get("temel")
        if ti is not None and getattr(ti, "dugumler", None):
            k0 = getattr(ti, "k0", None)
            dug = [(r["no"], r["X"], r["Y"]) for r in ti.dugumler]
    if not dug or not k0:
        return None
    q_em = ((tem.get("zemin") or {}).get("q_em")) if isinstance(tem, dict) else None
    return tip, float(k0), [(int(a), float(x), float(y)) for a, x, y in dug], q_em


def radye_alani(ic, durum, *, katsayilar=None):
    """§16.2 (c) Radye (ve mütemadi temel) Winkler taban basıncı ve oturması: temel düğümlerinde w = −u_Z, p = k0·w
    (basınç +). Radyede düğümler bir ızgaraya dizilir (eksik hücre None). Temel modülü yoksa None."""
    _ic_kontrol(ic)
    meta = _radye_meta(ic)
    if meta is None:
        return None
    tip, k0, dug, q_em = meta
    pa = alan_paketi(ic)
    liste = durum_katsayilari(ic, durum, katsayilar)
    G = _gamma_matrisi(pa, liste)
    d_idx = {no: i for i, no in enumerate(ic["paket"].dugum_no)}
    sec = [(no, X, Y) for no, X, Y in dug if no in d_idx]
    if not sec:
        return None
    uZ = np.tensordot(G, pa["DUG"][:, [d_idx[no] for no, _, _ in sec], 2], axes=(1, 0))      # (c, n)
    w = -uZ
    if len(liste) > 1:
        w = w.min(axis=0) if str(durum) == "zarf-" else w.max(axis=0)
    else:
        w = w[0]
    p = k0 * w
    xs = sorted({round(X, 6) for _, X, _ in sec})
    ys = sorted({round(Y, 6) for _, _, Y in sec})
    ix, iy = {v: i for i, v in enumerate(xs)}, {v: i for i, v in enumerate(ys)}
    W = [[None] * len(xs) for _ in ys]
    Pm = [[None] * len(xs) for _ in ys]
    for (no, X, Y), wi, pi in zip(sec, w, p):
        W[iy[round(Y, 6)]][ix[round(X, 6)]] = float(f"{wi:.5g}")
        Pm[iy[round(Y, 6)]][ix[round(X, 6)]] = float(f"{pi:.5g}")
    z = 0.0
    B = ic["alan"]["B"]
    try:
        z = float(B.kat[0]["kot"])
    except (AttributeError, KeyError, IndexError, TypeError):
        pass
    return {"tip": tip, "k0": k0, "q_em": q_em, "z": z, "x": xs, "y": ys, "w": W, "p": Pm,
            "dugumler": [{"no": no, "X": X, "Y": Y, "w": float(f"{wi:.5g}"), "p": float(f"{pi:.5g}")} for (no, X, Y), wi, pi in zip(sec, w, p)],
            "p_maks": float(np.max(p)), "p_min": float(np.min(p)), "w_maks": float(np.max(w)),
            "birim": {"w": "m", "p": "kN/m²"},
            "not": "Winkler zemini: p = k0·w (düğüm oturması w, yatak katsayısı k0); basınç +, çekme (−) zeminde oluşmaz — "
                   "negatif değer temelin kalktığını gösterir (doğrusal modelde gösterim)."}


# ============================================================================
# Eleman bilgi paneli için ortak yardımcılar (köprü bina_eleman_bilgi)
# ============================================================================
def fe_elemanlari(ic, tur, no):
    """Bina elemanı (tur: 'kolon' | 'kiris' | 'fe', no) → FE eleman kayıtları (ağ sırasıyla; kiriş parçaları dahil)."""
    _ic_kontrol(ic)
    ag = ic["alan"]["ag"]
    tur = str(tur or "").lower()
    try:
        no_i = int(no)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"Eleman numarası (no) tamsayı olmalı: {no!r}.") from None
    if tur in ("fe", "eleman", "cubuk"):
        sec = [e for e in ag["elemanlar"] if e["no"] == no_i]
    else:
        sec = [e for e in ag["elemanlar"] if e.get("tur") == tur and e.get("kaynak_no") == no_i]
    if not sec:
        raise MatrisHatasi(f"{tur or 'eleman'} {no} bu çözümün ağında yok.")
    return sec


def eleman_kaydi(ic, fe_no):
    """FE eleman no → sabit bilgiler: uç düğümleri ve koordinatları, L, yerel eksenler, kesit (yerel), malzeme, kaynak."""
    pa = alan_paketi(ic)
    i = pa["fe_idx"].get(int(fe_no))
    if i is None:
        raise MatrisHatasi(f"FE eleman {fe_no} bu çözümde yok.")
    el = pa["elemanlar"][i]
    return {k: v for k, v in el.items() if k not in ("lam", "x", "tasarim")} | {"x": [float(v) for v in el["x"]]}


def istasyon_kuvvetleri(ic, fe_no, durum, katsayilar=None):
    """FE eleman, durum/kombinasyon/zarf → {"x", "N", "Vy", "Vz", "T", "My", "Mz", "u", ...} (eleman_alanlari kaydı)."""
    al = eleman_alanlari(ic, durum, katsayilar=katsayilar, elemanlar=[int(fe_no)], paneller=False)
    if not al["elemanlar"]:
        raise MatrisHatasi(f"FE eleman {fe_no} bu çözümde yok.")
    return al["elemanlar"][0]


def uc_yer_degistirmeleri(ic, fe_no, durum, katsayilar=None):
    """FE eleman uçlarında düğüm yer değiştirme/dönmeleri: bina global ve yerel (x′, y′, z′) bileşenler."""
    pa = alan_paketi(ic)
    i = pa["fe_idx"].get(int(fe_no))
    if i is None:
        raise MatrisHatasi(f"FE eleman {fe_no} bu çözümde yok.")
    el = pa["elemanlar"][i]
    liste = durum_katsayilari(ic, durum, katsayilar)
    if len(liste) != 1:
        raise MatrisHatasi("Uç yer değiştirmeleri tek bir durum ya da kombinasyon için verilir (zarf değil).")
    G = _gamma_matrisi(pa, liste)[0]
    D = np.tensordot(G, pa["DUG"], axes=(0, 0))
    d_idx = {no: k for k, no in enumerate(ic["paket"].dugum_no)}
    lam = el["lam"]
    out = {}
    for uc, dn in zip(("i", "j"), el["dugumler"]):
        v = D[d_idx[dn]]
        out[uc] = {"dugum": dn, "u": [float(a) for a in v[:3]], "r": [float(a) for a in v[3:]],
                   "u_yerel": [float(a) for a in lam @ v[:3]], "r_yerel": [float(a) for a in lam @ v[3:]]}
    return out


def eleman_bilgi_alani(ic, tur, no, durum, *, katsayilar=None, istasyon=ISTASYON):
    """Bina elemanı (kolon / kiriş: bütün FE parçaları; 'fe': tek FE eleman) için alan özeti (bilgi paneli,
    ``bina_eleman_bilgi``): {"tur", "no", "durum", "fe": [no], "parcalar": [eleman_alanlari kaydı], "uclar": [uç yer
    değiştirmeleri] (zarfta None), "en_buyuk": {büyüklük: {deger, fe, x}}}."""
    fe = [e["no"] for e in fe_elemanlari(ic, tur, no)]
    al = eleman_alanlari(ic, durum, katsayilar=katsayilar, elemanlar=fe, paneller=False, istasyon=istasyon)
    zarf = str(durum).startswith("zarf")
    en = {}
    for kay in al["elemanlar"]:
        for ad, ek in (kay.get("ekstremum") or {}).items():
            if ek and (ad not in en or abs(ek["deger"]) > abs(en[ad]["deger"])):
                en[ad] = {"deger": ek["deger"], "x": ek["x"], "fe": kay["no"]}
    return {"tur": tur, "no": no, "durum": al["durum"], "fe": fe, "parcalar": al["elemanlar"], "birim": al["birim"],
            "uclar": None if zarf else [uc_yer_degistirmeleri(ic, f, durum, katsayilar) for f in fe],
            "en_buyuk": en, "not": al.get("not"), "isaret": ISARET}


def lif_gerilmesi(kesit, N, My, Mz, y, z):
    """Doğrusal elastik lif gerilmesi (MPa, çekme +): σ = N/A − Mz·y/Iz − My·z/Iy; y, z yerel (m), kesit ağırlık merkezinden.
    Mz > 0 alt (−y′) lifi, My > 0 −z′ lifini çeker (motorun işaret kuralı; testle kilitli). İstemci (isi_haritasi.js)
    aynı formülü kullanır."""
    A, Iy, Iz = float(kesit["A"]), float(kesit["Iy"]), float(kesit["Iz"])
    return (N / A - Mz * np.asarray(y, dtype=float) / Iz - My * np.asarray(z, dtype=float) / Iy) / 1000.0
