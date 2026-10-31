# -*- coding: utf-8 -*-
"""Sonlu eleman modülü (Matris Öğren): yay, çubuk, kafes, kiriş ve çerçeve modellerini adım adım çözer.

Kullanım::

    import sonlu_eleman as se
    r = se.se_coz(se.ornek_model("kafes-iki-cubuk"))   # sözlük ya da JSON metni
    r.deger          # u: global yer değiştirme vektörü (sympy Matrix; SD sırasıyla)
    r.veri           # yapılı sonuçlar (aşağıya bakın)
    r.anlatim        # adım adım anlatım (matris_ogren.Anlatim): md / math / sema / kod blokları
    r.python_kodu, r.python_ciktisi

Genel işlevler: ``se_coz(model, *, goster=None, anlat=True)``, ``coz_coklu(model, durumlar, *, diyagram_nokta=11)``
(çok yük durumu, anlatımsız; aşağıya bakın), ``coz_yalniz_cekme(model, durumlar, *, en_fazla_yineleme=10)``
(yalnız çekme çubuklu doğrusal olmayan çözüm), ``ornek_model(ad)``, ``ornek_listesi()``,
``ORNEK_MODELLER`` (yalnız sabit değerlerden oluşan sözlük).

Model şeması (sayılar sayı ya da metin olabilir: "200e6", "1/3", "E", "P" ...; koordinatlar sayı olmalıdır)::

    {"tip": "yay" | "cubuk" | "kafes" | "kiris" | "cerceve" | "kafes3b" | "cerceve3b",
     "baslik": "...", "birim": {"kuvvet": "kN", "uzunluk": "m"},
     "dugumler":  [{"no": 1, "x": 0, "y": 0, "z": 0}],
     "elemanlar": [{"no": 1, "dugumler": [1, 3], "E": "200e6", "A": "0.001", "I": "8e-6", "k": "1000",
                    "G": "80e6", "Iy": "1e-4", "Iz": "1e-4", "J": "2e-4", "zemin": "20000"}],
     "mesnetler": [{"dugum": 1, "ux": true, "uy": true, "rz": false}],
     "yukler":    [{"dugum": 3, "Fx": 0, "Fy": -10, "M": 0}],
     "yayili":    [{"eleman": 1, "q": -12, "qz": 0},
                   {"eleman": 2, "q1": 0, "q2": -12, "x1": 0, "x2": 4, "qz1": 0, "qz2": 0}],
     "yaylar":    [{"dugum": 1, "kx": 0, "ky": "50000", "kr": "20000"}],
     "cokmeler":  [{"dugum": 4, "uy": "-0.01"}],
     "diyaframlar": [{"ad": "Kat 1", "dugumler": [5, 6, 7, 8], "ana": {"no": 9001, "x": 2.5, "y": 3, "z": 2}}],
     "hesap":     "sayisal"}      # isteğe bağlı: SD ≤ 12 olsa da numpy (ondalık) kipini zorlar

* Düğüm başına SD: yay/çubuk 1 (u), kafes 2 (u, v), kiriş 2 (v, θ), çerçeve 3 (u, v, θ),
  uzay kafes (kafes3b) 3 (u, v, w), uzay çerçeve (cerceve3b) 6 (u, v, w, θx, θy, θz).
  Global SD numarası, "dugumler" listesindeki sıraya göre verilir: i. sıradaki düğüm
  d·(i-1)+1 … d·i numaralarını alır (SD etiketi u₁, v₁, θ₁ ... düğüm "no" değerini kullanır).
* Gerekli özellikler: yay → k; çubuk, kafes, kafes3b → E, A; kiriş → E, I; çerçeve → E, A, I;
  cerceve3b → E, G, A, Iy, Iz, J. Kiriş ve çerçeve elemanında isteğe bağlı ``zemin``: Winkler zemin
  yatak katsayısı k_s (kN/m²; birim boya düşen yay rijitliği), elastik zemine oturan temel kirişi için.
* Yay/çubuk modelinde yalnız x kullanılır (y yoksayılır); kirişte tüm düğümler aynı yatay doğruda olmalıdır.
  3 boyutlu türlerde z koordinatı da okunur (verilmezse 0). X sağa, Y yukarı, Z düzlemden dışa (sağ el).
* Mesnet bayrakları: yay/çubuk ux; kafes ux, uy; kiriş uy (çökme v), rz (dönme θ); çerçeve ux, uy, rz;
  kafes3b ux, uy, uz; cerceve3b ux, uy, uz, rx, ry, rz. Eksik bayrak = serbest.
  Yükler: yay/çubuk Fx; kafes Fx, Fy; kiriş Fy, M; çerçeve Fx, Fy, M; kafes3b Fx, Fy, Fz;
  cerceve3b Fx, Fy, Fz, Mx, My, Mz.
* ``yayili``: eleman yerel y yönünde yayılı yük (yerel y = eleman ekseninin 90° saat yönünün tersi;
  kiriş ve çerçeve için; + = yerel y yönü). Yatay, soldan sağa giden elemanda q < 0 aşağı doğrudur.
  Uzay çerçevede q yerel y, ``qz`` yerel z yönündedir. İki kayıt biçimi: düzgün ``q`` (bütün açıklık) ya da
  **parçalı doğrusal** ``q1, q2, x1, x2``: yük x1'de q1, x2'de q2 değerini alır ve arada doğrusal değişir
  (üçgen, trapez ya da kısmi açıklık); x1, x2 elemanın ilk düğümünden eleman ekseni boyunca ölçülür, sayı olmalıdır
  ve 0 ≤ x1 < x2 ≤ L (x1 verilmezse 0, x2 verilmezse L). Uzay çerçevede z′ için ``qz1, qz2`` (aynı x1, x2).
  Aynı elemana birden çok kayıt üst üste toplanır. Eşdeğer düğüm yükleri her parça için 3 noktalı Gauss–Legendre ile
  (Hermite kübik × doğrusal yük 4. derece: kesin) alınır; V ve M diyagramları parça başına kapalı formdur.
  **Eksenel (yerel x′) yayılı yük** (çerçeve, uzay çerçeve): ``qx`` ya da ``qx1, qx2`` (aynı x1, x2; + = x′ yönü, i → j).
  Eşdeğer yük doğrusal şekil fonksiyonlarıyla kapalı form (f_x,i = W − S/L, f_x,j = S/L); N(x) = N_i − ∫₀ˣ q_x ds.
  **Global yönlü yük**: ``"yon": "gx" | "gy" | "gz"`` (MOTOR eksenleri: gx sağa, gy yukarı, gz düzlemden dışa; bina
  eksenleri X, Y, Z (Z yukarı) değildir, yapı modülü çevirir). Şiddet ``q`` ya da ``q1, q2`` (+ = eksen yönü; öz ağırlık
  için "gy" ile q < 0) eleman boyu başınadır ve λ ile yerel x′, y′, z′ bileşenlerine ayrılır: q_yerel = q·λ·ĝ.
  ``"izdusum": true`` ise q, elemanın yük doğrultusuna dik düzleme izdüşüm boyu L_p = L·√(1 − (x̂′·ĝ)²) başınadır
  (izdüşüm boyu kuralı; düşey yükte yatay izdüşüm, kar/hareketli yük): eleman boyu başına şiddet q·L_p/L = q·cos θ
  (θ elemanın yatayla açısı), toplam yük q·L_p. Düzlem modelde "gz" ve kirişte "gx" (eksenel) kullanılamaz.
* Uç serbestlikleri (``serbest``; kiriş, çerçeve, uzay çerçeve elemanında): ``{"i": [...], "j": [...]}`` yerel iç kuvvet
  adları — uzay çerçeve "N", "Vy", "Vz", "T", "My", "Mz"; düzlem çerçeve "N", "V", "M"; kiriş "V", "M". Mafsal = My + Mz
  (2B'de M). Eleman düzeyinde statik yoğunlaştırma: k* = k_ff − k_fr k_rr⁻¹ k_rf, f*_eq = f_f − k_fr k_rr⁻¹ f_r; çözümden
  sonra d_r = k_rr⁻¹ (f_r − k_rf d_f) geri kazanılır ve uç kuvvetleri tam elemanla f = k d − f_eq (serbest uçta o bileşen 0).
  Kesin (sympy) kipte de çalışır. Bir düğümde bütün elemanlar aynı dönmeyi serbest bırakırsa ve mesnet/yay yoksa K tekildir
  (mekanizma hatası, ipucuyla); k_rr tekilse (iki uçta N ya da T) eleman kendi içinde kararsızdır (öğretici hata).
* Uzay çerçeve elemanında ``aci`` (derece; yerel eksen açısı): y′, z′ eksenleri x′ etrafında sağ el kuralıyla
  döndürülür (x′ izleyiciye bakarken saat yönünün tersine +): y″ = cos a·y′ + sin a·z′, z″ = −sin a·y′ + cos a·z′.
  aci = 90 → y″ = z′, z″ = −y′; I_y ile I_z'yi takas etmekle aynı global rijitlik. Öteki türlerde ``aci`` yok sayılır.
* ``yalniz_cekme: true`` (kafes, kafes3b, cerceve, cerceve3b): se_coz ve coz_coklu bu çubukları etkin sayar
  (doğrusal ön çözüm, uyarıyla); basınçta devre dışı bırakan yinelemeli çözüm ``coz_yalniz_cekme`` ile yapılır.
* Aynı konumdaki iki düğümü bağlayan eleman (uzaklık ≤ 1e-6 model birimi) sıfır boylu eleman hatası verir.
* ``yaylar`` (elastik mesnet / zemin yayı): düğüme bağlı öteleme ve dönme yayları; anahtarlar mesnet bayraklarının
  yay karşılığıdır (kx, ky, kz, kr; 3B çerçevede krx, kry, krz). Rijitlik K'nın köşegenine eklenir.
* ``cokmeler`` (mesnet çökmesi / verilen yer değiştirme): ilgili SD tutulu sayılır ve değeri sıfır yerine verilen
  değer olur; çözüm K_ff u_f = F_f − K_fs u_s ile yapılır.
* ``diyaframlar`` (yalnız cerceve3b; rijit kat diyaframı, efendi–köle bağı): ``dugumler`` aynı kottaki (y) köle düğümler,
  ``ana`` efendi düğüm: var olan bir düğümün numarası ya da yeni (sanal) bir düğüm sözlüğü ``{"no", "x", "z"[, "y"]}``
  (düğüm listesinin sonuna eklenir; SD numaraları değişmez). Döşeme yatay x–z düzleminde rijittir: köle s, efendi m için
  u_s = u_m + θy_m (z_s − z_m), w_s = w_m − θy_m (x_s − x_m), θy_s = θy_m (sağ el: ω × r); v, θx, θz köle düğümde
  bağımsız kalır. Sanal efendinin v, θx, θz serbestlikleri sıfır alınır (yük, mesnet ya da çökme verilemez). Çözüm
  indirgenmiş sistemde (K_r = Tᵀ K T, F_r = Tᵀ F, u = T u_r; mesnetler ve mekanizma denetimi indirgenmiş SD'lerde),
  yalnız sayısal kip. Köle düğümün ux, uz, ry serbestliklerine mesnet/çökme verilemez (efendiye verin); yaylar her SD'de
  kullanılabilir. Diyaframın köle düğüme uyguladığı iç kuvvetler ``veri["diyafram_kuvvetleri"]`` içinde (tepki değildir).
* Birimler kN ve m'dir (E: kN/m², A: m², I: m⁴). X sağa, Y yukarı, dönme ve moment saat yönünün tersi (+).
* Uzay çerçevede eleman yerel eksenleri: x' eleman boyunca; y' elemanı içeren düşey düzlemde yukarı doğru;
  z' = x' × y' (yatay). Düşey elemanda z' = Z alınır (Kassimali kuralı). Düzlemde (z = 0) soldan sağa tanımlı
  elemanlarda bu kural 2B çerçeveyle aynı yerel eksenleri verir.

Hesap modu: toplam SD ≤ 12 ise "kesin" (sympy, kesirli/sembolik; E, A, P ... harf olabilir),
daha büyükse "sayisal" (numpy, ondalık; harfli girdi öğretici hata verir). ``"hesap": "sayisal"`` anahtarı küçük
modelde de sayısal kipi zorlar. Eleman kayıtlarındaki bilinmeyen alanlar (``kaynak``, ``yardimci``, ``tur``, ``grup``, ``kat``,
``Lb``, ``K`` ...; uzay çerçeve dışında ``aci``) yok sayılır.

``coz_coklu(model, durumlar)``: aynı modeli birden çok yük durumu için çözer; modeldeki ``yukler``/``yayili``
yoksayılır, her durum ``{"yukler": [...], "yayili": [...]}`` biçimindedir; K bir kez kurulur, bütün sağ taraflar tek
``np.linalg.solve`` ile çözülür; dönüş ``{ad: kisa}`` (anlatımsız, motor koordinatında; ayrıntı işlevin belgesinde).

``Sonuc.veri`` sözlüğünün anahtarları (sayılar JSON'a uygun ``float``; sembolik çözümde sayı yerine ifade metni)::

    tip, baslik, birim {"kuvvet", "uzunluk"}, mod ("kesin" | "sayisal"), sd_sayisi, sd_etiketleri [str],
    serbest_sd (bilinmeyen sayısı; diyafram varsa indirgenmiş sistemde), boyut (2 | 3),
    dugumler  [{no, x, y, z, sd [global SD numaraları, 1'den], u [bu düğümün yer değiştirmeleri], sanal (diyafram efendisi)}],
    diyaframlar [{ad, ana (efendi düğüm no), sanal, dugumler [köle no]}],
    diyafram_kuvvetleri [{dugum, diyafram, Fx, Fz, My}],   # diyaframın köle düğüme uyguladığı iç kuvvet
    elemanlar [{no, dugumler [i, j], L, c, s, uc_kuvvetleri [yerel uç kuvvetleri, SE işaretiyle],
                N (çekme +), durum ("çekme" | "basınç" | "sıfır" | "eğilme"), zemin (k_s ya da None),
                zemin_kuvvetleri (zeminin düğümlere aktarılmış global kuvvetleri, 4 ya da 6 bileşen; zemin yoksa None),
                yon [cx, cy, cz] ve lam [[...]] (yalnız 3B: doğrultu kosinüsleri ve yerel eksen matrisi),
                yayili [{q1, q2, x1, x2}] (kiriş/çerçeve: yerel y′ yük parçaları; cerceve3b'de ayrıca yayili_z;
                çerçevelerde yayili_x: eksenel x′ parçaları; global yönlü yük yerel bileşenleriyle yazılır),
                serbest {i: [ad], j: [ad]} (kiriş/çerçeve), aci (cerceve3b, derece), yalniz_cekme (kafes/çerçeve),
                diyagram {x [yerel konum], N, V, M [aynı uzunlukta listeler]; cerceve3b'de ayrıca Vz, My, T}}],
    tepkiler  [{dugum, Fx, Fy, M}] (3B'de {dugum, Fx, Fy, Fz, Mx, My, Mz}),   # yalnız mesnetli düğümler
    yaylar    [{dugum, sd (etiket), bilesen (Fx|Fy|Fz|M|Mx|My|Mz), k, kuvvet}],  # yay kuvvetleri (yayın yapıya uyguladığı)
    cokmeler  [{dugum, sd, deger}],            # verilen yer değiştirmeler
    u [n], F [n],                              # global yer değiştirme ve (eşdeğer düğüm yükleriyle) yük vektörü
    denge {Fx, Fy, M} (3B'de {Fx, Fy, Fz, Mx, My, Mz}),   # dış kuvvet + tepki (+ yay, zemin) toplamı kalıntıları (≈ 0)
    olcek (şekil değiştirmiş biçim çizim ölçeği ya da None), K (n ≤ 60 ise yaylar dahil, mesnetsiz K; iç içe liste),
    uyarilar [metin] (anlatımdaki uyarılar: birim, z, yalnız-çekme doğrusal ön çözüm ...).
"""
from __future__ import annotations

import contextlib
import copy
import functools
import html as _html
import io
import json
import math
import re
import sys
import warnings
from types import SimpleNamespace

import sympy as sp

import matris_ogren as mo

try:  # numpy Pyodide ve Colab'da hazırdır; yoksa yalnız kesin mod çalışır
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

__version__ = "0.2.0"

MatrisHatasi = mo.MatrisHatasi
SD_ESIK = 12   # toplam SD bu sayıyı aşarsa hesap sayısal (numpy) yapılır

# 3B çizimlerin bakış açısı: Y ekseni etrafında dönme (derece) ve yukarıdan eğim (derece)
BAKIS_FI = -32.0
BAKIS_PSI = 22.0


# ============================================================================
# Örnek modeller (yalnız sabit değerler: ast.literal_eval ile okunabilir)
# ============================================================================
ORNEK_MODELLER = {
    "yay-seri": {
        "tip": "yay",
        "baslik": "Seri bağlı iki yay",
        "aciklama": "Soldaki ucu sabit, seri bağlı iki yayın serbest ucuna 10 kN çekme uygulanır; her yayın uzaması P/k ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 1, "y": 0},
            {"no": 3, "x": 2, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "k": "1000"},
            {"no": 2, "dugumler": [2, 3], "k": "2000"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True}],
        "yukler": [{"dugum": 3, "Fx": 10}],
    },
    "cubuk-kademeli": {
        "tip": "cubuk",
        "baslik": "Kademeli kesitli eksenel çubuk",
        "aciklama": "Kesit alanı yarıya düşen iki parçalı çubuk, serbest ucundan 100 kN çekilir; her parçanın uzaması PL/EA ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 1, "y": 0},
            {"no": 3, "x": 2, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.002"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True}],
        "yukler": [{"dugum": 3, "Fx": 100}],
    },
    "kafes-iki-cubuk": {
        "tip": "kafes",
        "baslik": "İki çubuklu kafes (üçgen)",
        "aciklama": "6 m açıklıklı, 4 m yüksekliğindeki iki çubuklu kafesin tepe düğümüne 10 kN aşağı yük gelir; iki çubuk da basınç çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 6, "y": 0},
            {"no": 3, "x": 3, "y": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 3], "E": "200e6", "A": "0.001"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 2, "ux": True, "uy": True},
        ],
        "yukler": [{"dugum": 3, "Fy": -10}],
    },
    "kafes-uc-cubuk": {
        "tip": "kafes",
        "baslik": "Üç çubuklu hiperstatik kafes",
        "aciklama": "Tek serbest düğüme üç mafsallı çubuk bağlıdır; bir çubuk fazla olduğundan denge denklemleri yetmez, rijitlik yöntemi çözer.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
            {"no": 4, "x": 3, "y": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 4], "E": "200e6", "A": "0.001"},
            {"no": 2, "dugumler": [2, 4], "E": "200e6", "A": "0.002"},
            {"no": 3, "dugumler": [3, 4], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 2, "ux": True, "uy": True},
            {"dugum": 3, "ux": True, "uy": True},
        ],
        "yukler": [{"dugum": 4, "Fx": 10, "Fy": -20}],
    },
    "kafes-pratt-kopru": {
        "tip": "kafes",
        "baslik": "Pratt kafes köprü",
        "aciklama": "12 m açıklıklı Pratt kafes köprünün üç alt düğümüne 10 kN düşey yük gelir; üst başlık basınç, alt başlık çekme çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
            {"no": 4, "x": 9, "y": 0},
            {"no": 5, "x": 12, "y": 0},
            {"no": 6, "x": 3, "y": 3},
            {"no": 7, "x": 6, "y": 3},
            {"no": 8, "x": 9, "y": 3},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.002"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.002"},
            {"no": 3, "dugumler": [3, 4], "E": "200e6", "A": "0.002"},
            {"no": 4, "dugumler": [4, 5], "E": "200e6", "A": "0.002"},
            {"no": 5, "dugumler": [6, 7], "E": "200e6", "A": "0.002"},
            {"no": 6, "dugumler": [7, 8], "E": "200e6", "A": "0.002"},
            {"no": 7, "dugumler": [1, 6], "E": "200e6", "A": "0.002"},
            {"no": 8, "dugumler": [5, 8], "E": "200e6", "A": "0.002"},
            {"no": 9, "dugumler": [2, 6], "E": "200e6", "A": "0.002"},
            {"no": 10, "dugumler": [3, 7], "E": "200e6", "A": "0.002"},
            {"no": 11, "dugumler": [4, 8], "E": "200e6", "A": "0.002"},
            {"no": 12, "dugumler": [6, 3], "E": "200e6", "A": "0.002"},
            {"no": 13, "dugumler": [8, 3], "E": "200e6", "A": "0.002"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 5, "uy": True},
        ],
        "yukler": [
            {"dugum": 2, "Fy": -10},
            {"dugum": 3, "Fy": -10},
            {"dugum": 4, "Fy": -10},
        ],
    },
    "kiris-konsol": {
        "tip": "kiris",
        "baslik": "Ucundan yüklü konsol kiriş",
        "aciklama": "3 m boyundaki ankastre konsolun serbest ucuna 10 kN aşağı yük gelir; uç çökmesi PL³/3EI, uç dönmesi PL²/2EI ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "8e-6"},
        ],
        "mesnetler": [{"dugum": 1, "uy": True, "rz": True}],
        "yukler": [{"dugum": 2, "Fy": -10}],
    },
    "kiris-basit-yayili": {
        "tip": "kiris",
        "baslik": "Yayılı yüklü basit kiriş",
        "aciklama": "6 m açıklıklı basit kiriş iki elemana bölünmüş ve 12 kN/m düzgün yayılı yük taşır; orta çökme 5qL⁴/384EI'dir.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "I": "2e-5"},
        ],
        "mesnetler": [
            {"dugum": 1, "uy": True},
            {"dugum": 3, "uy": True},
        ],
        "yayili": [
            {"eleman": 1, "q": -12},
            {"eleman": 2, "q": -12},
        ],
    },
    "kiris-ankastre-mafsalli": {
        "tip": "kiris",
        "baslik": "Bir ucu ankastre, bir ucu kayıcı kiriş",
        "aciklama": "4 m'lik tek elemanlı kiriş, sol ucu ankastre sağ ucu kayıcı mesnetli; 10 kN/m yayılı yükte hiperstatiktir (kayıcı tepkisi 3qL/8).",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 4, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"},
        ],
        "mesnetler": [
            {"dugum": 1, "uy": True, "rz": True},
            {"dugum": 2, "uy": True},
        ],
        "yayili": [{"eleman": 1, "q": -10}],
    },
    "kiris-elastik-zemin": {
        "tip": "kiris",
        "baslik": "Elastik zemine oturan temel kirişi (Winkler)",
        "aciklama": "8 m'lik betonarme sürekli temel kirişi zemin yayları (yatak katsayısı k_s = 20 000 kN/m²) üzerinde durur; "
                    "ortadaki kolondan 500 kN gelir. Mesnet yoktur: yükü zemin yayları taşır, kiriş zemine gömülerek dengelenir.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 1, "y": 0},
            {"no": 3, "x": 2, "y": 0},
            {"no": 4, "x": 3, "y": 0},
            {"no": 5, "x": 4, "y": 0},
            {"no": 6, "x": 5, "y": 0},
            {"no": 7, "x": 6, "y": 0},
            {"no": 8, "x": 7, "y": 0},
            {"no": 9, "x": 8, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 2, "dugumler": [2, 3], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 3, "dugumler": [3, 4], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 4, "dugumler": [4, 5], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 5, "dugumler": [5, 6], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 6, "dugumler": [6, 7], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 7, "dugumler": [7, 8], "E": "3e7", "I": "0.0072", "zemin": "20000"},
            {"no": 8, "dugumler": [8, 9], "E": "3e7", "I": "0.0072", "zemin": "20000"},
        ],
        "mesnetler": [],
        "yukler": [{"dugum": 5, "Fy": -500}],
    },
    "cerceve-konsol-kolon": {
        "tip": "cerceve",
        "baslik": "Yatay yüklü konsol kolon",
        "aciklama": "3 m'lik ankastre kolonun üst ucuna 10 kN yatay yük gelir; çerçeve elemanı hem eksenel hem eğilme rijitliğini birlikte taşır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 3},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "8e-6"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "rz": True}],
        "yukler": [{"dugum": 2, "Fx": 10}],
    },
    "cerceve-portal": {
        "tip": "cerceve",
        "baslik": "Portal çerçeve",
        "aciklama": "Ankastre tabanlı 6 m açıklıklı, 4 m yüksekliğindeki portal çerçeve; kirişte 10 kN/m yayılı yük, sol üst köşede 20 kN yatay yük vardır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 4},
            {"no": 3, "x": 6, "y": 4},
            {"no": 4, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "1e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.01", "I": "2e-4"},
            {"no": 3, "dugumler": [4, 3], "E": "200e6", "A": "0.01", "I": "1e-4"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "rz": True},
            {"dugum": 4, "ux": True, "uy": True, "rz": True},
        ],
        "yukler": [{"dugum": 2, "Fx": 20}],
        "yayili": [{"eleman": 2, "q": -10}],
    },
    "cerceve-iki-katli": {
        "tip": "cerceve",
        "baslik": "İki katlı betonarme çerçeve (kolon–kiriş sistemi)",
        "aciklama": "5 m açıklıklı, 3 + 3 m yüksekliğinde iki katlı çerçeve: 30×30 kolonlar, 25×50 kirişler, ankastre temeller. "
                    "Kat kirişlerinde 25 ve 15 kN/m düşey yayılı yük, kat düzeylerinde 20 ve 30 kN yatay (deprem benzeri) yük vardır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 3},
            {"no": 3, "x": 0, "y": 6},
            {"no": 4, "x": 5, "y": 0},
            {"no": 5, "x": 5, "y": 3},
            {"no": 6, "x": 5, "y": 6},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "3e7", "A": "0.09", "I": "6.75e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "3e7", "A": "0.09", "I": "6.75e-4"},
            {"no": 3, "dugumler": [4, 5], "E": "3e7", "A": "0.09", "I": "6.75e-4"},
            {"no": 4, "dugumler": [5, 6], "E": "3e7", "A": "0.09", "I": "6.75e-4"},
            {"no": 5, "dugumler": [2, 5], "E": "3e7", "A": "0.125", "I": "2.6e-3"},
            {"no": 6, "dugumler": [3, 6], "E": "3e7", "A": "0.125", "I": "2.6e-3"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "rz": True},
            {"dugum": 4, "ux": True, "uy": True, "rz": True},
        ],
        "yukler": [
            {"dugum": 2, "Fx": 20},
            {"dugum": 3, "Fx": 30},
        ],
        "yayili": [
            {"eleman": 5, "q": -25},
            {"eleman": 6, "q": -15},
        ],
    },
    "cerceve-elastik-mesnet": {
        "tip": "cerceve",
        "baslik": "Zemin yaylarına (elastik mesnet) oturan portal çerçeve",
        "aciklama": "Portal çerçevenin temelleri ankastre değil, zemini temsil eden yaylara oturur: her temelde yatay (kx), düşey (ky) "
                    "ve dönme (kr) yayı. Yay rijitlikleri K matrisinin köşegenine eklenir; temel dönünce kolon momentleri azalır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 4},
            {"no": 3, "x": 6, "y": 4},
            {"no": 4, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "1e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.01", "I": "2e-4"},
            {"no": 3, "dugumler": [4, 3], "E": "200e6", "A": "0.01", "I": "1e-4"},
        ],
        "mesnetler": [],
        "yaylar": [
            {"dugum": 1, "kx": "20000", "ky": "100000", "kr": "30000"},
            {"dugum": 4, "kx": "20000", "ky": "100000", "kr": "30000"},
        ],
        "yukler": [{"dugum": 2, "Fx": 20}],
        "yayili": [{"eleman": 2, "q": -10}],
    },
    "cerceve-mesnet-cokmesi": {
        "tip": "cerceve",
        "baslik": "Farklı temel oturması: sağ mesnedi 10 mm çöken portal çerçeve",
        "aciklama": "Portal çerçevenin sağ ankastre temeli 10 mm çöker (verilen yer değiştirme u_s = −0,01 m); kirişte 10 kN/m "
                    "yayılı yük de vardır. Çökme sağ tarafa K_fs·u_s olarak taşınır ve hiperstatik çerçevede ek iç kuvvet doğurur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 4},
            {"no": 3, "x": 6, "y": 4},
            {"no": 4, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "1e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.01", "I": "2e-4"},
            {"no": 3, "dugumler": [4, 3], "E": "200e6", "A": "0.01", "I": "1e-4"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "rz": True},
            {"dugum": 4, "ux": True, "uy": True, "rz": True},
        ],
        "cokmeler": [{"dugum": 4, "uy": "-0.01"}],
        "yukler": [],
        "yayili": [{"eleman": 2, "q": -10}],
    },
    "cerceve-temel-kirisi": {
        "tip": "cerceve",
        "baslik": "Sürekli temel kirişine oturan çerçeve (kolon–kiriş–temel sistemi)",
        "aciklama": "6 m açıklıklı tek katlı çerçeve, her iki yana 1 m taşan 8 m'lik sürekli temel kirişine oturur; temel kirişi Winkler "
                    "zemin yayları (k_s = 30 000 kN/m²) üzerindedir. Düşey yükü zemin taşır; yalnız düğüm 2'de yatay kayma tutulmuştur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": -1, "y": 0},
            {"no": 2, "x": 0, "y": 0},
            {"no": 3, "x": 3, "y": 0},
            {"no": 4, "x": 6, "y": 0},
            {"no": 5, "x": 7, "y": 0},
            {"no": 6, "x": 0, "y": 4},
            {"no": 7, "x": 6, "y": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "3e7", "A": "0.4", "I": "0.0171", "zemin": "30000"},
            {"no": 2, "dugumler": [2, 3], "E": "3e7", "A": "0.4", "I": "0.0171", "zemin": "30000"},
            {"no": 3, "dugumler": [3, 4], "E": "3e7", "A": "0.4", "I": "0.0171", "zemin": "30000"},
            {"no": 4, "dugumler": [4, 5], "E": "3e7", "A": "0.4", "I": "0.0171", "zemin": "30000"},
            {"no": 5, "dugumler": [2, 6], "E": "3e7", "A": "0.16", "I": "2.13e-3"},
            {"no": 6, "dugumler": [4, 7], "E": "3e7", "A": "0.16", "I": "2.13e-3"},
            {"no": 7, "dugumler": [6, 7], "E": "3e7", "A": "0.1", "I": "1.33e-3"},
        ],
        "mesnetler": [{"dugum": 2, "ux": True}],
        "yukler": [{"dugum": 6, "Fx": 15}],
        "yayili": [{"eleman": 7, "q": -30}],
    },
    "kafes3b-tripod": {
        "tip": "kafes3b",
        "baslik": "Üç ayaklı uzay kafes (tripod)",
        "aciklama": "Üç çubuk, tabandaki üç mafsallı mesnetten 3 m yükseklikteki tepe düğümünde birleşir; tepeye üç eksende de yük gelir. "
                    "Her çubuk 5 m'dir; statikçe belirli olduğundan çubuk kuvvetleri tek düğümün dengesinden de bulunabilir.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 4, "y": 0, "z": 0},
            {"no": 2, "x": 0, "y": 0, "z": 4},
            {"no": 3, "x": -4, "y": 0, "z": 0},
            {"no": 4, "x": 0, "y": 3, "z": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 4], "E": "200e6", "A": "0.001"},
            {"no": 2, "dugumler": [2, 4], "E": "200e6", "A": "0.001"},
            {"no": 3, "dugumler": [3, 4], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "uz": True},
            {"dugum": 2, "ux": True, "uy": True, "uz": True},
            {"dugum": 3, "ux": True, "uy": True, "uz": True},
        ],
        "yukler": [{"dugum": 4, "Fx": 10, "Fy": -30, "Fz": 5}],
    },
    "kafes3b-kule": {
        "tip": "kafes3b",
        "baslik": "Daralan kafes kule (uzay kafes)",
        "aciklama": "Tabanı 2×2 m, tepesi 1,2×1,2 m olan 3 m yüksekliğinde dört ayaklı kafes kule: ayaklar, tepe çerçevesi, her yüzde "
                    "bir diyagonal ve tepede bir düzlem diyagonali. Tepeye 4×20 kN düşey, rüzgâr yönünde 2×10 kN yatay yük gelir.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": -1, "y": 0, "z": -1},
            {"no": 2, "x": 1, "y": 0, "z": -1},
            {"no": 3, "x": 1, "y": 0, "z": 1},
            {"no": 4, "x": -1, "y": 0, "z": 1},
            {"no": 5, "x": -0.6, "y": 3, "z": -0.6},
            {"no": 6, "x": 0.6, "y": 3, "z": -0.6},
            {"no": 7, "x": 0.6, "y": 3, "z": 0.6},
            {"no": 8, "x": -0.6, "y": 3, "z": 0.6},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 5], "E": "200e6", "A": "0.0008"},
            {"no": 2, "dugumler": [2, 6], "E": "200e6", "A": "0.0008"},
            {"no": 3, "dugumler": [3, 7], "E": "200e6", "A": "0.0008"},
            {"no": 4, "dugumler": [4, 8], "E": "200e6", "A": "0.0008"},
            {"no": 5, "dugumler": [5, 6], "E": "200e6", "A": "0.0005"},
            {"no": 6, "dugumler": [6, 7], "E": "200e6", "A": "0.0005"},
            {"no": 7, "dugumler": [7, 8], "E": "200e6", "A": "0.0005"},
            {"no": 8, "dugumler": [8, 5], "E": "200e6", "A": "0.0005"},
            {"no": 9, "dugumler": [1, 6], "E": "200e6", "A": "0.0005"},
            {"no": 10, "dugumler": [2, 7], "E": "200e6", "A": "0.0005"},
            {"no": 11, "dugumler": [3, 8], "E": "200e6", "A": "0.0005"},
            {"no": 12, "dugumler": [4, 5], "E": "200e6", "A": "0.0005"},
            {"no": 13, "dugumler": [5, 7], "E": "200e6", "A": "0.0005"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "uz": True},
            {"dugum": 2, "ux": True, "uy": True, "uz": True},
            {"dugum": 3, "ux": True, "uy": True, "uz": True},
            {"dugum": 4, "ux": True, "uy": True, "uz": True},
        ],
        "yukler": [
            {"dugum": 5, "Fx": 10, "Fy": -20},
            {"dugum": 6, "Fy": -20},
            {"dugum": 7, "Fy": -20},
            {"dugum": 8, "Fx": 10, "Fy": -20},
        ],
    },
    "cerceve3b-konsol-L": {
        "tip": "cerceve3b",
        "baslik": "Uzayda L biçimli konsol: eğilme + burulma",
        "aciklama": "3 m'lik ankastre kol x yönünde, ucundan 2 m'lik ikinci kol z yönünde uzanır; serbest uca 10 kN düşey yük gelir. "
                    "İkinci kol eğilir, birinci kol hem eğilir hem burulur: uç çökmesi PL₂³/3EI + PL₁³/3EI + PL₂²L₁/GJ.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0, "z": 0},
            {"no": 2, "x": 3, "y": 0, "z": 0},
            {"no": 3, "x": 3, "y": 0, "z": 2},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "1e-4", "Iz": "1e-4", "J": "2e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "1e-4", "Iz": "1e-4", "J": "2e-4"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}],
        "yukler": [{"dugum": 3, "Fy": -10}],
    },
    "cerceve3b-izgara": {
        "tip": "cerceve3b",
        "baslik": "Kiriş ızgarası (grid): düzleme dik yüklü döşeme kirişleri",
        "aciklama": "6×6 m'lik yatay düzlemde 3 m aralıklı 30×50 betonarme kirişlerden oluşan ızgara dört köşesinden mafsallı mesnetlenir; "
                    "düğümlere düşey yükler gelir. Kirişler hem eğilir hem birbirini burar: 3B çerçevenin yalnız v, θx, θz serbestlikleri çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0, "z": 0},
            {"no": 2, "x": 3, "y": 0, "z": 0},
            {"no": 3, "x": 6, "y": 0, "z": 0},
            {"no": 4, "x": 0, "y": 0, "z": 3},
            {"no": 5, "x": 3, "y": 0, "z": 3},
            {"no": 6, "x": 6, "y": 0, "z": 3},
            {"no": 7, "x": 0, "y": 0, "z": 6},
            {"no": 8, "x": 3, "y": 0, "z": 6},
            {"no": 9, "x": 6, "y": 0, "z": 6},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 2, "dugumler": [2, 3], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 3, "dugumler": [4, 5], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 4, "dugumler": [5, 6], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 5, "dugumler": [7, 8], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 6, "dugumler": [8, 9], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 7, "dugumler": [1, 4], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 8, "dugumler": [4, 7], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 9, "dugumler": [2, 5], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 10, "dugumler": [5, 8], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 11, "dugumler": [3, 6], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
            {"no": 12, "dugumler": [6, 9], "E": "3e7", "G": "1.25e7", "A": "0.15", "Iy": "1.125e-3", "Iz": "3.125e-3", "J": "3e-3"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "uz": True},
            {"dugum": 3, "ux": True, "uy": True, "uz": True},
            {"dugum": 7, "ux": True, "uy": True, "uz": True},
            {"dugum": 9, "ux": True, "uy": True, "uz": True},
        ],
        "yukler": [
            {"dugum": 5, "Fy": -40},
            {"dugum": 2, "Fy": -20},
            {"dugum": 4, "Fy": -20},
            {"dugum": 6, "Fy": -20},
            {"dugum": 8, "Fy": -20},
        ],
    },
    "cerceve3b-portal": {
        "tip": "cerceve3b",
        "baslik": "Tek katlı uzay çerçeve (kutu çerçeve)",
        "aciklama": "5×4 m planlı, 3 m yüksekliğinde dört kolonlu, dört kirişli çelik uzay çerçeve; kolon tabanları ankastredir. "
                    "x doğrultusundaki kirişlerde 10 kN/m düşey yayılı yük, rüzgâr yüzündeki iki köşeye 15 kN yatay yük, "
                    "bir köşeye de z yönünde 10 kN yük gelir: altı iç kuvvet bileşeni (N, Vy, Vz, T, My, Mz) birlikte çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0, "z": 0},
            {"no": 2, "x": 5, "y": 0, "z": 0},
            {"no": 3, "x": 5, "y": 0, "z": 4},
            {"no": 4, "x": 0, "y": 0, "z": 4},
            {"no": 5, "x": 0, "y": 3, "z": 0},
            {"no": 6, "x": 5, "y": 3, "z": 0},
            {"no": 7, "x": 5, "y": 3, "z": 4},
            {"no": 8, "x": 0, "y": 3, "z": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 5], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "2e-4", "Iz": "2e-4", "J": "4e-4"},
            {"no": 2, "dugumler": [2, 6], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "2e-4", "Iz": "2e-4", "J": "4e-4"},
            {"no": 3, "dugumler": [3, 7], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "2e-4", "Iz": "2e-4", "J": "4e-4"},
            {"no": 4, "dugumler": [4, 8], "E": "200e6", "G": "80e6", "A": "0.01", "Iy": "2e-4", "Iz": "2e-4", "J": "4e-4"},
            {"no": 5, "dugumler": [5, 6], "E": "200e6", "G": "80e6", "A": "0.008", "Iy": "1e-4", "Iz": "3e-4", "J": "2e-4"},
            {"no": 6, "dugumler": [8, 7], "E": "200e6", "G": "80e6", "A": "0.008", "Iy": "1e-4", "Iz": "3e-4", "J": "2e-4"},
            {"no": 7, "dugumler": [6, 7], "E": "200e6", "G": "80e6", "A": "0.008", "Iy": "1e-4", "Iz": "3e-4", "J": "2e-4"},
            {"no": 8, "dugumler": [5, 8], "E": "200e6", "G": "80e6", "A": "0.008", "Iy": "1e-4", "Iz": "3e-4", "J": "2e-4"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True},
            {"dugum": 2, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True},
            {"dugum": 3, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True},
            {"dugum": 4, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True},
        ],
        "yukler": [
            {"dugum": 5, "Fx": 15},
            {"dugum": 8, "Fx": 15},
            {"dugum": 6, "Fz": -10},
        ],
        "yayili": [
            {"eleman": 5, "q": -10},
            {"eleman": 6, "q": -10},
        ],
    },
}


def ornek_model(ad):
    """Örnek modelin bağımsız bir kopyasını (sözlük) döndürür."""
    if ad not in ORNEK_MODELLER:
        raise MatrisHatasi(f"Örnek model yok: {ad!r}. Seçenekler: {', '.join(ORNEK_MODELLER)}.")
    return copy.deepcopy(ORNEK_MODELLER[ad])


def ornek_listesi():
    """Örnek modellerin kısa listesi: [{ad, baslik, tip, aciklama}, ...]."""
    return [{"ad": ad, "baslik": m.get("baslik", ad), "tip": m["tip"], "aciklama": m.get("aciklama", "")}
            for ad, m in ORNEK_MODELLER.items()]


# ============================================================================
# Tür bilgileri
# ============================================================================
_TIPLER = ("yay", "cubuk", "kafes", "kiris", "cerceve", "kafes3b", "cerceve3b")
_TIP_AD = {
    "yay": "yay sistemi (1 boyutlu)",
    "cubuk": "eksenel çubuk (1 boyutlu)",
    "kafes": "düzlem kafes",
    "kiris": "kiriş (Euler–Bernoulli)",
    "cerceve": "düzlem çerçeve",
    "kafes3b": "uzay kafes (3 boyutlu)",
    "cerceve3b": "uzay çerçeve (3 boyutlu)",
}
_UC_BOYUT = ("kafes3b", "cerceve3b")                      # z koordinatı okunan türler
_EGILME = ("kiris", "cerceve", "cerceve3b")               # eğilme (Hermite) taşıyan türler
_EKSENEL = ("yay", "cubuk", "kafes", "kafes3b")           # yalnız eksenel kuvvet taşıyan türler
_SD_SAYISI = {"yay": 1, "cubuk": 1, "kafes": 2, "kiris": 2, "cerceve": 3, "kafes3b": 3, "cerceve3b": 6}
_SD_ADLARI = {"yay": ("u",), "cubuk": ("u",), "kafes": ("u", "v"), "kiris": ("v", "θ"), "cerceve": ("u", "v", "θ"),
              "kafes3b": ("u", "v", "w"), "cerceve3b": ("u", "v", "w", "θx", "θy", "θz")}
_SD_LATEX = {"u": "u", "v": "v", "w": "w", "θ": r"\theta", "θx": r"\theta_{x", "θy": r"\theta_{y", "θz": r"\theta_{z"}
_MESNET_ANAHTAR = {"yay": ("ux",), "cubuk": ("ux",), "kafes": ("ux", "uy"), "kiris": ("uy", "rz"),
                   "cerceve": ("ux", "uy", "rz"), "kafes3b": ("ux", "uy", "uz"),
                   "cerceve3b": ("ux", "uy", "uz", "rx", "ry", "rz")}
_YAY_ANAHTAR = {"yay": ("kx",), "cubuk": ("kx",), "kafes": ("kx", "ky"), "kiris": ("ky", "kr"),
                "cerceve": ("kx", "ky", "kr"), "kafes3b": ("kx", "ky", "kz"),
                "cerceve3b": ("kx", "ky", "kz", "krx", "kry", "krz")}
_BILESEN = {"yay": ("Fx",), "cubuk": ("Fx",), "kafes": ("Fx", "Fy"), "kiris": ("Fy", "M"),
            "cerceve": ("Fx", "Fy", "M"), "kafes3b": ("Fx", "Fy", "Fz"),
            "cerceve3b": ("Fx", "Fy", "Fz", "Mx", "My", "Mz")}
_TUM_BILESEN = ("Fx", "Fy", "Fz", "M", "Mx", "My", "Mz")
_OZELLIK = {"yay": ("k",), "cubuk": ("E", "A"), "kafes": ("E", "A"), "kiris": ("E", "I"),
            "cerceve": ("E", "A", "I"), "kafes3b": ("E", "A"), "cerceve3b": ("E", "G", "A", "Iy", "Iz", "J")}
_OZELLIK_AD = {"E": "elastisite modülü", "A": "kesit alanı", "I": "atalet momenti", "k": "yay sabiti",
               "G": "kayma modülü", "Iy": "y′ eksenine göre atalet momenti", "Iz": "z′ eksenine göre atalet momenti",
               "J": "burulma sabiti", "zemin": "zemin yatak katsayısı"}
_RIJIT_HAREKET = {"yay": 1, "cubuk": 1, "kafes": 3, "kiris": 2, "cerceve": 3, "kafes3b": 6, "cerceve3b": 6}
# Uç serbestlikleri (end releases): yerel iç kuvvet adı -> elemanın bir ucundaki yerel SD sırası (j ucunda + d)
_SERBEST_ADLAR = {"kiris": ("V", "M"), "cerceve": ("N", "V", "M"), "cerceve3b": ("N", "Vy", "Vz", "T", "My", "Mz")}
_SERBEST_TAKMA = {"kiris": {"Vy": "V", "Mz": "M"}, "cerceve": {"Vy": "V", "Mz": "M"}, "cerceve3b": {"Mx": "T"}}
_YALNIZ_CEKME_TIP = ("kafes", "kafes3b", "cerceve", "cerceve3b")
# Global yönlü yayılı yük ("yon"): motor eksenleri (y yukarı); bina eksenleri (X, Y, Z) değildir (yapi.py çevirir)
_GLOBAL_YON = {"gx": 0, "gy": 1, "gz": 2}
_TR_SADE = str.maketrans("şçığöüŞÇİĞÖÜ", "scigouSCIGOU")

_ALT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_UST = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")


def _alt(n):
    return str(n).translate(_ALT)


def _ust(n):
    return str(n).translate(_UST)


# ============================================================================
# Sayı biçimleme
# ============================================================================
def _gercek(x):
    """Sayıysa float, sembolik/karmaşıksa None."""
    if isinstance(x, (bool, int, float)):
        return float(x)
    if np is not None and isinstance(x, np.generic):
        return float(x)
    try:
        x = sp.sympify(x)
        if x.free_symbols:
            return None
        return float(x)
    except (TypeError, ValueError, ArithmeticError):
        return None


def _ondalik_metin(v, basamak=None):
    """float → düz metin (anlamlı basamak sayısı kadar; çok büyük/küçükse 10'un kuvveti)."""
    if v == 0:
        return "0"
    b = int(basamak or mo.ayarlar.basamak)
    s = f"{v:.{b}g}"
    if "e" in s:
        m, e = s.split("e")
        return f"{m}×10{_ust(int(e))}"
    return s


def _metin(x, basamak=None):
    """Skaleri düz metne (md tablosu, SVG yazısı) çevirir; sembolik ifade olduğu gibi yazılır."""
    v = _gercek(x)
    if v is None:
        return str(sp.sympify(x)).replace("**", "^").replace("*", "·")
    return _ondalik_metin(v, basamak)


def _L_ondalik(v, basamak=None):
    if v == 0:
        return "0"
    b = int(basamak or mo.ayarlar.basamak)
    s = f"{v:.{b}g}"
    if "e" in s:
        m, e = s.split("e")
        return rf"{m}\times 10^{{{int(e)}}}"
    return s


def _L(x):
    """Skaler → LaTeX (kesin modda motorun kesir/ondalık ayarı; sayısal modda ondalık)."""
    if isinstance(x, float) or (np is not None and isinstance(x, np.floating)):
        return _L_ondalik(float(x))
    return mo.L(x)


def _Lp(x):
    s = _L(x)
    if s.startswith("-") or (isinstance(x, sp.Basic) and x.is_Add):
        return rf"\left({s}\right)"
    return s


SADE_ESIK = 60   # count_ops bu eşiğin altındaysa simplify denenir; üstünde cancel ile yetinilir


@functools.lru_cache(maxsize=4096)
def _sade_sembolik(x):
    """Harfli ifadeyi sadeleştirir. Önce cancel (pay/payda, polinom halkasında; hızlı ve kanonik), sonra
    yalnız küçük ifadelerde simplify (daha okunaklı biçim). Büyük ifadelerde simplify dakikalarca sürebilir."""
    try:
        y = sp.cancel(x)
    except Exception:  # noqa: BLE001  pragma: no cover
        y = x
    if sp.count_ops(y) <= SADE_ESIK:
        with contextlib.suppress(Exception):   # simplify nadiren hata verir; verirse cancel sonucu kalır
            z = sp.simplify(y)
            if sp.count_ops(z) <= sp.count_ops(y):
                y = z
    return y


def _sade(x):
    """Kesin moddaki ifadeleri sadeleştirir (sembolikse cancel + küçükse simplify, kök içeren sayıysa payda köksüz)."""
    if isinstance(x, sp.MatrixBase):
        return x.applyfunc(_sade)
    if not isinstance(x, sp.Basic):
        return x
    if x.free_symbols:
        return _sade_sembolik(x)
    if x.is_Rational:
        return x
    y = sp.radsimp(sp.expand(x))
    if y.is_Number:
        return y
    try:
        if abs(float(y)) < 1e-13 and sp.simplify(y) == 0:
            return sp.Integer(0)
    except (TypeError, ValueError):
        pass
    return y


def _veri_sayi(x):
    """JSON'a uygun değer: sayıysa float, sembolikse ifade metni."""
    v = _gercek(x)
    if v is not None:
        return v
    return str(sp.sympify(x))


def _isaret_negatif(x):
    """x negatif mi? (sembolik ifadede '-P' gibi eksi işareti çıkarılabiliyorsa negatif sayılır)."""
    v = _gercek(x)
    if v is not None:
        return v < 0
    try:
        return bool(sp.sympify(x).could_extract_minus_sign())
    except (AttributeError, TypeError):
        return False


# ============================================================================
# Model okuma ve doğrulama
# ============================================================================
def _tam(x, ad):
    if isinstance(x, bool):
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).")
    try:
        f = float(x)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).") from None
    if not math.isfinite(f) or not f.is_integer():
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).")
    return int(f)


def _bayrak(v):
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "evet", "doğru", "dogru", "var", "x")
    return bool(v)


def _say(deger, ad, zorunlu=False):
    """Bir model değerini sympy skalerine çevirir (hata iletisi ad ile başlar)."""
    if deger is None or (isinstance(deger, str) and not deger.strip()):
        if zorunlu:
            raise MatrisHatasi(f"{ad} verilmedi.")
        return sp.Integer(0)
    try:
        return mo.skaler_oku(deger)
    except MatrisHatasi as e:
        raise MatrisHatasi(f"{ad}: {e}") from None
    except Exception:  # noqa: BLE001
        raise MatrisHatasi(f"{ad}: değer anlaşılamadı ({deger!r}). Sayı ya da E, A, P gibi bir ifade yazın.") from None


def _koord(deger, ad):
    v = _say(deger, ad)
    if v.free_symbols or v.is_real is False:
        raise MatrisHatasi(f"{ad} sayı olmalı (harf/sembol olamaz; girilen: {deger!r}). "
                           "Koordinatlar yapının geometrisidir; sayısal verilmelidir.")
    return v


def _sd_tex(ad, no):
    """SD etiketi LaTeX: u_{1}, \\theta_{1}, \\theta_{x1} ..."""
    if ad in ("θx", "θy", "θz"):
        return rf"\theta_{{{ad[1]}{no}}}"
    return f"{_SD_LATEX[ad]}_{{{no}}}"


def _sd_etiketleri(tip, dugumler):
    uni, tex = [], []
    for dg in dugumler:
        for a in _SD_ADLARI[tip]:
            uni.append(f"{a}{_alt(dg.no)}")
            tex.append(_sd_tex(a, dg.no))
    return uni, tex


def _izdusum(x, y, z, fi=None, psi=None):
    """3B nokta → çizim düzlemi (yatay, düşey) koordinatları (model birimi): Y etrafında fi, sonra yukarıdan psi eğimi."""
    f = math.radians(BAKIS_FI if fi is None else fi)
    p = math.radians(BAKIS_PSI if psi is None else psi)
    x, y, z = float(x), float(y), float(z)
    u = x * math.cos(f) + z * math.sin(f)
    derin = -x * math.sin(f) + z * math.cos(f)          # izleyiciye doğru
    v = y * math.cos(p) - derin * math.sin(p)
    return u, v


def _eleman_boyu_sayi(M, e):
    """Elemanın boyu (ondalık): yayılı yük sınırlarının (x1, x2) doğrulanması için."""
    a, b = M.dugumler[e.ia], M.dugumler[e.ib]
    if M.tip in ("yay", "cubuk", "kiris"):
        return abs(float(b.x - a.x))
    return math.sqrt(float(b.x - a.x) ** 2 + float(b.y - a.y) ** 2 + float(b.z - a.z) ** 2)


def _bos(v):
    return v is None or (isinstance(v, str) and not v.strip())


# Rijit kat diyaframı: köle düğümün efendiye bağlanan (düzlem içi) SD'leri ve sanal efendinin sıfır alınan SD'leri
# (cerceve3b SD sırası u, v, w, θx, θy, θz; diyafram yatay x–z düzlemindedir, normali y)
_DIYAFRAM_SD = (0, 2, 4)        # u, w, θy: efendiye bağlanır
_DIYAFRAM_DISI_SD = (1, 3, 5)   # v, θx, θz: bağımsız kalır (sanal efendide hiçbir elemana bağlı değildir: 0 alınır)


def _diyaframlari_oku(model, tip, dugumler, dn):
    """'diyaframlar' listesini okur: [{"ad": "Kat 1", "dugumler": [köle no, ...], "ana": {"no", "x", "y", "z"} | no}].

    Yalnız uzay çerçevede (cerceve3b). Köle düğümler aynı kotta (y) olmalıdır; efendi ("ana") ya var olan bir düğümün
    numarası ya da yeni (sanal) bir düğüm sözlüğüdür (y verilmezse kat kotu alınır). Sanal efendi düğüm listesinin
    SONUNA eklenir (var olan SD numaraları değişmez) ve ``sanal=True`` işaretlenir. Dönüş: SimpleNamespace listesi
    (ad, ana [düğüm sırası], koleler [düğüm sıraları], sanal)."""
    ham = model.get("diyaframlar")
    if ham in (None, "", []):
        return []
    if not isinstance(ham, list):
        raise MatrisHatasi('"diyaframlar" bir liste olmalı: [{"ad": "Kat 1", "dugumler": [5, 6, 7, 8], '
                           '"ana": {"no": 9001, "x": 2.5, "y": 3, "z": 2}}].')
    if tip != "cerceve3b":
        raise MatrisHatasi(f"Rijit kat diyaframı (diyaframlar) yalnız uzay çerçevede (cerceve3b) tanımlanabilir; "
                           f"{_TIP_AD[tip]} modelinde kat düzlemi (x–z) ve düşey eksen (y) etrafında dönme yoktur.")
    diyaframlar, kole_kume, efendi_kume = [], set(), set()
    for k, dy in enumerate(ham, start=1):
        if not isinstance(dy, dict):
            raise MatrisHatasi(f"{k}. diyafram bir sözlük olmalı: {{\"ad\": \"Kat 1\", \"dugumler\": [5, 6, 7, 8], \"ana\": ...}}.")
        ad = str(dy.get("ad") or f"Diyafram {k}")
        liste = dy.get("dugumler")
        if not isinstance(liste, (list, tuple)) or not liste:
            raise MatrisHatasi(f"Diyafram '{ad}': 'dugumler' köle düğüm numaralarının listesi olmalı (en az bir düğüm), "
                               "örn. [5, 6, 7, 8] (katın kolon–kiriş birleşim düğümleri).")
        koleler = []
        for ham_no in liste:
            no = _tam(ham_no, f"Diyafram '{ad}': köle düğüm numarası")
            if no not in dn:
                raise MatrisHatasi(f"Diyafram '{ad}' tanımsız bir düğümü köle yapıyor: düğüm {no}. "
                                   f"Tanımlı düğümler: {sorted(dn)}.")
            if no in kole_kume:
                raise MatrisHatasi(f"Düğüm {no} birden çok diyaframa köle olamaz (diyafram '{ad}'): bir düğüm yalnız bir "
                                   "katın döşemesine bağlıdır; kat listelerini ayırın.")
            if no in efendi_kume:
                raise MatrisHatasi(f"Düğüm {no} başka bir diyaframın efendi düğümüdür; diyafram '{ad}' içinde köle olamaz.")
            kole_kume.add(no)
            koleler.append(dn[no])
        kot = dugumler[koleler[0]].y
        for i in koleler[1:]:
            if abs(float(dugumler[i].y - kot)) > 1e-9 * max(1.0, abs(float(kot))):
                raise MatrisHatasi(f"Diyafram '{ad}': köle düğümler aynı kotta (y) olmalı; düğüm {dugumler[koleler[0]].no} "
                                   f"y = {_metin(kot)}, düğüm {dugumler[i].no} y = {_metin(dugumler[i].y)}. Rijit döşeme "
                                   "yatay bir düzlemdir (x–z); her kat için ayrı bir diyafram tanımlayın.")
        ana = dy.get("ana")
        if _bos(ana):
            raise MatrisHatasi(f"Diyafram '{ad}': efendi düğüm ('ana') tanımsız. Ya var olan bir düğümün numarasını "
                               f"(\"ana\": 5) ya da yeni bir düğüm sözlüğünü (\"ana\": {{\"no\": 9001, \"x\": 2.5, "
                               f"\"y\": {_metin(kot)}, \"z\": 2}}; katın kütle merkezi) verin.")
        if isinstance(ana, dict):
            no = _tam(ana.get("no"), f"Diyafram '{ad}': efendi düğümün 'no' değeri")
            if no in dn:
                raise MatrisHatasi(f"Diyafram '{ad}': efendi düğüm {no} zaten tanımlı. Var olan bir düğümü efendi yapmak için "
                                   f"\"ana\": {no} yazın; yeni (sanal) efendi için kullanılmayan bir numara seçin.")
            x = _koord(ana.get("x", 0), f"Diyafram '{ad}': efendi düğüm x koordinatı")
            y = kot if _bos(ana.get("y")) else _koord(ana.get("y"), f"Diyafram '{ad}': efendi düğüm y koordinatı")
            z = _koord(ana.get("z", 0), f"Diyafram '{ad}': efendi düğüm z koordinatı")
            if abs(float(y - kot)) > 1e-9 * max(1.0, abs(float(kot))):
                raise MatrisHatasi(f"Diyafram '{ad}': efendi düğümün kotu y = {_metin(y)} köle düğümlerin kotundan "
                                   f"(y = {_metin(kot)}) farklı; efendi düğüm döşeme düzleminde olmalıdır ('y' boş "
                                   "bırakılırsa kat kotu alınır).")
            dn[no] = len(dugumler)
            dugumler.append(SimpleNamespace(no=no, x=x, y=y, z=z, i=len(dugumler), sanal=True))
            ana_i, sanal = dn[no], True
        else:
            no = _tam(ana, f"Diyafram '{ad}': efendi düğüm ('ana') numarası")
            if no not in dn:
                raise MatrisHatasi(f"Diyafram '{ad}': efendi düğüm {no} tanımsız. Tanımlı düğümler: {sorted(dn)}. "
                                   "Yeni (sanal) bir efendi için sözlük verin: \"ana\": {\"no\": 9001, \"x\": ..., \"z\": ...}.")
            if no in kole_kume:
                raise MatrisHatasi(f"Diyafram '{ad}': düğüm {no} hem efendi hem köle olamaz; köle listesinden çıkarın.")
            if no in efendi_kume:
                raise MatrisHatasi(f"Düğüm {no} iki diyaframın efendisi olamaz (diyafram '{ad}').")
            ana_i, sanal = dn[no], False
            if abs(float(dugumler[ana_i].y - kot)) > 1e-9 * max(1.0, abs(float(kot))):
                raise MatrisHatasi(f"Diyafram '{ad}': efendi düğüm {no} (y = {_metin(dugumler[ana_i].y)}) köle düğümlerle "
                                   f"aynı kotta (y = {_metin(kot)}) olmalıdır.")
        efendi_kume.add(no)
        diyaframlar.append(SimpleNamespace(ad=ad, ana=ana_i, koleler=koleler, sanal=sanal))
    return diyaframlar


def _serbest_oku(ham, no, tip, d):
    """Eleman uç serbestliklerini okur: {"i": ["My", "Mz"], "j": ["Mz"]} → serbest bırakılan yerel SD sıraları
    (0'dan; i ucu 0..d−1, j ucu d..2d−1). Adlar yerel iç kuvvetlerdir: uzay çerçevede N, Vy, Vz, T, My, Mz; düzlem
    çerçevede N, V, M; kirişte V, M. Liste yerine "My, Mz" gibi virgüllü metin de verilebilir."""
    if _bos(ham) or ham == {} or ham == []:
        return []
    if tip not in _SERBEST_ADLAR:
        raise MatrisHatasi(f"Eleman {no}: uç serbestlikleri ('serbest') yalnız kiriş, çerçeve ve uzay çerçeve elemanında "
                           f"tanımlıdır; {_TIP_AD[tip]} çubukları zaten uçlarında mafsallıdır (yalnız eksenel kuvvet taşır).")
    adlar = _SERBEST_ADLAR[tip]
    ornek = '{"i": ["My", "Mz"], "j": ["My", "Mz"]}' if tip == "cerceve3b" else '{"i": [], "j": ["M"]}'
    if not isinstance(ham, dict) or set(ham) - {"i", "j"}:
        raise MatrisHatasi(f"Eleman {no}: 'serbest' bir sözlük olmalı: {ornek} (i: ilk düğüm ucu, j: ikinci düğüm ucu; "
                           f"geçerli adlar: {', '.join(adlar)}).")
    r = set()
    for uc, kaydir in (("i", 0), ("j", d)):
        liste = ham.get(uc)
        if _bos(liste):
            continue
        if isinstance(liste, str):
            liste = [p for p in re.split(r"[,\s;]+", liste) if p]
        if not isinstance(liste, (list, tuple)):
            raise MatrisHatasi(f"Eleman {no}: 'serbest'.{uc} bir ad listesi olmalı, örn. {ornek}.")
        for ad in liste:
            a = str(ad).strip()
            a = _SERBEST_TAKMA[tip].get(a, a)
            if a not in adlar:
                raise MatrisHatasi(f"Eleman {no}: bilinmeyen uç serbestliği {ad!r} ({uc} ucu). {_TIP_AD[tip].capitalize()} "
                                   f"elemanında geçerli adlar (yerel iç kuvvetler): {', '.join(adlar)}. Mafsal için "
                                   + ("My ve Mz" if tip == "cerceve3b" else "M") + " yazın.")
            r.add(kaydir + adlar.index(a))
    return sorted(r)


def _serbest_metin(M, e):
    """Uç serbestliklerinin kısa metni: 'i: My, Mz · j: Mz' (yoksa '—')."""
    if not getattr(e, "serbest", None):
        return "—"
    adlar = _SERBEST_ADLAR[M.tip]
    parca = []
    for uc, kaydir in (("i", 0), ("j", M.d)):
        s = [adlar[k - kaydir] for k in e.serbest if kaydir <= k < kaydir + M.d]
        if s:
            parca.append(f"{uc}: {', '.join(s)}")
    return " · ".join(parca)


def _yayili_parca_oku(y, eno, L, anahtar_q1, anahtar_q2, duzgun_q, uzunluk):
    """Bir yayılı yük kaydından (q1, q2, x1, x2) parçasını okur; x2 verilmemişse eleman boyu L alınır (None döner,
    _hazirla'da doldurulur).

    q1/q2 verilmemişse düzgün yük ``duzgun_q`` kullanılır; yalnız biri verilmişse düzgün sayılır. x1, x2 eleman yerel
    ekseninde ilk düğümden ölçülür ve sayı olmalıdır: 0 ≤ x1 < x2 ≤ L. Yük sıfırsa None döner."""
    ham1, ham2 = y.get(anahtar_q1), y.get(anahtar_q2)
    if _bos(ham1) and _bos(ham2):
        if duzgun_q is None:
            return None
        q1 = q2 = duzgun_q
    else:
        q1 = None if _bos(ham1) else _say(ham1, f"Eleman {eno}: yayılı yük {anahtar_q1}")
        q2 = None if _bos(ham2) else _say(ham2, f"Eleman {eno}: yayılı yük {anahtar_q2}")
        q1 = q2 if q1 is None else q1
        q2 = q1 if q2 is None else q2
    x1 = _koord(y.get("x1", 0), f"Eleman {eno}: yayılı yük başlangıcı x1")
    x2 = None if _bos(y.get("x2")) else _koord(y.get("x2"), f"Eleman {eno}: yayılı yük bitişi x2")
    f1, f2 = float(x1), (L if x2 is None else float(x2))
    tol = 1e-9 * max(L, 1.0)
    if f1 < -tol or f1 > L + tol or f2 < -tol or f2 > L + tol:
        raise MatrisHatasi(f"Eleman {eno}: yayılı yük sınırları eleman üzerinde olmalı: 0 ≤ x1, x2 ≤ L = {L:g} {uzunluk} "
                           f"(girilen x1 = {f1:g}, x2 = {f2:g}). x1 ve x2 elemanın ilk düğümünden, eleman ekseni "
                           "boyunca ölçülür; eleman dışına taşan yükü komşu elemana ayrı bir kayıtla verin.")
    if f2 - f1 <= tol:
        raise MatrisHatasi(f"Eleman {eno}: yayılı yükte x1 < x2 olmalı (girilen x1 = {f1:g}, x2 = {f2:g}). "
                           "Sıfır ya da negatif uzunluktaki parçanın bileşkesi yoktur; sınırları düzeltin "
                           "(x2 verilmezse eleman sonu L alınır).")
    if q1 == 0 and q2 == 0:
        return None
    return (q1, q2, x1, x2)


def _yukleri_oku(M, model):
    """Model (ya da bir yük durumu) sözlüğündeki 'yukler' ve 'yayili' kayıtlarını okur.

    M'de tip, d, dn, en, dugumler, elemanlar, uzunluk bulunmalıdır. Dönüş: (yuk, yayili, yayili_z, yayili_x, sembolik):
    ``yuk[i][j]`` düğüm yük bileşenleri; ``yayili[e]`` / ``yayili_z[e]`` / ``yayili_x[e]`` elemanın yerel y′ / z′ / x′
    yönündeki parçalı doğrusal yük parçaları ``[(q1, q2, x1, x2), ...]`` (x2 None ise eleman sonu L). Bir kayıt ya düzgün
    (q, qz, qx) ya da parçalı doğrusal (q1, q2, x1, x2; qz1, qz2; qx1, qx2) olabilir; aynı elemana birden çok kayıt üst
    üste toplanır. ``"yon": "gx" | "gy" | "gz"`` verilirse q global (motor) eksen yönündedir ve λ ile yerel x′, y′, z′
    bileşenlerine ayrılır; ``"izdusum": true`` ise q, elemanın yük doğrultusuna dik düzleme izdüşüm boyu başınadır
    (düşey yükte yatay izdüşüm: eleman boyu başına şiddet q·cos θ). Global yük ayrıştırmaları ``M.yuk_notlari``na
    yazılır (anlatım için). ``se_coz`` ve ``coz_coklu`` aynı yardımcıyı kullanır."""
    tip, d, dn, en = M.tip, M.d, M.dn, M.en
    if not isinstance(model, dict):
        raise MatrisHatasi('Yük durumu bir sözlük olmalı: {"yukler": [{"dugum": 3, "Fy": -10}], '
                           '"yayili": [{"eleman": 1, "q": -12}]}.')
    semb = False
    yuk = [[sp.Integer(0)] * d for _ in M.dugumler]
    gecerli = _BILESEN[tip]
    # "M" ↔ "Mz" birbirinin yerine kabul edilir (düzlemde moment z eksenindedir)
    takma = {"M": "Mz", "Mz": "M"}
    for y in model.get("yukler") or []:
        if not isinstance(y, dict):
            raise MatrisHatasi('Her yük bir sözlük olmalı: {"dugum": 3, "Fy": -10}.')
        dno = _tam(y.get("dugum"), "Yükün 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Yük tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        for anahtar in _TUM_BILESEN:
            ham = y.get(anahtar)
            if ham is None and tip in ("yay", "cubuk") and anahtar == "Fx":
                ham = y.get("F")
            if ham is None:
                continue
            hedef = anahtar if anahtar in gecerli else takma.get(anahtar)
            if hedef not in gecerli:
                if _say(ham, f"Düğüm {dno}: {anahtar}") != 0:
                    raise MatrisHatasi(f"Düğüm {dno}: {anahtar} yükü bu model türünde ({_TIP_AD[tip]}) etkisizdir; "
                                       f"bu türde geçerli yükler: {', '.join(gecerli)}.")
                continue
            v = _say(ham, f"Düğüm {dno}: {anahtar} yükü")
            if v.free_symbols:
                semb = True
            j = gecerli.index(hedef)
            if M.dugumler[dn[dno]].sanal and j in _DIYAFRAM_DISI_SD and v != 0:
                raise MatrisHatasi(f"Düğüm {dno}: sanal efendi düğüme {anahtar} yükü verilemez; diyafram yalnız düzlem içi "
                                   "bileşenleri (Fx, Fz, My) katın düğümlerine aktarır. Düşey yükü (Fy) ve Mx, Mz'yi "
                                   "doğrudan ilgili kolon–kiriş düğümüne verin.")
            yuk[dn[dno]][j] += v

    # --- yayılı yükler: düzgün (q, qz, qx) ya da parçalı doğrusal (q1, q2, x1, x2; qz1, qz2; qx1, qx2);
    #     "yon": "gx" | "gy" | "gz" ile global yönlü (gerekirse "izdusum": true ile izdüşüm boyu başına) ---
    yayili = [[] for _ in M.elemanlar]
    yayili_z = [[] for _ in M.elemanlar]
    yayili_x = [[] for _ in M.elemanlar]
    notlar = []
    say = bool(getattr(M, "sayisal", False))
    for y in model.get("yayili") or []:
        if not isinstance(y, dict):
            raise MatrisHatasi('Her yayılı yük bir sözlük olmalı: {"eleman": 1, "q": -12} (düzgün) ya da '
                               '{"eleman": 1, "q1": 0, "q2": -12, "x1": 0, "x2": 4} (parçalı doğrusal).')
        if tip not in _EGILME:
            raise MatrisHatasi("Yayılı yük (yayili) yalnız kiriş ve çerçeve modelinde kullanılabilir; "
                               f"{_TIP_AD[tip]} yalnız düğüm yükü taşır.")
        eno = _tam(y.get("eleman"), "Yayılı yükün 'eleman' değeri")
        if eno not in en:
            raise MatrisHatasi(f"Yayılı yük tanımsız bir elemanda: eleman {eno}. Tanımlı elemanlar: {sorted(en)}.")
        e = M.elemanlar[en[eno]]
        L = _eleman_boyu_sayi(M, e)
        yon = y.get("yon")
        izdusum = _bayrak(y.get("izdusum")) if not _bos(y.get("izdusum")) else False
        if not _bos(yon) and str(yon).strip().lower() not in ("yerel", "local"):
            g = str(yon).strip().lower().replace("′", "").replace("'", "")
            if g not in _GLOBAL_YON:
                raise MatrisHatasi(f"Eleman {eno}: yayılı yük yönü {yon!r} anlaşılamadı. Global yön için motor eksenlerini "
                                   "yazın: \"gx\" (sağa), \"gy\" (yukarı), \"gz\" (düzlemden dışa); yerel yükte 'yon' "
                                   "vermeyin (q: y′, qz: z′, qx: x′). Bina eksenleri (X, Y, Z; Z yukarı) motor eksenlerine "
                                   "yapı modülünde çevrilir.")
            gi = _GLOBAL_YON[g]
            if any(not _bos(y.get(a)) for a in ("qz", "qz1", "qz2", "qx", "qx1", "qx2")):
                raise MatrisHatasi(f"Eleman {eno}: global yönlü yükte (yon = {g}) şiddet yalnız q (ya da q1, q2) ile "
                                   "verilir; qz/qx yerel eksen yükleridir, ayrı bir kayıtla verin.")
            if gi == 2 and not M.uc:
                raise MatrisHatasi(f"Eleman {eno}: \"gz\" yönünde yük düzlem modelde ({_TIP_AD[tip]}) tanımsızdır; "
                                   "yalnız \"gx\" ve \"gy\" kullanılabilir.")
            q = _say(y.get("q"), f"Eleman {eno}: yayılı yük q")
            parca = _yayili_parca_oku(y, eno, L, "q1", "q2", q, M.uzunluk)
            if parca is None:
                continue
            if parca[0].free_symbols or parca[1].free_symbols:
                semb = True
            lam = _yuk_eksenleri(M, e, say)
            bil = [lam[k][gi] for k in range(3)]          # λ ĝ: ĝ'nin x′, y′, z′ bileşenleri
            carpan = 1
            if izdusum:
                # yük, yük doğrultusuna dik düzleme izdüşmüş boy başına: L_p = L·√(1 − (x̂′·ĝ)²); eleman boyu başına
                # şiddet q·L_p/L (düşey yükte L_p yatay izdüşüm, çarpan cos θ_yatay)
                carpan = math.sqrt(max(0.0, 1.0 - float(bil[0]) ** 2)) if say else _sade(sp.sqrt(1 - bil[0] ** 2))
            hedefler = (yayili_x, yayili, yayili_z)
            bilesen = []
            for k in range(3):
                c = carpan * bil[k]
                if not say:
                    c = _sade(sp.sympify(c))
                if (abs(float(c)) <= 1e-12) if say else (c == 0):
                    continue
                if k == 0 and tip == "kiris":
                    raise MatrisHatasi(f"Eleman {eno}: \"gx\" yönündeki yük kiriş ekseni boyuncadır (eksenel); kiriş "
                                       "modelinde eksenel serbestlik yoktur. Eksenel yük için 'cerceve' türünü kullanın.")
                hedefler[k][e.idx].append((parca[0] * c, parca[1] * c, parca[2], parca[3]))
                bilesen.append((("x′", "y′", "z′")[k], c))
            notlar.append((eno, g, izdusum, parca, carpan, bilesen))
            continue
        if izdusum:
            raise MatrisHatasi(f"Eleman {eno}: \"izdusum\": true yalnız global yönlü yükte (\"yon\": \"gy\" gibi) "
                               "anlamlıdır; yerel eksen yükü her zaman eleman boyu başınadır.")
        q = _say(y.get("q"), f"Eleman {eno}: yayılı yük q")
        parca = _yayili_parca_oku(y, eno, L, "q1", "q2", q, M.uzunluk)
        if parca is not None:
            if parca[0].free_symbols or parca[1].free_symbols:
                semb = True
            yayili[e.idx].append(parca)
        if any(not _bos(y.get(a)) for a in ("qz", "qz1", "qz2")):
            vz = _say(y.get("qz"), f"Eleman {eno}: yayılı yük qz")
            parca_z = _yayili_parca_oku(y, eno, L, "qz1", "qz2", vz, M.uzunluk)
            if tip != "cerceve3b":
                if parca_z is not None:
                    raise MatrisHatasi(f"Eleman {eno}: qz (yerel z yönünde yayılı yük) yalnız uzay çerçevede (cerceve3b) "
                                       "kullanılabilir; düzlem modelde yayılı yük yalnız yerel y yönündedir (q).")
            elif parca_z is not None:
                if parca_z[0].free_symbols or parca_z[1].free_symbols:
                    semb = True
                yayili_z[e.idx].append(parca_z)
        if any(not _bos(y.get(a)) for a in ("qx", "qx1", "qx2")):
            vx = _say(y.get("qx"), f"Eleman {eno}: yayılı yük qx")
            parca_x = _yayili_parca_oku(y, eno, L, "qx1", "qx2", vx, M.uzunluk)
            if tip == "kiris":
                if parca_x is not None:
                    raise MatrisHatasi(f"Eleman {eno}: qx (yerel x′, eksenel yayılı yük) kiriş modelinde tanımsızdır "
                                       "(eksenel serbestlik yok); çerçeve ya da uzay çerçeve kullanın.")
            elif parca_x is not None:
                if parca_x[0].free_symbols or parca_x[1].free_symbols:
                    semb = True
                yayili_x[e.idx].append(parca_x)
    M.yuk_notlari = notlar
    return yuk, yayili, yayili_z, yayili_x, semb


def _yuk_eksenleri(M, e, say):
    """Global yönlü yayılı yükü ayrıştırmak için elemanın yerel eksen matrisi λ (3×3; satırlar x′, y′, z′ global
    bileşenlerle): kiriş birim matris; düzlem çerçeve [[c, s, 0], [−s, c, 0], [0, 0, 1]]; uzay çerçeve _lam3b (aci dahil).
    ``say`` ise ondalık, değilse kesin (sympy) hesaplanır."""
    a, b = M.dugumler[e.ia], M.dugumler[e.ib]
    if say:
        dx, dy, dz = (float(b.x) - float(a.x), float(b.y) - float(a.y), float(b.z) - float(a.z))
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        bir, sifir = 1.0, 0.0
    else:
        dx, dy, dz = b.x - a.x, b.y - a.y, b.z - a.z
        L = _sade(sp.sqrt(dx * dx + dy * dy + dz * dz))
        bir, sifir = sp.Integer(1), sp.Integer(0)
    if M.tip == "kiris":
        return [[bir, sifir, sifir], [sifir, bir, sifir], [sifir, sifir, bir]]
    if M.tip == "cerceve3b":
        yon = (dx / L, dy / L, dz / L) if say else tuple(_sade(v / L) for v in (dx, dy, dz))
        return _lam3b(*yon, say, getattr(e, "eksen_aci", 0))
    c, s = (dx / L, dy / L) if say else (_sade(dx / L), _sade(dy / L))
    return [[c, s, sifir], [-s, c, sifir], [sifir, sifir, bir]]


def _model_sozluk(model):
    """Model girdisini (sözlük ya da JSON metni) sözlüğe çevirir."""
    if isinstance(model, str):
        try:
            model = json.loads(model)
        except ValueError as e:
            raise MatrisHatasi(f"Model JSON olarak okunamadı: {e}") from None
    if not isinstance(model, dict):
        raise MatrisHatasi('Model bir sözlük (ya da JSON metni) olmalı: {"tip": "kafes", "dugumler": [...], '
                           '"elemanlar": [...], "mesnetler": [...], "yukler": [...]}.')
    return model


def _model_oku(model):
    """Sözlük ya da JSON metnini doğrulayıp hesaplanabilir bir model nesnesine (SimpleNamespace) çevirir.
    Bilinmeyen anahtarlar (eleman kayıtlarındaki ``kaynak``, ``yardimci`` gibi) yok sayılır."""
    model = _model_sozluk(model)
    tip = str(model.get("tip", "")).strip().lower().translate(_TR_SADE).replace("-", "").replace("_", "")
    if tip == "cerceve3d":
        tip = "cerceve3b"
    if tip == "kafes3d":
        tip = "kafes3b"
    if tip not in _TIPLER:
        raise MatrisHatasi(f"Bilinmeyen model türü: {model.get('tip')!r}. Seçenekler: {', '.join(_TIPLER)} "
                           "(yay, eksenel çubuk, kafes, kiriş, çerçeve, uzay kafes, uzay çerçeve).")
    d = _SD_SAYISI[tip]
    uc = tip in _UC_BOYUT
    birim = model.get("birim") if isinstance(model.get("birim"), dict) else {}
    kuvvet = str(birim.get("kuvvet", "kN"))
    uzunluk = str(birim.get("uzunluk", "m"))
    semb = False

    # --- düğümler ---
    dl = model.get("dugumler")
    if not isinstance(dl, list) or not dl:
        raise MatrisHatasi("Modelde düğüm yok: 'dugumler' listesi boş ya da eksik. "
                           "Örnek: [{\"no\": 1, \"x\": 0, \"y\": 0}, {\"no\": 2, \"x\": 3, \"y\": 0}].")
    dugumler, dn, z_yoksayilan = [], {}, []
    for k, dg in enumerate(dl, start=1):
        if not isinstance(dg, dict):
            raise MatrisHatasi(f"{k}. düğüm bir sözlük olmalı: {{\"no\": 1, \"x\": 0, \"y\": 0}}.")
        no = _tam(dg.get("no", k), f"{k}. düğümün 'no' değeri")
        if no in dn:
            raise MatrisHatasi(f"Düğüm {no} iki kez tanımlandı; her düğüm numarası yalnız bir kez kullanılabilir.")
        x = _koord(dg.get("x", 0), f"Düğüm {no}: x koordinatı")
        y = sp.Integer(0) if tip in ("yay", "cubuk") else _koord(dg.get("y", 0), f"Düğüm {no}: y koordinatı")
        z = _koord(dg.get("z", 0), f"Düğüm {no}: z koordinatı") if uc else sp.Integer(0)
        if not uc and dg.get("z") not in (None, "", 0, "0") and no not in z_yoksayilan:
            z_yoksayilan.append(no)
        dn[no] = len(dugumler)
        dugumler.append(SimpleNamespace(no=no, x=x, y=y, z=z, i=len(dugumler), sanal=False))
    if tip == "kiris":
        for dg in dugumler[1:]:
            if sp.simplify(dg.y - dugumler[0].y) != 0:
                raise MatrisHatasi(
                    f"Kiriş modelinde bütün düğümler aynı yatay doğru üzerinde olmalı (y aynı): düğüm {dg.no} "
                    f"y={dg.y}, düğüm {dugumler[0].no} y={dugumler[0].y}. Eğik ya da kırık eksenli taşıyıcılar "
                    "için 'cerceve' türünü kullanın.")

    # --- elemanlar ---
    el = model.get("elemanlar")
    if not isinstance(el, list) or not el:
        raise MatrisHatasi("Modelde eleman yok: 'elemanlar' listesi boş ya da eksik. Örnek: "
                           "[{\"no\": 1, \"dugumler\": [1, 2], \"E\": \"200e6\", \"A\": \"0.001\"}].")
    elemanlar, en = [], {}
    for k, e in enumerate(el, start=1):
        if not isinstance(e, dict):
            raise MatrisHatasi(f"{k}. eleman bir sözlük olmalı: {{\"no\": 1, \"dugumler\": [1, 2], ...}}.")
        no = _tam(e.get("no", k), f"{k}. elemanın 'no' değeri")
        if no in en:
            raise MatrisHatasi(f"Eleman {no} iki kez tanımlandı; her eleman numarası yalnız bir kez kullanılabilir.")
        dd = e.get("dugumler")
        if not isinstance(dd, (list, tuple)) or len(dd) != 2:
            raise MatrisHatasi(f"Eleman {no}: 'dugumler' iki düğüm numarası içermeli, örn. [1, 2].")
        a = _tam(dd[0], f"Eleman {no}: birinci düğüm numarası")
        b = _tam(dd[1], f"Eleman {no}: ikinci düğüm numarası")
        for dno in (a, b):
            if dno not in dn:
                raise MatrisHatasi(f"Eleman {no} tanımsız bir düğüme bağlı: düğüm {dno}. "
                                   f"Tanımlı düğümler: {sorted(dn)}.")
        ia, ib = dn[a], dn[b]
        dx = dugumler[ib].x - dugumler[ia].x
        dy = dugumler[ib].y - dugumler[ia].y
        dz = dugumler[ib].z - dugumler[ia].z
        # aynı konumdaki iki düğüm (tolerans 1e-6 model uzunluk birimi; m'de 1 µm) sıfır boylu eleman sayılır
        boy2 = float(dx) ** 2 if tip in ("yay", "cubuk", "kiris") else float(dx) ** 2 + float(dy) ** 2 + float(dz) ** 2
        sifir = boy2 <= 1e-12
        if a == b or sifir:
            raise MatrisHatasi(f"Eleman {no}'nin boyu sıfır: düğüm {a} ve düğüm {b} aynı noktada (aralarındaki uzaklık "
                               f"{math.sqrt(boy2):.3g} {uzunluk} ≤ 1e-6). "
                               "Sıfır boylu elemanın rijitliği tanımsızdır (EA/L, EI/L³ ifadelerinde L = 0 olurdu); "
                               "düğüm koordinatlarını düzeltin.")
        if tip == "kiris" and dx < 0:
            raise MatrisHatasi(f"Eleman {no}: kiriş elemanları soldan sağa tanımlanmalıdır (ilk düğümün x'i küçük "
                               f"olmalı); düğüm sırasını [{b}, {a}] yapın. (Yerel y ekseni yukarıyı gösterir; "
                               "yayılı yük q aşağı için negatiftir.)")
        ozel = {}
        for p in _OZELLIK[tip]:
            v = _say(e.get(p), f"Eleman {no}: {p} ({_OZELLIK_AD[p]})", zorunlu=True)
            if v.free_symbols:
                semb = True
            elif v.is_real is False or v <= 0:
                raise MatrisHatasi(f"Eleman {no}: {p} ({_OZELLIK_AD[p]}) pozitif bir sayı olmalı (girilen: {e.get(p)!r}). "
                                   "Sıfır ya da negatif rijitlik yapıyı çözülemez yapar.")
            ozel[p] = v
        zemin = None
        if e.get("zemin") is not None and str(e.get("zemin")).strip() != "":
            v = _say(e.get("zemin"), f"Eleman {no}: zemin (Winkler yatak katsayısı k_s)")
            if tip not in ("kiris", "cerceve"):
                if v != 0:
                    raise MatrisHatasi(f"Eleman {no}: 'zemin' (Winkler yatak katsayısı) yalnız kiriş ve düzlem çerçeve "
                                       f"elemanında kullanılabilir; {_TIP_AD[tip]} elemanında elastik zemin tanımlı değildir.")
            elif v.free_symbols:
                semb = True
                zemin = v
            elif v.is_real is False or v < 0:
                raise MatrisHatasi(f"Eleman {no}: zemin (Winkler yatak katsayısı k_s) negatif olamaz (girilen: {e.get('zemin')!r}). "
                                   "k_s, birim boya düşen zemin yayı rijitliğidir (kN/m²); zemin yoksa boş bırakın.")
            elif v != 0:
                zemin = v
        serbest = _serbest_oku(e.get("serbest"), no, tip, d)
        eksen_aci = sp.Integer(0)
        if tip == "cerceve3b" and not _bos(e.get("aci")):
            eksen_aci = _koord(e.get("aci"), f"Eleman {no}: yerel eksen açısı aci (derece)")
            if abs(float(eksen_aci)) > 1e-12:
                eksen_aci = eksen_aci if eksen_aci.is_Rational else sp.nsimplify(eksen_aci)
            else:
                eksen_aci = sp.Integer(0)
        yalniz_cekme = False
        if not _bos(e.get("yalniz_cekme")) and _bayrak(e.get("yalniz_cekme")):
            if tip not in _YALNIZ_CEKME_TIP:
                raise MatrisHatasi(f"Eleman {no}: 'yalniz_cekme' yalnız kafes, uzay kafes, çerçeve ve uzay çerçeve "
                                   f"elemanında kullanılabilir ({_TIP_AD[tip]} elemanında eksenel çubuk davranışı yoktur).")
            yalniz_cekme = True
        en[no] = len(elemanlar)
        elemanlar.append(SimpleNamespace(no=no, dno=(a, b), ia=ia, ib=ib, idx=len(elemanlar),
                                         E=ozel.get("E"), A=ozel.get("A"), I=ozel.get("I"), k=ozel.get("k"),
                                         G=ozel.get("G"), Iy=ozel.get("Iy"), Iz=ozel.get("Iz"), J=ozel.get("J"),
                                         zemin=zemin, serbest=serbest, eksen_aci=eksen_aci,
                                         yalniz_cekme=yalniz_cekme, etkin=True))

    # --- rijit kat diyaframları (sanal efendi düğümler listenin sonuna eklenir) ---
    diyaframlar = _diyaframlari_oku(model, tip, dugumler, dn)
    kole = {}                       # köle düğüm sırası -> diyafram
    for dy in diyaframlar:
        for i in dy.koleler:
            kole[i] = dy

    kullanilan = {x for e in elemanlar for x in e.dno}
    for dg in dugumler:
        if dg.no not in kullanilan and not dg.sanal:
            raise MatrisHatasi(f"Düğüm {dg.no} hiçbir elemana bağlı değil: bu düğümün serbestlikleri için denklem "
                               "yazılamaz (K matrisinde sıfır satır/sütun oluşur). Düğümü bir elemana bağlayın "
                               "ya da modelden çıkarın.")

    # --- mesnetler ---
    mesnet = [[False] * d for _ in dugumler]
    for m in model.get("mesnetler") or []:
        if not isinstance(m, dict):
            raise MatrisHatasi('Her mesnet bir sözlük olmalı: {"dugum": 1, "ux": true, "uy": true}.')
        dno = _tam(m.get("dugum"), "Mesnetin 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Mesnet tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        for k, anahtar in enumerate(_MESNET_ANAHTAR[tip]):
            deger = m.get(anahtar)
            if deger is None and tip in ("yay", "cubuk") and anahtar == "ux":
                deger = m.get("u")
            if _bayrak(deger):
                if dn[dno] in kole and k in _DIYAFRAM_SD:
                    raise MatrisHatasi(
                        f"Düğüm {dno}: {anahtar} serbestliği rijit diyafram '{kole[dn[dno]].ad}' ile efendi düğüme bağlıdır; "
                        "köle düğümün düzlem içi serbestlikleri (ux, uz, ry) ayrıca mesnetlenemez. Katı tutmak için mesneti "
                        f"efendi düğüme ({dugumler[kole[dn[dno]].ana].no}) verin; düşey (uy) ve diğer dönmeler (rx, rz) köle "
                        "düğümde mesnetlenebilir.")
                mesnet[dn[dno]][k] = True

    # --- hesap modu anahtarı (yük ayrıştırmasının kesin/ondalık yapılacağını önceden bilmek için burada okunur) ---
    hesap = str(model.get("hesap") or "").strip().lower().translate(_TR_SADE)
    if hesap and hesap not in ("sayisal", "kesin", "otomatik"):
        raise MatrisHatasi(f"Bilinmeyen 'hesap' değeri: {model.get('hesap')!r}. Seçenekler: \"sayisal\" (numpy), "
                           f"\"kesin\" (sympy; en çok {SD_ESIK} SD) ya da boş (otomatik).")
    on_sayisal = hesap == "sayisal" or bool(diyaframlar) or d * len(dugumler) > SD_ESIK

    # --- yükler ve yayılı yükler (coz_coklu de aynı yardımcıyı kullanır) ---
    M = SimpleNamespace(tip=tip, d=d, uc=uc, dugumler=dugumler, dn=dn, elemanlar=elemanlar, en=en, uzunluk=uzunluk,
                        diyaframlar=diyaframlar, kole=kole, sayisal=on_sayisal)
    yuk, yayili, yayili_z, yayili_x, semb_yuk = _yukleri_oku(M, model)
    semb = semb or semb_yuk

    # --- elastik mesnetler (yaylar) ---
    yay = [[sp.Integer(0)] * d for _ in dugumler]
    yay_anahtar = _YAY_ANAHTAR[tip]
    yay_takma = {"kr": "krz", "krz": "kr"}
    for y in model.get("yaylar") or []:
        if not isinstance(y, dict):
            raise MatrisHatasi('Her yay (elastik mesnet) bir sözlük olmalı: {"dugum": 1, "ky": 50000, "kr": 20000}.')
        dno = _tam(y.get("dugum"), "Yayın (elastik mesnet) 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Yay (elastik mesnet) tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        for anahtar, ham in y.items():
            if anahtar == "dugum" or ham is None or (isinstance(ham, str) and not ham.strip()):
                continue
            # "kr" ↔ "krz" birbirinin yerine kabul edilir (düzlemde dönme yayı z eksenindedir)
            if anahtar not in yay_anahtar:
                anahtar = yay_takma.get(anahtar, anahtar)
            if anahtar not in yay_anahtar:
                v = _say(ham, f"Düğüm {dno}: {anahtar}")
                if v != 0:
                    raise MatrisHatasi(f"Düğüm {dno}: {anahtar} yayı bu model türünde ({_TIP_AD[tip]}) tanımlı değil; "
                                       f"bu türde geçerli yay anahtarları: {', '.join(yay_anahtar)}.")
                continue
            v = _say(ham, f"Düğüm {dno}: {anahtar} yay rijitliği")
            if v.free_symbols:
                semb = True
            elif v.is_real is False or v < 0:
                raise MatrisHatasi(f"Düğüm {dno}: {anahtar} yay rijitliği negatif olamaz (girilen: {ham!r}). "
                                   "Yay rijitliği K'nın köşegenine eklenir; negatif değer yapıyı kararsız yapar.")
            yay[dn[dno]][yay_anahtar.index(anahtar)] += v

    # --- mesnet çökmeleri (verilen yer değiştirmeler) ---
    cokme = {}
    for c in model.get("cokmeler") or []:
        if not isinstance(c, dict):
            raise MatrisHatasi('Her mesnet çökmesi bir sözlük olmalı: {"dugum": 4, "uy": -0.01}.')
        dno = _tam(c.get("dugum"), "Mesnet çökmesinin 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Mesnet çökmesi tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        for anahtar, ham in c.items():
            if anahtar == "dugum" or ham is None or (isinstance(ham, str) and not ham.strip()):
                continue
            if anahtar == "u" and tip in ("yay", "cubuk"):
                anahtar = "ux"
            if anahtar not in _MESNET_ANAHTAR[tip]:
                raise MatrisHatasi(f"Düğüm {dno}: {anahtar} çökmesi bu model türünde ({_TIP_AD[tip]}) tanımlı değil; "
                                   f"geçerli anahtarlar: {', '.join(_MESNET_ANAHTAR[tip])}.")
            v = _say(ham, f"Düğüm {dno}: {anahtar} verilen yer değiştirme")
            if v.free_symbols:
                semb = True
            k = _MESNET_ANAHTAR[tip].index(anahtar)
            if dn[dno] in kole and k in _DIYAFRAM_SD:
                raise MatrisHatasi(f"Düğüm {dno}: {anahtar} serbestliği rijit diyafram '{kole[dn[dno]].ad}' ile efendi düğüme "
                                   "bağlıdır; köle düğümün düzlem içi serbestliğine (ux, uz, ry) çökme verilemez. Verilen yer "
                                   f"değiştirmeyi efendi düğüme ({dugumler[kole[dn[dno]].ana].no}) uygulayın.")
            if dugumler[dn[dno]].sanal and k in _DIYAFRAM_DISI_SD:
                raise MatrisHatasi(f"Düğüm {dno}: sanal efendi düğümün {anahtar} serbestliği hiçbir elemana bağlı değildir "
                                   "(diyafram yalnız ux, uz, ry'yi aktarır); bu serbestliğe çökme verilemez.")
            mesnet[dn[dno]][k] = True
            if v != 0:
                cokme[d * dn[dno] + k] = v

    M.baslik = str(model.get("baslik") or f"{_TIP_AD[tip].capitalize()} modeli")
    M.kuvvet, M.uzunluk = kuvvet, uzunluk
    M.mesnet, M.yuk, M.yayili, M.yayili_z, M.yay, M.cokme = mesnet, yuk, yayili, yayili_z, yay, cokme
    M.yayili_x = yayili_x
    M.serbest_var = any(e.serbest for e in elemanlar)
    M.aci_var = any(e.eksen_aci != 0 for e in elemanlar)
    M.yalniz_cekme_var = any(e.yalniz_cekme for e in elemanlar)
    M.n, M.sembolik, M.uyarilar = d * len(dugumler), semb, []
    M.sd_et, M.sd_tex = _sd_etiketleri(tip, dugumler)
    M.yay_var = any(v != 0 for satir in yay for v in satir)
    M.zemin_var = any(e.zemin is not None for e in elemanlar)
    if z_yoksayilan:
        M.uyarilar.append(
            f"Düğüm {', '.join(str(n) for n in z_yoksayilan)} için z koordinatı verildi ama {_TIP_AD[tip]} düzlem "
            "modelidir: z yoksayıldı. Uzay geometri için 'kafes3b' ya da 'cerceve3b' türünü seçin.")

    if M.yalniz_cekme_var:
        ycs = [e.no for e in elemanlar if e.yalniz_cekme]
        M.uyarilar.append(
            f"Yalnız çekme çubukları var (eleman {', '.join(str(n) for n in ycs)}): bu çözüm DOĞRUSAL ÖN ÇÖZÜMDÜR, bütün "
            "çubuklar etkin sayıldı. Basınca düşen yalnız-çekme çubuğunu devre dışı bırakan doğrusal olmayan çözüm için "
            "coz_yalniz_cekme kullanın (doğrusal olmayan durum: süperpozisyon geçersizdir; her yük birleşimi "
            "ayrı ve yinelemeli çözülür).")

    # --- hesap modu ("hesap": "sayisal" anahtarı küçük modelde de numpy modunu zorlar) ---
    if hesap == "sayisal" and semb:
        raise MatrisHatasi("\"hesap\": \"sayisal\" ile harfli (sembolik) girdi bir arada olamaz: E, A, P gibi harfleri "
                           "sayıyla değiştirin ya da 'hesap' anahtarını kaldırın.")
    if diyaframlar:
        if semb:
            raise MatrisHatasi("Rijit kat diyaframı (diyaframlar) yalnız sayısal kipte çözülür; harfli (sembolik) girdiyle "
                               "bir arada olamaz: E, A, P gibi harfleri sayıyla değiştirin.")
        if hesap == "kesin":
            raise MatrisHatasi("Rijit kat diyaframı (diyaframlar) yalnız sayısal kipte çözülür: \"hesap\": \"kesin\" ile "
                               "bir arada olamaz; 'hesap' anahtarını kaldırın.")
        hesap = "sayisal"
    if M.n > SD_ESIK or hesap == "sayisal":
        if semb:
            raise MatrisHatasi(
                f"Harfli (sembolik) girdi en çok {SD_ESIK} serbestlik derecesinde (SD) çözülür; bu model {M.n} SD içeriyor. "
                "Sembolik çözüm büyüdükçe ifadeler okunamaz hale gelir: E, A, P gibi harfleri sayıyla değiştirin "
                f"ya da modeli {SD_ESIK} SD'ye indirin.")
        M.mod = "sayisal"
        if np is None:
            raise MatrisHatasi(f"{M.n} SD için sayısal hesap gerekir ama numpy yüklü değil.")
    else:
        M.mod = "kesin"
    M.sayisal = M.mod == "sayisal"

    # --- birim uyarısı (E değeri MPa girilmiş olabilir) ---
    if kuvvet == "kN" and uzunluk == "m":
        for e in elemanlar:
            v = _gercek(e.E) if e.E is not None else None
            if v is not None and 1e3 <= v <= 1e6:
                s = f"{v:,.0f}".replace(",", " ")
                M.uyarilar.append(
                    f"E = {s} girildi: MPa mı? Birimler kN ve m ise E, kN/m² cinsinden yazılmalıdır "
                    f"(1 MPa = 1000 kN/m²): çelik için 2,0×10⁸ kN/m² (200 GPa), beton için yaklaşık 3×10⁷ kN/m². "
                    f"Eleman {e.no}'de E değeri bu beklentinin çok altında.")
                break

    if M.sayisal:
        _floata_cevir(M)
    return M


def _floata_cevir(M):
    for dg in M.dugumler:
        dg.x, dg.y, dg.z = float(dg.x), float(dg.y), float(dg.z)
    for e in M.elemanlar:
        for p in ("E", "A", "I", "k", "G", "Iy", "Iz", "J", "zemin", "eksen_aci"):
            v = getattr(e, p)
            if v is not None:
                setattr(e, p, float(v))
    M.yuk = [[float(v) for v in satir] for satir in M.yuk]
    M.yay = [[float(v) for v in satir] for satir in M.yay]
    M.yayili = _parcalari_floata_cevir(M.yayili)
    M.yayili_z = _parcalari_floata_cevir(M.yayili_z)
    M.yayili_x = _parcalari_floata_cevir(M.yayili_x)
    M.cokme = {k: float(v) for k, v in M.cokme.items()}


def _parcalari_floata_cevir(yayili):
    return [[tuple(None if v is None else float(v) for v in p) for p in liste] for liste in yayili]


# ============================================================================
# Parçalı doğrusal yayılı yük: eşdeğer düğüm yükleri (3 noktalı Gauss–Legendre) ve kapalı form integraller
# ============================================================================
_GAUSS3_SAYI = ((-math.sqrt(0.6), 5.0 / 9.0), (0.0, 8.0 / 9.0), (math.sqrt(0.6), 5.0 / 9.0))
_GAUSS3_KESIN = ((-sp.sqrt(sp.Rational(3, 5)), sp.Rational(5, 9)), (sp.Integer(0), sp.Rational(8, 9)),
                 (sp.sqrt(sp.Rational(3, 5)), sp.Rational(5, 9)))


def _hermite_N(x, L):
    """Hermite kübik şekil fonksiyonları (N1, N2, N3, N4) ↔ (v_i, θ_i, v_j, θ_j)."""
    xi = x / L
    return (1 - 3 * xi ** 2 + 2 * xi ** 3, L * (xi - 2 * xi ** 2 + xi ** 3),
            3 * xi ** 2 - 2 * xi ** 3, L * (-xi ** 2 + xi ** 3))


def _feq_parcali(L, parcalar, sayisal=True):
    """Parçalı doğrusal yayılı yükün eşdeğer düğüm yükleri [f_v,i, m_i, f_v,j, m_j] = Σ ∫_{x1}^{x2} Nᵀ q(x) dx.

    Her parça (q1, q2, x1, x2) için q(x) = q1 + (q2 − q1)(x − x1)/(x2 − x1); Hermite kübik × doğrusal = 4. dereceden
    polinom olduğundan 3 noktalı Gauss–Legendre (5. dereceye kadar kesin) integrali tam verir. Kesin kipte Gauss
    düğümleri √(3/5) içerir; sp.expand ile köklü terimler birbirini götürür ve sonuç kesirli polinomdur."""
    gauss = _GAUSS3_SAYI if sayisal else _GAUSS3_KESIN
    f = [0.0, 0.0, 0.0, 0.0] if sayisal else [sp.Integer(0)] * 4
    for q1, q2, x1, x2 in parcalar:
        h = (x2 - x1) / 2
        for g, w in gauss:
            x = x1 + h * (1 + g)
            q = q1 + (q2 - q1) * (x - x1) / (x2 - x1)
            N = _hermite_N(x, L)
            f = [fa + w * h * q * Na for fa, Na in zip(f, N)]
    if not sayisal:
        f = [sp.expand(v) for v in f]
    return f


def _feq_eksenel(L, parcalar, sayisal=True):
    """Yerel x′ (eksenel) parçalı doğrusal yayılı yükün eşdeğer düğüm yükleri [f_x,i, f_x,j] = Σ ∫ [1 − x/L, x/L] q(x) dx.
    Doğrusal şekil fonksiyonlarıyla kapalı form: parçanın bileşkesi W ve ilk düğüme göre statik momenti S ile
    f_x,j = S/L, f_x,i = W − S/L (bileşke, uçlara basit kiriş tepkisi gibi paylaşılır)."""
    fi = fj = (0.0 if sayisal else sp.Integer(0))
    for q1, q2, x1, x2 in parcalar:
        W, S = _yuk_bileskesi(q1, q2, x1, x2)
        fi = fi + W - S / L
        fj = fj + S / L
    if not sayisal:
        fi, fj = sp.expand(fi), sp.expand(fj)
    return [fi, fj]


def _yuk_bileskesi(q1, q2, x1, x2):
    """Bir parçanın bileşkesi W = ∫ q dx ve ilk düğüme göre statik momenti S = ∫ q·x dx (eleman ekseni boyunca)."""
    D = x2 - x1
    W = (q1 + q2) * D / 2
    S = q1 * x1 * D + q1 * D ** 2 / 2 + (q2 - q1) * (x1 * D / 2 + D ** 2 / 3)
    return W, S


def _yuk_integralleri(parcalar, x, sifir=0.0):
    """Q(x) = ∫₀ˣ q(s) ds ve MQ(x) = ∫₀ˣ (x − s) q(s) ds: kesme ve moment diyagramının yayılı yük katkısı (kapalı form).
    x ve parça sınırları sayıdır; q1, q2 sayı ya da sembolik olabilir."""
    Q, MQ = sifir, sifir
    xf = float(x)
    for q1, q2, x1, x2 in parcalar:
        D = x2 - x1
        k = (q2 - q1) / D
        if xf <= float(x1) + 1e-12 * max(1.0, abs(float(x1))):
            continue
        if xf < float(x2):
            t = x - x1
            Q = Q + q1 * t + k * t ** 2 / 2
            MQ = MQ + q1 * t ** 2 / 2 + k * t ** 3 / 6
        else:
            W, S = _yuk_bileskesi(q1, q2, x1, x2)
            Q = Q + W
            MQ = MQ + W * x - S
    return Q, MQ


def _q_aralik(parcalar, xa, xb):
    """[xa, xb] aralığını bütünüyle örten parçaların uçlardaki değer toplamı (q(xa), q(xb)); aralık parça sınırı içermez."""
    qa = qb = 0
    tol = 1e-9 * max(1.0, abs(float(xb)))
    for q1, q2, x1, x2 in parcalar:
        if float(x1) <= float(xa) + tol and float(x2) >= float(xb) - tol:
            k = (q2 - q1) / (x2 - x1)
            qa = qa + q1 + k * (xa - x1)
            qb = qb + q1 + k * (xb - x1)
    return qa, qb


def _duzgun_mu(e):
    """Elemanın yayılı yükü tek bir düzgün, bütün açıklığa yayılı parçadan mı oluşuyor? (q, qz) ya da None döner."""
    def tek(parcalar):
        if not parcalar:
            return 0
        if len(parcalar) == 1:
            q1, q2, x1, x2 = parcalar[0]
            if q1 == q2 and float(x1) == 0.0 and abs(float(x2) - float(e.L)) <= 1e-9 * max(1.0, float(e.L)):
                return q1
        return None
    q, qz = tek(e.parcalar), tek(e.parcalar_z)
    if q is None or qz is None:
        return None
    return q, qz


def _parca_metin(parcalar, L):
    """Yük tablosu hücresi: düzgün bütün açıklık için 'q', yoksa 'q1→q2 [x1, x2]' (parçalar ; ile)."""
    if not parcalar:
        return "0"
    hucre = []
    for q1, q2, x1, x2 in parcalar:
        tam = float(x1) == 0.0 and abs(float(x2) - float(L)) <= 1e-9 * max(1.0, float(L))
        if q1 == q2 and tam:
            hucre.append(_metin(q1))
        else:
            hucre.append(f"{_metin(q1)}→{_metin(q2)} [{_metin(x1)}, {_metin(x2)}]")
    return "; ".join(hucre)



# ============================================================================
# Hesap çekirdeği (kesin: sympy, sayısal: numpy)
# ============================================================================
def _mat(M, satirlar):
    return np.array(satirlar, dtype=float) if M.sayisal else sp.Matrix(satirlar)


def _vek(M, liste):
    return np.array(liste, dtype=float) if M.sayisal else sp.Matrix(liste)


def _sifir_mat(M, n):
    return np.zeros((n, n)) if M.sayisal else sp.zeros(n, n)


def _sifir_vek(M, n):
    return np.zeros(n) if M.sayisal else sp.zeros(n, 1)


def _liste(v):
    return [v[i] for i in range(len(v))]


def _al(M, v, idx):
    idx = list(idx)
    return v[idx] if M.sayisal else sp.Matrix([v[i] for i in idx])


def _k_kiris(E, I, L):
    a = E * I / L ** 3
    return [[12 * a, 6 * L * a, -12 * a, 6 * L * a],
            [6 * L * a, 4 * L * L * a, -6 * L * a, 2 * L * L * a],
            [-12 * a, -6 * L * a, 12 * a, -6 * L * a],
            [6 * L * a, 2 * L * L * a, -6 * L * a, 4 * L * L * a]]


def _k_cerceve(E, A, I, L):
    ea = E * A / L
    a = E * I / L ** 3
    return [[ea, 0, 0, -ea, 0, 0],
            [0, 12 * a, 6 * L * a, 0, -12 * a, 6 * L * a],
            [0, 6 * L * a, 4 * L * L * a, 0, -6 * L * a, 2 * L * L * a],
            [-ea, 0, 0, ea, 0, 0],
            [0, -12 * a, -6 * L * a, 0, 12 * a, -6 * L * a],
            [0, 6 * L * a, 2 * L * L * a, 0, -6 * L * a, 4 * L * L * a]]


def _T_cerceve(c, s):
    return [[c, s, 0, 0, 0, 0], [-s, c, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
            [0, 0, 0, c, s, 0], [0, 0, 0, -s, c, 0], [0, 0, 0, 0, 0, 1]]


def _k_zemin(ks, L):
    """Winkler zemine oturan Hermite kiriş elemanının tutarlı zemin rijitlik matrisi (v₁, θ₁, v₂, θ₂): (k_s L/420)[…]."""
    a = ks * L / 420
    return [[156 * a, 22 * L * a, 54 * a, -13 * L * a],
            [22 * L * a, 4 * L * L * a, 13 * L * a, -3 * L * L * a],
            [54 * a, 13 * L * a, 156 * a, -22 * L * a],
            [-13 * L * a, -3 * L * L * a, -22 * L * a, 4 * L * L * a]]


def _k_cerceve3b(E, G, A, Iy, Iz, J, L):
    """Uzay çerçeve elemanının 12×12 yerel rijitlik matrisi; sıra u, v, w, θx, θy, θz (i ucu), aynısı (j ucu)."""
    ea, gj = E * A / L, G * J / L
    by, bz = E * Iy / L ** 3, E * Iz / L ** 3
    k = [[0] * 12 for _ in range(12)]

    def koy(i, j, v):
        k[i][j] = v
        k[j][i] = v

    koy(0, 0, ea); koy(0, 6, -ea); koy(6, 6, ea)                       # eksenel
    koy(3, 3, gj); koy(3, 9, -gj); koy(9, 9, gj)                       # burulma
    koy(1, 1, 12 * bz); koy(1, 5, 6 * L * bz); koy(1, 7, -12 * bz); koy(1, 11, 6 * L * bz)      # x'y' düzleminde eğilme
    koy(5, 5, 4 * L * L * bz); koy(5, 7, -6 * L * bz); koy(5, 11, 2 * L * L * bz)
    koy(7, 7, 12 * bz); koy(7, 11, -6 * L * bz); koy(11, 11, 4 * L * L * bz)
    koy(2, 2, 12 * by); koy(2, 4, -6 * L * by); koy(2, 8, -12 * by); koy(2, 10, -6 * L * by)    # x'z' düzleminde eğilme
    koy(4, 4, 4 * L * L * by); koy(4, 8, 6 * L * by); koy(4, 10, 2 * L * L * by)
    koy(8, 8, 12 * by); koy(8, 10, 6 * L * by); koy(10, 10, 4 * L * L * by)
    return k


def _lam3b(cx, cy, cz, sayisal, aci=0):
    """Uzay çerçeve yerel eksen matrisi λ (satırlar x', y', z'): y' elemanı içeren düşey düzlemde yukarı,
    z' = x' × y' yatay; düşey elemanda z' = Z (Kassimali kuralı).

    ``aci`` (derece; yerel eksen açısı): y' ve z' x' ekseni etrafında sağ el kuralıyla aci kadar döndürülür
    (x' izleyiciye bakarken saat yönünün tersine): y'' = cos a·y' + sin a·z', z'' = −sin a·y' + cos a·z'. aci = 90°
    → y'' = z', z'' = −y' (I_y ile I_z'nin takası ile aynı rijitlik)."""
    if sayisal:
        D = math.hypot(cx, cz)
        dusey = D < 1e-9
    else:
        D = _sade(sp.sqrt(cx * cx + cz * cz))
        dusey = (D == 0)
    if dusey:
        bir = 1.0 if sayisal else sp.Integer(1)
        sifir = 0.0 if sayisal else sp.Integer(0)
        lam = [[sifir, cy, sifir], [-cy, sifir, sifir], [sifir, sifir, bir]]
    else:
        lam = [[cx, cy, cz],
               [-cx * cy / D, D, -cy * cz / D],
               [-cz / D, 0 if not sayisal else 0.0, cx / D]]
    if aci is not None and aci != 0:
        if sayisal:
            ca, sa = math.cos(math.radians(float(aci))), math.sin(math.radians(float(aci)))
        else:
            a = sp.pi * sp.nsimplify(aci) / 180
            ca, sa = sp.cos(a), sp.sin(a)
        y2 = [ca * y + sa * z for y, z in zip(lam[1], lam[2])]
        z2 = [-sa * y + ca * z for y, z in zip(lam[1], lam[2])]
        lam = [lam[0], y2, z2]
    return lam if sayisal else [[_sade(sp.sympify(v)) for v in satir] for satir in lam]


def _T3b(lam):
    T = [[0] * 12 for _ in range(12)]
    for b in range(4):
        for i in range(3):
            for j in range(3):
                T[3 * b + i][3 * b + j] = lam[i][j]
    return T


def _sembol_degerleri(*nesneler):
    """Sembolleri (E, A, P ...) mekanizma denetimi için pozitif sayılara bağlar."""
    semb = set()
    for o in nesneler:
        if isinstance(o, (sp.Basic, sp.MatrixBase)):
            semb |= o.free_symbols
    return {s: sp.Rational(13 + 7 * i, 10) for i, s in enumerate(sorted(semb, key=lambda s: s.name))}


def _hazirla(M):
    """Eleman geometrisi, eleman matrisleri, birleştirilmiş K (yaylar dahil), yük vektörü F, mesnet listeleri."""
    tip, d, say = M.tip, M.d, M.sayisal
    bir, sifir = (1.0, 0.0) if say else (sp.Integer(1), sp.Integer(0))
    for dg in M.dugumler:   # çizim düzlemi koordinatları (3B'de izdüşüm)
        dg.px, dg.py = _izdusum(dg.x, dg.y, dg.z) if M.uc else (float(dg.x), float(dg.y))
    for e in M.elemanlar:
        a, b = M.dugumler[e.ia], M.dugumler[e.ib]
        dx, dy, dz = b.x - a.x, b.y - a.y, b.z - a.z
        e.lam = None
        if tip in ("yay", "cubuk"):
            e.L = abs(dx)
            e.c, e.s = (bir if dx > 0 else -bir), sifir
        elif tip == "kiris":
            e.L, e.c, e.s = dx, bir, sifir
        elif M.uc:
            if say:
                e.L = math.sqrt(dx * dx + dy * dy + dz * dz)
                e.yon = (dx / e.L, dy / e.L, dz / e.L)
            else:
                e.L = _sade(sp.sqrt(dx * dx + dy * dy + dz * dz))
                e.yon = (_sade(dx / e.L), _sade(dy / e.L), _sade(dz / e.L))
            e.c, e.s = e.yon[0], e.yon[1]
            if tip == "cerceve3b":
                e.lam = _lam3b(*e.yon, say, e.eksen_aci)
        elif say:
            e.L = math.hypot(dx, dy)
            e.c, e.s = dx / e.L, dy / e.L
        else:
            e.L = _sade(sp.sqrt(dx * dx + dy * dy))
            e.c, e.s = _sade(dx / e.L), _sade(dy / e.L)
        e.aci = math.degrees(math.atan2(float(dy), float(dx)))
        E, A, I, k, L, c, s = e.E, e.A, e.I, e.k, e.L, e.c, e.s
        if tip == "yay":
            kl = _mat(M, [[k, -k], [-k, k]])
        elif tip in ("cubuk", "kafes", "kafes3b"):
            ea = E * A / L
            kl = _mat(M, [[ea, -ea], [-ea, ea]])
        elif tip == "kiris":
            kl = _mat(M, _k_kiris(E, I, L))
        elif tip == "cerceve":
            kl = _mat(M, _k_cerceve(E, A, I, L))
        else:
            kl = _mat(M, _k_cerceve3b(E, e.G, A, e.Iy, e.Iz, e.J, L))
        if tip == "kafes":
            e.T = _mat(M, [[c, s, 0, 0], [0, 0, c, s]])
        elif tip == "kafes3b":
            cx, cy, cz = e.yon
            e.T = _mat(M, [[cx, cy, cz, 0, 0, 0], [0, 0, 0, cx, cy, cz]])
        elif tip == "cerceve":
            e.T = _mat(M, _T_cerceve(c, s))
        elif tip == "cerceve3b":
            e.T = _mat(M, _T3b(e.lam))
        else:
            e.T = None
        # Winkler zemini: tutarlı zemin matrisi eğilme serbestliklerine eklenir
        e.kz_yerel = None
        kl_toplam = kl
        if e.zemin is not None:
            kz4 = _k_zemin(e.zemin, L)
            if tip == "kiris":
                kz = _mat(M, kz4)
            else:
                yer = (1, 2, 4, 5)
                kz6 = [[0] * 6 for _ in range(6)]
                for a_, i_ in enumerate(yer):
                    for b_, j_ in enumerate(yer):
                        kz6[i_][j_] = kz4[a_][b_]
                kz = _mat(M, kz6)
            if not say:
                kz = _sade(kz)
            e.kz_yerel = kz
            kl_toplam = kl + kz
        if not say:
            kl = _sade(kl)
            kl_toplam = kl if e.kz_yerel is None else _sade(kl_toplam)
        # uç serbestlikleri: statik yoğunlaştırma k* = k_ff − k_fr k_rr⁻¹ k_rf (serbest bırakılan SD'lerin satır/sütunu 0)
        e.yog = None
        k_atanan = _yogunlastir(M, e, kl_toplam) if e.serbest else kl_toplam
        ke = k_atanan if e.T is None else e.T.T @ k_atanan @ e.T
        if not say:
            ke = _sade(ke)
        e.k_yerel, e.k_toplam, e.k_atanan, e.ke = kl, kl_toplam, k_atanan, ke
        e.dofs = [d * e.ia + j for j in range(d)] + [d * e.ib + j for j in range(d)]
        _eleman_yuku(M, e, M.yayili[e.idx], M.yayili_z[e.idx], M.yayili_x[e.idx])

    n = M.n
    # elastik mesnetler (yaylar): K_kur köşegene ekler
    M.yay_sd = {}
    for i, satir in enumerate(M.yay):
        for j, v in enumerate(satir):
            if v != 0:
                M.yay_sd[d * i + j] = v
    _K_kur(M)
    _F_kur(M)
    M.sabit = [d * i + j for i, fl in enumerate(M.mesnet) for j, f in enumerate(fl) if f]
    ks = set(M.sabit)
    M.serbest = [i for i in range(n) if i not in ks]
    _diyafram_kur(M)
    _mekanizma_kontrol(M)


def _K_kur(M):
    """Global K: etkin elemanların (yalnız-çekme çözümünde devre dışı bırakılanlar hariç) e.ke matrisleri toplanır,
    yay rijitlikleri köşegene eklenir. M.K_eleman (yaysız) ve M.K kurulur."""
    n, say = M.n, M.sayisal
    K = _sifir_mat(M, n)
    for e in M.elemanlar:
        if not e.etkin:
            continue
        if say:
            K[np.ix_(e.dofs, e.dofs)] += e.ke
        else:
            for a_, I_ in enumerate(e.dofs):
                for b_, J_ in enumerate(e.dofs):
                    K[I_, J_] += e.ke[a_, b_]
    M.K_eleman = K.copy() if say else _sade(K)
    for k, v in M.yay_sd.items():
        K[k, k] += v
    M.K = K if say else _sade(K)


def _yogunlastir(M, e, k):
    """Uç serbestlikli elemanın yoğunlaştırılmış yerel matrisi (tam boyutlu; serbest bırakılan r satır/sütunları 0):
    k* = k_ff − k_fr k_rr⁻¹ k_rf. Yük ve geri kazanım için e.yog = (r, f, k_rr⁻¹, A = k_rr⁻¹ k_rf, k_fr) saklanır.
    k_rr tekilse (örneğin iki uçta da N ya da T serbest; iki uçta Mz ve bir uçta Vy serbest) eleman kendi içinde
    mekanizmadır: öğretici hata."""
    n = 2 * M.d
    r = list(e.serbest)
    f = [i for i in range(n) if i not in r]
    if M.sayisal:
        krr = k[np.ix_(r, r)]
        tekil = _sifir_ozdeger_sayisi(krr) > 0
    else:
        krr = k.extract(r, r)
        det = _sade(krr.det())
        if det.free_symbols:
            det = det.subs(_sembol_degerleri(det))
        tekil = sp.simplify(det) == 0
    if tekil:
        raise MatrisHatasi(
            f"Eleman {e.no}: uç serbestlikleri ({_serbest_metin(M, e)}) elemanı kendi içinde kararsız (mekanizma) yapıyor: "
            "serbest bırakılan iç kuvvetler elemanın rijit cisim hareketini tutamaz (k_rr tekil). Örnek: iki uçta da N "
            "(eksenel) ya da iki uçta da T (burulma) serbestse eleman eksenel/burulma yönünde boşta kalır; iki uçta M ve "
            "bir uçta V serbestse eleman döner. Serbestliklerden birini kaldırın (eksenel/burulma serbestliğini yalnız bir "
            "uçta verin).")
    if M.sayisal:
        Kinv = np.linalg.inv(krr)
        kfr = k[np.ix_(f, r)]
        A = Kinv @ k[np.ix_(r, f)]
        kc = np.zeros((n, n))
        kc[np.ix_(f, f)] = k[np.ix_(f, f)] - kfr @ A
        kc = (kc + kc.T) / 2
    else:
        Kinv = _sade(krr.inv())
        kfr = k.extract(f, r)
        A = _sade(Kinv * k.extract(r, f))
        kff = _sade(k.extract(f, f) - kfr * A)
        kc = sp.zeros(n, n)
        for a_, i_ in enumerate(f):
            for b_, j_ in enumerate(f):
                kc[i_, j_] = kff[a_, b_]
    e.yog = SimpleNamespace(r=r, f=f, Kinv=Kinv, A=A, kfr=kfr)
    return kc


def _yog_yuk(M, e, fy):
    """Yoğunlaştırılmış eşdeğer düğüm yükü f* = f_f − k_fr k_rr⁻¹ f_r (r satırları 0)."""
    y = e.yog
    if M.sayisal:
        fc = np.zeros(len(fy))
        fc[y.f] = fy[y.f] - y.kfr @ (y.Kinv @ fy[y.r])
        return fc
    fr = sp.Matrix([fy[i] for i in y.r])
    ff = sp.Matrix([fy[i] for i in y.f]) - y.kfr * (y.Kinv * fr)
    fc = sp.zeros(len(fy), 1)
    for a_, i_ in enumerate(y.f):
        fc[i_] = ff[a_]
    return _sade(fc)


def _diyafram_kur(M):
    """Rijit kat diyaframı dönüşümü u = T u_r (efendi–köle / çok noktalı bağ, MPC). Diyafram yoksa indirgenmiş sistem
    tam sistemin kendisidir (T = None; K_r, sabit_r, serbest_r tam sistemin listeleridir).

    Köle s, efendi m; diyafram yatay x–z düzleminde, dönme y ekseni etrafında (sağ el: köle yer değiştirmesi ω × r,
    ω = θy ŷ, r = (x_s − x_m, 0, z_s − z_m); ŷ × x̂ = −ẑ, ŷ × ẑ = x̂):
        u_s = u_m + θy_m (z_s − z_m),   w_s = w_m − θy_m (x_s − x_m),   θy_s = θy_m;
    v, θx, θz köle düğümde bağımsız kalır. Sanal efendinin v, θx, θz serbestlikleri hiçbir elemana bağlı olmadığından
    indirgenmiş sistemde yer almaz (sıfır alınır). K_r = Tᵀ K T, F_r = Tᵀ F, mesnetler indirgenmiş SD'lerde.
    M.T (n × n_r), M.ind (sütun → tam SD), M.kol (tam SD → sütun), M.kole_sd (köle bağlı SD'ler), M.oto_sd (sanal
    efendinin sıfır SD'leri), M.n_r, M.K_r, M.sabit_r, M.serbest_r."""
    d, n = M.d, M.n
    M.kole_sd, M.oto_sd = set(), set()
    if not M.diyaframlar:
        M.T, M.ind, M.kol = None, list(range(n)), {i: i for i in range(n)}
        M.n_r, M.K_r, M.sabit_r, M.serbest_r = n, M.K, M.sabit, M.serbest
        return
    bag = {}   # köle SD -> [(efendi SD, katsayı), ...]
    for dy in M.diyaframlar:
        m = M.dugumler[dy.ana]
        if dy.sanal:
            M.oto_sd.update(d * dy.ana + j for j in _DIYAFRAM_DISI_SD)
        for si in dy.koleler:
            s = M.dugumler[si]
            dx, dz = s.x - m.x, s.z - m.z
            bag[d * si + 0] = [(d * dy.ana + 0, 1.0), (d * dy.ana + 4, dz)]     # u_s = u_m + θy_m (z_s − z_m)
            bag[d * si + 2] = [(d * dy.ana + 2, 1.0), (d * dy.ana + 4, -dx)]    # w_s = w_m − θy_m (x_s − x_m)
            bag[d * si + 4] = [(d * dy.ana + 4, 1.0)]                           # θy_s = θy_m
    M.kole_sd = set(bag)
    M.ind = [i for i in range(n) if i not in bag and i not in M.oto_sd]
    M.kol = {i: a for a, i in enumerate(M.ind)}
    M.n_r = len(M.ind)
    T = np.zeros((n, M.n_r))
    for i in M.ind:
        T[i, M.kol[i]] = 1.0
    for i, terimler in bag.items():
        for q, c in terimler:
            T[i, M.kol[q]] += c
    M.T = T
    M.K_r = _TKT(M, bag) if (M.sayisal and isinstance(M.K, np.ndarray) and not _BLAS_VAR) else T.T @ M.K @ T
    M.sabit_r = [M.kol[i] for i in M.sabit if i in M.kol]   # sanal efendinin sıfır SD'leri zaten sistem dışıdır
    ks = set(M.sabit_r)
    M.serbest_r = [a for a in range(M.n_r) if a not in ks]


_BLAS_VAR = sys.platform != "emscripten"     # Pyodide (WebAssembly) numpy'si BLAS'sızdır: yoğun matris çarpımı çok yavaş


def _TKT(M, bag):
    """K_r = Tᵀ K T, T'nin yapısıyla (bağımsız SD'ler birim sütun, köle SD'ler efendi SD'lerine katsayılı bağ): sütun / satır
    toplama — yoğun n × n_r matris çarpımı yok. Sonuç yoğun çarpımla yuvarlama düzeyinde aynıdır (toplama sırası farklı). Yalnız
    BLAS'sız numpy'de (Pyodide) kullanılır: orada yoğun çarpım binlerce SD'de dakikalar sürer (betonarme-4kat-radye: 144 s);
    masaüstü CPython'da (BLAS) yoğun çarpım hem hızlı hem de önceki sonuçlarla bayt bayt aynıdır."""
    K, ind, kol = M.K, M.ind, M.kol
    A = K[:, ind]                                  # K T: bağımsız SD sütunları (kopya)
    for i, terimler in bag.items():
        for q, c in terimler:
            A[:, kol[q]] += c * K[:, i]
    Kr = A[ind, :]                                 # Tᵀ (K T)
    for i, terimler in bag.items():
        for q, c in terimler:
            Kr[kol[q], :] += c * A[i, :]
    return Kr


def _F_indirgenmis(M):
    """İndirgenmiş yük vektörü F_r = Tᵀ F (diyafram yoksa F)."""
    return M.F if M.T is None else M.T.T @ M.F


def _eleman_yuku(M, e, parcalar, parcalar_z, parcalar_x=()):
    """Elemanın yayılı yük parçalarını (x2 = None → L) yerleştirir ve eşdeğer düğüm yüklerini kurar
    (e.parcalar, e.parcalar_z, e.parcalar_x, e.feq_yerel [tam], e.feq_yerel_c [uç serbestliğiyle yoğunlaştırılmış],
    e.feq [global, yoğunlaştırılmış]). coz_coklu her yük durumu için yeniden çağırır."""
    tip, say, L = M.tip, M.sayisal, e.L
    doldur = lambda p: [(q1, q2, x1, (L if x2 is None else x2)) for q1, q2, x1, x2 in p]  # noqa: E731
    e.parcalar = doldur(parcalar) if tip in _EGILME else []
    e.parcalar_z = doldur(parcalar_z) if tip == "cerceve3b" else []
    e.parcalar_x = doldur(parcalar_x) if tip in ("cerceve", "cerceve3b") else []
    e.feq_yerel = e.feq_yerel_c = e.feq = None
    if not (e.parcalar or e.parcalar_z or e.parcalar_x):
        return
    fy4 = _feq_parcali(L, e.parcalar, say)
    fx2 = _feq_eksenel(L, e.parcalar_x, say)
    if tip == "kiris":
        fy = _vek(M, fy4)
    elif tip == "cerceve":
        fy = _vek(M, [fx2[0], fy4[0], fy4[1], fx2[1], fy4[2], fy4[3]])
    else:
        fz4 = _feq_parcali(L, e.parcalar_z, say)    # z′ yönü: θ_y = −w′ olduğundan moment satırları ters işaretli
        fy = _vek(M, [fx2[0], fy4[0], fz4[0], 0, -fz4[1], fy4[1], fx2[1], fy4[2], fz4[2], 0, -fz4[3], fy4[3]])
    if not say:
        fy = _sade(fy)
    fc = _yog_yuk(M, e, fy) if e.yog is not None else fy
    fg = fc if e.T is None else e.T.T @ fc
    if not say:
        fg = _sade(fg)
    e.feq_yerel, e.feq_yerel_c, e.feq = fy, fc, fg


def _F_kur(M):
    """Yük vektörü: düğüm yükleri (M.F_dugum) + elemanların eşdeğer düğüm yükleri → M.F."""
    d, n, say = M.d, M.n, M.sayisal
    Fd = _sifir_vek(M, n)
    for i, satir in enumerate(M.yuk):
        for j, v in enumerate(satir):
            Fd[d * i + j] += v
    F = Fd.copy()
    for e in M.elemanlar:
        if e.feq is not None:
            for a_, I_ in enumerate(e.dofs):
                F[I_] += e.feq[a_]
    M.F_dugum, M.F = Fd, (F if say else _sade(F))


def _sifir_ozdeger_sayisi(Ks, esik=1e-10):
    """Simetrik, pozitif yarı tanımlı Ks'nin (sayısal) sıfır özdeğer sayısı = rijit/mekanizma hareketi sayısı.

    Köşegenle ölçeklenir (Jacobi: S = D^-1/2 Ks D^-1/2, D = diag Ks): çok rijit bir yay (10¹³) ile yumuşak bir
    eleman (10⁵) aynı matriste olunca ham özdeğerlerde yuvarlama gürültüsü gerçek sıfırları gizler ya da
    yumuşak modları sıfır sanırdı; ölçeklenmiş matrisin köşegeni 1'dir ve tekillik ölçeklemeyle değişmez.
    Köşegeni sıfır olan SD hiçbir şeye bağlı değildir (satırı bütünüyle sıfır): doğrudan sayılır."""
    n = Ks.shape[0]
    if n == 0:
        return 0
    dg = np.diag(Ks).astype(float)
    olcek = max(float(np.abs(Ks).max()), 1e-300)
    bagli = dg > 1e-14 * olcek
    z = int((~bagli).sum())
    if bagli.any():
        idx = np.flatnonzero(bagli)
        s = 1.0 / np.sqrt(dg[idx])
        S = Ks[np.ix_(idx, idx)] * s[:, None] * s[None, :]
        w = np.linalg.eigvalsh((S + S.T) / 2)
        z += int((w <= esik).sum())
    return z


def _mekanizma_kontrol(M):
    """İndirgenmiş K tekilse (mekanizma / yetersiz mesnet) öğretici hata verir (diyafram varsa K_r üzerinde)."""
    if not M.serbest_r:
        return
    Ks = M.K_r[np.ix_(M.serbest_r, M.serbest_r)] if M.sayisal else M.K_r.extract(M.serbest_r, M.serbest_r)
    z = 0
    if np is not None:
        if not M.sayisal:
            Ks = np.array(Ks.subs(_sembol_degerleri(Ks)).evalf(20).tolist(), dtype=float)
        z = _sifir_ozdeger_sayisi(Ks)
    else:  # pragma: no cover (numpy yoksa: kesin kip)
        z = Ks.shape[0] - Ks.subs(_sembol_degerleri(Ks)).rank()
    if z == 0:
        return
    gerek = _RIJIT_HAREKET[M.tip]
    ipucu = {
        "yay": "En az bir düğümün u serbestliğini tutun (ux: true).",
        "cubuk": "En az bir düğümün u serbestliğini tutun (ux: true).",
        "kafes": "Düzlem kafes için en az 3 bileşen tutulmalıdır: örneğin bir düğümde ux ve uy, başka bir düğümde uy "
                 "(üç mesnet çubuğu tek noktada kesişmemeli, hepsi paralel olmamalı). Ayrıca her düğümün çubuklarla "
                 "kararlı bağlandığını (üçgenleme) denetleyin.",
        "kiris": "Kiriş için en az 2 bileşen tutulmalıdır: bir ankastre (uy ve rz) ya da iki farklı noktada uy.",
        "cerceve": "Düzlem çerçeve için en az 3 bileşen tutulmalıdır: bir ankastre (ux, uy, rz) ya da bir sabit "
                   "(ux, uy) ile bir kayıcı (uy) mesnet gibi.",
        "kafes3b": "Uzay kafes için en az 6 bileşen tutulmalıdır (3 öteleme + 3 dönme engeli): örneğin bir düğümde "
                   "ux, uy, uz; ikinci düğümde uy, uz; üçüncü düğümde uy. Her düğüm en az üç bağımsız doğrultuda "
                   "çubukla tutulmalıdır (düzlem içinde kalan çubuklar düzleme dik hareketi engelleyemez).",
        "cerceve3b": "Uzay çerçeve için en az 6 bileşen tutulmalıdır: bir ankastre (ux, uy, uz, rx, ry, rz) ya da "
                     "birkaç düğümde dağıtılmış öteleme mesnetleri. Burulma serbestliğini (rx) yalnız tek elemanın "
                     "ucunda bırakmak elemanın serbestçe dönmesine yol açar.",
    }[M.tip]
    ek = ""
    if M.yay_var or M.zemin_var:
        ek = " Yaylar ve zemin yalnız bağlı oldukları serbestlikleri tutar; kalan rijit hareketleri mesnetle engelleyin."
    if getattr(M, "serbest_var", False):
        ek += (" Uç serbestlikleri (mafsal) bir düğümde bütün elemanlarda verilmiş olabilir: o düğümün dönmesini (ya da "
               "serbest bırakılan öteki serbestliğini) hiçbir eleman tutmaz ve K'da sıfır satır oluşur. Mafsalı yalnız "
               "elemanların birinde (örneğin kirişin ucunda) verin, düğümde en az bir elemanı sürekli bırakın ya da "
               "o serbestliğe mesnet/yay ekleyin (bütün çubukları mafsallı kafes benzeri düğümde dönmeyi rz ile tutun).")
    pasif = [e.no for e in M.elemanlar if not e.etkin]
    if pasif:
        ek += (f" Basınca düşen yalnız-çekme çubukları devre dışı bırakıldı (eleman {', '.join(str(n) for n in pasif)}); "
               "kalan çubuklar yükü taşıyacak kararlı bir sistem oluşturmuyor.")
    raise MatrisHatasi(
        f"Mesnetler yetersiz ya da yapı mekanizma: yapı {z} bağımsız rijit cisim hareketi (ya da mekanizma "
        f"hareketi) yapabilir; indirgenmiş K matrisi tekildir ve çözüm tek değildir. Hiç mesnetsiz bir "
        f"{_TIP_AD[M.tip]} {gerek} rijit hareket yapabilir; mesnetler bunların hepsini engellemelidir. {ipucu}{ek}")


def _coz(M):
    """K_ff u_f = F_f − K_fs u_s sistemini çözer (kesin: sympy LU, sayısal: numpy), sonra tepkileri hesaplar.
    u_s tutulu SD'lerin bilinen değerleridir (mesnet çökmesi yoksa 0). Rijit diyafram varsa sistem indirgenmiş
    SD'lerde (K_r = Tᵀ K T, F_r = Tᵀ F) çözülür, sonra u = T u_r (sayısal kip)."""
    if M.sayisal:
        u_r = np.zeros(M.n_r)
        for i, v in M.cokme.items():
            u_r[M.kol[i]] = v
        if M.serbest_r:
            rhs = _F_indirgenmis(M)[M.serbest_r].copy()
            if M.cokme:
                rhs = rhs - M.K_r[np.ix_(M.serbest_r, M.sabit_r)] @ u_r[M.sabit_r]
            u_r[M.serbest_r] = np.linalg.solve(M.K_r[np.ix_(M.serbest_r, M.serbest_r)], rhs)
        M.u_r = u_r
        u = u_r if M.T is None else M.T @ u_r
    else:
        u = sp.zeros(M.n, 1)
        for i, v in M.cokme.items():
            u[i] = v
        M.F_cokme = sp.zeros(0, 1)
        if M.serbest:
            Ks = M.K.extract(M.serbest, M.serbest)
            Fs = sp.Matrix([M.F[i] for i in M.serbest])
            if M.cokme:
                Kfs = M.K.extract(M.serbest, M.sabit)
                us_ = sp.Matrix([u[i] for i in M.sabit])
                Fs = Fs - Kfs * us_
            M.F_cokme = Fs
            us = _kesin_coz(Ks, Fs)
            for a, i in enumerate(M.serbest):
                u[i] = _sade(us[a])
    M.u = u
    _tepki_hesapla(M)


def _kesin_coz(Ks, Fs):
    """Kesin modda K_ff u_f = F_f çözümü. LUsolve'un ürettiği kesirli ifadeler köklü (√13 gibi) ya da harfli
    girdide onbinlerce terime şişer ve sadeleştirme bitmez; sympy'nin linsolve'u (polinom halkası üzerinde Gauss
    yok etme) aynı çözümü küçük ifadelerle verir, ardından cancel ile pay/payda sadeleştirilir."""
    try:
        cozum = sp.linsolve((Ks, Fs))
    except (ValueError, NotImplementedError):  # pragma: no cover
        cozum = None
    if cozum is not None and cozum is not sp.S.EmptySet and len(cozum) == 1:
        (vek,) = cozum
        if not any(getattr(x, "free_symbols", set()) - Ks.free_symbols - Fs.free_symbols for x in vek):
            return sp.Matrix([sp.cancel(x) for x in vek])
    return Ks.LUsolve(Fs)


def _tepki_hesapla(M):
    """R = K u − F: yalnız tutulu SD'lerde sıfırdan farklı olmalı (serbest SD'lerde sağlama).
    Yay (elastik mesnet) kuvvetleri F_yay = −k u ve zemin kuvvetleri F_zemin (düğümlere aktarılmış) ayrıca tutulur.
    Rijit diyaframda köle düğümün bağlı SD'lerindeki artık, diyaframın düğüme uyguladığı iç kuvvettir: tepki değil,
    M.F_diyafram'a ayrılır; tepkiler indirgenmiş sistemde R_r = Tᵀ(K u − F) ile bulunur (efendi düğüm köle
    kuvvetlerini toplar)."""
    R = M.K @ M.u - M.F
    Fd = _sifir_vek(M, M.n)
    if M.T is not None:
        R_r = M.T.T @ R
        for i in M.kole_sd:
            Fd[i] = R[i]
        R = np.zeros(M.n)
        R[M.ind] = R_r
    M.F_diyafram = Fd
    if M.sayisal:
        olcek = max(1.0, float(np.abs(M.F).max()), float(np.abs(R).max()))
        ks = set(M.sabit)
        for i in range(M.n):
            if i not in ks and abs(R[i]) <= 1e-9 * olcek:
                R[i] = 0.0
    else:
        R = _sade(R)
    M.R_tam = R
    Fy_ = _sifir_vek(M, M.n)
    for i, k in M.yay_sd.items():
        Fy_[i] = -k * M.u[i]
    M.F_yay = Fy_ if M.sayisal else _sade(Fy_)


def _eleman_kuvvetleri(M):
    """Her eleman için u_e, yerel yer değiştirme d, uç kuvvetleri f = k d − f_eq ve eksenel kuvvet N.
    Winkler zeminli elemanda k = k_kiriş + k_zemin (düğümlerin elemana uyguladığı kuvvet); zeminin düğümlere
    aktarılmış eşdeğer kuvveti f_zemin = −k_zemin d ayrıca tutulur (denge sağlaması için)."""
    tip = M.tip
    Fz_ = _sifir_vek(M, M.n)
    for e in M.elemanlar:
        ue = _al(M, M.u, e.dofs)
        e.ue = ue
        e.f_zemin = None
        if tip in _EKSENEL:
            e.dyerel = e.c * ue if e.T is None else e.T @ ue
            ea = e.k if tip == "yay" else e.E * e.A / e.L
            N = ea * (e.dyerel[1] - e.dyerel[0])
            e.N_sanal = N                     # devre dışı (yalnız-çekme) çubukta da uzamadan hesaplanan kuvvet
            if not e.etkin:
                N = _sifir_degeri(M)
            e.N = N if M.sayisal else _sade(N)
            e.ea = ea
            e.f = None
            e.sigma = None if tip == "yay" else (e.N / e.A if M.sayisal else _sade(e.N / e.A))
        else:
            dy = ue if e.T is None else e.T @ ue
            if e.yog is not None:
                dy = _geri_kazan(M, e, dy)
            if e.etkin:
                f = e.k_toplam @ dy
                if e.feq_yerel is not None:
                    f = f - e.feq_yerel
            else:   # devre dışı yalnız-çekme çubuğu: rijitliği yok; kendi yayılı yükü düğümlere eşdeğer yük olarak gider
                f = (-e.feq_yerel) if e.feq_yerel is not None else _sifir_vek(M, 2 * M.d)
            if not M.sayisal:
                dy, f = _sade(dy), _sade(f)
            if e.yog is not None and e.etkin:
                for i_ in e.yog.r:      # serbest uçta iç kuvvet tam sıfırdır (yuvarlama kalıntısı temizlenir)
                    f[i_] = _sifir_degeri(M)
            e.dyerel, e.f = dy, f
            e.N = _sifir_degeri(M) if tip == "kiris" else -f[0]
            e.N_sanal = None if tip == "kiris" else e.E * e.A / e.L * (dy[M.d] - dy[0])
            e.sigma = None
            if e.kz_yerel is not None:
                fz = -(e.kz_yerel @ dy)
                fzg = fz if e.T is None else e.T.T @ fz
                if not M.sayisal:
                    fz, fzg = _sade(fz), _sade(fzg)
                e.f_zemin, e.f_zemin_g = fz, fzg
                for a_, I_ in enumerate(e.dofs):
                    Fz_[I_] += fzg[a_]
    M.F_zemin = Fz_ if M.sayisal else _sade(Fz_)


def _geri_kazan(M, e, dy):
    """Yoğunlaştırılan (serbest bırakılan) yerel SD'lerin yer değiştirmesini geri kazanır:
    d_r = k_rr⁻¹ (f_r − k_rf d_f) = k_rr⁻¹ f_r − A d_f (serbest uçta iç kuvvet sıfır koşulundan)."""
    y = e.yog
    if M.sayisal:
        dy = np.array(dy, dtype=float).copy()
        dr = -(y.A @ dy[y.f])
        if e.feq_yerel is not None:
            dr = dr + y.Kinv @ e.feq_yerel[y.r]
        dy[y.r] = dr
        return dy
    dy = sp.Matrix(dy)
    dr = -(y.A * sp.Matrix([dy[i] for i in y.f]))
    if e.feq_yerel is not None:
        dr = dr + y.Kinv * sp.Matrix([e.feq_yerel[i] for i in y.r])
    for a_, i_ in enumerate(y.r):
        dy[i_] = _sade(dr[a_])
    return dy


def _sifir_degeri(M):
    return 0.0 if M.sayisal else sp.Integer(0)


def _bilesen_vektoru(M, i, kaynak):
    """Düğüm i'deki (fx, fy, fz, mx, my, mz) bileşenleri: kaynak[j] = j. SD'nin değeri."""
    v = {"Fx": 0, "Fy": 0, "Fz": 0, "Mx": 0, "My": 0, "Mz": 0}
    for j, ad in enumerate(_BILESEN[M.tip]):
        v["Mz" if ad == "M" else ad] = kaynak(M.d * i + j)
    return v


def _denge_hesapla(M):
    """Dış yükler (düğüm yükleri + yayılı yük bileşkeleri), mesnet tepkileri, yay ve zemin kuvvetlerinin dengesi
    (ilk düğüme göre moment). 3B'de altı bileşen, 2B'de üç."""
    tip, d = M.tip, M.d
    sifir = _sifir_degeri(M)
    dg0 = M.dugumler[0]
    x0, y0, z0 = dg0.x, dg0.y, dg0.z
    top = {k: sifir for k in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")}

    def ekle(rx, ry, rz, fx, fy, fz, mx=0, my=0, mz=0):
        top["Fx"] = top["Fx"] + fx
        top["Fy"] = top["Fy"] + fy
        top["Fz"] = top["Fz"] + fz
        top["Mx"] = top["Mx"] + mx + ry * fz - rz * fy
        top["My"] = top["My"] + my + rz * fx - rx * fz
        top["Mz"] = top["Mz"] + mz + rx * fy - ry * fx

    sabit = set(M.sabit)
    for i, dg in enumerate(M.dugumler):
        def kaynak(k, i=i):
            v = M.yuk[i][k - d * i] + M.F_yay[k] + M.F_zemin[k]
            if k in sabit:
                v = v + M.R_tam[k]
            return v
        v = _bilesen_vektoru(M, i, kaynak)
        ekle(dg.x - x0, dg.y - y0, dg.z - z0, v["Fx"], v["Fy"], v["Fz"], v["Mx"], v["My"], v["Mz"])
    for e in M.elemanlar:
        # yayılı yük parçası: bileşke W ilk düğüme (a) uygulanır, eksen boyunca dağılımın statik momenti S ise
        # x̂ × ŷ (= ẑ) ya da x̂ × ẑ (= −ŷ) yönünde kuvvet çifti olarak eklenir (W = 0 olan antisimetrik yükte de doğru)
        a = M.dugumler[e.ia]
        if tip == "cerceve3b":
            xh, yonler = e.lam[0], ((e.parcalar, e.lam[1]), (e.parcalar_z, e.lam[2]), (e.parcalar_x, e.lam[0]))
        else:
            # eksenel (x′) yükün bileşkesi eksen üzerindedir: x̂ × x̂ = 0, moment çifti yok
            xh, yonler = (e.c, e.s, 0), ((e.parcalar, (-e.s, e.c, 0)), (e.parcalar_x, (e.c, e.s, 0)))
        for parcalar, yon in yonler:
            for q1, q2, x1, x2 in parcalar:
                W, S = _yuk_bileskesi(q1, q2, x1, x2)
                cx = xh[1] * yon[2] - xh[2] * yon[1]
                cy = xh[2] * yon[0] - xh[0] * yon[2]
                cz = xh[0] * yon[1] - xh[1] * yon[0]
                ekle(a.x - x0, a.y - y0, a.z - z0, yon[0] * W, yon[1] * W, yon[2] * W, S * cx, S * cy, S * cz)
    if not M.sayisal:
        top = {k: _sade(v) for k, v in top.items()}
    if M.uc:
        M.denge = top
    else:
        M.denge = {"Fx": top["Fx"], "Fy": top["Fy"], "M": top["Mz"]}
    uKu = (M.u @ (M.K @ M.u)) if M.sayisal else _sade((M.u.T * M.K * M.u)[0, 0])
    FR = M.F + M.R_tam if M.cokme else M.F   # mesnet çökmesinde tepkiler de iş yapar
    uF = (M.u @ FR) if M.sayisal else _sade((M.u.T * FR)[0, 0])
    M.enerji = {"uKu": uKu, "uF": uF}


# ============================================================================
# Şema çizimi: bağımsız SVG (var() renkleri style özniteliğinde; <marker> ve <script> yok)
# ============================================================================
_AILE = {  # aile -> (dolgu, çizgi); PWA'nın --sema-* değişkenleri yoksa yazılı renkler kullanılır
    "a": ("var(--sema-a-bg,rgba(59,130,246,.14))", "var(--sema-a,#3b82f6)"),     # mavi
    "b": ("var(--sema-b-bg,rgba(245,158,11,.16))", "var(--sema-b,#f59e0b)"),     # amber
    "c": ("var(--sema-c-bg,rgba(16,185,129,.16))", "var(--sema-c,#10b981)"),     # yeşil
    "sil": ("var(--sema-sil-bg,rgba(239,68,68,.10))", "var(--sema-sil,#ef4444)"),  # kırmızı
}
_NOTR = "var(--sema-cizgi,#94a3b8)"
_KART = "var(--kart,#fff)"
_YAZI_AILESI = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"


def _n(v):
    """Koordinatı en çok 1 ondalıkla yazar."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _st(dolgu=None, cizgi=None):
    """var() içeren renkleri style özniteliğine koyar (sunum özniteliklerinde var() her tarayıcıda güvenilir değildir)."""
    parca = ([f"fill:{dolgu}"] if dolgu else []) + ([f"stroke:{cizgi}"] if cizgi else [])
    return f'style="{";".join(parca)}"' if parca else ""


def _sv(x, basamak=None):
    """SVG etiketi için sayı metni (gerçek eksi işareti)."""
    return _metin(x, basamak).replace("-", "−")


class _Cizim:
    """Tek bir şema karesi için küçük SVG çizici: dünya (x, y) -> ekran (piksel, y aşağı) dönüşümü ve temel parçalar.

    Her parça çizildiği yerin sınırını kaydeder; görünüm kutusu (viewBox) bu sınırlardan hesaplanır.
    Kademe sınıfları: elemanlar g0, mesnetler g1, yükler/oklar g2, yazılar g3, şekil değiştirmiş biçim g4."""

    def __init__(self, M, genislik=400.0, en_buyuk=110.0):
        self.M = M
        xs = [dg.px for dg in M.dugumler]
        ys = [dg.py for dg in M.dugumler]
        self.xmin, self.ymax = min(xs), max(ys)
        self.gx, self.gy = max(xs) - min(xs), max(ys) - min(ys)
        aday = [en_buyuk]
        if self.gx > 0:
            aday.append(genislik / self.gx)
        if self.gy > 0:
            aday.append(0.9 * genislik / self.gy)
        self.s = min(aday)
        self.arka, self.orta, self.on = [], [], []
        self._e = [math.inf, math.inf, -math.inf, -math.inf]
        pts = [self.D(i) for i in range(len(M.dugumler))]
        self.merkez = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # --- koordinat ---------------------------------------------------------
    def P(self, x, y):
        """Çizim düzlemi koordinatı (2B modelde dünya x, y) → ekran pikseli (y aşağı)."""
        return (float(x) - self.xmin) * self.s, (self.ymax - float(y)) * self.s

    def W(self, x, y, z=0.0):
        """Dünya noktası → ekran (3B modelde izdüşümle)."""
        if self.M.uc:
            return self.P(*_izdusum(x, y, z))
        return self.P(x, y)

    def yon3(self, v):
        """3B dünya yön vektörü → ekran birim vektörü (y aşağı); izdüşümde sıfırlanırsa (0, −1)."""
        u0, v0 = _izdusum(0.0, 0.0, 0.0)
        u1, v1 = _izdusum(*v)
        dx, dy = u1 - u0, -(v1 - v0)
        uz = math.hypot(dx, dy)
        return (dx / uz, dy / uz) if uz > 1e-9 else (0.0, -1.0)

    def D(self, i):
        dg = self.M.dugumler[i]
        return self.P(dg.px, dg.py)

    def E(self, e):
        return self.D(e.ia), self.D(e.ib)

    def kapsa(self, x0, y0, x1=None, y1=None):
        if x1 is None:
            x1, y1 = x0, y0
        k = self._e
        k[0], k[1] = min(k[0], x0, x1), min(k[1], y0, y1)
        k[2], k[3] = max(k[2], x0, x1), max(k[3], y0, y1)

    # --- parçalar ----------------------------------------------------------
    @staticmethod
    def _boya(aile):
        if aile is None:
            return 'stroke="currentColor"'
        if aile == "n":
            return _st(None, _NOTR)
        return _st(None, _AILE[aile][1])

    def cizgi(self, a, b, aile=None, kalin=2.4, sinif="g0", kesik=None, opak=None, katman="orta"):
        oz = (f' stroke-dasharray="{kesik}"' if kesik else "") + (f' opacity="{opak}"' if opak is not None else "")
        sn = f' class="{sinif}"' if sinif else ""
        getattr(self, katman).append(
            f'<line{sn} x1="{_n(a[0])}" y1="{_n(a[1])}" x2="{_n(b[0])}" y2="{_n(b[1])}" {self._boya(aile)} '
            f'stroke-width="{kalin}" stroke-linecap="round"{oz}/>')
        self.kapsa(a[0], a[1], b[0], b[1])

    def yol(self, pts, aile=None, kalin=2.0, sinif="g4", animasyon=False, kesik=None, opak=None, katman="orta"):
        if len(pts) < 2:
            return
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts)
        sn = f"ok {sinif}" if animasyon else sinif
        pl = ' pathLength="1"' if animasyon else ""
        oz = (f' stroke-dasharray="{kesik}"' if kesik else "") + (f' opacity="{opak}"' if opak is not None else "")
        getattr(self, katman).append(
            f'<path class="{sn}"{pl} d="{d}" fill="none" {self._boya(aile)} stroke-width="{kalin}" '
            f'stroke-linecap="round" stroke-linejoin="round"{oz}/>')
        for x, y in pts:
            self.kapsa(x, y)

    def poligon(self, pts, aile, sinif="g3", katman="arka"):
        if len(pts) < 3:
            return
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts) + " Z"
        getattr(self, katman).append(f'<path class="{sinif}" d="{d}" {_st(_AILE[aile][0], None)} stroke="none"/>')
        for x, y in pts:
            self.kapsa(x, y)

    def daire(self, c, r, aile=None, kalin=1.6, sinif="g0", katman="on", dolgu=_KART):
        if aile is None:
            boya = f'{_st(dolgu, None)} stroke="currentColor"'
        else:
            boya = _st(dolgu, _AILE[aile][1])
        getattr(self, katman).append(
            f'<circle class="{sinif}" cx="{_n(c[0])}" cy="{_n(c[1])}" r="{r}" {boya} stroke-width="{kalin}"/>')
        self.kapsa(c[0] - r, c[1] - r, c[0] + r, c[1] + r)

    def dikdortgen(self, x, y, w, h, aile=None, sinif="g0", katman="orta", kalin=1.8):
        dolgu = _AILE[aile or "a"][0]
        getattr(self, katman).append(
            f'<rect class="{sinif}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2" '
            f'{_st(dolgu, None)} stroke="currentColor" stroke-width="{kalin}"/>')
        self.kapsa(x, y, x + w, y + h)

    def yazi(self, x, y, metin, hiza="middle", boyut=None, aile=None, kalin=False, sinif="g3", opak=None, cizik=False):
        metin = str(metin)
        oz = f' class="{sinif}"' if sinif else ""
        oz += f' x="{_n(x)}" y="{_n(y)}" dy=".35em" text-anchor="{hiza}"'
        oz += ' fill="currentColor"' if aile is None else f" {_st(_AILE[aile][1], None)}"
        if boyut:
            oz += f' font-size="{boyut}"'
        if kalin:
            oz += ' font-weight="600"'
        if opak is not None:
            oz += f' opacity="{opak}"'
        self.on.append(f"<text{oz}>{_html.escape(metin, quote=False)}</text>")
        b = boyut or 13
        gen = len(metin) * b * 0.58
        x0 = x - gen / 2 if hiza == "middle" else (x if hiza == "start" else x - gen)
        self.kapsa(x0, y - b * 0.7, x0 + gen, y + b * 0.7)
        if cizik:
            self.cizgi((x0 - 1, y), (x0 + gen + 1, y), "sil", kalin=1.6, sinif=sinif, katman="on")

    def ok(self, a, b, aile, g=2, kalin=2.0, uc=7.0, katman="orta"):
        """a -> b ok: <path class="ok" pathLength="1"> gövde + <polyline class="ok-uc"> ok başı."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        uz = math.hypot(dx, dy)
        if uz < 1.0:
            return
        tx, ty = dx / uz, dy / uz
        bx, by = b[0] - tx * uc, b[1] - ty * uc
        k = uc * 0.55
        p1, p2 = (bx - ty * k, by + tx * k), (bx + ty * k, by - tx * k)
        cz = self._boya(aile)
        lst = getattr(self, katman)
        lst.append(f'<path class="ok g{g}" pathLength="1" d="M{_n(a[0])} {_n(a[1])} L{_n(b[0])} {_n(b[1])}" '
                   f'fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round"/>')
        lst.append(f'<polyline class="ok-uc g{g}" points="{_n(p1[0])},{_n(p1[1])} {_n(b[0])},{_n(b[1])} '
                   f'{_n(p2[0])},{_n(p2[1])}" fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>')
        self.kapsa(a[0], a[1], b[0], b[1])

    def yay_ok(self, c, r, ccw, aile, g=2, kalin=2.0, bas=40.0, son=280.0, katman="orta"):
        """Moment/dönme oku: c merkezli yay (ccw: saat yönünün tersi); açılar derece, dünya yönünde."""
        f0, f1 = (bas, son) if ccw else (son, bas)
        pts = []
        for k in range(25):
            f = math.radians(f0 + (f1 - f0) * k / 24)
            pts.append((c[0] + r * math.cos(f), c[1] - r * math.sin(f)))
        sg = 1.0 if f1 > f0 else -1.0
        fa = math.radians(f1)
        tx, ty = -math.sin(fa) * sg, -math.cos(fa) * sg
        b = pts[-1]
        bx, by = b[0] - tx * 6.0, b[1] - ty * 6.0
        k = 3.6
        p1, p2 = (bx - ty * k, by + tx * k), (bx + ty * k, by - tx * k)
        cz = self._boya(aile)
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts)
        lst = getattr(self, katman)
        lst.append(f'<path class="ok g{g}" pathLength="1" d="{d}" fill="none" {cz} stroke-width="{kalin}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
        lst.append(f'<polyline class="ok-uc g{g}" points="{_n(p1[0])},{_n(p1[1])} {_n(b[0])},{_n(b[1])} '
                   f'{_n(p2[0])},{_n(p2[1])}" fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>')
        self.kapsa(c[0] - r - 2, c[1] - r - 2, c[0] + r + 2, c[1] + r + 2)

    def mesnet(self, X, Y, tur, yon="alt", g=1):
        """Mesnet simgesi: sabit (üçgen), kayıcı (üçgen + ayrık çizgi), ankastre (taralı duvar). yon: gövdenin düğüme göre yeri."""
        def P(a, b):
            return {"alt": (X + a, Y + b), "ust": (X + a, Y - b), "sol": (X - b, Y + a), "sag": (X + b, Y + a)}[yon]

        def seg(p, q):
            return f"M{_n(p[0])} {_n(p[1])} L{_n(q[0])} {_n(q[1])}"

        ince = _st(None, _NOTR)
        parca = []
        if tur == "ankastre":
            d = seg(P(-16, 0), P(16, 0)) + "".join(" " + seg(P(t, 0), P(t - 6, 9)) for t in (-12, -6, 0, 6, 12))
            parca.append(f'<path d="{d}" fill="none" {ince} stroke-width="1.8" stroke-linecap="round"/>')
            self.kapsa(*P(-16, 0), *P(16, 0))
            self.kapsa(*P(-18, 10), *P(18, 10))
        else:
            h = 14 if tur == "sabit" else 12
            nok = " ".join(f"{_n(p[0])},{_n(p[1])}" for p in (P(0, 0), P(-9, h), P(9, h)))
            parca.append(f'<polygon points="{nok}" {_st(_KART, _NOTR)} stroke-width="1.8" stroke-linejoin="round"/>')
            z = h if tur == "sabit" else h + 4
            d = seg(P(-15, z), P(15, z)) + "".join(" " + seg(P(t, z), P(t - 5, z + 6)) for t in (-10, -3, 4, 11))
            parca.append(f'<path d="{d}" fill="none" {ince} stroke-width="1.8" stroke-linecap="round"/>')
            self.kapsa(*P(-16, 0), *P(16, z + 7))
        self.orta.append(f'<g class="g{g}">' + "".join(parca) + "</g>")

    @staticmethod
    def zigzag(a, b):
        """Yay simgesi için kırık çizgi noktaları."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        uz = math.hypot(dx, dy)
        if uz < 8:
            return [a, b]
        tx, ty = dx / uz, dy / uz
        nx, ny = -ty, tx
        kol = min(14.0, uz * 0.18)
        orta = uz - 2 * kol
        tepe = max(2, min(7, int(orta / 14)))
        pts = [a, (a[0] + tx * kol, a[1] + ty * kol)]
        for k in range(2 * tepe):
            t = kol + orta * (k + 0.5) / (2 * tepe)
            sg = 1 if k % 2 == 0 else -1
            pts.append((a[0] + tx * t + nx * 7.0 * sg, a[1] + ty * t + ny * 7.0 * sg))
        pts += [(a[0] + tx * (uz - kol), a[1] + ty * (uz - kol)), b]
        return pts

    def dugum_noktalari(self, aile=None, opak=None):
        for i in range(len(self.M.dugumler)):
            self.daire(self.D(i), 4.5, aile=aile, sinif="g0")

    def dugum_numaralari(self, mesafe=15.0):
        """Düğüm numaralarını yapının merkezinden dışarıya doğru yazar."""
        for i, dg in enumerate(self.M.dugumler):
            X, Y = self.D(i)
            vx, vy = X - self.merkez[0], Y - self.merkez[1] - 8.0
            uz = math.hypot(vx, vy) or 1.0
            self.yazi(X + vx / uz * mesafe, Y + vy / uz * mesafe, str(dg.no), boyut=12, kalin=True, opak=0.85)

    def mafsallar(self, r=4.2, mesafe=9.0):
        """Uç serbestliği olan eleman uçlarına küçük içi boş daire (mafsal simgesi), düğümden eleman boyunca
        ``mesafe`` piksel içeride. Moment serbestliği (M, My, Mz) dolu çizgi; başka serbestlik (N, V, T) kesikli."""
        tip = getattr(self.M, "tip", None)
        adlar = _SERBEST_ADLAR.get(tip)
        if not adlar:
            return
        d = len(adlar)
        for e in self.M.elemanlar:
            r_ = getattr(e, "serbest", None)
            if not r_:
                continue
            a, b = self.E(e)
            uz = math.hypot(b[0] - a[0], b[1] - a[1])
            if uz < 1e-9:
                continue
            t = ((b[0] - a[0]) / uz, (b[1] - a[1]) / uz)
            m = min(mesafe, 0.3 * uz)
            for uc, p0, yon in ((0, a, 1.0), (1, b, -1.0)):
                ser = [adlar[k - uc * d] for k in r_ if uc * d <= k < (uc + 1) * d]
                if not ser:
                    continue
                c = (p0[0] + yon * t[0] * m, p0[1] + yon * t[1] * m)
                moment = any(x in ("M", "My", "Mz") for x in ser)
                kalin = 1.6 if moment else 1.2
                self.on.append(f'<circle class="g0" cx="{_n(c[0])}" cy="{_n(c[1])}" r="{r}" '
                               f'{_st(_KART, None)} stroke="currentColor" stroke-width="{kalin}"'
                               + ('' if moment else ' stroke-dasharray="2 1.5"') + '/>')
                self.kapsa(c[0] - r, c[1] - r, c[0] + r, c[1] + r)

    def eleman_daireleri(self, yukari=False):
        """Eleman numaralarını orta noktada küçük daire içinde yazar (yukari: elemanın üstüne kaydırma, piksel)."""
        kayma = 24.0 if yukari is True else float(yukari or 0)
        for e in self.M.elemanlar:
            a, b = self.E(e)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - kayma
            self.daire((mx, my), 9, aile="b", kalin=1.5, sinif="g3")
            self.yazi(mx, my, str(e.no), boyut=11, kalin=True)

    # --- çıktı -------------------------------------------------------------
    def svg(self, baslik, pay=14.0):
        k = self._e
        if k[0] == math.inf:
            k = [0.0, 0.0, 10.0, 10.0]
        x0, y0 = k[0] - pay, k[1] - pay
        w, h = k[2] - k[0] + 2 * pay, k[3] - k[1] + 2 * pay
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_n(x0)} {_n(y0)} {_n(w)} {_n(h)}" '
            f'width="{_n(w)}" height="{_n(h)}" style="max-width:100%;height:auto" '
            f'font-family="{_YAZI_AILESI}" font-size="13" role="img" aria-label="{_html.escape(baslik, quote=True)}">'
            + "".join(self.arka + self.orta + self.on) + "</svg>")


# ============================================================================
# Anlatım yardımcıları: tablo, etiketli matris, diyagram verisi, ölçek
# ============================================================================
def _tablo(basliklar, satirlar):
    """md tablosu (hücrelerde '|' ve '$' bulunmamalı)."""
    def h(x):
        return str(x).replace("|", "/")
    ust = "| " + " | ".join(h(b) for b in basliklar) + " |"
    ara = "|" + "|".join("---" for _ in basliklar) + "|"
    return "\n".join([ust, ara] + ["| " + " | ".join(h(x) for x in s) + " |" for s in satirlar])


def _etiketli(A, satir_et, sut_et=None):
    """Kenarlarında SD etiketleri olan matris (KaTeX array; \\bordermatrix kullanılmaz)."""
    sut_et = satir_et if sut_et is None else sut_et
    r, c = len(satir_et), len(sut_et)
    ust = " & ".join([""] + [rf"\scriptstyle {t}" for t in sut_et])
    govde = [" & ".join([rf"\scriptstyle {satir_et[i]}"] + [_L(A[i, j]) for j in range(c)]) for i in range(r)]
    return (r"\left[\begin{array}{c|" + "c" * c + "}" + ust + r" \\ \hline " + r" \\ ".join(govde)
            + r"\end{array}\right]")


def _etiketli_vek(v, satir_et):
    govde = r" \\ ".join(rf"\scriptstyle {satir_et[i]} & {_L(v[i])}" for i in range(len(satir_et)))
    return r"\left[\begin{array}{c|c}" + govde + r"\end{array}\right]"


def _yerel_etiketler(M, e):
    a, b = e.dno
    t = M.tip
    if t in ("yay", "cubuk"):
        return [rf"u_{{{a}}}", rf"u_{{{b}}}"]
    if t in ("kafes", "kafes3b"):
        return [rf"\bar u_{{{a}}}", rf"\bar u_{{{b}}}"]
    if t == "kiris":
        return [rf"v_{{{a}}}", rf"\theta_{{{a}}}", rf"v_{{{b}}}", rf"\theta_{{{b}}}"]
    if t == "cerceve3b":
        return [x for n in (a, b) for x in (rf"\bar u_{{{n}}}", rf"\bar v_{{{n}}}", rf"\bar w_{{{n}}}",
                                             rf"\bar\theta_{{x{n}}}", rf"\bar\theta_{{y{n}}}", rf"\bar\theta_{{z{n}}}")]
    return [rf"\bar u_{{{a}}}", rf"\bar v_{{{a}}}", rf"\theta_{{{a}}}",
            rf"\bar u_{{{b}}}", rf"\bar v_{{{b}}}", rf"\theta_{{{b}}}"]


def _genel_etiketler(M, e):
    return [M.sd_tex[i] for i in e.dofs]


def _buyukluk(v):
    """Mutlak değer (sembolik ifadede eksi işareti çıkarılabiliyorsa işareti atar)."""
    return -v if _isaret_negatif(v) else v


def _sv_isaretli(x, basamak=None):
    s = _sv(x, basamak)
    return s if s.startswith("−") or s == "0" else "+" + s


def _guzel_olcek(x):
    """x'ten küçük ya da eşit en yakın 1-2-5 dizisi sayısı (ölçek çarpanı için)."""
    p = 10.0 ** math.floor(math.log10(x))
    m = x / p
    for t in (5.0, 2.0, 1.0):
        if m >= t:
            return t * p
    return p


def _ol_metin(x):
    return f"{x:g}"


def _kisa(v):
    """Yazı etiketi için kısa sayı (en çok 3 anlamlı basamak)."""
    return _sv(v, 3)


# --- diyagram verisi ---------------------------------------------------------
def _istasyonlar(M, e, adet):
    """Eleman boyunca diyagram istasyonları: adet + 1 eşit aralıklı nokta ve yayılı yük parça sınırları (x1, x2)."""
    L = e.L
    xs = [float(L) * i / adet for i in range(adet + 1)] if M.sayisal else [L * sp.Rational(i, adet) for i in range(adet + 1)]
    Lf = float(L)
    tol = 1e-9 * max(1.0, Lf)
    for parcalar in (e.parcalar, e.parcalar_z, getattr(e, "parcalar_x", [])):
        for q1, q2, x1, x2 in parcalar:
            for xb in (x1, x2):
                fb = float(xb)
                if tol < fb < Lf - tol and all(abs(fb - float(x)) > tol for x in xs):
                    xs.append(xb)
    return sorted(xs, key=float)


def _kesme_sifirlari(M, e, f1, xs):
    """Yayılı yüklü elemanda V(x) = 0 olan iç noktalar (M ekstremumları). Ardışık istasyonlar arasında q doğrusal
    olduğundan V(xa + t) = V(xa) + q_a t + (q_b − q_a) t²/(2Δ) karesel denklemi çözülür; düzgün parçada t = −V(xa)/q_a.
    Kesin kipte kökler tam (gerekirse köklü) ifadedir. Sembolik (harfli) yükte ekstremum aranmaz."""
    kokler = []
    say = M.sayisal
    for xa, xb in zip(xs[:-1], xs[1:]):
        Va = f1 + _yuk_integralleri(e.parcalar, xa, _sifir_degeri(M))[0]
        qa, qb = _q_aralik(e.parcalar, xa, xb)
        D = xb - xa
        gVa, gqa, gqb, gD = _gercek(Va), _gercek(qa), _gercek(qb), float(D)
        if gVa is None or gqa is None or gqb is None:
            continue
        tol = 1e-9 * max(1.0, gD)
        adaylar = []
        if abs(gqb - gqa) <= 1e-12 * max(abs(gqa), abs(gqb), 1e-300):
            if gqa != 0:
                adaylar.append(-Va / qa)
        else:
            k = (qb - qa) / D
            disk = qa * qa - 2 * k * Va
            gdisk = float(disk)
            if gdisk >= 0:
                kok = math.sqrt(gdisk) if say else sp.sqrt(disk)
                adaylar += [(-qa + kok) / k, (-qa - kok) / k]
        for t in adaylar:
            gt = float(t)
            if tol < gt < gD - tol:
                x = xa + t
                kokler.append(x if say else _sade(x))
    return kokler


def _ortak_istasyonlar(M, adet, parca_listeleri):
    """coz_coklu için eleman başına ORTAK istasyon kümesi: adet + 1 eşit aralıklı nokta + bütün yük durumlarının
    parça sınırlarının birleşimi (V = 0 kökleri eklenmez). Dönüş {e.idx: [x...]}; bütün durumlar ve kombinasyonlar
    aynı x'te hesaplanır, süperpozisyon istasyon-istasyon kesin olur."""
    sabit = {}
    for e in M.elemanlar:
        L = float(e.L)
        xs = [L * i / adet for i in range(adet + 1)]
        tol = 1e-9 * max(1.0, L)
        for listeler in parca_listeleri:
            for parcalar in (yayili[e.idx] for yayili in listeler):
                for q1, q2, x1, x2 in parcalar:
                    for xb in (x1, x2):
                        if xb is None:
                            continue
                        fb = float(xb)
                        if tol < fb < L - tol and all(abs(fb - x) > tol for x in xs):
                            xs.append(fb)
        sabit[e.idx] = sorted(xs)
    return sabit


def _diyagram_hazirla(M, adet=20, sabit_x=None):
    """Her eleman için boyunca x, N, V, M dizileri (yapı işaret kuralı) ve uç/ekstremum değerleri.

    ``sabit_x`` ({e.idx: [x...]}) verilirse istasyonlar bu kümedir ve V = 0 kökleri EKLENMEZ (coz_coklu: bütün yük
    durumları aynı x'te); kökler yalnız ``e.ekst`` (en büyük |M| ekstremumu) için ayrıca değerlendirilir.

    N çekme +; V(x) = f1 + Q(x); M(x) = −m1 + f1·x + MQ(x) (alt lif çekme +, yani 'sagging' +) ile
    Q(x) = ∫₀ˣ q ds, MQ(x) = ∫₀ˣ (x − s) q(s) ds parçalı doğrusal yük için kapalı formdur (düzgün q'da q·x ve q·x²/2).
    İstasyonlara parça sınırları ve V = 0 noktaları eklenir. Winkler zeminli elemanda zemin basıncı p(x) = −k_s v(x)
    (v: Hermite çökme) de kesite girer: V(x) += ∫₀ˣ p dξ, M(x) += ∫₀ˣ (x−ξ) p dξ. Uzay çerçevede ayrıca
    Vz(x) = fz1 + Qz(x), My(x) = my1 + fz1·x + MQz(x) (−z lifi çekme +) ve burulma T = −mx1 sabittir."""
    tip, say = M.tip, M.sayisal
    for e in M.elemanlar:
        L = e.L
        e.ekst = None
        e.dVz = e.dMy = e.dT = None
        if tip in _EGILME:
            z0 = _sifir_degeri(M)
            if tip == "kiris":
                f1, m1, f2, m2, N = e.f[0], e.f[1], e.f[2], e.f[3], z0
                v1, t1, v2, t2 = e.dyerel[0], e.dyerel[1], e.dyerel[2], e.dyerel[3]
            elif tip == "cerceve":
                f1, m1, f2, m2, N = e.f[1], e.f[2], e.f[4], e.f[5], -e.f[0]
                v1, t1, v2, t2 = e.dyerel[1], e.dyerel[2], e.dyerel[4], e.dyerel[5]
            else:
                f1, m1, f2, m2, N = e.f[1], e.f[5], e.f[7], e.f[11], -e.f[0]
                v1 = t1 = v2 = t2 = z0
            xs = _istasyonlar(M, e, adet) if sabit_x is None else list(sabit_x[e.idx])
            xe, kokler = None, []
            if e.parcalar and e.zemin is None:
                kokler = _kesme_sifirlari(M, e, f1, xs)   # V(x) = 0: M ekstremumları
                if kokler and sabit_x is None:
                    xs = sorted(xs + kokler, key=float)      # istasyon olarak eklenir (tek durumlu çözüm)
            V = [f1 + _yuk_integralleri(e.parcalar, x, z0)[0] for x in xs]
            Mo = [-m1 + f1 * x + _yuk_integralleri(e.parcalar, x, z0)[1] for x in xs]
            Mk = {}
            if kokler:
                for r in kokler:
                    Mk[r] = Mo[xs.index(r)] if sabit_x is None else (-m1 + f1 * r + _yuk_integralleri(e.parcalar, r, z0)[1])
                xe = max(kokler, key=lambda r: abs(float(Mk[r])))
            if e.zemin is not None:
                ks = e.zemin
                a0, a1 = v1, t1
                a2 = -3 * v1 / L ** 2 - 2 * t1 / L + 3 * v2 / L ** 2 - t2 / L
                a3 = 2 * v1 / L ** 3 + t1 / L ** 2 - 2 * v2 / L ** 3 + t2 / L ** 2
                V = [v - ks * (a0 * x + a1 * x ** 2 / 2 + a2 * x ** 3 / 3 + a3 * x ** 4 / 4) for v, x in zip(V, xs)]
                Mo = [m - ks * (a0 * x ** 2 / 2 + a1 * x ** 3 / 6 + a2 * x ** 4 / 12 + a3 * x ** 5 / 20) for m, x in zip(Mo, xs)]
                e.zemin_katsayi = (a0, a1, a2, a3)
            if not say:
                V = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in V]
                Mo = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in Mo]
            if e.parcalar_x:     # eksenel yayılı yük: N(x) = N_i − ∫₀ˣ q_x ds (parçada doğrusal yükte karesel)
                dN = [N - _yuk_integralleri(e.parcalar_x, x, z0)[0] for x in xs]
                if not say:
                    dN = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in dN]
            else:
                dN = [N] * len(xs)
            e.dx, e.dV, e.dM, e.dN = xs, V, Mo, dN
            if xe is not None:
                e.ekst = (xe, Mk[xe])
            e.m_uc, e.v_uc = (-m1, m2), (f1, -f2)
            kM, kV = Mo[-1] - m2, V[-1] + f2
            if not say and _gercek(kM) is None:
                kM = sp.simplify(kM)
            if not say and _gercek(kV) is None:
                kV = sp.simplify(kV)
            e.kontrol = (kM, kV)
            if tip == "cerceve3b":
                fz1, my1, fz2, my2, mx1 = e.f[2], e.f[4], e.f[8], e.f[10], e.f[3]
                Vz = [fz1 + _yuk_integralleri(e.parcalar_z, x, z0)[0] for x in xs]
                My = [my1 + fz1 * x + _yuk_integralleri(e.parcalar_z, x, z0)[1] for x in xs]
                if not say:
                    Vz = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in Vz]
                    My = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in My]
                e.dVz, e.dMy, e.dT = Vz, My, [-mx1] * len(xs)
                e.my_uc, e.vz_uc = (my1, -my2), (fz1, -fz2)
                kMy, kVz = My[-1] + my2, Vz[-1] + fz2
                if not say:
                    kMy, kVz = sp.simplify(kMy), sp.simplify(kVz)
                e.kontrol3 = (kMy, kVz)
            if e.yog is not None and say:
                _serbest_uclari_sifirla(M, e)
        else:
            z = _sifir_degeri(M)
            e.dx, e.dN, e.dV, e.dM = [z, L], [e.N, e.N], [z, z], [z, z]
            e.m_uc = e.v_uc = (z, z)
            e.kontrol = (z, z)


# j ucunda serbest bırakılan yerel SD → o uçta sıfırlanacak diyagram ("T" bütün eleman boyunca)
_SERBEST_DIYAGRAM = {"kiris": {2: "dV", 3: "dM"}, "cerceve": {3: "dN", 4: "dV", 5: "dM"},
                     "cerceve3b": {6: "dN", 7: "dV", 8: "dVz", 10: "dMy", 11: "dM"}}


def _serbest_uclari_sifirla(M, e):
    """Sayısal kipte serbest bırakılan j ucundaki diyagram değeri i ucundan integralle bulunur ve ~1e-14 yuvarlama
    kalıntısı taşır; serbest uçta iç kuvvet tanım gereği sıfır olduğundan tam 0 yazılır (i ucundaki değerler zaten
    uç kuvvetinden doğrudan gelir ve tam sıfırdır). Burulma bir uçta serbestse eleman boyunca T = 0."""
    for k, ad in _SERBEST_DIYAGRAM[M.tip].items():
        if k in e.yog.r:
            getattr(e, ad)[-1] = 0.0
    if M.tip == "cerceve3b" and (3 in e.yog.r or 9 in e.yog.r):
        e.dT = [0.0] * len(e.dT)


def _durum(M, e, nmax):
    if M.tip in _EGILME:
        return "eğilme"
    v = _gercek(e.N)
    if v is None:
        if e.N == 0:
            return "sıfır"
        return "basınç" if _isaret_negatif(e.N) else "çekme"
    if abs(v) <= 1e-9 * max(nmax, 1e-300) or v == 0:
        return "sıfır"
    return "çekme" if v > 0 else "basınç"


# --- şekil değiştirmiş biçim (sayısal) ----------------------------------------
def _hermite(xi, L, v1, t1, v2, t2):
    n1, n2 = 1 - 3 * xi ** 2 + 2 * xi ** 3, L * (xi - 2 * xi ** 2 + xi ** 3)
    n3, n4 = 3 * xi ** 2 - 2 * xi ** 3, L * (-xi ** 2 + xi ** 3)
    return n1 * v1 + n2 * t1 + n3 * v2 + n4 * t2


def _deplasman_ornekleri(M, e, adet=12):
    """[(taban (X, Y[, Z]), yer değiştirme (dX, dY[, dZ]))]: elemanın 0..L boyunca dünya koordinatlarında örnekleri
    (3B modelde üç bileşen)."""
    tip = M.tip
    a, b = M.dugumler[e.ia], M.dugumler[e.ib]
    xa, ya, xb, yb = float(a.x), float(a.y), float(b.x), float(b.y)
    za, zb = float(a.z), float(b.z)
    L, c, s = float(e.L), float(e.c), float(e.s)
    ue = [float(v) for v in e.ue]
    dy = [float(v) for v in e.dyerel]
    lam = [[float(v) for v in satir] for satir in e.lam] if e.lam is not None else None
    cikti = []
    for k in range(adet + 1):
        xi = k / adet
        X, Y = xa + xi * (xb - xa), ya + xi * (yb - ya)
        if tip in ("yay", "cubuk"):
            d = ((1 - xi) * ue[0] + xi * ue[1], 0.0)
        elif tip == "kafes":
            d = ((1 - xi) * ue[0] + xi * ue[2], (1 - xi) * ue[1] + xi * ue[3])
        elif tip == "kafes3b":
            d = tuple((1 - xi) * ue[j] + xi * ue[3 + j] for j in range(3))
        elif tip == "cerceve3b":
            ul = (1 - xi) * dy[0] + xi * dy[6]
            vl = _hermite(xi, L, dy[1], dy[5], dy[7], dy[11])
            wl = _hermite(xi, L, dy[2], -dy[4], dy[8], -dy[10])
            d = tuple(lam[0][j] * ul + lam[1][j] * vl + lam[2][j] * wl for j in range(3))
        else:
            if tip == "kiris":
                u1, v1, t1, u2, v2, t2 = 0.0, dy[0], dy[1], 0.0, dy[2], dy[3]
            else:
                u1, v1, t1, u2, v2, t2 = dy
            vl = _hermite(xi, L, v1, t1, v2, t2)
            ul = (1 - xi) * u1 + xi * u2
            d = (ul * c - vl * s, ul * s + vl * c)
        if M.uc:
            cikti.append(((X, Y, za + xi * (zb - za)), d))
        else:
            cikti.append(((X, Y), d))
    return cikti


def _olcek_bul(M):
    xs = [float(g.x) for g in M.dugumler]
    ys = [float(g.y) for g in M.dugumler]
    zs = [float(g.z) for g in M.dugumler]
    boyut = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    um = 0.0
    for e in M.elemanlar:
        for _, d in _deplasman_ornekleri(M, e):
            um = max(um, math.hypot(*d))
    if um <= 0 or boyut <= 0:
        return 1.0
    return _guzel_olcek(0.1 * boyut / um)


# ============================================================================
# Anlatım adımları: metin, tablo, matris (şemalar sonraki bölümde)
# ============================================================================
def _basla(anl, no, baslik, ne):
    anl.baslik(f"{no}. Adım: {baslik}", 3)
    anl.metin("**Ne yapıyoruz, neden?** " + ne)


def _birimler(M):
    k, u = M.kuvvet, M.uzunluk
    return {"F": k, "L": u, "E": f"{k}/{u}²", "G": f"{k}/{u}²", "A": f"{u}²", "I": f"{u}⁴", "Iy": f"{u}⁴",
            "Iz": f"{u}⁴", "J": f"{u}⁴", "k": f"{k}/{u}", "q": f"{k}/{u}", "qz": f"{k}/{u}", "zemin": f"{k}/{u}²",
            "M": f"{k}·{u}", "Mx": f"{k}·{u}", "My": f"{k}·{u}", "Mz": f"{k}·{u}", "Fx": k, "Fy": k, "Fz": k,
            "sigma": f"{k}/{u}²", "kx": f"{k}/{u}", "ky": f"{k}/{u}", "kz": f"{k}/{u}", "kr": f"{k}·{u}/rad",
            "krx": f"{k}·{u}/rad", "kry": f"{k}·{u}/rad", "krz": f"{k}·{u}/rad"}


def _mesnet_turu(M, i):
    """(anahtar, açıklama): anahtar ankastre / sabit / kayici / donme (mesnet yoksa None)."""
    fl, t = M.mesnet[i], M.tip
    if not any(fl):
        return None, ""
    if t in ("yay", "cubuk"):
        return "ankastre", "sabit uç (u = 0)"
    if t == "kafes3b":
        if all(fl):
            return "sabit", "sabit (küresel mafsallı) mesnet"
        return "kayici", "kayıcı mesnet (" + ", ".join(a for a, f in zip(("ux", "uy", "uz"), fl) if f) + " tutulu)"
    if t == "cerceve3b":
        if all(fl):
            return "ankastre", "ankastre mesnet (altı serbestlik tutulu)"
        if all(fl[:3]):
            return "sabit", "sabit (mafsallı) mesnet" + ("" if not any(fl[3:]) else " + bazı dönmeler tutulu")
        if any(fl[:3]):
            return "kayici", "kayıcı mesnet (" + ", ".join(a for a, f in zip(_MESNET_ANAHTAR[t], fl) if f) + " tutulu)"
        return "donme", "yalnız dönmeyi tutan mesnet"
    if t == "kafes":
        if all(fl):
            return "sabit", "sabit (mafsallı) mesnet"
        return "kayici", ("yatay hareketi tutan kayıcı mesnet" if fl[0] else "düşey hareketi tutan kayıcı mesnet")
    if t == "kiris":
        if all(fl):
            return "ankastre", "ankastre mesnet (çökme ve dönme tutulu)"
        if fl[0]:
            return "sabit", "mafsallı ya da kayıcı mesnet (çökme tutulu, dönme serbest)"
        return "donme", "dönmeyi tutan mesnet"
    if all(fl):
        return "ankastre", "ankastre mesnet"
    if fl[0] and fl[1]:
        return "sabit", "sabit (mafsallı) mesnet"
    if fl[0] or fl[1]:
        return "kayici", ("yatay hareketi tutan kayıcı mesnet" if fl[0] else "düşey hareketi tutan kayıcı mesnet")
    return "donme", "dönmeyi tutan mesnet"


def _hesap_modu_notu(M):
    if M.sayisal:
        return (f"**Hesap modu: sayısal.** Model {M.n} serbestlik derecesi (SD) içerdiği için (eşik: {SD_ESIK}) hesap "
                "numpy ile ondalık sayılarla yapılır; tam matrisler yazılmaz, özet tablolar ve şemalar gösterilir.")
    ek = " Harfli (sembolik) büyüklükler olduğu gibi taşınır." if M.sembolik else ""
    return (f"**Hesap modu: kesin.** Model {M.n} SD içerdiği için (eşik: {SD_ESIK}) hesap sympy ile kesirli sayılarla "
            "yapılır; yuvarlama hatası yoktur." + ek)


def _adim_model(M, anl):
    t, b = M.tip, _birimler(M)
    anl.baslik(M.baslik, 2)
    _basla(anl, 1, "Modeli tanıyalım: veri tabloları",
           "Matris yöntemi yapıyı yalnızca dört tabloyla tanır: düğümler, elemanlar, mesnetler ve yükler. Hesaba "
           "girmeden önce bu tabloları bir arada görüyoruz; girdide bir hata varsa en ucuz burada yakalanır.")
    anl.metin(f"**Model türü:** {_TIP_AD[t]}. Düğüm başına {M.d} serbestlik derecesi (SD): "
              f"{', '.join(_SD_ADLARI[t])}; toplam {M.n} SD. **Birimler:** kuvvet {M.kuvvet}, uzunluk {M.uzunluk}.")
    anl.metin(_hesap_modu_notu(M))
    for u in M.uyarilar:
        anl.uyari(u)

    if t in ("yay", "cubuk"):
        ust = ["Düğüm", f"x [{M.uzunluk}]"]
        sat = [[dg.no, _metin(dg.x)] for dg in M.dugumler]
    elif M.uc:
        ust = ["Düğüm", f"x [{M.uzunluk}]", f"y [{M.uzunluk}]", f"z [{M.uzunluk}]"]
        sat = [[f"{dg.no} (sanal efendi)" if dg.sanal else dg.no, _metin(dg.x), _metin(dg.y), _metin(dg.z)]
               for dg in M.dugumler]
    else:
        ust = ["Düğüm", f"x [{M.uzunluk}]", f"y [{M.uzunluk}]"]
        sat = [[dg.no, _metin(dg.x), _metin(dg.y)] for dg in M.dugumler]
    anl.metin("**Düğümler**\n\n" + _tablo(ust, sat))

    ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]"] + (["θ"] if t in ("kafes", "cerceve") else []) \
        + (["cx", "cy", "cz"] if M.uc else []) + [f"{p} [{b[p]}]" for p in _OZELLIK[t]] \
        + ([f"zemin k_s [{b['zemin']}]"] if M.zemin_var else []) \
        + (["Uç serbestliği"] if M.serbest_var else []) + (["Eksen açısı"] if M.aci_var else []) \
        + (["Yalnız çekme"] if M.yalniz_cekme_var else [])
    sat = []
    for e in M.elemanlar:
        satir = [e.no, f"{e.dno[0]} → {e.dno[1]}", _metin(e.L)]
        if t in ("kafes", "cerceve"):
            satir.append(f"{e.aci + 0.0:.2f}°")
        if M.uc:
            satir += [_metin(v, 4) for v in e.yon]
        satir += [_metin(getattr(e, p)) for p in _OZELLIK[t]]
        if M.zemin_var:
            satir.append("—" if e.zemin is None else _metin(e.zemin))
        if M.serbest_var:
            satir.append(_serbest_metin(M, e))
        if M.aci_var:
            satir.append(f"{_metin(e.eksen_aci)}°")
        if M.yalniz_cekme_var:
            satir.append("evet" if e.yalniz_cekme else "—")
        sat.append(satir)
    anl.metin("**Elemanlar**\n\n" + _tablo(ust, sat))
    if M.serbest_var:
        anl.metin("**Uç serbestlikleri (mafsal / end release):** tabloda adı geçen yerel iç kuvvet o uçta sıfırdır "
                  "(örneğin Mz serbest = o uçta moment taşınmaz; kirişin kolona mafsallı bağlanması). Eleman düğüme yine "
                  "bağlıdır; yalnız serbest bırakılan bileşen aktarılmaz. Hesapta eleman matrisi **statik yoğunlaştırma** "
                  "ile küçültülür (4. adım).")
    if M.aci_var:
        anl.metin("**Yerel eksen açısı:** elemanın $y'$, $z'$ eksenleri $x'$ etrafında sağ el kuralıyla (x′ size bakarken "
                  "saat yönünün tersine) verilen açı kadar döndürülür (yerel eksen açısı). 90° döndürmek, "
                  "$I_y$ ile $I_z$'yi takas etmekle aynı rijitliği verir.")
    if M.zemin_var:
        anl.metin("**Elastik zemin (Winkler):** k_s verilen elemanlar zemine oturur; zemin, çökmeyle orantılı dağılı "
                  "tepki verir ($p=-k_s v$). Bu, elemanın eğilme serbestliklerine eklenen bir **zemin rijitlik matrisi** "
                  "olarak hesaba girer (4. adım).")

    sat = []
    for i, dg in enumerate(M.dugumler):
        if any(M.mesnet[i]):
            parca = []
            for j in range(M.d):
                if M.mesnet[i][j]:
                    k = M.d * i + j
                    parca.append(f"{M.sd_et[k]} = {_metin(M.cokme[k])}" if k in M.cokme else f"{M.sd_et[k]} = 0")
            sat.append([dg.no, ", ".join(parca), _mesnet_turu(M, i)[1]])
    if sat:
        anl.metin("**Mesnetler** (tutulu serbestlikler)\n\n" + _tablo(["Düğüm", "Tutulu SD", "Mesnet türü"], sat))
    else:
        anl.metin("**Mesnetler:** yok" + (" (yapıyı yaylar ve/veya zemin taşır)." if (M.yay_var or M.zemin_var) else "."))
    if M.cokme:
        anl.metin("**Mesnet çökmesi (verilen yer değiştirme):** tutulu SD'lerden bazıları sıfır yerine bilinen bir değer "
                  "alır; bu değerler çözümde sağ tarafa taşınır (7. adım).")
    if M.diyaframlar:
        sat = [[dy.ad, f"{M.dugumler[dy.ana].no}{' (sanal; yalnız u, w, θy)' if dy.sanal else ''}",
                ", ".join(str(M.dugumler[i].no) for i in dy.koleler)] for dy in M.diyaframlar]
        anl.metin("**Rijit kat diyaframları** (döşeme kendi düzleminde rijit: köle düğümlerin u, w, θy serbestlikleri "
                  "efendi düğüme bağlanır; 7. adım)\n\n" + _tablo(["Diyafram", "Efendi düğüm", "Köle düğümler"], sat))
    if M.yay_var:
        ya = _YAY_ANAHTAR[t]
        ust = ["Düğüm"] + [f"{a} [{b[a]}]" for a in ya]
        sat = [[dg.no] + [_metin(M.yay[i][j]) for j in range(M.d)]
               for i, dg in enumerate(M.dugumler) if any(v != 0 for v in M.yay[i])]
        anl.metin("**Elastik mesnetler (yaylar)** — zemini ya da esnek bir mesnedi temsil eder; kuvvet = −k·(yer değiştirme)\n\n"
                  + _tablo(ust, sat))

    ad = _BILESEN[t]
    ust = ["Düğüm"] + [f"{a} [{b[a]}]" for a in ad]
    sat = [[dg.no] + [_metin(M.yuk[i][j]) for j in range(M.d)]
           for i, dg in enumerate(M.dugumler) if any(v != 0 for v in M.yuk[i])]
    if sat:
        anl.metin("**Düğüm yükleri**\n\n" + _tablo(ust, sat))
    else:
        anl.metin("**Düğüm yükleri:** yok.")
    parcali = any(_duzgun_mu(e) is None for e in M.elemanlar if e.parcalar or e.parcalar_z or e.parcalar_x)
    nitelik = ("parçalı doğrusal: $q_1 \\to q_2$ değeri $[x_1, x_2]$ aralığında doğrusal değişir; $x$ elemanın ilk "
               "düğümünden ölçülür, tek değer bütün açıklıkta düzgün yük demektir" if parcali else "düzgün yayılı")
    eksenel = any(e.parcalar_x for e in M.elemanlar)
    if t == "cerceve3b":
        qs = [[e.no, _parca_metin(e.parcalar, e.L), _parca_metin(e.parcalar_z, e.L)]
              + ([_parca_metin(e.parcalar_x, e.L)] if eksenel else [])
              for e in M.elemanlar if e.parcalar or e.parcalar_z or e.parcalar_x]
        if qs:
            anl.metin(f"**Yayılı yükler** (elemanın yerel y′ ve z′{' ve x′' if eksenel else ''} yönlerinde; {nitelik})\n\n"
                      + _tablo(["Eleman", f"q (y′) [{b['q']}]", f"qz (z′) [{b['q']}]"]
                               + ([f"qx (x′, eksenel) [{b['q']}]"] if eksenel else []), qs)
                      + "\n\nYerel y′ elemanı içeren düşey düzlemde yukarıyı gösterir; aşağı doğru yük **negatif** q ile girilir.")
    else:
        qs = [[e.no, _parca_metin(e.parcalar, e.L)] + ([_parca_metin(e.parcalar_x, e.L)] if eksenel else [])
              for e in M.elemanlar if e.parcalar or e.parcalar_x]
        if qs:
            anl.metin(f"**Yayılı yükler** (elemanın yerel y yönünde{'; qx eleman ekseni boyunca' if eksenel else ''}; {nitelik})\n\n"
                      + _tablo(["Eleman", f"q [{b['q']}]"] + ([f"qx (x′, eksenel) [{b['q']}]"] if eksenel else []), qs)
                      + "\n\nYatay ve soldan sağa giden bir elemanda yerel y yukarıyı gösterir; bu yüzden aşağı doğru yük "
                        "**negatif** q ile girilir.")
    notlar = getattr(M, "yuk_notlari", None) or []
    if notlar:
        sat = []
        for eno, g, izd, parca, carpan, bilesen in notlar:
            q1, q2 = parca[0], parca[1]
            qm = _metin(q1) if q1 == q2 else f"{_metin(q1)}→{_metin(q2)}"
            sat.append([eno, f"{qm} ({g})", "izdüşüm boyu başına" if izd else "eleman boyu başına",
                        _metin(carpan, 4) if izd else "1",
                        ", ".join(f"{ad}: {_metin(c, 4)}·q" for ad, c in bilesen) or "0"])
        anl.metin("**Global yönlü yayılı yükler** — yük global (motor) eksen yönünde verildi ($g_x$ sağa, $g_y$ yukarı, "
                  "$g_z$ dışa); elemanın yerel eksen matrisi $\\boldsymbol\\lambda$ ile yerel bileşenlere ayrıldı: "
                  "$[q_{x'}, q_{y'}, q_{z'}] = c\\,q\\,\\boldsymbol\\lambda\\,\\hat{\\mathbf g}$. İzdüşümlü yükte $q$, "
                  "elemanın yük doğrultusuna dik düzleme izdüşüm boyu $L_p = L\\sqrt{1-(\\hat{\\mathbf x}'\\cdot\\hat{\\mathbf g})^2}$ "
                  "başınadır (düşey yükte yatay izdüşüm; kar ve hareketli yük böyle verilir); eleman boyu başına şiddet "
                  "$c = L_p/L$ ($= \\cos\\theta$, θ elemanın yatayla açısı) çarpanıyla küçülür, toplam yük $q\\,L_p$ olur.\n\n"
                  + _tablo(["Eleman", f"q [{b['q']}]", "Şiddet", "c", "Yerel bileşenler"], sat))
    if M.uc:
        anl.metin("*İşaret kuralı:* x sağa, y yukarı, z düzlemden dışa (izleyiciye doğru) pozitiftir; sağ el kuralı geçerlidir: "
                  "kuvvetler eksen yönünde, momentler ve dönmeler eksen etrafında sağ el kuralıyla pozitiftir "
                  "($M_z$ düzlemdeki saat yönünün tersi momenttir).")
    else:
        anl.metin("*İşaret kuralı:* x sağa, y yukarı pozitiftir; kuvvetler eksen yönünde pozitif, moment ve dönme "
                  "saat yönünün tersine pozitiftir.")


def _adim_sd(M, anl):
    d, t = M.d, M.tip
    _basla(anl, 3, "Serbestlik dereceleri (SD) ve numaralandırma",
           "Matrislerin satır ve sütunlarına birer numara vermemiz gerekir. Her düğümün her hareket olasılığına "
           "(SD) sırayla bir numara veriyoruz; bundan sonra bu numaralar hep K matrisinin satır ve sütun numarası olacak.")
    anl.metin(f"Numaralama kuralı: \"dugumler\" listesindeki sırayla, her düğüme art arda {d} numara verilir "
              f"({', '.join(_SD_ADLARI[t])} sırasıyla). Listede i. sıradaki düğüm {d}(i−1)+1 … {d}i numaralarını alır. "
              "Python 0'dan saydığı için kodda her numaradan 1 çıkarılır.")
    ust = ["Düğüm", "SD numaraları (1'den)", "Python indisleri (0'dan)", "Tutulu mu?"]
    sat = []
    for i, dg in enumerate(M.dugumler):
        nolar = ", ".join(f"{M.sd_et[d * i + j]} = {d * i + j + 1}" for j in range(d))
        py = ", ".join(str(d * i + j) for j in range(d))
        tut = ", ".join(M.sd_et[d * i + j] for j in range(d) if M.mesnet[i][j]) or "hayır"
        sat.append([dg.no, nolar, py, tut])
    anl.metin(_tablo(ust, sat))
    sabit = [i + 1 for i in M.sabit]
    serbest = [i + 1 for i in M.serbest]
    bilinen = "yer değiştirmesi bilinen: mesnet çökmesi verilenler dışında sıfır" if M.cokme else "yer değiştirmesi sıfır"
    anl.metin(f"**Tutulu SD'ler** ({bilinen}, {len(sabit)} adet): {sabit}. "
              f"**Serbest SD'ler** (bilinmeyen, {len(serbest)} adet): {serbest}.")
    if M.diyaframlar:
        anl.metin(f"Rijit kat diyaframı: köle düğümlerin u, w, θy serbestlikleri ({len(M.kole_sd)} SD) efendi düğüme "
                  f"bağlıdır; 7. adımda dönüşüm matrisiyle bilinmeyen sayısı {M.n}'den {M.n_r}'ye iner.")
    if M.n <= 12:
        vek = ", ".join(M.sd_tex)
    else:
        vek = ", ".join(M.sd_tex[:d * 2]) + r", \ldots, " + ", ".join(M.sd_tex[-d:])
    anl.mat(rf"\mathbf{{u}} = \left[{vek}\right]^T \quad\Rightarrow\quad \mathbf{{K}}:\ {M.n}\times{M.n},\qquad "
            rf"\mathbf{{F}}:\ {M.n}\times 1")


# --- Adım 4: eleman matrisleri ---------------------------------------------
def _yerel_k_formul(M):
    """Yerel eleman matrisinin harfli (formül) biçimi (LaTeX)."""
    t = M.tip
    if t == "yay":
        return r"\mathbf{k} = k\begin{bmatrix}1&-1\\-1&1\end{bmatrix}"
    if t in ("cubuk", "kafes", "kafes3b"):
        return r"\mathbf{k} = \dfrac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}"
    if t == "kiris":
        return (r"\mathbf{k} = \dfrac{EI}{L^3}\begin{bmatrix}12&6L&-12&6L\\6L&4L^2&-6L&2L^2\\"
                r"-12&-6L&12&-6L\\6L&2L^2&-6L&4L^2\end{bmatrix}")
    if t == "cerceve3b":
        return (r"\mathbf{k} = \begin{bmatrix}"
                r"a&0&0&0&0&0&-a&0&0&0&0&0\\"
                r"0&12b_z&0&0&0&6Lb_z&0&-12b_z&0&0&0&6Lb_z\\"
                r"0&0&12b_y&0&-6Lb_y&0&0&0&-12b_y&0&-6Lb_y&0\\"
                r"0&0&0&t&0&0&0&0&0&-t&0&0\\"
                r"0&0&-6Lb_y&0&4L^2b_y&0&0&0&6Lb_y&0&2L^2b_y&0\\"
                r"0&6Lb_z&0&0&0&4L^2b_z&0&-6Lb_z&0&0&0&2L^2b_z\\"
                r"-a&0&0&0&0&0&a&0&0&0&0&0\\"
                r"0&-12b_z&0&0&0&-6Lb_z&0&12b_z&0&0&0&-6Lb_z\\"
                r"0&0&-12b_y&0&6Lb_y&0&0&0&12b_y&0&6Lb_y&0\\"
                r"0&0&0&-t&0&0&0&0&0&t&0&0\\"
                r"0&0&-6Lb_y&0&2L^2b_y&0&0&0&6Lb_y&0&4L^2b_y&0\\"
                r"0&6Lb_z&0&0&0&2L^2b_z&0&-6Lb_z&0&0&0&4L^2b_z"
                r"\end{bmatrix},\quad a=\frac{EA}{L},\ t=\frac{GJ}{L},\ b_y=\frac{EI_y}{L^3},\ b_z=\frac{EI_z}{L^3}")
    return (r"\mathbf{k} = \begin{bmatrix}"
            r"\frac{EA}{L}&0&0&-\frac{EA}{L}&0&0\\"
            r"0&\frac{12EI}{L^3}&\frac{6EI}{L^2}&0&-\frac{12EI}{L^3}&\frac{6EI}{L^2}\\"
            r"0&\frac{6EI}{L^2}&\frac{4EI}{L}&0&-\frac{6EI}{L^2}&\frac{2EI}{L}\\"
            r"-\frac{EA}{L}&0&0&\frac{EA}{L}&0&0\\"
            r"0&-\frac{12EI}{L^3}&-\frac{6EI}{L^2}&0&\frac{12EI}{L^3}&-\frac{6EI}{L^2}\\"
            r"0&\frac{6EI}{L^2}&\frac{2EI}{L}&0&-\frac{6EI}{L^2}&\frac{4EI}{L}"
            r"\end{bmatrix}")


def _geometri_latex(M, e):
    t = M.tip
    ga, gb = M.dugumler[e.ia], M.dugumler[e.ib]
    a, b = e.dno
    dx = rf"{_Lp(gb.x)} - {_Lp(ga.x)}"
    dy = rf"{_Lp(gb.y)} - {_Lp(ga.y)}"
    if t in ("yay", "cubuk"):
        return rf"L = \left|x_{{{b}}} - x_{{{a}}}\right| = \left|{dx}\right| = {_L(e.L)}"
    if t == "kiris":
        return rf"L = x_{{{b}}} - x_{{{a}}} = {dx} = {_L(e.L)}"
    if M.uc:
        dz = rf"{_Lp(gb.z)} - {_Lp(ga.z)}"
        cx, cy, cz = e.yon
        return (rf"L = \sqrt{{({dx})^2 + ({dy})^2 + ({dz})^2}} = {_L(e.L)},\quad "
                rf"c_x = \dfrac{{{dx}}}{{L}} = {_L(cx)},\quad c_y = \dfrac{{{dy}}}{{L}} = {_L(cy)},\quad "
                rf"c_z = \dfrac{{{dz}}}{{L}} = {_L(cz)}")
    aci = f"{e.aci:.2f}"
    return (rf"L = \sqrt{{({dx})^2 + ({dy})^2}} = {_L(e.L)},\quad "
            rf"c = \cos\theta = \dfrac{{{dx}}}{{L}} = {_L(e.c)},\quad "
            rf"s = \sin\theta = \dfrac{{{dy}}}{{L}} = {_L(e.s)},\quad \theta = {aci}^{{\circ}}")


def _katsayi_denklemleri(M, e):
    """Rijitlik katsayılarının sayısal açılımı (EA/L, EI/L³ ...)."""
    t, L = M.tip, e.L
    sade = (lambda v: v) if M.sayisal else _sade
    sat = []
    if t == "yay":
        sat.append(rf"k = {_L(e.k)}\ \text{{{M.kuvvet}/{M.uzunluk}}}")
    if t in ("cubuk", "kafes", "kafes3b", "cerceve", "cerceve3b"):
        ea = sade(e.E * e.A / L)
        sat.append(rf"\dfrac{{EA}}{{L}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.A)}}}{{{_Lp(L)}}} = {_L(ea)}")
    if t in ("kiris", "cerceve"):
        ei = sade(e.E * e.I / L ** 3)
        sat.append(rf"\dfrac{{EI}}{{L^3}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.I)}}}{{({_Lp(L)})^3}} = {_L(ei)}")
    if t == "cerceve3b":
        gj = sade(e.G * e.J / L)
        sat.append(rf"\dfrac{{GJ}}{{L}} = \dfrac{{{_Lp(e.G)}\cdot {_Lp(e.J)}}}{{{_Lp(L)}}} = {_L(gj)}")
        by = sade(e.E * e.Iy / L ** 3)
        bz = sade(e.E * e.Iz / L ** 3)
        sat.append(rf"\dfrac{{EI_y}}{{L^3}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.Iy)}}}{{({_Lp(L)})^3}} = {_L(by)},\qquad "
                   rf"\dfrac{{EI_z}}{{L^3}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.Iz)}}}{{({_Lp(L)})^3}} = {_L(bz)}")
    if e.zemin is not None:
        sat.append(rf"\dfrac{{k_s L}}{{420}} = \dfrac{{{_Lp(e.zemin)}\cdot {_Lp(L)}}}{{420}} = {_L(sade(e.zemin * L / 420))}")
    return sat


def _T_formul(M):
    if M.tip == "kafes":
        return r"\begin{bmatrix} c & s & 0 & 0 \\ 0 & 0 & c & s \end{bmatrix}"
    if M.tip == "kafes3b":
        return r"\begin{bmatrix} c_x & c_y & c_z & 0 & 0 & 0 \\ 0 & 0 & 0 & c_x & c_y & c_z \end{bmatrix}"
    if M.tip == "cerceve3b":
        return (r"\begin{bmatrix} \boldsymbol\lambda&0&0&0\\0&\boldsymbol\lambda&0&0\\0&0&\boldsymbol\lambda&0\\"
                r"0&0&0&\boldsymbol\lambda \end{bmatrix}")
    return (r"\begin{bmatrix} c&s&0&0&0&0 \\ -s&c&0&0&0&0 \\ 0&0&1&0&0&0 \\ "
            r"0&0&0&c&s&0 \\ 0&0&0&-s&c&0 \\ 0&0&0&0&0&1 \end{bmatrix}")


def _lam_latex(M, e):
    """Uzay çerçeve yerel eksen matrisi λ (satırlar x', y', z')."""
    lam = _mat(M, e.lam)
    return _etiketli(lam, [r"x'", r"y'", r"z'"], ["X", "Y", "Z"])


def _eleman_ayrinti(M, anl, e):
    """Tek elemanın geometrisi, yerel matrisi, T'si ve global eleman matrisi."""
    t, no = M.tip, e.no
    a, b = e.dno
    yer, gen = _yerel_etiketler(M, e), _genel_etiketler(M, e)
    anl.metin(f"**Eleman {no}** (düğüm {a} → düğüm {b})")
    anl.mat(_geometri_latex(M, e))
    for denk in _katsayi_denklemleri(M, e):
        anl.mat(denk)
    if t == "cerceve3b":
        cx, cz = _gercek(e.yon[0]), _gercek(e.yon[2])
        dusey = cx is not None and cz is not None and math.hypot(cx, cz) < 1e-9
        if dusey:
            anl.metin("Eleman **düşey** olduğundan düşey düzlem kuralı tanımsızdır; Kassimali kuralıyla $z'=Z$ alınır, "
                      "$y' = z' \\times x'$:")
        else:
            anl.metin("Yerel eksenler: $x'$ eleman boyunca; $z' = x'\\times Y/|x'\\times Y|$ yatay; "
                      "$y' = z'\\times x'$ elemanı içeren düşey düzlemde yukarı. Satırları birim vektörler olan $\\boldsymbol\\lambda$:")
        anl.mat(rf"\boldsymbol\lambda^{{({no})}} = {_lam_latex(M, e)}")
    if e.zemin is not None:
        anl.metin("Elemanın **kendi ekseninde** yazılmış kiriş rijitlik matrisi:")
        anl.mat(rf"\mathbf{{k}}^{{({no})}}_{{\text{{kiriş}}}} = {_etiketli(e.k_yerel, yer)}")
        anl.metin("Elastik zemin (Winkler) katkısı: $p=-k_s v(x)$ dağılı tepkisinin tutarlı eleman matrisi "
                  "$\\mathbf{k}_z=\\int_0^L k_s\\mathbf{N}^T\\mathbf{N}\\,dx$ (Hermite şekil fonksiyonları) — "
                  "yalnız çökme ve dönme serbestliklerine gelir:")
        anl.mat(r"\mathbf{k}_z = \dfrac{k_s L}{420}\begin{bmatrix}156&22L&54&-13L\\22L&4L^2&13L&-3L^2\\"
                r"54&13L&156&-22L\\-13L&-3L^2&-22L&4L^2\end{bmatrix}")
        anl.mat(rf"\mathbf{{k}}^{{({no})}}_z = {_etiketli(e.kz_yerel, yer)}")
        anl.metin("Elemanın toplam yerel matrisi $\\mathbf{k}=\\mathbf{k}_{\\text{kiriş}}+\\mathbf{k}_z$:")
        anl.mat(rf"\mathbf{{k}}^{{({no})}} = {_etiketli(e.k_toplam, yer)}")
        if e.T is None:
            anl.metin("Yerel eksen global eksenle çakışık olduğu için dönüşüm gerekmez; bu matris doğrudan global eleman matrisidir.")
            if e.yog is not None:
                _yogunlastirma_anlat(M, anl, e)
            return
    elif e.T is None:
        anl.metin("Yerel eksen global eksenle çakışık olduğu için dönüşüm gerekmez; yerel matris doğrudan "
                  "global eleman matrisidir. Satır ve sütun başlıkları o satırın hangi SD'ye ait olduğunu gösterir:")
        anl.mat(rf"\mathbf{{k}}^{{({no})}} = {_etiketli(e.k_yerel, yer)}")
        if e.yog is not None:
            _yogunlastirma_anlat(M, anl, e)
        return
    else:
        anl.metin("Elemanın **kendi ekseninde (yerel)** yazılmış rijitlik matrisi:")
        anl.mat(rf"\mathbf{{k}}^{{({no})}}_{{\text{{yerel}}}} = {_etiketli(e.k_yerel, yer)}")
    if e.yog is not None:
        _yogunlastirma_anlat(M, anl, e)
    anl.metin("Yerel yer değiştirmelerle global yer değiştirmeler arasındaki **dönüşüm matrisi** "
              "$\\mathbf{T}$ (sütunlar global SD'lere, satırlar yerel SD'lere karşılık gelir):")
    anl.mat(rf"\mathbf{{T}}^{{({no})}} = {_T_formul(M)} = {_etiketli(e.T, yer, gen)}")
    anl.metin("Global eksendeki eleman matrisi $\\mathbf{k}_e = \\mathbf{T}^T\\,\\mathbf{k}\\,\\mathbf{T}$:")
    anl.mat(rf"\mathbf{{k}}^{{({no})}}_e = \mathbf{{T}}^T\,\mathbf{{k}}\,\mathbf{{T}} = {_etiketli(e.ke, gen)}")


_YOGUN_KURAL = ("**Uç serbestliği (mafsal) — statik yoğunlaştırma:** serbest bırakılan yerel SD'ler $r$, kalanlar $f$ "
                "olsun. Serbest uçta ilgili iç kuvvet sıfırdır: $\\mathbf{k}_{rf}\\mathbf{d}_f+\\mathbf{k}_{rr}\\mathbf{d}_r-"
                "\\mathbf{f}_{eq,r}=\\mathbf{0}$. Buradan $\\mathbf{d}_r=\\mathbf{k}_{rr}^{-1}(\\mathbf{f}_{eq,r}-\\mathbf{k}_{rf}"
                "\\mathbf{d}_f)$ çekilip yerine konunca eleman yalnız $f$ SD'leriyle düğümlere bağlanır:")
_YOGUN_FORMUL = (r"\mathbf{k}^{*} = \mathbf{k}_{ff}-\mathbf{k}_{fr}\,\mathbf{k}_{rr}^{-1}\,\mathbf{k}_{rf},\qquad "
                 r"\mathbf{f}^{*}_{eq} = \mathbf{f}_{eq,f}-\mathbf{k}_{fr}\,\mathbf{k}_{rr}^{-1}\,\mathbf{f}_{eq,r}")


def _yogunlastirma_anlat(M, anl, e):
    """Bir elemanın uç serbestliği yoğunlaştırması (kısa): serbest SD'ler ve k* (r satır/sütunları sıfır)."""
    yer = _yerel_etiketler(M, e)
    adlar = ", ".join(f"${yer[i]}$" for i in e.yog.r)
    anl.metin(f"Bu elemanın uç serbestliği: {_serbest_metin(M, e)} → serbest bırakılan yerel SD'ler {adlar}. "
              "Statik yoğunlaştırma $\\mathbf{k}^{*}=\\mathbf{k}_{ff}-\\mathbf{k}_{fr}\\mathbf{k}_{rr}^{-1}\\mathbf{k}_{rf}$ "
              "(serbest SD'lerin satır ve sütunu sıfır olur; birleştirmeye bu matris girer):")
    anl.mat(rf"\mathbf{{k}}^{{*({e.no})}} = {_etiketli(e.k_atanan, yer)}")


def _eleman_tablosu(M):
    """Büyük modellerde eleman özeti (md tablosu)."""
    t, b = M.tip, _birimler(M)
    sade = (lambda v: v) if M.sayisal else _sade
    if t == "yay":
        ust = ["Eleman", "Düğümler", f"k [{b['k']}]"]
    elif t == "cubuk":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", f"EA/L [{b['k']}]"]
    elif t == "kafes":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "c", "s", f"EA/L [{b['k']}]"]
    elif t == "kafes3b":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "cx", "cy", "cz", f"EA/L [{b['k']}]"]
    elif t == "kiris":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", f"EI/L³ [{b['F']}/{M.uzunluk}]"]
    elif t == "cerceve3b":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "cx", "cy", "cz", "EA/L", "GJ/L", "12EIy/L³", "12EIz/L³"]
    else:
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "c", "s", "EA/L", "12EI/L³", "6EI/L²", "4EI/L"]
    if M.zemin_var:
        ust.append("k_s L/420")
    if getattr(M, "serbest_var", False):
        ust.append("Uç serbestliği")
    sat = []
    for e in M.elemanlar:
        L = e.L
        satir = [e.no, f"{e.dno[0]} → {e.dno[1]}"]
        if t == "yay":
            satir.append(_metin(e.k))
        elif t == "cubuk":
            satir += [_metin(L), _metin(sade(e.E * e.A / L))]
        elif t == "kafes":
            satir += [_metin(L), _metin(e.c), _metin(e.s), _metin(sade(e.E * e.A / L))]
        elif t == "kafes3b":
            satir += [_metin(L)] + [_metin(v, 4) for v in e.yon] + [_metin(sade(e.E * e.A / L))]
        elif t == "kiris":
            satir += [_metin(L), _metin(sade(e.E * e.I / L ** 3))]
        elif t == "cerceve3b":
            satir += [_metin(L)] + [_metin(v, 4) for v in e.yon] + [
                _metin(sade(e.E * e.A / L)), _metin(sade(e.G * e.J / L)),
                _metin(sade(12 * e.E * e.Iy / L ** 3)), _metin(sade(12 * e.E * e.Iz / L ** 3))]
        else:
            ei3 = sade(e.E * e.I / L ** 3)
            satir += [_metin(L), _metin(e.c), _metin(e.s), _metin(sade(e.E * e.A / L)), _metin(12 * ei3),
                      _metin(6 * ei3 * L), _metin(4 * ei3 * L * L)]
        if M.zemin_var:
            satir.append("—" if e.zemin is None else _metin(sade(e.zemin * L / 420)))
        if getattr(M, "serbest_var", False):
            satir.append(_serbest_metin(M, e))
        sat.append(satir)
    return _tablo(ust, sat)


_ELEMAN_ACILIS = {
    "yay": ("Yapıyı elemanlara (parçalara) ayırıp her elemanı tek başına tanımlıyoruz. Bir elemanın **rijitlik matrisi**, "
            "\"elemanın uçlarını şu kadar oynatırsam uçlarında hangi kuvvetler doğar?\" sorusunun cevabıdır. "
            "Yay için bu cevap Hooke yasasıdır: kuvvet = k × uzama."),
    "cubuk": ("Yapıyı elemanlara ayırıp her elemanın **rijitlik matrisini** yazıyoruz: elemanın uçlarını oynatırsak "
              "uçlarında hangi kuvvetler doğar? Eksenel çubukta bu cevap Hooke yasasının çubuktaki karşılığıdır: "
              "kuvvet = (EA/L) × uzama."),
    "kafes": ("Kafes çubuğu yalnız **kendi ekseni boyunca** kuvvet taşır; oysa düğüm yer değiştirmelerini ortak $x$–$y$ "
              "eksenlerinde ($u$, $v$) tanımlıyoruz. Bu yüzden önce çubuğu kendi ekseninde (yerel) tanımlar, sonra bir "
              "**dönüşüm matrisi** $\\mathbf{T}$ ile global eksenlere çeviririz: $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
    "kiris": ("Kiriş elemanının her ucunda iki serbestlik vardır: çökme $v$ ve dönme $\\theta$. Rijitlik matrisi, bu dört "
              "serbestlikten birine birim yer değiştirme verip diğerlerini tuttuğumuzda uçlarda doğan kuvvet ve "
              "momentlerdir (Euler–Bernoulli kirişi). Yatay kirişte yerel eksen global eksenle aynıdır; dönüşüm gerekmez."),
    "cerceve": ("Çerçeve elemanı hem eksenel kuvvet hem eğilme taşır. Yerel $6\\times6$ matris eksenel ($EA/L$) ve eğilme "
                "($EI/L^3$) parçalarının birleşimidir; elemanın kendi ekseninde yazılır. Eleman eğik olabildiği için "
                "dönüşüm matrisi $\\mathbf{T}$ ile global eksenlere çevrilir: $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
    "kafes3b": ("Uzay kafes çubuğu da yalnız **kendi ekseni boyunca** kuvvet taşır; düğüm yer değiştirmeleri ise üç global eksende "
                "($u$, $v$, $w$) tanımlıdır. Düzlem kafesteki $c$, $s$ çiftinin yerini üç **doğrultu kosinüsü** $c_x, c_y, c_z$ alır; "
                "dönüşüm $2\\times6$ olur ve global eleman matrisi $6\\times6$: $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
    "cerceve3b": ("Uzay çerçeve elemanı her ucunda altı serbestlikle eksenel kuvvet, iki düzlemde eğilme ve **burulma** taşır. "
                  "Yerel $12\\times12$ matris dört bağımsız parçadan kurulur: eksenel ($EA/L$), burulma ($GJ/L$), $x'y'$ düzleminde "
                  "eğilme ($EI_z$) ve $x'z'$ düzleminde eğilme ($EI_y$). Yerel eksen takımı $\\boldsymbol\\lambda$ ile global eksenlere "
                  "çevrilir: $\\mathbf{T}=\\operatorname{diag}(\\boldsymbol\\lambda,\\boldsymbol\\lambda,\\boldsymbol\\lambda,\\boldsymbol\\lambda)$, "
                  "$\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
}


def _adim_elemanlar(M, anl):
    t = M.tip
    _basla(anl, 4, "Eleman rijitlik matrisleri", _ELEMAN_ACILIS[t])
    anl.kural("Rijitlik matrisinin **$j$. sütunu**, $j$. serbestliğe birim yer değiştirme verilip diğerleri tutulduğunda "
              "elemanın uçlarında doğan kuvvetlerdir. Matris simetriktir ve sütunları toplandığında (rijit ötelenme) "
              "sıfır çıkar: eleman rijit cisim gibi hareket ederse içinde kuvvet doğmaz.")
    anl.mat(_yerel_k_formul(M))
    if t == "cerceve3b":
        anl.metin("Sıra: $[\\bar u_i, \\bar v_i, \\bar w_i, \\bar\\theta_{xi}, \\bar\\theta_{yi}, \\bar\\theta_{zi}, \\ldots]$. "
                  "$x'z'$ düzlemindeki eğilme terimlerinin işareti $x'y'$ düzlemindekinin tersidir, çünkü sağ el kuralında "
                  "$\\theta_y = -\\,dw/dx$ olur (y ekseni etrafında pozitif dönme $w$'yi azaltır).")
        anl.metin("**Yerel eksen kuralı:** $x'$ eleman boyunca (i → j); $y'$, elemanı içeren düşey düzlemde ve yukarı doğru "
                  "($z' = x'\\times Y$ yatay, $y' = z'\\times x'$); düşey elemanda $z'=Z$ alınır. Bu, düzlemdeki (z = 0, soldan "
                  "sağa) elemanlar için 2B çerçeveyle aynı yerel eksenleri verir. $I_z$ **$y'$ yönündeki yüke** (çoğu kirişte "
                  "düşey yük, kuvvetli eksen), $I_y$ ise $z'$ yönündeki yüke karşı eğilme rijitliğidir.")
    if t == "kafes3b":
        anl.metin("Çubuğun yerel uzaması düğüm hareketinin çubuk eksenine izdüşümüdür: $\\bar u = c_x u + c_y v + c_z w$. "
                  "Global eleman matrisi, $\\mathbf{c}=[c_x, c_y, c_z]$ ile $\\dfrac{EA}{L}\\begin{bmatrix}\\mathbf{c}^T\\mathbf{c} & "
                  "-\\mathbf{c}^T\\mathbf{c}\\\\ -\\mathbf{c}^T\\mathbf{c} & \\mathbf{c}^T\\mathbf{c}\\end{bmatrix}$ biçimindedir.")
    if M.zemin_var:
        anl.metin("**Elastik zemin:** zemine oturan elemanlarda kiriş matrisine Winkler zemin matrisi $\\mathbf{k}_z$ eklenir; "
                  "aşağıda her zeminli elemanda ayrıca gösterilir.")
    if M.serbest_var:
        anl.kural(_YOGUN_KURAL)
        anl.mat(_YOGUN_FORMUL)
        anl.metin("Global eleman matrisi $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}^{*}\\mathbf{T}$ olur. Çözümden sonra serbest "
                  "uçtaki yer değiştirme (örneğin mafsalın kendi dönmesi) $\\mathbf{d}_r$ ile geri kazanılır ve uç kuvvetleri "
                  "tam eleman matrisiyle $\\mathbf{f}=\\mathbf{k}\\,\\mathbf{d}-\\mathbf{f}_{eq}$ bulunur; serbest uçtaki bileşen "
                  "kendiliğinden sıfır çıkar.")
    if t in ("kafes", "cerceve"):
        if t == "kafes":
            anl.metin("$c=\\cos\\theta$ ve $s=\\sin\\theta$; $\\theta$, $x$ ekseninden çubuğa saat yönünün tersine ölçülen açıdır. "
                      "Çubuğun yerel yer değiştirmesi $\\bar u = c\\,u + s\\,v$ olur (düğüm hareketinin çubuk eksenindeki izdüşümü).")
            anl.mat(r"\mathbf{k}_e = \dfrac{EA}{L}\begin{bmatrix} c^2 & cs & -c^2 & -cs \\ cs & s^2 & -cs & -s^2 \\ "
                    r"-c^2 & -cs & c^2 & cs \\ -cs & -s^2 & cs & s^2 \end{bmatrix}")
        else:
            anl.metin("$c=\\cos\\theta$ ve $s=\\sin\\theta$; $\\theta$, $x$ ekseninden eleman eksenine saat yönünün tersine ölçülen "
                      "açıdır. Yerel yer değiştirmeler $\\bar u = c\\,u + s\\,v$, $\\bar v = -s\\,u + c\\,v$ ve $\\theta$ (dönme eksen "
                      "takımından bağımsızdır).")
    if M.sayisal:
        anl.metin(f"Model büyük olduğundan ({M.n} SD) yalnız **ilk eleman** ayrıntılı gösterilir; hepsinin özeti aşağıdaki "
                  "tablodadır. Diğer elemanlar aynı adımlarla hesaplanır.")
        _eleman_ayrinti(M, anl, M.elemanlar[0])
        ornek = next((e for e in M.elemanlar if e.yog is not None), None)
        if ornek is not None and ornek is not M.elemanlar[0]:
            anl.metin(f"**Örnek uç serbestlikli eleman: Eleman {ornek.no}** (düğüm {ornek.dno[0]} → düğüm {ornek.dno[1]})")
            _yogunlastirma_anlat(M, anl, ornek)
        anl.metin("**Tüm elemanların özeti**\n\n" + _eleman_tablosu(M))
    else:
        for e in M.elemanlar:
            _eleman_ayrinti(M, anl, e)


# --- Adım 5: birleştirme ----------------------------------------------------
GAUSS_ANLATIM_OPS = 80     # indirgenmiş K'nın toplam işlem sayısı bu eşiği aşarsa adım adım yok etme yazılmaz


def _gauss_anlatimi_sigar(M):
    """Harfli (sembolik) indirgenmiş sistemde adım adım Gauss yok etme anlatımı makul boyutta kalır mı?
    Ara ifadeler sembol sayısı ve SD sayısıyla üstel büyür; köklü sayılar (√14 gibi) sadeleştirmeyi daha da
    yavaşlatır. Sayısal (kesirli) sistemlerde anlatım her zaman yazılır."""
    Ks = M.K.extract(M.serbest, M.serbest)
    if not Ks.free_symbols:
        return True
    if sum(sp.count_ops(x) for x in Ks) > GAUSS_ANLATIM_OPS:
        return False
    if len(Ks.free_symbols) * len(M.serbest) > 12:
        return False
    # köklü sayı var mı? (sembolsüz, tam sayı olmayan üslü kuvvet)
    return not any(p.base.is_number and not p.exp.is_Integer for p in Ks.atoms(sp.Pow))


def _motor_bloklari(sonuc, anl):
    """Motor işlevinin anlatım bloklarını bizim anlatıma ekler: ilk başlık ve 'kod' blokları atılır."""
    bl = list(sonuc.anlatim.bloklar)
    if bl and bl[0][0] == "md" and bl[0][1].lstrip().startswith("#"):
        bl = bl[1:]
    for b in bl:
        if b[0] != "kod":
            anl.bloklar.append(b)


def _simetrik_mi(M, A):
    if M.sayisal:
        return bool(np.allclose(A, A.T, rtol=1e-9, atol=1e-9 * max(1.0, float(np.abs(A).max()))))
    return all(sp.simplify(x) == 0 for x in (A - A.T))


def _adim_birlestirme(M, anl):
    t = M.tip
    _basla(anl, 5, "Birleştirme (assembly): global K matrisi",
           "Elemanlar düğümlerde birbirine bağlıdır: bir düğümün hareketi o düğüme bağlı **bütün** elemanları etkiler. "
           "Bunu hesaba katmak için her eleman matrisini, kendi SD'lerinin global numaralarına karşılık gelen satır ve "
           "sütunlara **toplayarak** yapının tek bir rijitlik matrisini ($\\mathbf{K}$) kuruyoruz.")
    sat = []
    for e in M.elemanlar:
        sat.append([e.no, ", ".join(M.sd_et[i] for i in e.dofs), [i + 1 for i in e.dofs], e.dofs])
    anl.metin("**Her elemanın SD'leri hangi global satır/sütunlara denk geliyor?**\n\n"
              + _tablo(["Eleman", "Yerel SD sırası", "Global SD numaraları (1'den)", "Python indisleri (0'dan)"], sat))
    if [e.no for e in M.elemanlar] != list(range(1, len(M.elemanlar) + 1)):
        eslesme = ", ".join(f"{k}. = eleman {e.no}" for k, e in enumerate(M.elemanlar, start=1))
        anl.uyari(f"Aşağıdaki birleştirme anlatımında elemanlar listedeki sıralarıyla numaralanır: {eslesme}.")
    if not M.sayisal:
        elemanlar = [(e.ke, [i + 1 for i in e.dofs]) for e in M.elemanlar]
        r = mo.birlestir(elemanlar, M.n, ad="K", goster="yok")
        _motor_bloklari(r, anl)
    else:
        esik = 1e-12 * max(float(np.abs(M.K).max()), 1e-300)
        dolu = np.abs(M.K) > esik
        nz = int(dolu.sum())
        ii, jj = np.nonzero(dolu)
        bant = int(np.abs(ii - jj).max()) if nz else 0
        anl.metin(f"$\\mathbf{{K}}$ matrisi {M.n}×{M.n} boyutundadır ve tam olarak yazılmayacak. Yalnız aynı elemanda "
                  f"buluşan SD çiftleri sıfırdan farklıdır: {nz} terim dolu, doluluk oranı %{100.0 * nz / M.n ** 2:.1f}, "
                  f"yarı bant genişliği {bant}. Aşağıdaki **doluluk haritası** hangi terime hangi elemanın katkı verdiğini gösterir.")
        anl.sema("Doluluk haritası", _sema_doluluk(M))
        m = min(6, M.n)
        anl.metin(f"Örnek olarak $\\mathbf{{K}}$ matrisinin sol üst {m}×{m} köşesi:")
        anl.mat(rf"\mathbf{{K}}_{{1\ldots {m}}} = {_etiketli(M.K[:m, :m], M.sd_tex[:m])}")
    if M.yay_sd:
        sat = [[i + 1, M.sd_et[i], _metin(k), _metin(M.K[i, i])] for i, k in M.yay_sd.items()]
        anl.kural("**Elastik mesnet (yay):** bir düğüme bağlı yay, yapıyı $-k\\,u_i$ kuvvetiyle tutar; bu, tek serbestlikli "
                  "bir eleman gibi $\\mathbf{K}$'nın **köşegen** terimine eklenir: $K_{ii} \\mathrel{+}= k$. Zemin yayları, "
                  "temel dönme yayları ve esnek mesnetler hep bu yolla modellenir.")
        anl.metin("**Yay rijitlikleri köşegene eklendi**\n\n"
                  + _tablo(["SD no", "SD", "Yay k", "K_ii (yay sonrası)"], sat))
        if not M.sayisal and M.n <= 12:
            anl.mat(rf"\mathbf{{K}} = {_etiketli(M.K, M.sd_tex)}")
    sim = _simetrik_mi(M, M.K)
    ekle = ("" if not (M.yay_var or M.zemin_var) else
            " Yaylar ve zemin, bağlı oldukları serbestlikleri tuttuğundan bu sayı azalabilir; yine de kalan rijit "
            "hareketleri mesnet engellemelidir.")
    anl.metin(("**Sağlama:** $\\mathbf{K}$ simetriktir ($K_{ij}=K_{ji}$) ✔; her eleman matrisi simetrik olduğundan toplamı da öyledir. "
               if sim else "**Uyarı:** $\\mathbf{K}$ simetrik çıkmadı; eleman matrislerini denetleyin. ")
              + f"Henüz mesnet uygulanmadığı için yalnız elemanlardan gelen $\\mathbf{{K}}$ **tekildir**: yapı hiç tutulmadan "
                f"{_RIJIT_HAREKET[t]} bağımsız rijit cisim hareketi yapabilir (enerji harcamadan). Mesnetler bu hareketleri "
                "engelleyecek." + ekle)


# --- Adım 6: yük vektörü ------------------------------------------------------
def _parca_latex(parcalar, M, L):
    """Anlatım için parça listesi: q₁→q₂ [x₁, x₂] (düzgün bütün açıklık: yalnız q)."""
    b = f"\\ \\text{{{M.kuvvet}/{M.uzunluk}}}"
    Lf = float(L)
    return "; ".join(f"${_L(q1)}{b}$" if (q1 == q2 and float(x1) == 0.0 and abs(float(x2) - Lf) <= 1e-9 * max(1.0, Lf))
                     else f"${_L(q1)} \\to {_L(q2)}{b}$ $[{_L(x1)},\\ {_L(x2)}]\\ \\text{{{M.uzunluk}}}$"
                     for q1, q2, x1, x2 in parcalar)


def _feq_formul_parcali(M):
    return (r"\mathbf{f}_{eq} = \sum_{\text{parça}} \int_{x_1}^{x_2} \mathbf{N}^T q(x)\,dx,\qquad "
            r"q(x) = q_1 + (q_2 - q_1)\,\frac{x - x_1}{x_2 - x_1},\qquad "
            r"\mathbf{N} = \begin{bmatrix} 1-3\xi^2+2\xi^3 \\ L(\xi-2\xi^2+\xi^3) \\ 3\xi^2-2\xi^3 \\ L(-\xi^2+\xi^3) \end{bmatrix},"
            r"\ \xi = x/L")


def _feq_formul(M):
    if M.tip == "kiris":
        return (r"\mathbf{f}_{eq} = \int_0^L \mathbf{N}^T q\,dx = "
                r"\begin{bmatrix} qL/2 \\ qL^2/12 \\ qL/2 \\ -qL^2/12 \end{bmatrix}")
    if M.tip == "cerceve3b":
        return (r"\mathbf{f}_{eq} = \int_0^L \mathbf{N}^T \mathbf{q}\,dx = "
                r"\begin{bmatrix} 0 \\ qL/2 \\ q_zL/2 \\ 0 \\ -q_zL^2/12 \\ qL^2/12 \\ "
                r"0 \\ qL/2 \\ q_zL/2 \\ 0 \\ q_zL^2/12 \\ -qL^2/12 \end{bmatrix}")
    return (r"\mathbf{f}_{eq} = \int_0^L \mathbf{N}^T q\,dx = "
            r"\begin{bmatrix} 0 \\ qL/2 \\ qL^2/12 \\ 0 \\ qL/2 \\ -qL^2/12 \end{bmatrix}")


def _adim_yukler(M, anl):
    t, d = M.tip, M.d
    yayili = [e for e in M.elemanlar if e.feq is not None]
    ac = ("Denklem takımının sağ tarafı yüklerdir. Her serbestlik derecesine (SD) karşılık gelen yük, $\\mathbf{F}$ "
          "vektörünün o SD'nin satırına yazılır. Düğüme etkiyen yükler olduğu gibi yazılır")
    ac += (", elemanın içine yayılmış yükler ise önce düğümlere aktarılır." if yayili else ".")
    _basla(anl, 6, "Yük vektörü F", ac)
    if yayili:
        parcali = any(_duzgun_mu(e) is None for e in yayili) and any(e.parcalar or e.parcalar_z for e in yayili)
        anl.kural("$\\mathbf{K}\\mathbf{u}=\\mathbf{F}$ denklemi yalnız **düğümlerde** yazılır; bu yüzden eleman boyunca yayılı yük, "
                  "elemanın uçlarına **eşdeğer düğüm yükleri** olarak aktarılır: $\\mathbf{f}_{eq}=\\int_0^L \\mathbf{N}^T q\\,dx$ "
                  "($\\mathbf{N}$: şekil fonksiyonları). Düzgün $q$ için her uca $qL/2$ kuvvet ve $\\pm qL^2/12$ moment gelir "
                  "(ankastre uç tepkilerinin ters işaretlisi). Bu yalnız bir hesap kolaylığıdır: eleman içindeki gerçek $V$ ve "
                  "$M$ diyagramı 8. adımda $\\mathbf{f}_{eq}$ çıkarılarak düzeltilir."
                  + (" Uzay çerçevede $z'$ yönündeki $q_z$ için momentler $y'$ ekseni etrafındadır ve işaretleri terstir "
                     "($\\theta_y=-dw/dx$)." if t == "cerceve3b" else "")
                  + (" **Parçalı doğrusal** (üçgen/trapez ya da kısmi açıklıkta) yükte integral her parça için ayrı alınır; "
                     "Hermite kübiği × doğrusal yük 4. dereceden polinom olduğundan 3 noktalı Gauss–Legendre integrali "
                     "($x_g = \\tfrac{x_1+x_2}{2} + \\tfrac{x_2-x_1}{2}\\,\\xi_g$; $\\xi_g = 0, \\pm\\sqrt{3/5}$; "
                     "$w_g = 8/9, 5/9$) **tam** sonuç verir. Üçgen yük $0 \\to q$ için "
                     "$\\mathbf{f}_{eq} = [3qL/20,\\ qL^2/30,\\ 7qL/20,\\ -qL^2/20]$ çıkar." if parcali else ""))
        anl.mat(_feq_formul_parcali(M) if parcali else _feq_formul(M))
        for e in yayili:
            yer = _yerel_etiketler(M, e)
            if t == "cerceve3b":
                anl.metin(f"**Eleman {e.no}**: $q$ (yerel $y'$): {_parca_latex(e.parcalar, M, e.L) or '$0$'}; "
                          f"$q_z$ (yerel $z'$): {_parca_latex(e.parcalar_z, M, e.L) or '$0$'}; "
                          f"$L={_L(e.L)}\\ \\text{{{M.uzunluk}}}$.")
            else:
                anl.metin(f"**Eleman {e.no}**: $q$ = {_parca_latex(e.parcalar, M, e.L)}, $L={_L(e.L)}\\ \\text{{{M.uzunluk}}}$ "
                          "(yerel $y$ yönünde; aşağı yönlü yük negatiftir).")
            if e.parcalar_x:
                anl.metin(f"Eksenel (yerel $x'$) yayılı yük $q_x$ = {_parca_latex(e.parcalar_x, M, e.L)}: doğrusal şekil "
                          "fonksiyonlarıyla $f_{x,i} = W - S/L$, $f_{x,j} = S/L$ ($W=\\int q_x\\,dx$ bileşke, "
                          "$S=\\int q_x\\,x\\,dx$ ilk düğüme göre statik moment; kapalı form).")
            anl.mat(rf"\mathbf{{f}}_{{eq}}^{{({e.no})}} = {_etiketli_vek(e.feq_yerel, yer)}")
            if e.yog is not None:
                anl.metin("Elemanın uç serbestliği olduğundan eşdeğer yük de yoğunlaştırılır: "
                          "$\\mathbf{f}^{*}_{eq}=\\mathbf{f}_{eq,f}-\\mathbf{k}_{fr}\\mathbf{k}_{rr}^{-1}\\mathbf{f}_{eq,r}$ "
                          "(serbest uçtaki yük payı öteki uca ve sürekli bileşenlere aktarılır):")
                anl.mat(rf"\mathbf{{f}}_{{eq}}^{{*({e.no})}} = {_etiketli_vek(e.feq_yerel_c, yer)}")
            if e.T is not None:
                gen = _genel_etiketler(M, e)
                anl.metin("Eleman eğik ya da dönüşüm gerektiriyorsa eşdeğer yük global eksenlere çevrilir ($\\mathbf{T}^T\\mathbf{f}_{eq}$):")
                anl.mat(rf"\mathbf{{T}}^T\mathbf{{f}}_{{eq}}^{{{'*' if e.yog is not None else ''}({e.no})}} = {_etiketli_vek(e.feq, gen)}")
    fark = M.F - M.F_dugum
    sat = []
    for i in range(M.n):
        if M.F[i] != 0 or M.F_dugum[i] != 0:
            sat.append([f"{M.sd_et[i]} (SD {i + 1})", _metin(M.F_dugum[i]), _metin(fark[i]), _metin(M.F[i])])
    if sat:
        anl.metin("**$\\mathbf{F}$ vektörünün sıfırdan farklı satırları**\n\n"
                  + _tablo(["SD", "Düğüm yükü", "Yayılı yükten eşdeğer", "F toplam"], sat))
    else:
        anl.metin("Hiçbir yük tanımlanmadığı için $\\mathbf{F}=\\mathbf{0}$ (çözüm sıfır yer değiştirme verir).")
    b = _birimler(M)
    birim = f"Kuvvetler {M.kuvvet}" + (f", momentler {b['M']}" if t in _EGILME else "") + " cinsindendir."
    if M.n <= 12:
        anl.mat(rf"\mathbf{{F}} = {_etiketli_vek(M.F, M.sd_tex)}")
        anl.metin(birim)
    else:
        anl.metin(f"$\\mathbf{{F}}$ vektörü {M.n} satırlıdır; yukarıdaki tabloda yalnız dolu satırlar gösterildi (kalan satırlar 0). {birim}")


# ============================================================================
# Şemalar: yapı modeli, doluluk haritası, sonuçlar
# ============================================================================
_YON_VEK = {"alt": (0.0, 1.0), "ust": (0.0, -1.0), "sol": (-1.0, 0.0), "sag": (1.0, 0.0)}


def _birim_vek(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    uz = math.hypot(dx, dy) or 1.0
    return dx / uz, dy / uz


def _don(v, derece):
    f = math.radians(derece)
    return v[0] * math.cos(f) - v[1] * math.sin(f), v[0] * math.sin(f) + v[1] * math.cos(f)


def _komsu_yonler(c, M, i):
    """Düğüme bağlı elemanların ekran birim vektörleri (düğümden uzağa doğru)."""
    cikti = []
    for e in M.elemanlar:
        if e.ia == i:
            cikti.append(_birim_vek(c.D(i), c.D(e.ib)))
        elif e.ib == i:
            cikti.append(_birim_vek(c.D(i), c.D(e.ia)))
    return cikti


def _bos_yon(dolu, adet=16):
    """Dolu yönlerden en uzak yönü seçer (eşitlikte yukarıdan başlayarak ilk bulunan)."""
    en = None
    for k in range(adet):
        f = math.pi / 2 + 2 * math.pi * k / adet
        v = (math.cos(f), -math.sin(f))
        mn = math.pi
        for d in dolu:
            mn = min(mn, math.acos(max(-1.0, min(1.0, v[0] * d[0] + v[1] * d[1]))))
        if en is None or mn > en[0] + 1e-9:
            en = (mn, v)
    return en[1]


def _f(v):
    g = _gercek(v)
    return 0.0 if g is None else g


def _mesnet_yonu(c, M, i, kom, ilk_kayan):
    """(simge türü, gövde yönü): modeldeki tutulu serbestliklere göre mesnet simgesi seçer."""
    t = M.tip
    tur, _ = _mesnet_turu(M, i)
    mx = sum(v[0] for v in kom)
    my = sum(v[1] for v in kom)
    if t in ("yay", "cubuk"):
        if len(kom) >= 2:
            return "sabit", "alt"
        return "ankastre", ("sol" if mx > 0 else "sag")
    if M.uc:
        return ("ankastre" if tur in ("ankastre", "donme") else tur), ("ust" if my > 0.5 else "alt")
    if tur in ("ankastre", "donme"):
        if abs(mx) >= abs(my):
            return "ankastre", ("sol" if mx > 0 else "sag")
        return "ankastre", ("ust" if my > 0 else "alt")
    if t == "kiris":
        return ("sabit" if i == ilk_kayan else "kayici"), "alt"
    fl = M.mesnet[i]
    if tur == "kayici" and fl[0] and not fl[1]:
        return "kayici", ("sol" if mx > 0 else "sag")
    return tur, ("ust" if my > 0.5 else "alt")


def _mesnetleri_ciz(c, M, dolu):
    ilk = None
    if M.tip == "kiris":
        aday = [i for i, fl in enumerate(M.mesnet) if fl[0] and not fl[1]]
        if aday:
            ilk = min(aday, key=lambda i: float(M.dugumler[i].x))
    for i in range(len(M.dugumler)):
        if _mesnet_turu(M, i)[0] is None:
            continue
        X, Y = c.D(i)
        tur, yon = _mesnet_yonu(c, M, i, _komsu_yonler(c, M, i), ilk)
        c.mesnet(X, Y, tur, yon, g=1)
        v = _YON_VEK[yon]
        aci = 45 if tur == "ankastre" else 30
        dolu[i] += [v, _don(v, aci), _don(v, -aci)]


def _kuvvet_oku(c, M, X, Y, ad, v, aile, fmax, dolu, onek="", kom=()):
    """Düğümde tek bileşenli kuvvet/moment oku. Ok ucu düğüme yönelir; yazı kuyruğun ardındadır."""
    g = _gercek(v)
    neg = (g < 0) if g is not None else _isaret_negatif(v)
    if ad in ("M", "Mz", "Mx", "My"):
        c.yay_ok((X, Y), 17, not neg, aile, g=2)
        etiket = f"{onek}{_kisa(_buyukluk(v))} {M.kuvvet}·{M.uzunluk}"
        if ad in ("Mx", "My"):
            etiket = f"{ad} " + etiket if not onek else etiket
        kayma = {"M": 0, "Mz": 0, "Mx": 1, "My": 2}[ad]
        c.yazi(X + 22, Y - 22 - 14 * kayma, etiket, hiza="start", boyut=12)
        dolu.append((0.7, -0.7))
        return
    sg = -1.0 if neg else 1.0
    if ad == "Fz":
        wx, wy = c.yon3((0.0, 0.0, 1.0))
        d = (sg * wx, sg * wy)
    elif ad == "Fx" and M.uc:
        wx, wy = c.yon3((1.0, 0.0, 0.0))
        d = (sg * wx, sg * wy)
    else:
        wx, wy = (1.0, 0.0) if ad == "Fx" else (0.0, 1.0)
        d = (sg * wx, -sg * wy)
    uz = 30.0 + 22.0 * abs(g) / fmax if (g is not None and fmax > 0) else 44.0
    # kuyruk elemanın üstüne düşüyorsa ok düğümden dışarıya doğru çizilir (kuyruk düğümde)
    cekme = any(-d[0] * m[0] - d[1] * m[1] > 0.8 for m in kom)
    if cekme:
        kuyruk = (X + d[0] * 6.0, Y + d[1] * 6.0)
        tip = (X + d[0] * (6.0 + uz), Y + d[1] * (6.0 + uz))
        uc = tip
        yon = d
    else:
        tip = (X - d[0] * 6.0, Y - d[1] * 6.0)
        kuyruk = (X - d[0] * (6.0 + uz), Y - d[1] * (6.0 + uz))
        uc = kuyruk
        yon = (-d[0], -d[1])
    c.ok(kuyruk, tip, aile, g=2)
    metin = f"{onek}{_kisa(_buyukluk(v))} {M.kuvvet}"
    if abs(yon[0]) > 0.5:
        c.yazi(uc[0] + yon[0] * 6.0, uc[1], metin, hiza=("start" if yon[0] > 0 else "end"), boyut=12)
    else:
        c.yazi(uc[0], uc[1] + yon[1] * 12.0, metin, boyut=12)
    dolu.append(yon if not cekme else (d[0], d[1]))


def _fmax(M):
    degerler = [abs(_f(M.yuk[i][j])) for i in range(len(M.dugumler)) for j, ad in enumerate(_BILESEN[M.tip])
                if not ad.startswith("M")]
    return max(degerler or [0.0])


def _yerel_ekran_yon(c, M, e, eksen):
    """Elemanın yerel y' (eksen=1) ya da z' (eksen=2) ekseninin ekran birim vektörü (y aşağı)."""
    if M.tip == "cerceve3b":
        return c.yon3(tuple(float(v) for v in e.lam[eksen]))
    if M.tip == "kafes3b":
        return c.yon3((0.0, 1.0, 0.0))
    return (-float(e.s), -float(e.c))


def _yayili_ciz(c, M, e, parcalar, n, etiket, dolu):
    """Yayılı yük parçalarını çizer: ok boyu |q(x)| ile orantılı (trapez/üçgen biçim), düzgün yükte sabit 26 px.
    Yük işareti ok yönünü belirler (q < 0: yerel y′ tersine, yani aşağı)."""
    a, b = c.E(e)
    L = float(e.L)
    uzp = math.hypot(b[0] - a[0], b[1] - a[1])
    qmax = max((abs(_f(v)) for q1, q2, _, _ in parcalar for v in (q1, q2)), default=0.0)
    yon_kaydi = set()
    for q1, q2, x1, x2 in parcalar:
        f1, f2 = float(x1), float(x2)
        g1, g2 = _f(q1), _f(q2)
        sembolik = _gercek(q1) is None or _gercek(q2) is None
        parca_uz = uzp * (f2 - f1) / L
        adet = max(2, int(round(parca_uz / 26.0)))
        kuy = []
        for k in range(adet + 1):
            r = f1 / L + (f2 - f1) / L * k / adet
            qx = g1 + (g2 - g1) * k / adet
            if sembolik:
                qx = -1.0 if _isaret_negatif(q1 if k * 2 <= adet else q2) else 1.0
            boy = 26.0 if (sembolik or qmax <= 0) else 26.0 * abs(qx) / qmax
            d = (-n[0], -n[1]) if qx < 0 else n
            p = (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)
            kp = (p[0] - d[0] * boy, p[1] - d[1] * boy)
            if boy >= 6.0:
                c.ok(kp, (p[0] - d[0] * 3.0, p[1] - d[1] * 3.0), "b", g=2, kalin=1.8, uc=6.0)
            kuy.append(kp)
            yon_kaydi.add((-d[0], -d[1]))
        c.yol(kuy, "b", kalin=1.8, sinif="g2")
        orta = kuy[len(kuy) // 2]
        dmid = (-n[0], -n[1]) if (g1 + g2) < 0 else n
        if sembolik:
            dmid = (-n[0], -n[1]) if _isaret_negatif(q1) else n
        if q1 == q2:
            deger = _kisa(_buyukluk(q1))
        elif sembolik or g1 * g2 >= 0:
            deger = f"{_kisa(_buyukluk(q1))}→{_kisa(_buyukluk(q2))}"
        else:   # işaret değiştiren yük: değerler işaretli yazılır
            deger = f"{_kisa(q1)}→{_kisa(q2)}"
        c.yazi(orta[0] - dmid[0] * 13.0, orta[1] - dmid[1] * 13.0, f"{etiket} = {deger} {M.kuvvet}/{M.uzunluk}", boyut=12)
    for yon in yon_kaydi:
        dolu[e.ia].append(yon)
        dolu[e.ib].append(yon)


def _yaylari_ciz(c, M, dolu):
    """Elastik mesnetler: öteleme yayı zikzak (düğümden dışarı), dönme yayı küçük sarmal; etiketi k değeridir."""
    ya = _YAY_ANAHTAR[M.tip]
    for i, satir in enumerate(M.yay):
        if not any(v != 0 for v in satir):
            continue
        X, Y = c.D(i)
        kom = _komsu_yonler(c, M, i)
        for j, v in enumerate(satir):
            if v == 0:
                continue
            ad = ya[j]
            if ad.startswith("kr"):
                c.yay_ok((X, Y), 13, True, "c", g=1, kalin=1.6, bas=20.0, son=330.0)
                c.yazi(X + 18, Y + 20, f"{ad} = {_kisa(v)}", hiza="start", boyut=11)
                dolu[i].append((0.7, 0.7))
                continue
            if ad == "kz":
                w = c.yon3((0.0, 0.0, 1.0))
            elif ad == "kx" and M.uc:
                w = c.yon3((1.0, 0.0, 0.0))
            else:
                w = (1.0, 0.0) if ad == "kx" else (0.0, -1.0)
            # yay, elemanların olmadığı tarafa doğru çizilir
            if any(w[0] * m[0] + w[1] * m[1] > 0.6 for m in kom):
                w = (-w[0], -w[1])
            uc = (X + w[0] * 44.0, Y + w[1] * 44.0)
            c.yol(c.zigzag((X + w[0] * 5.0, Y + w[1] * 5.0), uc), "c", kalin=1.8, sinif="g1")
            p = (-w[1], w[0])
            c.cizgi((uc[0] - p[0] * 9, uc[1] - p[1] * 9), (uc[0] + p[0] * 9, uc[1] + p[1] * 9), "n", kalin=1.8, sinif="g1")
            c.yazi(uc[0] + w[0] * 10.0 + p[0] * 12.0, uc[1] + w[1] * 10.0 + p[1] * 12.0, f"{ad} = {_kisa(v)}", boyut=11,
                   hiza=("start" if w[0] > 0.5 else ("end" if w[0] < -0.5 else "middle")))
            dolu[i].append(w)


def _zemini_ciz(c, M):
    """Winkler zemini: elemanın −y' tarafında taralı bant ve küçük yaylar."""
    for e in M.elemanlar:
        if e.zemin is None:
            continue
        a, b = c.E(e)
        n = _yerel_ekran_yon(c, M, e, 1)
        alt = (-n[0], -n[1])
        uzp = math.hypot(b[0] - a[0], b[1] - a[1])
        adet = max(2, int(round(uzp / 30.0)))
        for k in range(adet):
            r = (k + 0.5) / adet
            p = (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)
            c.yol(c.zigzag((p[0] + alt[0] * 4.0, p[1] + alt[1] * 4.0), (p[0] + alt[0] * 26.0, p[1] + alt[1] * 26.0)),
                  "c", kalin=1.4, sinif="g1")
        p0 = (a[0] + alt[0] * 28.0, a[1] + alt[1] * 28.0)
        p1 = (b[0] + alt[0] * 28.0, b[1] + alt[1] * 28.0)
        c.cizgi(p0, p1, "n", kalin=1.6, sinif="g1")
        t = _birim_vek(p0, p1)
        for k in range(int(uzp // 9) + 1):
            q0 = (p0[0] + t[0] * 9 * k, p0[1] + t[1] * 9 * k)
            c.cizgi(q0, (q0[0] - t[0] * 5 + alt[0] * 6, q0[1] - t[1] * 5 + alt[1] * 6), "n", kalin=1.0, sinif="g1")
        mid = ((p0[0] + p1[0]) / 2 + alt[0] * 16.0, (p0[1] + p1[1]) / 2 + alt[1] * 16.0)
        c.yazi(mid[0], mid[1], f"kₛ = {_kisa(e.zemin)}", boyut=11, opak=0.85)


def _yukleri_ciz(c, M, dolu):
    t = M.tip
    fmax = _fmax(M)
    for i in range(len(M.dugumler)):
        X, Y = c.D(i)
        for j, ad in enumerate(_BILESEN[t]):
            v = M.yuk[i][j]
            if v != 0:
                _kuvvet_oku(c, M, X, Y, ad, v, "b", fmax, dolu[i], kom=_komsu_yonler(c, M, i))
    for e in M.elemanlar:
        if e.parcalar:
            _yayili_ciz(c, M, e, e.parcalar, _yerel_ekran_yon(c, M, e, 1), "q", dolu)
        if t == "cerceve3b" and e.parcalar_z:
            _yayili_ciz(c, M, e, e.parcalar_z, _yerel_ekran_yon(c, M, e, 2), "qz", dolu)
        if getattr(e, "parcalar_x", None):     # eksenel yük: eleman boyunca küçük oklar ve etiket
            a, b = c.E(e)
            uz = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            tt = ((b[0] - a[0]) / uz, (b[1] - a[1]) / uz)
            nn = (-tt[1], tt[0])
            isr = sum(_f(q1) + _f(q2) for q1, q2, _, _ in e.parcalar_x)
            yon = tt if isr >= 0 else (-tt[0], -tt[1])
            for k in (0.3, 0.5, 0.7):
                p = (a[0] + (b[0] - a[0]) * k + nn[0] * 7.0, a[1] + (b[1] - a[1]) * k + nn[1] * 7.0)
                c.ok((p[0] - yon[0] * 7.0, p[1] - yon[1] * 7.0), (p[0] + yon[0] * 7.0, p[1] + yon[1] * 7.0), "b", g=2,
                     kalin=1.6, uc=5.0)
            orta = (a[0] + (b[0] - a[0]) * 0.5 + nn[0] * 20.0, a[1] + (b[1] - a[1]) * 0.5 + nn[1] * 20.0)
            c.yazi(orta[0], orta[1], f"qx = {_parca_metin(e.parcalar_x, e.L)} {M.kuvvet}/{M.uzunluk}", boyut=11)


def _dugum_numaralari_yaz(c, M, dolu):
    for i, dg in enumerate(M.dugumler):
        X, Y = c.D(i)
        v = _bos_yon(dolu[i] + _komsu_yonler(c, M, i))
        c.yazi(X + v[0] * 15.0, Y + v[1] * 15.0, str(dg.no), boyut=12, kalin=True, opak=0.9)


def _birinci_boyut(M):
    return M.tip in ("yay", "cubuk")


def _cubuk_yuksekligi(M, e):
    amax = max((_f(x.A) for x in M.elemanlar), default=0.0)
    a = _gercek(e.A)
    return 24.0 if (a is None or amax <= 0) else 14.0 + 22.0 * a / amax


def _birinci_boyut_elemanlar(c, M):
    for e in M.elemanlar:
        a, b = c.E(e)
        if M.tip == "yay":
            c.yol(c.zigzag(a, b), None, kalin=2.0, sinif="g0")
        else:
            h = _cubuk_yuksekligi(M, e)
            c.dikdortgen(min(a[0], b[0]), a[1] - h / 2, abs(b[0] - a[0]), h, aile="a", sinif="g0")
    for e in M.elemanlar:
        a, b = c.E(e)
        mx = (a[0] + b[0]) / 2
        if M.tip == "yay":
            etiket = f"k = {_kisa(e.k)}"
        else:
            etiket = f"EA = {_kisa(e.E * e.A)}"
        c.yazi(mx, a[1] + (28.0 if M.tip == "yay" else _cubuk_yuksekligi(M, e) / 2 + 14.0), etiket, boyut=11, opak=0.85)


def _sema_yapi(M):
    """İki kare: (1) çizilmiş yapı, (2) serbestlik derecesi numaraları."""
    kareler = []
    # --- kare 1: yapı ---
    c = _Cizim(M)
    dolu = {i: [] for i in range(len(M.dugumler))}
    if _birinci_boyut(M):
        _birinci_boyut_elemanlar(c, M)
    else:
        for e in M.elemanlar:
            c.cizgi(*c.E(e), None, kalin=3.0, sinif="g0")
    if M.uc:
        _eksen_ucgeni(c, M)
    _zemini_ciz(c, M)
    _mesnetleri_ciz(c, M, dolu)
    _yaylari_ciz(c, M, dolu)
    _yukleri_ciz(c, M, dolu)
    c.mafsallar()
    c.dugum_noktalari()
    c.eleman_daireleri(yukari=(24 if M.tip == "yay" else 34) if _birinci_boyut(M) else False)
    _dugum_numaralari_yaz(c, M, dolu)
    sat = f"Düğüm numarası: yazı · eleman numarası: daire · birimler {M.kuvvet}, {M.uzunluk}"
    if M.yay_var or M.zemin_var:
        sat += " · yeşil zikzak: yay / zemin"
    if getattr(M, "serbest_var", False):
        sat += " · içi boş daire: uç serbestliği (mafsal)"
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, sat, boyut=11, opak=0.8)
    kareler.append({"baslik": "Yapı: düğümler, elemanlar, mesnetler, yükler", "svg": c.svg("Yapı modeli")})
    # --- kare 2: SD numaraları ---
    c = _Cizim(M)
    for e in M.elemanlar:
        c.cizgi(*c.E(e), None, kalin=2.2, sinif="g0", opak=0.3)
    d, t = M.d, M.tip
    wz = c.yon3((0.0, 0.0, 1.0)) if M.uc else (0.0, 1.0)
    for i, dg in enumerate(M.dugumler):
        X, Y = c.D(i)
        donme = []
        for j, ad in enumerate(_SD_ADLARI[t]):
            k = d * i + j
            aile = "sil" if M.mesnet[i][j] else "a"
            if ad == "θ":
                c.yay_ok((X, Y), 22, True, aile, g=2, kalin=1.8, bas=110.0, son=340.0)
                ax, ay = X + 33.0 * math.cos(math.radians(225)), Y - 33.0 * math.sin(math.radians(225))
                c.yazi(ax, ay, str(k + 1), boyut=12, kalin=True, aile=aile)
            elif ad in ("θx", "θy", "θz"):
                donme.append((k + 1, aile))
            elif ad == "w":
                c.ok((X + wz[0] * 12.0, Y + wz[1] * 12.0), (X + wz[0] * 44.0, Y + wz[1] * 44.0), aile, g=2, kalin=1.8)
                c.yazi(X + wz[0] * 56.0, Y + wz[1] * 56.0, str(k + 1), boyut=12, kalin=True, aile=aile)
            elif M.uc and ad == "u":
                wx = c.yon3((1.0, 0.0, 0.0))
                c.ok((X + wx[0] * 12.0, Y + wx[1] * 12.0), (X + wx[0] * 46.0, Y + wx[1] * 46.0), aile, g=2, kalin=1.8)
                c.yazi(X + wx[0] * 58.0, Y + wx[1] * 58.0, str(k + 1), boyut=12, kalin=True, aile=aile)
            elif (t in ("yay", "cubuk", "kafes", "cerceve")) and ad == "u":
                c.ok((X + 12.0, Y), (X + 48.0, Y), aile, g=2, kalin=1.8)
                c.yazi(X + 58.0, Y, str(k + 1), boyut=12, kalin=True, aile=aile)
            else:
                c.ok((X, Y - 12.0), (X, Y - 48.0), aile, g=2, kalin=1.8)
                c.yazi(X, Y - 59.0, str(k + 1), boyut=12, kalin=True, aile=aile)
        if donme:
            c.yay_ok((X, Y), 20, True, donme[0][1], g=2, kalin=1.6, bas=200.0, son=330.0)
            aile = "sil" if all(a == "sil" for _, a in donme) else "a"
            c.yazi(X - 14.0, Y + 32.0, "θ: " + ", ".join(str(no) for no, _ in donme), boyut=11, kalin=True, aile=aile, hiza="start")
        c.daire((X, Y), 10, aile=None, sinif="g0")
        c.yazi(X, Y, str(dg.no), boyut=11, kalin=True)
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0,
           "ok yanındaki sayı = SD numarası · mavi: serbest, kırmızı: tutulu"
           + (" · θ: dönme SD'leri (x, y, z)" if t == "cerceve3b" else ""), boyut=11, opak=0.8)
    kareler.append({"baslik": "Serbestlik dereceleri (SD) numaraları", "svg": c.svg("Serbestlik dereceleri")})
    return kareler


def _eksen_ucgeni(c, M):
    """3B şemalarda sol altta küçük X–Y–Z eksen takımı."""
    k = c._e
    if k[0] == math.inf:
        return
    ox, oy = k[0] - 30.0, k[3] + 30.0
    for ad, v in (("X", (1.0, 0.0, 0.0)), ("Y", (0.0, 1.0, 0.0)), ("Z", (0.0, 0.0, 1.0))):
        w = c.yon3(v)
        c.ok((ox, oy), (ox + w[0] * 26.0, oy + w[1] * 26.0), "n", g=0, kalin=1.4, uc=5.0)
        c.yazi(ox + w[0] * 34.0, oy + w[1] * 34.0, ad, boyut=11, opak=0.8)


# --- doluluk haritası (sayısal mod) -----------------------------------------
def _hucre_ciz(c, x, y, w, h, aile, sinif="g0", opak=0.85):
    c.orta.append(f'<rect class="{sinif}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="1" '
                  f'style="fill:{_AILE[aile][1]};fill-opacity:{opak}"/>')
    c.kapsa(x, y, x + w, y + h)


def _matris_haritasi(M, idx, cnt, baslik, bant=(), vurgu=False):
    c = _Cizim(M)
    m = len(idx)
    nb = min(m, 60)
    blk = -(-m // nb)
    nb = -(-m // blk)
    cs = max(3.0, min(14.0, 300.0 / nb))
    x0, y0 = 34.0, 22.0
    gen = nb * cs
    c.cizgi((x0, y0), (x0 + gen, y0), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0, y0 + gen), (x0 + gen, y0 + gen), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0, y0), (x0, y0 + gen), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0 + gen, y0), (x0 + gen, y0 + gen), "n", kalin=1.2, sinif="g0")
    for s in bant:
        p = s // blk
        c.arka.append(f'<rect class="g1" x="{_n(x0)}" y="{_n(y0 + p * cs)}" width="{_n(gen)}" height="{_n(cs)}" '
                      f'{_st(_AILE["sil"][0], None)}/>')
        c.arka.append(f'<rect class="g1" x="{_n(x0 + p * cs)}" y="{_n(y0)}" width="{_n(cs)}" height="{_n(gen)}" '
                      f'{_st(_AILE["sil"][0], None)}/>')
    for bi in range(nb):
        for bj in range(nb):
            alt = cnt[np.ix_(idx[bi * blk:(bi + 1) * blk], idx[bj * blk:(bj + 1) * blk])]
            mx = int(alt.max()) if alt.size else 0
            if mx > 0:
                _hucre_ciz(c, x0 + bj * cs, y0 + bi * cs, cs - 0.6, cs - 0.6, "a" if mx == 1 else "b")
    adim = max(1, nb // 10)
    for p in range(0, nb, adim):
        no = str(idx[p * blk] + 1)
        c.yazi(x0 + (p + 0.5) * cs, y0 - 9.0, no, boyut=10, opak=0.8)
        c.yazi(x0 - 6.0, y0 + (p + 0.5) * cs, no, hiza="end", boyut=10, opak=0.8)
    if vurgu:
        c.on.append(f'<rect class="vurgu" rx="6" x="{_n(x0 - 4)}" y="{_n(y0 - 4)}" width="{_n(gen + 8)}" '
                    f'height="{_n(gen + 8)}" fill="none" {_st(None, _AILE["c"][1])} stroke-width="2.5"/>')
        c.kapsa(x0 - 4, y0 - 4, x0 + gen + 4, y0 + gen + 4)
    sat1 = ("mavi: tek elemanın katkısı · sarı: birden çok eleman toplanır" if not vurgu
            else "yeşil çerçeve: çözülecek indirgenmiş matris")
    c.yazi(x0 + gen / 2, y0 + gen + 20.0, sat1, boyut=11, opak=0.8)
    if bant:
        c.yazi(x0 + gen / 2, y0 + gen + 36.0, "kırmızı bant: tutulu SD'nin satır ve sütunu", boyut=11, opak=0.8)
    if blk > 1:
        c.yazi(x0 + gen / 2, y0 + gen + (52.0 if bant else 36.0), f"her hücre {blk}×{blk} SD bloğu", boyut=11, opak=0.8)
    return {"baslik": baslik, "svg": c.svg("Doluluk haritası")}


def _sema_doluluk(M):
    n = M.n
    cnt = np.zeros((n, n), dtype=int)
    for e in M.elemanlar:
        for I in e.dofs:
            for J in e.dofs:
                cnt[I, J] += 1
    kareler = [_matris_haritasi(M, list(range(n)), cnt, "K matrisinin dolu terimleri", bant=M.sabit)]
    if M.serbest:
        kareler.append(_matris_haritasi(M, list(M.serbest), cnt, "Mesnet satır/sütunları atıldıktan sonra", vurgu=True))
    return kareler


# --- sonuç şemaları -----------------------------------------------------------
def _dugum_yer_degistirme(M, i):
    d, t, u = M.d, M.tip, M.u
    if t in ("yay", "cubuk"):
        return float(u[i]), 0.0
    if t == "kiris":
        return 0.0, float(u[d * i])
    if M.uc:
        return float(u[d * i]), float(u[d * i + 1]), float(u[d * i + 2])
    return float(u[d * i]), float(u[d * i + 1])


def _dugum_ekran_deforme(c, M, i, sc):
    """Düğümün ölçekli şekil değiştirmiş konumunun ekran koordinatı."""
    dg = M.dugumler[i]
    dd = _dugum_yer_degistirme(M, i)
    if M.uc:
        return c.W(float(dg.x) + sc * dd[0], float(dg.y) + sc * dd[1], float(dg.z) + sc * dd[2])
    return c.P(float(dg.x) + sc * dd[0], float(dg.y) + sc * dd[1])


def _gorunum_sonuc(M):
    """Sonuç karelerinin hepsi aynı ölçüde çizilsin diye ortak çizim nesnesi üretir."""
    return _Cizim(M)


def _sekil_kare(M, dolu):
    c = _Cizim(M)
    sc = _olcek_bul(M)
    _mesnetleri_ciz(c, M, dolu)
    if _birinci_boyut(M):
        kayma = 70.0
        for i in range(len(M.dugumler)):
            X, Y = c.D(i)
            dx, _ = _dugum_yer_degistirme(M, i)
            X2 = c.P(float(M.dugumler[i].x) + sc * dx, 0.0)[0]
            c.cizgi((X, Y), (X, Y + kayma - 6), "n", kalin=1.0, sinif="g0", kesik="3 3", opak=0.7)
            c.daire((X2, Y + kayma), 4.5, aile="a", sinif="g4")
            if abs(dx) > 0:
                c.yazi(X2, Y + kayma + 20.0, f"{M.sd_et[i]} = {_kisa(M.u[i])}", boyut=11)
        for e in M.elemanlar:
            a, b = c.E(e)
            c.cizgi(a, b, "n", kalin=1.6, sinif="g0", kesik="5 4", opak=0.8)
            pa = c.P(float(M.dugumler[e.ia].x) + sc * _dugum_yer_degistirme(M, e.ia)[0], 0.0)
            pb = c.P(float(M.dugumler[e.ib].x) + sc * _dugum_yer_degistirme(M, e.ib)[0], 0.0)
            c.yol([(pa[0], pa[1] + kayma), (pb[0], pb[1] + kayma)], "a", kalin=3.0, sinif="g4", animasyon=True)
    else:
        for e in M.elemanlar:
            c.cizgi(*c.E(e), "n", kalin=1.6, sinif="g0", kesik="5 4", opak=0.8)
        for e in M.elemanlar:
            if M.uc:
                pts = [c.W(X + sc * dX, Y + sc * dY, Z + sc * dZ) for (X, Y, Z), (dX, dY, dZ) in _deplasman_ornekleri(M, e)]
            else:
                pts = [c.P(X + sc * dX, Y + sc * dY) for (X, Y), (dX, dY) in _deplasman_ornekleri(M, e)]
            c.yol(pts, "a", kalin=2.8, sinif="g4", animasyon=True)
        for i in range(len(M.dugumler)):
            c.daire(_dugum_ekran_deforme(c, M, i, sc), 3.8, aile="a", sinif="g4")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"kesikli: ilk durum · mavi: şekil değiştirmiş (×{_ol_metin(sc)} büyütülmüş)",
           boyut=11, opak=0.8)
    return {"baslik": "Şekil değiştirmiş biçim", "svg": c.svg("Şekil değiştirmiş biçim")}


def _normal_kare(M):
    """yay / çubuk / kafes: eleman eksenel kuvvetleri (çekme mavi, basınç kırmızı, kalınlık |N| ile orantılı)."""
    c = _Cizim(M)
    nmax = max((abs(_f(e.N)) for e in M.elemanlar), default=0.0)
    xs = [p for i in range(len(M.dugumler)) for p in [c.D(i)]]
    mx0 = sum(p[0] for p in xs) / len(xs)
    my0 = sum(p[1] for p in xs) / len(xs)
    for e in M.elemanlar:
        a, b = c.E(e)
        n = _f(e.N)
        if nmax <= 0 or abs(n) <= 1e-9 * nmax:
            aile, kalin = "n", 2.0
        else:
            aile, kalin = ("a" if n > 0 else "sil"), 2.5 + 5.0 * abs(n) / nmax
        c.yol([a, b], aile, kalin=kalin, sinif="g4", animasyon=True)
        t = _birim_vek(a, b)
        nv = (t[1], -t[0])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if _birinci_boyut(M):
            nv = (0.0, -1.0)
        elif nv[0] * (mid[0] - mx0) + nv[1] * (mid[1] - my0) < 0:
            nv = (-nv[0], -nv[1])
        c.yazi(mid[0] + nv[0] * 14.0, mid[1] + nv[1] * 14.0, _kisa(e.N), boyut=12, kalin=True)
    c.dugum_noktalari()
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"N [{M.kuvvet}] · mavi: çekme (+) · kırmızı: basınç (−)", boyut=11, opak=0.8)
    return {"baslik": "Eksenel kuvvet N", "svg": c.svg("Eksenel kuvvet")}


_KESIT_AD = {"N": "Eksenel kuvvet N diyagramı", "V": "Kesme kuvveti V diyagramı", "M": "Eğilme momenti M diyagramı",
             "Vz": "Kesme kuvveti Vz diyagramı", "My": "Eğilme momenti My diyagramı", "T": "Burulma momenti T diyagramı"}


def _kesit_kare(M, tur):
    """kiris / cerceve / cerceve3b: N, V, M (uzayda ayrıca Vz, My, T) diyagramı (momentler çekme tarafına çizilir)."""
    anahtar = {"N": "dN", "V": "dV", "M": "dM", "Vz": "dVz", "My": "dMy", "T": "dT"}[tur]
    vmax = max((abs(_f(v)) for e in M.elemanlar for v in getattr(e, anahtar)), default=0.0)
    if vmax <= 1e-12:
        return None
    c = _Cizim(M)
    ol = 46.0 / vmax
    isaret = -1.0 if tur in ("M", "My") else 1.0
    yerlesen = []
    for e in M.elemanlar:
        a, b = c.E(e)
        Lp = math.hypot(b[0] - a[0], b[1] - a[1])
        t = _birim_vek(a, b)
        n = _yerel_ekran_yon(c, M, e, 2 if tur in ("Vz", "My") else 1)
        d = (isaret * n[0], isaret * n[1])
        L = _f(e.L)
        deger = [_f(v) for v in getattr(e, anahtar)]
        xs = [_f(x) for x in e.dx]
        taban = [(a[0] + t[0] * Lp * x / L, a[1] + t[1] * Lp * x / L) for x in xs]
        tepe = [(p[0] + d[0] * v * ol, p[1] + d[1] * v * ol) for p, v in zip(taban, deger)]
        parcalar, cur = [], [(taban[0], tepe[0], deger[0])]
        for k in range(1, len(xs)):
            v0, v1 = deger[k - 1], deger[k]
            if v0 * v1 < 0:
                r = v0 / (v0 - v1)
                z = (taban[k - 1][0] + (taban[k][0] - taban[k - 1][0]) * r, taban[k - 1][1] + (taban[k][1] - taban[k - 1][1]) * r)
                cur.append((z, z, 0.0))
                parcalar.append(cur)
                cur = [(z, z, 0.0)]
            cur.append((taban[k], tepe[k], v1))
        parcalar.append(cur)
        for pr in parcalar:
            isr = sum(p[2] for p in pr)
            aile = "a" if isr >= 0 else "sil"
            c.poligon([p[0] for p in pr] + [p[1] for p in reversed(pr)], aile, sinif="g3", katman="arka")
            c.yol([p[1] for p in pr], aile, kalin=2.2, sinif="g4", animasyon=True)
        c.cizgi(a, b, None, kalin=2.4, sinif="g0")
        for p, q in ((taban[0], tepe[0]), (taban[-1], tepe[-1])):
            c.cizgi(p, q, "n", kalin=1.0, sinif="g3")
        adaylar = [(0, deger[0]), (len(xs) - 1, deger[-1])]
        if tur == "M" and e.ekst is not None:
            xe, me = _f(e.ekst[0]), _f(e.ekst[1])
            adaylar.append((min(range(len(xs)), key=lambda k: abs(xs[k] - xe)), me))
        for k, v in adaylar:
            if abs(v) <= 1e-9 * vmax:
                continue
            sg = 1.0 if v > 0 else -1.0
            pos = (tepe[k][0] + d[0] * sg * 12.0, tepe[k][1] + d[1] * sg * 12.0)
            if any(math.hypot(pos[0] - q[0], pos[1] - q[1]) < 16.0 for q in yerlesen):
                continue
            yerlesen.append(pos)
            c.yazi(pos[0], pos[1], _kisa(v), boyut=12, kalin=True)
    c.mafsallar()
    c.dugum_noktalari()
    birim = f"{M.kuvvet}·{M.uzunluk}" if tur in ("M", "My", "T") else M.kuvvet
    ek = " · çekme tarafına çizilir" if tur in ("M", "My") else ""
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"{tur} [{birim}] · mavi: + · kırmızı: −{ek}", boyut=11, opak=0.8)
    ad = _KESIT_AD[tur]
    return {"baslik": ad, "svg": c.svg(ad)}


def _tepki_kare(M, dolu):
    c = _Cizim(M)
    d, t = M.d, M.tip
    for e in M.elemanlar:
        c.cizgi(*c.E(e), None, kalin=2.6, sinif="g0", opak=0.55)
    _yukleri_ciz(c, M, dolu)
    olcek = max([abs(_f(M.R_tam[d * i + j])) for i, fl in enumerate(M.mesnet) for j, f in enumerate(fl)
                 if f and not _BILESEN[t][j].startswith("M")]
                + [abs(_f(v)) for i, v in enumerate(M.F_yay) if not _BILESEN[t][i % d].startswith("M")], default=0.0)
    esik = 1e-9 * max(olcek, 1e-300)
    ad_r = {"Fx": "Rx", "Fy": "Ry", "Fz": "Rz", "M": "Mz", "Mx": "Mx", "My": "My", "Mz": "Mz"}
    for i, fl in enumerate(M.mesnet):
        X, Y = c.D(i)
        for j, f in enumerate(fl):
            if not f:
                continue
            v = M.R_tam[d * i + j]
            if abs(_f(v)) <= esik and _gercek(v) is not None:
                continue
            _kuvvet_oku(c, M, X, Y, _BILESEN[t][j], v, "c", olcek, dolu[i], onek=ad_r[_BILESEN[t][j]] + " = ",
                       kom=_komsu_yonler(c, M, i))
    for k, v in enumerate(M.F_yay):
        if k not in M.yay_sd or (abs(_f(v)) <= esik and _gercek(v) is not None):
            continue
        i, j = divmod(k, d)
        X, Y = c.D(i)
        _kuvvet_oku(c, M, X, Y, _BILESEN[t][j], v, "c", olcek, dolu[i], onek="yay " + ad_r[_BILESEN[t][j]] + " = ",
                   kom=_komsu_yonler(c, M, i))
    c.dugum_noktalari()
    ek = " ve yay kuvvetleri" if M.yay_sd else ""
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"yeşil: mesnet tepkileri{ek} · sarı: dış yükler", boyut=11, opak=0.8)
    return {"baslik": "Mesnet tepkileri", "svg": c.svg("Mesnet tepkileri")}


def _zemin_kare(M):
    """Winkler zemin basıncı p(x) = −k_s v(x) diyagramı (zemine oturan elemanlar)."""
    c = _Cizim(M)
    deg = []
    for e in M.elemanlar:
        if e.zemin is None:
            continue
        a0, a1, a2, a3 = (_f(v) for v in e.zemin_katsayi)
        ks = _f(e.zemin)
        e.dp = [-ks * (a0 + a1 * x + a2 * x * x + a3 * x ** 3) for x in (_f(v) for v in e.dx)]
        deg += [abs(v) for v in e.dp]
    vmax = max(deg, default=0.0)
    if vmax <= 1e-12:
        return None
    ol = 40.0 / vmax
    for e in M.elemanlar:
        a, b = c.E(e)
        c.cizgi(a, b, None, kalin=2.4, sinif="g0")
        if e.zemin is None:
            continue
        n = _yerel_ekran_yon(c, M, e, 1)
        d = (-n[0], -n[1])     # p = −k_s·v > 0 (kiriş çöker, zemin yukarı iter): elemanın altına çizilir
        Lp = math.hypot(b[0] - a[0], b[1] - a[1])
        t = _birim_vek(a, b)
        L = _f(e.L)
        xs = [_f(x) for x in e.dx]
        taban = [(a[0] + t[0] * Lp * x / L, a[1] + t[1] * Lp * x / L) for x in xs]
        tepe = [(p[0] + d[0] * v * ol, p[1] + d[1] * v * ol) for p, v in zip(taban, e.dp)]
        c.poligon(taban + list(reversed(tepe)), "c", sinif="g3", katman="arka")
        c.yol(tepe, "c", kalin=2.0, sinif="g4", animasyon=True)
        k = max(range(len(xs)), key=lambda i: abs(e.dp[i]))
        c.yazi(tepe[k][0] + d[0] * 12.0, tepe[k][1] + d[1] * 12.0, _kisa(e.dp[k]), boyut=11, kalin=True)
    c.dugum_noktalari()
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"zemin basıncı p = −kₛ·v [{M.kuvvet}/{M.uzunluk}] · pozitif: zemin yukarı iter (altına çizilir)",
           boyut=11, opak=0.8)
    return {"baslik": "Zemin basıncı diyagramı", "svg": c.svg("Zemin basıncı")}


def _diyagram_turleri(M):
    t = M.tip
    if t == "cerceve3b":
        return ("N", "V", "M", "Vz", "My", "T")
    if t == "cerceve":
        return ("N", "V", "M")
    if t == "kiris":
        return ("V", "M")
    return ()


def _sema_sonuc(M):
    """Sonuç şemaları; harfli (sembolik) modellerde sayısal değer olmadığından boş liste döner."""
    if M.sembolik:
        return []
    t = M.tip
    dolu = {i: [] for i in range(len(M.dugumler))}
    kareler = [_sekil_kare(M, dolu)]
    if t in _EKSENEL:
        kareler.append(_normal_kare(M))
    else:
        for tur in _diyagram_turleri(M):
            k = _kesit_kare(M, tur)
            if k is not None:
                kareler.append(k)
        if M.zemin_var:
            k = _zemin_kare(M)
            if k is not None:
                kareler.append(k)
    dolu2 = {i: [] for i in range(len(M.dugumler))}
    kareler.append(_tepki_kare(M, dolu2))
    return kareler


def _adim_sema_model(M, anl):
    _basla(anl, 2, "Yapı modeli: şekil üzerinde",
           "Tablolar tam ama soyuttur. Aynı bilgiyi çizerek, modelin gerçekten kafamızdaki yapı olup olmadığını denetliyoruz: "
           "yanlış bağlanmış bir düğüm ya da ters yönlü bir yük şekilde hemen göze çarpar. İkinci karede her düğümün hangi "
           "serbestlik derecelerine (SD) hangi numarayı aldığını görüyoruz.")
    anl.metin("*Okuma kılavuzu:* düğüm numaraları yazıyla, eleman numaraları dairenin içinde gösterilir; sarı oklar yüklerdir, "
              "taralı simgeler mesnetlerdir. İkinci karede **mavi** oklar serbest, **kırmızı** olanlar tutulu (mesnetli) SD'leri gösterir.")
    anl.sema("Yapı modeli", _sema_yapi(M))


# ============================================================================
# Adım 7: sınır koşulları ve çözüm
# ============================================================================
def _hucre(M, x):
    """Tablo hücresi: sayı (ondalık); kesin modda kesirli bir sayıysa yanına p/q eklenir."""
    s = _metin(x)
    if not M.sayisal and not mo.ayarlar.ondalik:
        y = sp.sympify(x)
        if y.is_Rational and not y.is_Integer:
            s += f" ({y.p}/{y.q})"
    return s


def _sd_birimi(M, ad):
    return "rad" if ad.startswith("θ") else M.uzunluk


def _kuvvet_olcegi(M):
    v = [abs(_gercek(x)) for x in list(M.F) + list(M.R_tam) if _gercek(x) is not None]
    return max([1.0] + v)


def _sifir_mi(M, x, olcek=1.0):
    v = _gercek(x)
    if v is None:
        return sp.simplify(x) == 0
    return abs(v) <= 1e-9 * max(olcek, 1e-300)


def _yer_degistirme_tablosu(M):
    t, d = M.tip, M.d
    ust = ["Düğüm"] + [f"{a} [{_sd_birimi(M, a)}]" for a in _SD_ADLARI[t]]
    sat = []
    for i, dg in enumerate(M.dugumler):
        sat.append([dg.no] + [_hucre(M, M.u[d * i + j]) for j in range(d)])
    kesik = ""
    if len(sat) > 30:
        sat = sat[:30]
        kesik = f"\n\n*(İlk 30 düğüm gösterildi; tümü `veri[\"dugumler\"]` içindedir.)*"
    return _tablo(ust, sat) + kesik


_TEPKI_AD = {"Fx": "Rx", "Fy": "Ry", "Fz": "Rz", "M": "Rm", "Mx": "Rmx", "My": "Rmy", "Mz": "Rmz"}


def _tepki_tablosu(M):
    t, d = M.tip, M.d
    ad_r = dict(_TEPKI_AD)
    if t in ("yay", "cubuk"):
        ad_r = {"Fx": "R"}
    b = _birimler(M)
    ust = ["Düğüm"] + [f"{ad_r[a]} [{b[a]}]" for a in _BILESEN[t]]
    sat = []
    for i, dg in enumerate(M.dugumler):
        if any(M.mesnet[i]):
            sat.append([dg.no] + [(_hucre(M, M.R_tam[d * i + j]) if M.mesnet[i][j] else "—") for j in range(d)])
    return _tablo(ust, sat)


def _diyafram_tablosu(M):
    d = M.d
    b = _birimler(M)
    sat = []
    for dy in M.diyaframlar:
        for i in dy.koleler:
            sat.append([dy.ad, M.dugumler[i].no, _hucre(M, M.F_diyafram[d * i]), _hucre(M, M.F_diyafram[d * i + 2]),
                        _hucre(M, M.F_diyafram[d * i + 4])])
    return _tablo(["Diyafram", "Köle düğüm", f"Fx [{b['Fx']}]", f"Fz [{b['Fz']}]", f"My [{b['My']}]"], sat)


def _diyafram_anlatimi(M, anl):
    """7. adımın başında kısa 'rijit diyafram' alt adımı: kural, bir köle için T'nin üç satırı, SD sayısının azalması."""
    anl.baslik("Rijit kat diyaframı (efendi–köle bağı)", 4)
    anl.kural("Kat döşemesi kendi düzleminde (x–z) çok rijittir: katın bütün düğümleri tek bir rijit cisim gibi birlikte "
              "ötelenir ve düşey eksen (y) etrafında birlikte döner. Bu yüzden her **köle** düğümün düzlem içi üç "
              "serbestliği ($u$, $w$, $\\theta_y$) **efendi** düğümün üç serbestliğine bağlanır; düşey öteleme $v$ ile "
              "$\\theta_x$, $\\theta_z$ köle düğümde bağımsız kalır. Sağ el kuralıyla köle düğümün yer değiştirmesi "
              "$\\boldsymbol{\\omega}\\times\\mathbf{r}$'dir ($\\boldsymbol{\\omega}=\\theta_{y,m}\\,\\hat{y}$, "
              "$\\mathbf{r}$ efendiden köleye; $\\hat{y}\\times\\hat{x}=-\\hat{z}$, $\\hat{y}\\times\\hat{z}=\\hat{x}$): "
              "$u_s = u_m + \\theta_{y,m}\\,(z_s - z_m)$, $w_s = w_m - \\theta_{y,m}\\,(x_s - x_m)$, "
              "$\\theta_{y,s}=\\theta_{y,m}$.")
    sat = [[dy.ad, f"{M.dugumler[dy.ana].no}{' (sanal)' if dy.sanal else ''}",
            ", ".join(str(M.dugumler[i].no) for i in dy.koleler)] for dy in M.diyaframlar]
    anl.metin("**Diyaframlar**\n\n" + _tablo(["Diyafram", "Efendi düğüm", "Köle düğümler"], sat))
    dy = M.diyaframlar[0]
    s, m = M.dugumler[dy.koleler[0]], M.dugumler[dy.ana]
    dz, dx = s.z - m.z, s.x - m.x
    anl.metin(f"Örnek: diyafram '{dy.ad}', köle düğüm {s.no}, efendi düğüm {m.no} "
              f"($x_s-x_m={_metin(dx)}$, $z_s-z_m={_metin(dz)}$). $\\mathbf{{T}}$'nin bu köleye ait üç satırı:")
    anl.mat(rf"\begin{{bmatrix}} u_{{{s.no}}} \\ w_{{{s.no}}} \\ \theta_{{y,{s.no}}} \end{{bmatrix}} = "
            rf"\begin{{bmatrix}} 1 & 0 & {_L(dz)} \\ 0 & 1 & {_L(-dx)} \\ 0 & 0 & 1 \end{{bmatrix}}"
            rf"\begin{{bmatrix}} u_{{{m.no}}} \\ w_{{{m.no}}} \\ \theta_{{y,{m.no}}} \end{{bmatrix}}")
    oto = (f", sanal efendi düğümün {len(M.oto_sd)} serbestliği ($v$, $\\theta_x$, $\\theta_z$) hiçbir elemana bağlı "
           "olmadığından sıfır alındı" if M.oto_sd else "")
    anl.metin(f"Bütün bağlar tek bir dönüşüm matrisinde toplanır: $\\mathbf{{u}}=\\mathbf{{T}}\\,\\mathbf{{u}}_r$ "
              f"($\\mathbf{{T}}$: {M.n}×{M.n_r}; bağımsız SD'lerin satırı birim, köle SD'lerin satırı yukarıdaki "
              f"katsayılar). Rijitlik ve yük buna göre indirgenir: $\\mathbf{{K}}_r=\\mathbf{{T}}^T\\mathbf{{K}}\\mathbf{{T}}$, "
              f"$\\mathbf{{F}}_r=\\mathbf{{T}}^T\\mathbf{{F}}$. **SD sayısı {M.n} → {M.n_r}** ({len(M.kole_sd)} köle SD'si "
              f"efendiye bağlandı{oto}). Mesnetler ve mekanizma denetimi indirgenmiş sistemdedir; çözümden sonra "
              "$\\mathbf{u}=\\mathbf{T}\\mathbf{u}_r$ ile tam vektöre dönülür. Köle SD'lerinde $\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ "
              "artığı sıfır değildir: bu, diyaframın düğüme uyguladığı **iç kuvvettir** (aşağıda ayrı tablo), mesnet "
              "tepkisi değildir; tepkiler $\\mathbf{R}_r=\\mathbf{T}^T(\\mathbf{K}\\mathbf{u}-\\mathbf{F})$ ile bulunur.")


def _yay_tablosu(M):
    t, d = M.tip, M.d
    b = _birimler(M)
    ya = _YAY_ANAHTAR[t]
    sat = []
    for k, kk in M.yay_sd.items():
        i, j = divmod(k, d)
        birim = b["M"] if ya[j].startswith("kr") else M.kuvvet
        sat.append([M.dugumler[i].no, M.sd_et[k], _hucre(M, kk), _hucre(M, M.u[k]), f"{_hucre(M, M.F_yay[k])} {birim}"])
    return _tablo(["Düğüm", "SD", "k", "u", "Yay kuvveti −k·u"], sat)


def _adim_cozum(M, anl):
    t, d = M.tip, M.d
    _basla(anl, 7, "Sınır koşulları ve çözüm",
           "Mesnetsiz yapının $\\mathbf{K}$ matrisi tekildir (yapı rijit cisim gibi kayabilir), bu yüzden "
           "$\\mathbf{K}\\mathbf{u}=\\mathbf{F}$ tek başına çözülemez. Mesnetler bazı SD'lerin yer değiştirmesini sıfıra "
           "bağlar; bu bilinen değerleri denklemden çıkarıp yalnız **bilinmeyen** (serbest) SD'ler için küçük bir sistem "
           "çözüyoruz. Sonra tutulu SD'lerdeki denge artığından **mesnet tepkilerini** buluyoruz.")
    if M.diyaframlar:
        _diyafram_anlatimi(M, anl)
    sabit1 = [i + 1 for i in M.sabit]
    serbest1 = [i + 1 for i in M.serbest]
    if M.sabit:
        sat = [[i + 1, M.sd_et[i], M.dugumler[i // d].no, _metin(M.cokme.get(i, 0))] for i in M.sabit]
        anl.metin("**Tutulu SD'ler** (mesnet; yer değiştirme bilinir)\n\n" + _tablo(["SD no", "SD", "Düğüm", "Bilinen değer"], sat))
    anl.metin(f"Tutulu SD'ler: {sabit1}. Serbest (bilinmeyen) SD'ler: {serbest1 or 'yok'}. "
              + (f"Diyafram bağlarından sonra bilinmeyen sayısı {len(M.serbest_r)}; " if M.diyaframlar else "")
              + f"İndirgenmiş sistemin boyutu {len(M.serbest_r)}×{len(M.serbest_r)}.")
    if M.yay_sd:
        anl.metin("Yaylarla tutulan serbestlikler **serbest** sayılır: yay, yer değiştirmeyi sıfırlamaz, yalnız ona karşı "
                  "kuvvet üretir (5. adımda köşegene eklendi).")
    if M.cokme:
        anl.kural("**Mesnet çökmesi:** tutulu SD'lerden bazılarının değeri sıfır değil, bilinen bir $\\mathbf{u}_s$'dir. "
                  "Sistemi serbest (f) ve tutulu (s) bloklara bölersek "
                  "$\\begin{bmatrix}\\mathbf{K}_{ff}&\\mathbf{K}_{fs}\\\\\\mathbf{K}_{sf}&\\mathbf{K}_{ss}\\end{bmatrix}"
                  "\\begin{bmatrix}\\mathbf{u}_f\\\\\\mathbf{u}_s\\end{bmatrix}="
                  "\\begin{bmatrix}\\mathbf{F}_f\\\\\\mathbf{F}_s+\\mathbf{R}\\end{bmatrix}$; ilk satırdan "
                  "$\\mathbf{K}_{ff}\\mathbf{u}_f=\\mathbf{F}_f-\\mathbf{K}_{fs}\\mathbf{u}_s$ çıkar: bilinen yer değiştirmenin "
                  "etkisi **eşdeğer bir yük** gibi sağ tarafa taşınır. Tepkiler yine $\\mathbf{R}=\\mathbf{K}\\mathbf{u}-\\mathbf{F}$.")
        F_r = _F_indirgenmis(M)
        if M.sayisal:
            Kfs = M.K_r[np.ix_(M.serbest_r, M.sabit_r)]
            us_ = M.u_r[M.sabit_r]
            ek = Kfs @ us_
            Fc = F_r[M.serbest_r] - ek
        else:
            Kfs = M.K.extract(M.serbest, M.sabit)
            us_ = sp.Matrix([M.u[i] for i in M.sabit])
            ek = _sade(Kfs * us_)
            Fc = M.F_cokme
        sat = []
        for a_, c in enumerate(M.serbest_r):
            i = M.ind[c]
            if ek[a_] != 0 or F_r[c] != 0:
                sat.append([f"{M.sd_et[i]} (SD {i + 1})", _metin(F_r[c]), _metin(-ek[a_]), _metin(Fc[a_])])
        if sat:
            anl.metin("**Sağ tarafın düzeltilmesi** $\\mathbf{F}_f-\\mathbf{K}_{fs}\\mathbf{u}_s$ (yalnız dolu satırlar)\n\n"
                      + _tablo(["SD", "F_f", "−K_fs·u_s", "Düzeltilmiş sağ taraf"], sat))
        elif not M.serbest:
            anl.metin("Serbest SD olmadığından düzeltilecek sağ taraf yoktur; bütün yer değiştirmeler bilinir, "
                      "tepkiler doğrudan $\\mathbf{R}=\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ ile bulunur.")
    if not M.serbest:
        anl.metin("Bütün SD'ler tutulu olduğundan bilinmeyen yer değiştirme yoktur; mesnet tepkileri "
                  "$\\mathbf{R}=\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ ile bulunur.")
    elif not M.sayisal and not M.cokme and _gauss_anlatimi_sigar(M):
        anl.metin("Aşağıda motorun Gauss yok etme anlatımı vardır: tutulu satır/sütunlar atılır, indirgenmiş sistem çözülür, "
                  "tepkiler $\\mathbf{R}=\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ ile bulunur.")
        try:
            r = mo.sinir_kosulu(M.K, M.F, sabit=sabit1, goster="yok")
            _motor_bloklari(r, anl)
        except MatrisHatasi as e:  # pragma: no cover (mekanizma denetimi daha önce yapıldı)
            anl.uyari(f"Ayrıntılı çözüm anlatımı oluşturulamadı: {e}")
    elif not M.sayisal:
        Ks = M.K.extract(M.serbest, M.serbest)
        et = [M.sd_tex[i] for i in M.serbest]
        if not M.cokme:
            anl.metin("Harfli ifadeler büyük olduğundan Gauss yok etmenin her adımı yazılmadı (ara ifadeler sayfalarca "
                      "uzardı); indirgenmiş sistem ve çözümü aşağıdadır. Sayı girilirse adım adım yok etme de gösterilir.")
        anl.metin("İndirgenmiş sistem (tutulu satır ve sütunlar atılmış, sağ taraf düzeltilmiş) ve çözümü:")
        anl.mat(rf"\mathbf{{K}}_{{ff}} = {_etiketli(Ks, et)},\qquad \mathbf{{F}}_f-\mathbf{{K}}_{{fs}}\mathbf{{u}}_s = {_etiketli_vek(M.F_cokme, et)}")
        anl.mat(rf"\mathbf{{u}}_f = \mathbf{{K}}_{{ff}}^{{-1}}\left(\mathbf{{F}}_f-\mathbf{{K}}_{{fs}}\mathbf{{u}}_s\right) = "
                rf"{_etiketli_vek(sp.Matrix([M.u[i] for i in M.serbest]), et)}")
    else:
        m = len(M.serbest_r)
        Ks = M.K_r[np.ix_(M.serbest_r, M.serbest_r)]
        Fs = _F_indirgenmis(M)[M.serbest_r]
        if M.cokme:
            Fs = Fs - M.K_r[np.ix_(M.serbest_r, M.sabit_r)] @ M.u_r[M.sabit_r]
        us = M.u_r[M.serbest_r]
        kosul = float(np.linalg.cond(Ks))
        art = float(np.abs(Ks @ us - Fs).max())
        K_ad = "\\mathbf{K}_r" if M.diyaframlar else "\\mathbf{K}"
        anl.metin(f"Tutulu {len(M.sabit_r)} SD'nin satır ve sütunları ${K_ad}$'dan atılır; kalan "
                  f"$\\mathbf{{K}}_s$ ({m}×{m}) simetrik ve pozitif tanımlıdır. Sistem "
                  f"$\\mathbf{{K}}_s\\mathbf{{u}}_s=\\mathbf{{F}}_s$"
                  + (" (sağ taraf $\\mathbf{F}_f-\\mathbf{K}_{fs}\\mathbf{u}_s$ ile düzeltilmiş)" if M.cokme else "")
                  + " `numpy.linalg.solve` ile (LU ayrışımı) çözülür. "
                  f"Koşul sayısı ≈ {kosul:.3g}; sağlama $\\max|\\mathbf{{K}}_s\\mathbf{{u}}_s-\\mathbf{{F}}_s|$ = {art:.2g} "
                  f"(yuvarlama düzeyinde ✔).")
        anl.kural("Koşul sayısı, çözümün veri hatasına duyarlılığını gösterir: yaklaşık $10^{k}$ ise ondalık basamakların "
                  "$k$ tanesi kaybolur. Tek cins eleman ve makul mesnetle genelde küçüktür; çok farklı rijitlikler "
                  "(çok ince ile çok kalın eleman) bunu büyütür.")
    anl.metin("**Düğüm yer değiştirmeleri** ($\\mathbf{u}$)\n\n" + _yer_degistirme_tablosu(M))
    if M.sabit:
        ad_r = ("R" if t in ("yay", "cubuk") else ", ".join(_TEPKI_AD[a] for a in _BILESEN[t]))
        anl.metin(f"**Mesnet tepkileri** ($\\mathbf{{R}}=\\mathbf{{K}}\\mathbf{{u}}-\\mathbf{{F}}$; {ad_r}: mesnedin yapıya uyguladığı "
                  "kuvvet, global eksenin pozitif yönünde +). Tablo yalnız tutulu bileşenleri gösterir; serbest SD'lerde "
                  "$R_i=0$ çıkmalıdır (sağlama).\n\n" + _tepki_tablosu(M))
        if M.sayisal:
            kalan = max([abs(float(M.R_tam[i])) for i in M.serbest] + [0.0])
            anl.metin(f"Serbest SD'lerdeki tepkilerin en büyüğü {kalan:.2g} (≈ 0) ✔.")
    if M.diyaframlar:
        anl.metin("**Diyafram kuvvetleri** (diyaframın köle düğüme uyguladığı düzlem içi kuvvet $\\mathbf{T}$ bağından "
                  "gelen $\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ artığıdır; iç kuvvettir, tepki değildir: bir katın kuvvetleri "
                  "efendi düğümdeki yük ve tepkiyle dengelenir, Σ ≈ 0)\n\n" + _diyafram_tablosu(M))
    if M.yay_sd:
        anl.metin("**Yay (elastik mesnet) kuvvetleri:** yayın yapıya uyguladığı kuvvet $F_{yay}=-k\\,u$ (yer değiştirmeye zıt). "
                  "Bunlar da mesnet tepkisi gibi dengeye girer.\n\n" + _yay_tablosu(M))


# ============================================================================
# Adım 8: eleman kuvvetleri
# ============================================================================
def _en_buyuk_N(M):
    v = [abs(_gercek(e.N)) for e in M.elemanlar if _gercek(e.N) is not None]
    return max(v) if v else 0.0


def _eksenel_adim(M, anl):
    t = M.tip
    _basla(anl, 8, "Eleman kuvvetleri: eksenel kuvvet N" + ("" if t == "yay" else " ve gerilme σ"),
           "Yer değiştirmeleri bilmek yetmez; mühendis asıl olarak elemanın **ne kadar yüklendiğini** ister. Her elemanın iki "
           "ucundaki yer değiştirmeyi eleman eksenine çevirip uzamasını (δ) buluyor, rijitlikle çarparak kuvvete geçiyoruz.")
    if t == "yay":
        anl.kural("Yay kuvveti: $F=k\\,\\delta$, $\\delta=u_j-u_i$ (uzama). Çekme **+**, basınç **−**.")
    elif t == "cubuk":
        anl.kural("Eksenel kuvvet: $N=\\dfrac{EA}{L}\\,\\delta$, $\\delta=u_j-u_i$ (uzama); gerilme $\\sigma=N/A$. "
                  "Çekme **+**, basınç **−**.")
    elif t == "kafes3b":
        anl.kural("Uzay kafes elemanı yalnız eksenel kuvvet taşır. Eleman ekseni yönündeki uzama "
                  "$\\delta=\\mathbf{c}\\cdot(\\mathbf{u}_j-\\mathbf{u}_i)=c_x(u_j-u_i)+c_y(v_j-v_i)+c_z(w_j-w_i)$; "
                  "$N=\\dfrac{EA}{L}\\,\\delta$, $\\sigma=N/A$. Çekme **+**, basınç **−**.")
    else:
        anl.kural("Kafes elemanı yalnız eksenel kuvvet taşır. Eleman ekseni yönündeki uzama "
                  "$\\delta=-c\\,u_i-s\\,v_i+c\\,u_j+s\\,v_j$ ($c=\\cos\\alpha$, $s=\\sin\\alpha$); "
                  "$N=\\dfrac{EA}{L}\\,\\delta$, $\\sigma=N/A$. Çekme **+**, basınç **−**.")
    nmax = _en_buyuk_N(M)
    for e in M.elemanlar:
        e.durum = _durum(M, e, nmax)
        e.delta = e.dyerel[1] - e.dyerel[0]
        if not M.sayisal:
            e.delta = _sade(e.delta)
    if not M.sayisal and len(M.elemanlar) <= 12:
        for e in M.elemanlar:
            ea = "k" if t == "yay" else r"\frac{EA}{L}"
            deger = _Lp(e.ea)
            anl.mat(rf"\delta_{{{e.no}}} = {_L(e.delta)},\qquad N_{{{e.no}}} = {ea}\,\delta_{{{e.no}}} = "
                    rf"{deger}\cdot {_Lp(e.delta)} = {_L(e.N)}")
    ust = ["Eleman", f"L [{M.uzunluk}]", f"δ [{M.uzunluk}]", f"N [{M.kuvvet}]"]
    if t != "yay":
        ust.append(f"σ=N/A [{M.kuvvet}/{M.uzunluk}²]")
    ust.append("Durum")
    sat = []
    for e in M.elemanlar[:60]:
        s = [e.no, _metin(e.L), _hucre(M, e.delta), _hucre(M, e.N)]
        if t != "yay":
            s.append(_hucre(M, e.sigma))
        s.append(e.durum)
        sat.append(s)
    anl.metin("**Eleman kuvvetleri**\n\n" + _tablo(ust, sat))
    if len(M.elemanlar) > 60:
        anl.metin("*(İlk 60 eleman gösterildi; tümü `veri[\"elemanlar\"]` içindedir.)*")
    sifir = [e.no for e in M.elemanlar if e.durum == "sıfır"]
    if sifir and t in ("kafes", "kafes3b"):
        anl.metin(f"**Sıfır çubuk(lar):** eleman {', '.join(str(x) for x in sifir)} bu yük altında kuvvet taşımıyor; "
                  "yük değişince taşıyabilir, bu yüzden kafesten çıkarılmaz.")
    cek = [e.no for e in M.elemanlar if e.durum == "çekme"]
    bas = [e.no for e in M.elemanlar if e.durum == "basınç"]
    anl.metin(f"Çekilen elemanlar: {cek or 'yok'}; basılan elemanlar: {bas or 'yok'}. Basınç çubukları burkulma "
              "açısından da kontrol edilmelidir (yalnız σ yetmez).")


def _egilme_etiketleri(M, e):
    a, b = e.dno
    if M.tip == "kiris":
        return [rf"f_{{y,{a}}}", rf"m_{{{a}}}", rf"f_{{y,{b}}}", rf"m_{{{b}}}"]
    if M.tip == "cerceve3b":
        return [x for n in (a, b) for x in (rf"f_{{x,{n}}}", rf"f_{{y,{n}}}", rf"f_{{z,{n}}}",
                                             rf"m_{{x,{n}}}", rf"m_{{y,{n}}}", rf"m_{{z,{n}}}")]
    return [rf"f_{{x,{a}}}", rf"f_{{y,{a}}}", rf"m_{{{a}}}", rf"f_{{x,{b}}}", rf"f_{{y,{b}}}", rf"m_{{{b}}}"]


def _egilme_adim(M, anl):
    t = M.tip
    _basla(anl, 8, "Eleman uç kuvvetleri ve iç kuvvet diyagramları",
           "Elemanın iki ucundaki yer değiştirmeleri ($\\mathbf{d}$) bildiğimize göre, uç kuvvetlerini rijitlik matrisinden "
           "buluyoruz. Bu kuvvetler 'sonlu eleman işaretiyle' çıkar; tasarımda kullandığımız kesme kuvveti $V$ ve eğilme "
           "momenti $M$ işaretine çevirip eleman boyunca diyagramını çiziyoruz.")
    anl.kural("Uç kuvvetleri: $\\mathbf{f}=\\mathbf{k}\\,\\mathbf{d}-\\mathbf{f}_{eq}$ ($\\mathbf{d}=\\mathbf{T}\\mathbf{u}_e$ eleman "
              "yerel eksenindeki yer değiştirme; yayılı yük varsa $\\mathbf{f}_{eq}$ çıkarılır, çünkü o yük 6. adımda düğümlere "
              "aktarılmıştı). Sonlu eleman işaretinden yapı işaretine geçiş (i: başlangıç, j: bitiş ucu):\n\n"
              "$V(0)=f_{y,i}$, $V(L)=-f_{y,j}$, $M(0)=-m_i$, $M(L)=m_j$, $N=-f_{x,i}$. "
              "Eleman içinde: $V(x)=f_{y,i}+q\\,x$, $M(x)=-m_i+f_{y,i}\\,x+q\\,x^2/2$ "
              "($M>0$: alt lif çekilir; $N>0$: çekme)."
              + (" Parçalı doğrusal yükte $q\\,x$ yerine $Q(x)=\\int_0^x q\\,ds$, $q\\,x^2/2$ yerine "
                 "$\\int_0^x (x-s)\\,q(s)\\,ds$ gelir (her parça için kapalı form: $V$ parçada karesel, $M$ kübik); "
                 "parça sınırları diyagram istasyonlarına eklenir."
                 if any(_duzgun_mu(e) is None for e in M.elemanlar if e.parcalar or e.parcalar_z) else "")
              + ("\n\nUzay çerçevede $m_i\\to m_{z,i}$ ve ayrıca $x'z'$ düzlemi için $V_z(x)=f_{z,i}+q_z\\,x$, "
                 "$M_y(x)=m_{y,i}+f_{z,i}\\,x+q_z\\,x^2/2$; uçlarda $M_y(0)=m_{y,i}$, $M_y(L)=-m_{y,j}$ "
                 "($M_y>0$: $-z'$ lifi çekilir; sağ el kuralı yüzünden $m_y$'nin işareti $m_z$'ye göre terstir), "
                 "burulma $T=-m_{x,i}$ (eleman boyunca sabit)." if t == "cerceve3b" else "")
              + ("\n\nZemine oturan elemanda $\\mathbf{k}=\\mathbf{k}_{\\text{kiriş}}+\\mathbf{k}_z$ ile bulunan $\\mathbf{f}$, "
                 "düğümlerin elemana uyguladığı kuvvettir; eleman içinde zemin basıncı $p(x)=-k_s v(x)$ da kesite girer: "
                 "$V(x)=f_{y,i}+q\\,x+\\int_0^x p\\,d\\xi$, $M(x)=-m_i+f_{y,i}\\,x+q\\,x^2/2+\\int_0^x (x-\\xi)\\,p\\,d\\xi$ "
                 "($v$ Hermite kübiği olduğundan $V$ 4., $M$ 5. dereceden polinomdur)." if M.zemin_var else "")
              + ("\n\n**Uç serbestliği:** serbest bırakılan SD'nin yer değiştirmesi önce geri kazanılır, "
                 "$\\mathbf{d}_r=\\mathbf{k}_{rr}^{-1}(\\mathbf{f}_{eq,r}-\\mathbf{k}_{rf}\\mathbf{d}_f)$; sonra "
                 "$\\mathbf{f}=\\mathbf{k}\\,\\mathbf{d}-\\mathbf{f}_{eq}$ tam eleman matrisiyle alınır, böylece mafsallı uçta "
                 "moment (ya da serbest bırakılan öteki iç kuvvet) sıfırdır." if M.serbest_var else "")
              + ("\n\n**Eksenel yayılı yük:** $N(x)=-f_{x,i}-\\int_0^x q_x\\,ds$ (düzgün $q_x$'te doğrusal, doğrusal "
                 "$q_x$'te karesel değişir); tabloda $N$ i ucundaki değerdir." if any(e.parcalar_x for e in M.elemanlar) else ""))
    ayrinti = M.elemanlar if (not M.sayisal and len(M.elemanlar) <= 6) else M.elemanlar[:1]
    for e in ayrinti:
        yer = _egilme_etiketleri(M, e)
        anl.mat(rf"\mathbf{{f}}^{{({e.no})}} = \mathbf{{k}}\mathbf{{d}}" + (r" - \mathbf{f}_{eq}" if e.feq_yerel is not None else "")
                + rf" = {_etiketli_vek(e.f, yer)}")
    if len(ayrinti) < len(M.elemanlar):
        anl.metin(f"Yalnız ilk elemanın vektörü gösterildi; hepsinin uç kuvvetleri aşağıdaki tablodadır.")
    mb = f"{M.kuvvet}·{M.uzunluk}"
    if t == "cerceve3b":
        ust = ["Eleman", f"N [{M.kuvvet}]", f"Vy(0) [{M.kuvvet}]", f"Mz(0) [{mb}]", f"Vy(L) [{M.kuvvet}]", f"Mz(L) [{mb}]",
               f"Vz(0) [{M.kuvvet}]", f"My(0) [{mb}]", f"Vz(L) [{M.kuvvet}]", f"My(L) [{mb}]", f"T [{mb}]"]
    else:
        ust = ["Eleman", f"N [{M.kuvvet}]", f"V(0) [{M.kuvvet}]", f"M(0) [{mb}]",
               f"V(L) [{M.kuvvet}]", f"M(L) [{mb}]", "M ekstremum (x*)"]
    sat = []
    for e in M.elemanlar[:60]:
        satir = [e.no, _hucre(M, e.N), _hucre(M, e.v_uc[0]), _hucre(M, e.m_uc[0]), _hucre(M, e.v_uc[1]), _hucre(M, e.m_uc[1])]
        if t == "cerceve3b":
            satir += [_hucre(M, e.vz_uc[0]), _hucre(M, e.my_uc[0]), _hucre(M, e.vz_uc[1]), _hucre(M, e.my_uc[1]),
                      _hucre(M, e.dT[0])]
        else:
            ek = "—"
            if e.ekst is not None:
                ek = f"{_hucre(M, e.ekst[1])} (x = {_metin(e.ekst[0])})"
            satir.append(ek)
        sat.append(satir)
    anl.metin("**Uç iç kuvvetleri (yapı işaret kuralı)**\n\n" + _tablo(ust, sat))
    if len(M.elemanlar) > 60:
        anl.metin("*(İlk 60 eleman gösterildi; tümü `veri[\"elemanlar\"]` içindedir.)*")
    if any(e.ekst is not None for e in M.elemanlar):
        anl.metin("Yayılı yüklü elemanda $V(x)=0$ olduğu yerde $M$ ekstremumdur: düzgün yükte $x^*=-f_{y,i}/q$, "
                  "parçalı doğrusal yükte $V$'nin karesel ifadesinin kökü. "
                  "Moment diyagramı bu noktada eğimini değiştirir (parabol tepesi).")
    olcek = _kuvvet_olcegi(M)
    kotu = [e.no for e in M.elemanlar
            if not (_sifir_mi(M, e.kontrol[0], olcek) and _sifir_mi(M, e.kontrol[1], olcek))
            or (t == "cerceve3b" and not (_sifir_mi(M, e.kontrol3[0], olcek) and _sifir_mi(M, e.kontrol3[1], olcek)))]
    if kotu:
        anl.uyari(f"Eleman {kotu} için eleman içi diyagram uç değerlerle tutmadı; modeli denetleyin.")
    else:
        anl.metin("**Sağlama:** eleman boyunca $V(x)$ ve $M(x)$ ifadeleri j ucunda $M(L)=m_j$ ve $V(L)=-f_{y,j}$ "
                  "değerlerine ulaşıyor ✔ (uç kuvvetleri ile iç kuvvet diyagramları tutarlı)."
                  + (" $x'z'$ düzleminde de $V_z(L)=-f_{z,j}$ ve $M_y(L)=-m_{y,j}$ sağlanıyor ✔ "
                     "($M_y$'nin uç bağıntıları $M_y(0)=m_{y,i}$, $M_y(L)=-m_{y,j}$: sağ el kuralı yüzünden "
                     "$M_z$'ninkinin tersidir)." if t == "cerceve3b" else ""))
    if M.zemin_var:
        sat = []
        for e in M.elemanlar:
            if e.zemin is None:
                continue
            fz = e.f_zemin
            top = fz[0] + fz[2] if t == "kiris" else fz[1] + fz[4]
            sat.append([e.no, _hucre(M, top if M.sayisal else _sade(top))])
        anl.metin("**Zemin tepkisi** (her zeminli elemanın altındaki toplam zemin kuvveti, yerel y; yukarı +)\n\n"
                  + _tablo(["Eleman", f"Σ zemin kuvveti [{M.kuvvet}]"], sat)
                  + "\n\nToplam zemin kuvveti düşey yükleri dengeler (10. adımda sağlanır).")


def _adim_eleman_kuvvetleri(M, anl):
    if M.tip in _EKSENEL:
        _eksenel_adim(M, anl)
    else:
        _egilme_adim(M, anl)
        nmax = _en_buyuk_N(M)
        for e in M.elemanlar:
            e.durum = "eğilme"


# ============================================================================
# Adım 9: sonuç şemaları, Adım 10: denge ve enerji sağlaması
# ============================================================================
def _adim_sema_sonuc(M, anl):
    t = M.tip
    _basla(anl, 9, "Sonuçlar şekil üzerinde",
           "Sayılar doğrudur ama sezgi vermez. Yer değiştirmiş biçim, iç kuvvet diyagramları ve tepkiler birlikte "
           "bakıldığında 'bu sonuç makul mu?' sorusuna hızlıca cevap verir: yük aşağı ise yapı aşağı sarkmalı, mesnet "
           "tepkileri yükü dengelemeli, moment çekilen tarafa çizilmeli.")
    kareler = _sema_sonuc(M)
    if not kareler:
        anl.metin("Sonuçlar harfli (sembolik) olduğundan sayısal şekil çizilemez. Harfleri sayıyla değiştirip modeli yeniden "
                  "çözerseniz şekil değiştirmiş biçim ve diyagramlar çizilir.")
        return
    ek = {"yay": "Yer değiştirmiş biçim abartılı çizilir (ölçek karede yazılıdır); ikinci karede eleman kuvvetleri, sonda tepkiler.",
          "cubuk": "Yer değiştirmiş biçim abartılı çizilir (ölçek karede yazılıdır); ikinci karede eleman kuvvetleri, sonda tepkiler.",
          "kafes": "Eksenel kuvvet karesinde **mavi** çekme, **kırmızı** basınç çubuğudur; kalınlık |N| ile orantılıdır.",
          "kafes3b": "Uzay yapı eğik (aksonometrik) izdüşümle çizilir; eksen takımı sol alttadır. Eksenel kuvvet karesinde "
                     "**mavi** çekme, **kırmızı** basınç çubuğudur; kalınlık |N| ile orantılıdır.",
          "kiris": "V ve M diyagramları eleman eksenine dik çizilir; moment çekilen lif tarafındadır.",
          "cerceve": "N, V ve M diyagramları eleman eksenine dik çizilir; moment çekilen lif tarafındadır.",
          "cerceve3b": "Uzay yapı eğik (aksonometrik) izdüşümle çizilir. V ve M (Mz) diyagramları elemanın yerel y′ yönünde, "
                       "Vz ve My diyagramları yerel z′ yönünde çizilir; momentler çekilen lif tarafındadır; T burulmadır."}[t]
    if M.zemin_var:
        ek += " Zemin basıncı karesinde eğri, zeminin elemanı ittiği dağılı kuvveti (p = −kₛ·v) gösterir."
    anl.metin("*Okuma kılavuzu:* ilk karede kesik çizgi yüksüz, düz çizgi yüklü (abartılı) biçimdir. " + ek)
    anl.sema("Sonuçlar", kareler)


_DENGE_ANAHTAR = {"yay": ("Fx",), "cubuk": ("Fx",), "kafes": ("Fx", "Fy", "M"), "kiris": ("Fy", "M"),
                  "cerceve": ("Fx", "Fy", "M"), "kafes3b": ("Fx", "Fy", "Fz", "Mx", "My", "Mz"),
                  "cerceve3b": ("Fx", "Fy", "Fz", "Mx", "My", "Mz")}


def _adim_denge(M, anl):
    t = M.tip
    _basla(anl, 10, "Sağlama: denge ve enerji",
           "Bir hesabın doğru olduğuna sonuç makul görünüyor diye değil, **bağımsız bir denetimle** inanırız. İki denetim "
           "yapıyoruz: (1) dış yükler ile mesnet tepkileri bütün yapıyı dengelemeli, (2) yükün yaptığı iş, yapıda "
           "depolanan şekil değiştirme enerjisine eşit olmalı.")
    dg0 = M.dugumler[0]
    if t in ("yay", "cubuk"):
        nokta = f"düğüm {dg0.no}"
    elif M.uc:
        nokta = f"düğüm {dg0.no} ({_metin(dg0.x)}, {_metin(dg0.y)}, {_metin(dg0.z)})"
    else:
        nokta = f"düğüm {dg0.no} ({_metin(dg0.x)}, {_metin(dg0.y)})"
    olcek = _kuvvet_olcegi(M)
    ad = {"Fx": "ΣFx", "Fy": "ΣFy", "Fz": "ΣFz", "M": f"ΣM ({nokta})", "Mx": f"ΣMx ({nokta})", "My": f"ΣMy ({nokta})",
          "Mz": f"ΣMz ({nokta})"}
    b = _birimler(M)
    sat, hepsi = [], True
    for a in _DENGE_ANAHTAR[t]:
        v = M.denge[a]
        ok = _sifir_mi(M, v, olcek)
        hepsi = hepsi and ok
        sat.append([ad[a], f"{_metin(v)} {b[a]}", "✔" if ok else "✘ (denge sağlanmıyor)"])
    ek = ""
    if M.yay_sd:
        ek += " Yay kuvvetleri (−k·u) de mesnet tepkisi gibi toplama girer."
    if M.zemin_var:
        ek += " Zemin basıncının düğümlere aktarılmış eşdeğeri (−k_z·d) de toplama girer; eşdeğer yükler bileşke ve momenti korur."
    if M.cokme:
        ek += " Mesnet çökmesi yük değildir; dengeye yalnız doğurduğu tepkiler girer."
    anl.kural("Denge: dış yükler (düğüm yükleri ve yayılı yük bileşkeleri) ile mesnet tepkilerinin toplamı sıfır olmalıdır. "
              "Moment toplamı herhangi bir noktaya göre alınabilir; burada ilk düğüm seçildi." + ek)
    anl.metin("**Denge toplamları** (yük + tepki" + (" + yay" if M.yay_sd else "") + (" + zemin" if M.zemin_var else "")
              + ")\n\n" + _tablo(["Toplam", "Değer", "Sonuç"], sat))
    if hepsi:
        anl.metin("Dış kuvvetler ile tepkiler dengededir ✔: çözüm fiziksel olarak tutarlı (çözüm tek başına doğruluğu "
                  "kanıtlamaz ama hatalı mesnet, yük işareti ve birleştirme hatalarını yakalar).")
    else:
        anl.uyari("Denge sağlanmadı: yük işaretlerini, mesnetleri ve eleman bağlantılarını denetleyin.")
    uKu, uF = M.enerji["uKu"], M.enerji["uF"]
    fark = uKu - uF
    ok_e = _sifir_mi(M, fark, max(1.0, abs(_gercek(uF) or 0.0)))
    birim_e = f"{M.kuvvet}·{M.uzunluk}"
    W_tex = r"W=\tfrac12\,\mathbf{u}^T(\mathbf{F}+\mathbf{R})" if M.cokme else r"W=\tfrac12\,\mathbf{u}^T\mathbf{F}"
    if M.sembolik:
        anl.mat(rf"U=\tfrac12\,\mathbf{{u}}^T\mathbf{{K}}\mathbf{{u}} = {_L(_sade(uKu / 2))},\qquad "
                rf"{W_tex} = {_L(_sade(uF / 2))}")
    else:
        anl.mat(rf"U=\tfrac12\,\mathbf{{u}}^T\mathbf{{K}}\mathbf{{u}} = {_L(uKu / 2)}\ \text{{{birim_e}}},\qquad "
                rf"{W_tex} = {_L(uF / 2)}\ \text{{{birim_e}}}")
    anl.metin("**Enerji sağlaması (Clapeyron):** doğrusal elastik yapıda dış yükün yaptığı iş "
              "$W=\\tfrac12\\mathbf{u}^T\\mathbf{F}$, yapıda depolanan şekil değiştirme enerjisi "
              "$U=\\tfrac12\\mathbf{u}^T\\mathbf{K}\\mathbf{u}$'ya eşittir; $\\mathbf{K}$ pozitif tanımlı olduğundan $U>0$ "
              + ("olmalıdır. " if not _sifir_mi(M, uF, 1.0) else "(yük yoksa ikisi de 0'dır). ")
              + ("Mesnet çökmesinde tepkiler de verilen yer değiştirme üzerinden iş yapar; bu yüzden $W$'ye "
                 "$\\tfrac12\\mathbf{u}^T\\mathbf{R}$ eklenir. " if M.cokme else "")
              + ("Yay ve zemin enerjisi $\\mathbf{K}$ içinde olduğundan $U$'ya dahildir. " if (M.yay_sd or M.zemin_var) else "")
              + ("Eşitlik sağlandı ✔." if ok_e else "Eşitlik sağlanmadı; hesabı denetleyin."))
    if M.sayisal:
        buyuk = float(np.abs(M.u).max())
        k = int(np.abs(M.u).argmax())
        ek = f"En büyük yer değiştirme: {M.sd_et[k]} = {_ondalik_metin(float(M.u[k]))} {_sd_birimi(M, _SD_ADLARI[t][k % M.d])}."
    else:
        ek = ""
    if M.n <= 12:
        ozet = rf"\mathbf{{u}} = {_etiketli_vek(M.u, M.sd_tex)}"
        anl.sonuc(ozet, f"Global yer değiştirme vektörü ({M.uzunluk}; dönmeler rad). {ek}".strip())
    else:
        anl.sonuc(r"\mathbf{u}\ \text{(" + str(M.n) + r" bileşen; tablolar yukarıda)}", ek or "Yer değiştirmeler yukarıdaki tabloda.")


# ============================================================================
# Adım 11: bağımsız Python betiği (gerçekten çalıştırılır)
# ============================================================================
def _py_sayi(M, x):
    """Üretilen betiğe yazılacak sayı metni (kesin modda tam kesirli)."""
    if M.sayisal:
        return repr(float(x))
    x = sp.sympify(x)
    if x.is_Integer:
        return str(int(x))
    if x.is_Rational:
        return f"sp.Rational({x.p}, {x.q})"
    if x.is_Float:
        return repr(float(x))
    s = sp.sstr(x).replace("sqrt(", "sp.sqrt(")
    return re.sub(r"(?<![\w.])(\d+)/(\d+)", r"sp.Rational(\1, \2)", s)


_PY_ELEMAN = {
    "yay": '''def eleman_matrisleri(e):
    i, j, kk = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    ci = 1 if dx > 0 else -1              # eleman ekseni yönü (+x ya da -x)
    kl = mat([[kk, -kk], [-kk, kk]])      # yerel yay matrisi
    Te = mat([[ci, 0], [0, ci]])          # dönüşüm (yalnız yön işareti)
    return kl, Te, [sd*i, sd*j], None
''',
    "cubuk": '''def eleman_matrisleri(e):
    i, j, Ek, Ak = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    Lb = abs(dx)                          # eleman boyu
    ci = 1 if dx > 0 else -1              # eleman ekseni yönü (+x ya da -x)
    ea = Ek*Ak/Lb
    kl = mat([[ea, -ea], [-ea, ea]])      # yerel matris EA/L [[1,-1],[-1,1]]
    Te = mat([[ci, 0], [0, ci]])
    return kl, Te, [sd*i, sd*j], None
''',
    "kafes": '''def eleman_matrisleri(e):
    i, j, Ek, Ak = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    dy = dugum_xy[j][1] - dugum_xy[i][1]
    Lb = kok(dx**2 + dy**2)               # eleman boyu
    ci, si = dx/Lb, dy/Lb                 # cos ve sin
    ea = Ek*Ak/Lb
    kl = mat([[ea, -ea], [-ea, ea]])      # yerel matris EA/L [[1,-1],[-1,1]]
    Te = mat([[ci, si, 0, 0], [0, 0, ci, si]])   # global -> eleman ekseni
    return kl, Te, [sd*i, sd*i + 1, sd*j, sd*j + 1], None
''',
    "kiris": '''def eleman_matrisleri(e):
    i, j, Ek, Ik, yuk = e
    Lb = dugum_xy[j][0] - dugum_xy[i][0]  # eleman boyu
    a = Ek*Ik/Lb**3
    kl = mat([[12*a, 6*Lb*a, -12*a, 6*Lb*a],
              [6*Lb*a, 4*Lb**2*a, -6*Lb*a, 2*Lb**2*a],
              [-12*a, -6*Lb*a, 12*a, -6*Lb*a],
              [6*Lb*a, 2*Lb**2*a, -6*Lb*a, 4*Lb**2*a]])
    feq = None
    if yuk:                               # yayılı yükün eşdeğer düğüm yükleri
        feq = mat(feq_yayili(Lb, yuk))
    return kl, None, [sd*i, sd*i + 1, sd*j, sd*j + 1], feq
''',
    "cerceve": '''def eleman_matrisleri(e):
    i, j, Ek, Ak, Ik, yuk = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    dy = dugum_xy[j][1] - dugum_xy[i][1]
    Lb = kok(dx**2 + dy**2)               # eleman boyu
    ci, si = dx/Lb, dy/Lb                 # cos ve sin
    ea = Ek*Ak/Lb
    a = Ek*Ik/Lb**3
    kl = mat([[ea, 0, 0, -ea, 0, 0],
              [0, 12*a, 6*Lb*a, 0, -12*a, 6*Lb*a],
              [0, 6*Lb*a, 4*Lb**2*a, 0, -6*Lb*a, 2*Lb**2*a],
              [-ea, 0, 0, ea, 0, 0],
              [0, -12*a, -6*Lb*a, 0, 12*a, -6*Lb*a],
              [0, 6*Lb*a, 2*Lb**2*a, 0, -6*Lb*a, 4*Lb**2*a]])
    Te = mat([[ci, si, 0, 0, 0, 0], [-si, ci, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
              [0, 0, 0, ci, si, 0], [0, 0, 0, -si, ci, 0], [0, 0, 0, 0, 0, 1]])
    feq = None
    if yuk:                               # yayılı yükün eşdeğer düğüm yükleri (yerel eksende)
        fq = feq_yayili(Lb, yuk)
        feq = mat([0, fq[0], fq[1], 0, fq[2], fq[3]])
    return kl, Te, [sd*i, sd*i + 1, sd*i + 2, sd*j, sd*j + 1, sd*j + 2], feq
''',
    "kiris_zemin": '''def eleman_matrisleri(e):
    i, j, Ek, Ik, yuk, ks = e
    Lb = dugum_xy[j][0] - dugum_xy[i][0]  # eleman boyu
    a = Ek*Ik/Lb**3
    kl = mat([[12*a, 6*Lb*a, -12*a, 6*Lb*a],
              [6*Lb*a, 4*Lb**2*a, -6*Lb*a, 2*Lb**2*a],
              [-12*a, -6*Lb*a, 12*a, -6*Lb*a],
              [6*Lb*a, 2*Lb**2*a, -6*Lb*a, 4*Lb**2*a]])
    if ks != 0:                           # Winkler zemini: tutarlı zemin matrisi (k_s L/420)[...]
        z = ks*Lb/420
        kl = kl + mat([[156*z, 22*Lb*z, 54*z, -13*Lb*z],
                       [22*Lb*z, 4*Lb**2*z, 13*Lb*z, -3*Lb**2*z],
                       [54*z, 13*Lb*z, 156*z, -22*Lb*z],
                       [-13*Lb*z, -3*Lb**2*z, -22*Lb*z, 4*Lb**2*z]])
    feq = None
    if yuk:                               # yayılı yükün eşdeğer düğüm yükleri
        feq = mat(feq_yayili(Lb, yuk))
    return kl, None, [sd*i, sd*i + 1, sd*j, sd*j + 1], feq
''',
    "cerceve_zemin": '''def eleman_matrisleri(e):
    i, j, Ek, Ak, Ik, yuk, ks = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    dy = dugum_xy[j][1] - dugum_xy[i][1]
    Lb = kok(dx**2 + dy**2)               # eleman boyu
    ci, si = dx/Lb, dy/Lb                 # cos ve sin
    ea = Ek*Ak/Lb
    a = Ek*Ik/Lb**3
    kl = mat([[ea, 0, 0, -ea, 0, 0],
              [0, 12*a, 6*Lb*a, 0, -12*a, 6*Lb*a],
              [0, 6*Lb*a, 4*Lb**2*a, 0, -6*Lb*a, 2*Lb**2*a],
              [-ea, 0, 0, ea, 0, 0],
              [0, -12*a, -6*Lb*a, 0, 12*a, -6*Lb*a],
              [0, 6*Lb*a, 2*Lb**2*a, 0, -6*Lb*a, 4*Lb**2*a]])
    if ks != 0:                           # Winkler zemini: v ve θ serbestliklerine (k_s L/420)[...]
        z = ks*Lb/420
        kz = mat([[156*z, 22*Lb*z, 54*z, -13*Lb*z],
                  [22*Lb*z, 4*Lb**2*z, 13*Lb*z, -3*Lb**2*z],
                  [54*z, 13*Lb*z, 156*z, -22*Lb*z],
                  [-13*Lb*z, -3*Lb**2*z, -22*Lb*z, 4*Lb**2*z]])
        yer = (1, 2, 4, 5)
        for a_, p in enumerate(yer):
            for b_, r in enumerate(yer):
                kl[p, r] += kz[a_, b_]
    Te = mat([[ci, si, 0, 0, 0, 0], [-si, ci, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
              [0, 0, 0, ci, si, 0], [0, 0, 0, -si, ci, 0], [0, 0, 0, 0, 0, 1]])
    feq = None
    if yuk:                               # yayılı yükün eşdeğer düğüm yükleri (yerel eksende)
        fq = feq_yayili(Lb, yuk)
        feq = mat([0, fq[0], fq[1], 0, fq[2], fq[3]])
    return kl, Te, [sd*i, sd*i + 1, sd*i + 2, sd*j, sd*j + 1, sd*j + 2], feq
''',
    "kafes3b": '''def eleman_matrisleri(e):
    i, j, Ek, Ak = e
    dx = dugum_xyz[j][0] - dugum_xyz[i][0]
    dy = dugum_xyz[j][1] - dugum_xyz[i][1]
    dz = dugum_xyz[j][2] - dugum_xyz[i][2]
    Lb = kok(dx**2 + dy**2 + dz**2)       # eleman boyu
    cx, cy, cz = dx/Lb, dy/Lb, dz/Lb      # doğrultu kosinüsleri
    ea = Ek*Ak/Lb
    kl = mat([[ea, -ea], [-ea, ea]])      # yerel matris EA/L [[1,-1],[-1,1]]
    Te = mat([[cx, cy, cz, 0, 0, 0], [0, 0, 0, cx, cy, cz]])   # global -> eleman ekseni
    return kl, Te, [sd*i, sd*i + 1, sd*i + 2, sd*j, sd*j + 1, sd*j + 2], None
''',
    "cerceve3b": '''def eleman_matrisleri(e):
    i, j, Ek, Gk, Ak, Iy, Iz, Jk, yuk, yukz = e
    dx = dugum_xyz[j][0] - dugum_xyz[i][0]
    dy = dugum_xyz[j][1] - dugum_xyz[i][1]
    dz = dugum_xyz[j][2] - dugum_xyz[i][2]
    Lb = kok(dx**2 + dy**2 + dz**2)       # eleman boyu
    cx, cy, cz = dx/Lb, dy/Lb, dz/Lb      # doğrultu kosinüsleri
    ea, gj = Ek*Ak/Lb, Gk*Jk/Lb
    by, bz = Ek*Iy/Lb**3, Ek*Iz/Lb**3
    kl = sifirlar(12, 12)                 # sıra: u, v, w, θx, θy, θz (i), aynısı (j)
    def koy(a, b, v):
        kl[a, b] = v
        kl[b, a] = v
    koy(0, 0, ea); koy(0, 6, -ea); koy(6, 6, ea)                                   # eksenel
    koy(3, 3, gj); koy(3, 9, -gj); koy(9, 9, gj)                                   # burulma
    koy(1, 1, 12*bz); koy(1, 5, 6*Lb*bz); koy(1, 7, -12*bz); koy(1, 11, 6*Lb*bz)   # x'y' eğilme (Iz)
    koy(5, 5, 4*Lb**2*bz); koy(5, 7, -6*Lb*bz); koy(5, 11, 2*Lb**2*bz)
    koy(7, 7, 12*bz); koy(7, 11, -6*Lb*bz); koy(11, 11, 4*Lb**2*bz)
    koy(2, 2, 12*by); koy(2, 4, -6*Lb*by); koy(2, 8, -12*by); koy(2, 10, -6*Lb*by)  # x'z' eğilme (Iy)
    koy(4, 4, 4*Lb**2*by); koy(4, 8, 6*Lb*by); koy(4, 10, 2*Lb**2*by)
    koy(8, 8, 12*by); koy(8, 10, 6*Lb*by); koy(10, 10, 4*Lb**2*by)
    D = kok(cx**2 + cz**2)                # yerel eksenler: y' düşey düzlemde yukarı, z' yatay
    if D {DUSEY}:                            # düşey eleman: z' = Z
        lam = [[0, cy, 0], [-cy, 0, 0], [0, 0, 1]]
    else:
        lam = [[cx, cy, cz], [-cx*cy/D, D, -cy*cz/D], [-cz/D, 0, cx/D]]
    Te = sifirlar(12, 12)
    for b in range(4):
        for a in range(3):
            for c in range(3):
                Te[3*b + a, 3*b + c] = lam[a][c]
    feq = None
    if yuk or yukz:                       # yayılı yükün eşdeğer düğüm yükleri (yerel y' ve z'; θy = -w' olduğundan z' momentleri ters)
        fq, fz = feq_yayili(Lb, yuk), feq_yayili(Lb, yukz)
        feq = mat([0, fq[0], fz[0], 0, -fz[1], fq[1], 0, fq[2], fz[2], 0, -fz[3], fq[3]])
    return kl, Te, [sd*i + a for a in range(6)] + [sd*j + a for a in range(6)], feq
''',
}

# Parçalı doğrusal yayılı yükün eşdeğer düğüm yükleri (betikte; motorun _feq_parcali'siyle aynı 3 noktalı Gauss)
_PY_FEQ = '''GAUSS = {GAUSS}   # 3 noktalı Gauss–Legendre: (ξ, w); 5. dereceye kadar polinomu tam integre eder

def feq_yayili(Lb, yuk):
    """[f_v,i, m_i, f_v,j, m_j] = Σ ∫ N^T q(x) dx; yuk = [(q1, q2, x1, x2), ...] (q doğrusal, N Hermite kübik)."""
    f = [0, 0, 0, 0]
    for q1, q2, x1, x2 in yuk:
        h = (x2 - x1)/2
        for g, w in GAUSS:
            x = x1 + h*(1 + g)
            q = q1 + (q2 - q1)*(x - x1)/(x2 - x1)
            xi = x/Lb
            N = (1 - 3*xi**2 + 2*xi**3, Lb*(xi - 2*xi**2 + xi**3), 3*xi**2 - 2*xi**3, Lb*(-xi**2 + xi**3))
            for a in range(4):
                f[a] += w*h*q*N[a]
    return {DONUS}
'''


def _py_parcalar(M, parcalar):
    """Betikte yayılı yük listesi: [(q1, q2, x1, x2), ...]."""
    return "[" + ", ".join("(" + ", ".join(_py_sayi(M, v) for v in p) + ")" for p in parcalar) + "]"


def _py_eleman_satiri(M, e):
    t = M.tip
    z = e.zemin if e.zemin is not None else 0
    yuk = _py_parcalar(M, e.parcalar)
    deg = {"yay": [e.k], "cubuk": [e.E, e.A], "kafes": [e.E, e.A], "kafes3b": [e.E, e.A],
           "kiris": [e.E, e.I, yuk] + ([z] if M.zemin_var else []),
           "cerceve": [e.E, e.A, e.I, yuk] + ([z] if M.zemin_var else []),
           "cerceve3b": [e.E, e.G, e.A, e.Iy, e.Iz, e.J, yuk, _py_parcalar(M, e.parcalar_z)]}[t]
    if _py_eksenel_var(M):
        deg.append(_py_parcalar(M, e.parcalar_x))
    if t == "cerceve3b" and M.aci_var:
        deg.append(e.eksen_aci)
    return "(" + ", ".join([str(e.ia), str(e.ib)] + [v if isinstance(v, str) else _py_sayi(M, v) for v in deg]) + "),"


def _py_eksenel_var(M):
    return M.tip in ("cerceve", "cerceve3b") and any(getattr(e, "parcalar_x", None) for e in M.elemanlar)


_PY_EKSENEL = '''def feq_eksenel(Lb, yuk):
    """[f_x,i, f_x,j] = Σ ∫ [1 - x/L, x/L] q(x) dx (yerel x', doğrusal şekil fonksiyonları; kapalı form)."""
    fi, fj = 0, 0
    for q1, q2, x1, x2 in yuk:
        D = x2 - x1
        W = (q1 + q2)*D/2                                       # parçanın bileşkesi
        S = q1*x1*D + q1*D**2/2 + (q2 - q1)*(x1*D/2 + D**2/3)   # ilk düğüme göre statik momenti
        fi += W - S/Lb
        fj += S/Lb
    return [fi, fj]
'''

_PY_YOGUN_SAYI = '''def yogunlastir(kl, feq, r):
    """Uç serbestliği (statik yoğunlaştırma): r serbest bırakılan yerel SD'ler.
    k* = k_ff - k_fr k_rr^-1 k_rf,  f* = f_f - k_fr k_rr^-1 f_r  (r satır/sütunları 0)."""
    n = kl.shape[0]
    f = [a for a in range(n) if a not in r]
    krr = kl[np.ix_(r, r)]
    kc = np.zeros((n, n))
    kc[np.ix_(f, f)] = kl[np.ix_(f, f)] - kl[np.ix_(f, r)] @ np.linalg.solve(krr, kl[np.ix_(r, f)])
    fc = None
    if feq is not None:
        fc = np.zeros(n)
        fc[f] = feq[f] - kl[np.ix_(f, r)] @ np.linalg.solve(krr, feq[r])
    return kc, fc

def geri_kazan(kl, feq, de, r):
    """Serbest bırakılan SD'lerin yer değiştirmesi: d_r = k_rr^-1 (f_r - k_rf d_f) (serbest uçta iç kuvvet 0)."""
    f = [a for a in range(len(de)) if a not in r]
    fr = np.zeros(len(r)) if feq is None else feq[r]
    de = np.array(de, dtype=float)
    de[r] = np.linalg.solve(kl[np.ix_(r, r)], fr - kl[np.ix_(r, f)] @ de[f])
    return de
'''

_PY_YOGUN_KESIN = '''def yogunlastir(kl, feq, r):
    """Uç serbestliği (statik yoğunlaştırma): r serbest bırakılan yerel SD'ler.
    k* = k_ff - k_fr k_rr^-1 k_rf,  f* = f_f - k_fr k_rr^-1 f_r  (r satır/sütunları 0)."""
    n = kl.shape[0]
    f = [a for a in range(n) if a not in r]
    Kinv = kl.extract(r, r).inv()
    kff = kl.extract(f, f) - kl.extract(f, r)*Kinv*kl.extract(r, f)
    kc = sp.zeros(n, n)
    for a, p in enumerate(f):
        for b, q in enumerate(f):
            kc[p, q] = sp.cancel(kff[a, b])
    fc = None
    if feq is not None:
        ff = sp.Matrix([feq[a] for a in f]) - kl.extract(f, r)*Kinv*sp.Matrix([feq[a] for a in r])
        fc = sp.zeros(n, 1)
        for a, p in enumerate(f):
            fc[p] = sp.cancel(ff[a])
    return kc, fc

def geri_kazan(kl, feq, de, r):
    """Serbest bırakılan SD'lerin yer değiştirmesi: d_r = k_rr^-1 (f_r - k_rf d_f) (serbest uçta iç kuvvet 0)."""
    f = [a for a in range(len(de)) if a not in r]
    fr = sp.zeros(len(r), 1) if feq is None else sp.Matrix([feq[a] for a in r])
    dr = kl.extract(r, r).inv()*(fr - kl.extract(r, f)*sp.Matrix([de[a] for a in f]))
    de = sp.Matrix(de)
    for k, a in enumerate(r):
        de[a] = sp.cancel(dr[k])
    return de
'''


def _py_eleman_kodu(M, sablon, kesin):
    """Eleman matrisi şablonu; eksenel yayılı yük (yukx) ve yerel eksen açısı (aci) kullanılıyorsa şablon genişletilir."""
    t = M.tip
    kod = _PY_ELEMAN[sablon].replace("{DUSEY}", "== 0" if kesin else "< 1e-12")
    ek = []
    if _py_eksenel_var(M):
        ek.append("yukx")
    if t == "cerceve3b" and M.aci_var:
        ek.append("aci")
    if ek:
        satirlar = kod.split("\n")
        satirlar[1] = satirlar[1].replace(" = e", ", " + ", ".join(ek) + " = e")
        kod = "\n".join(satirlar)
    if "yukx" in ek:
        if t == "cerceve":
            eski = ("    if yuk:                               # yayılı yükün eşdeğer düğüm yükleri (yerel eksende)\n"
                    "        fq = feq_yayili(Lb, yuk)\n"
                    "        feq = mat([0, fq[0], fq[1], 0, fq[2], fq[3]])\n")
            yeni = ("    if yuk or yukx:                       # yayılı yükün eşdeğer düğüm yükleri (yerel y' ve eksenel x')\n"
                    "        fq, fx = feq_yayili(Lb, yuk), feq_eksenel(Lb, yukx)\n"
                    "        feq = mat([fx[0], fq[0], fq[1], fx[1], fq[2], fq[3]])\n")
        else:
            eski = ("    if yuk or yukz:                       # yayılı yükün eşdeğer düğüm yükleri (yerel y' ve z'; θy = -w' olduğundan z' momentleri ters)\n"
                    "        fq, fz = feq_yayili(Lb, yuk), feq_yayili(Lb, yukz)\n"
                    "        feq = mat([0, fq[0], fz[0], 0, -fz[1], fq[1], 0, fq[2], fz[2], 0, -fz[3], fq[3]])\n")
            yeni = ("    if yuk or yukz or yukx:               # yayılı yükün eşdeğer düğüm yükleri (yerel y', z' ve eksenel x'; θy = -w' olduğundan z' momentleri ters)\n"
                    "        fq, fz, fx = feq_yayili(Lb, yuk), feq_yayili(Lb, yukz), feq_eksenel(Lb, yukx)\n"
                    "        feq = mat([fx[0], fq[0], fz[0], 0, -fz[1], fq[1], fx[1], fq[2], fz[2], 0, -fz[3], fq[3]])\n")
        assert eski in kod
        kod = kod.replace(eski, yeni)
    if "aci" in ek:
        don = ("sp.cos(sp.pi*aci/180), sp.sin(sp.pi*aci/180)" if kesin else "np.cos(np.radians(aci)), np.sin(np.radians(aci))")
        eski = "    Te = sifirlar(12, 12)\n"
        yeni = ("    if aci != 0:                          # yerel eksen açısı: y', z' x' etrafında aci kadar döner (sağ el)\n"
                f"        ca, sa = {don}\n"
                "        lam = [lam[0], [ca*lam[1][k] + sa*lam[2][k] for k in range(3)],\n"
                "               [-sa*lam[1][k] + ca*lam[2][k] for k in range(3)]]\n" + eski)
        kod = kod.replace(eski, yeni, 1)
    return kod


def _py_betik(M):
    t, d, kesin = M.tip, M.d, not M.sayisal
    S = lambda x: _py_sayi(M, x)  # noqa: E731
    ad_e = {"yay": "(i, j, k)", "cubuk": "(i, j, E, A)", "kafes": "(i, j, E, A)", "kafes3b": "(i, j, E, A)",
            "kiris": "(i, j, E, I, yuk, k_s)" if M.zemin_var else "(i, j, E, I, yuk)",
            "cerceve": "(i, j, E, A, I, yuk, k_s)" if M.zemin_var else "(i, j, E, A, I, yuk)",
            "cerceve3b": "(i, j, E, G, A, Iy, Iz, J, yuk, yukz)"}[t]
    sablon = t + ("_zemin" if (M.zemin_var and t in ("kiris", "cerceve")) else "")
    koord = "dugum_xyz" if M.uc else "dugum_xy"
    s = [f"# {M.baslik}: {_TIP_AD[t]}, {M.n} SD, doğrudan rijitlik yöntemi (tek başına çalışır)"]
    if kesin:
        s += ["import sympy as sp", "mat = sp.Matrix", "kok = sp.sqrt", ""]
        semb = set()
        for e in M.elemanlar:
            yuk_degerleri = [v for p in e.parcalar + e.parcalar_z for v in p[:2]]
            for v in (e.E, e.A, e.I, e.k, e.G, e.Iy, e.Iz, e.J, e.zemin, *yuk_degerleri):
                if isinstance(v, sp.Basic):
                    semb |= v.free_symbols
        for satir in list(M.yuk) + list(M.yay):
            for v in satir:
                semb |= sp.sympify(v).free_symbols
        for v in M.cokme.values():
            semb |= sp.sympify(v).free_symbols
        if semb:
            ad = sorted(x.name for x in semb)
            s += [f"{', '.join(ad)} = sp.symbols('{' '.join(ad)}')" if len(ad) > 1
                  else f"{ad[0]} = sp.symbols('{ad[0]}')", ""]

        s += ["def sifirlar(n, m=1):", "    return sp.zeros(n, m)", ""]
    else:
        s += ["import numpy as np", "np.set_printoptions(precision=6, suppress=True, linewidth=110)",
              "kok = np.sqrt", "", "def mat(a):", "    return np.array(a, dtype=float)", "",
              "def sifirlar(n, m=1):", "    return np.zeros(n) if m == 1 else np.zeros((n, m))", ""]
    if M.uc:
        koord_satir = f"{koord} = [" + ", ".join(f"({S(g.x)}, {S(g.y)}, {S(g.z)})" for g in M.dugumler) + "]   # düğüm koordinatları"
    else:
        koord_satir = f"{koord} = [" + ", ".join(f"({S(g.x)}, {S(g.y)})" for g in M.dugumler) + "]   # düğüm koordinatları"
    s += [f"sd = {d}                   # düğüm başına SD ({', '.join(_SD_ADLARI[t])})",
          "",
          "# --- model verisi ---",
          koord_satir,
          f"# elemanlar: {ad_e}; i, j = düğüm sırası (0'dan)"
          + ("; yuk = [(q1, q2, x1, x2), ...] yerel y' yönünde parçalı doğrusal yayılı yük" if t in _EGILME else "")
          + (" (yukz: yerel z')" if t == "cerceve3b" else ""),
          "elemanlar = ["] + ["    " + _py_eleman_satiri(M, e) for e in M.elemanlar] + ["]"]
    fd = [M.F_dugum[i] for i in range(M.n)]
    s += ["F_dugum = [" + ", ".join(S(v) for v in fd) + "]   # düğüm yükleri (SD sırasıyla)",
          f"sabit = {list(M.sabit)}   # tutulu SD'ler (0'dan)"]
    if M.yay_sd:
        s += ["yaylar = [" + ", ".join(f"({k}, {S(v)})" for k, v in M.yay_sd.items()) + "]   # elastik mesnetler: (SD, k)"]
    if M.cokme:
        s += ["cokme = {" + ", ".join(f"{k}: {S(v)}" for k, v in M.cokme.items()) + "}   # verilen yer değiştirmeler: SD -> değer"]
    if M.diyaframlar:
        s += ["diyaframlar = [" + ", ".join(f"({dy.ana}, {list(dy.koleler)})" for dy in M.diyaframlar)
              + "]   # rijit kat diyaframları: (efendi düğüm, köle düğümler) düğüm sırasıyla (0'dan)",
              f"sifir_sd = {sorted(M.oto_sd)}   # sanal efendi düğümlerin v, θx, θz SD'leri: hiçbir elemana bağlı değil, sıfır alınır"]
    if M.serbest_var:
        s += ["uc_serbest = {" + ", ".join(f"{e.idx}: {list(e.serbest)}" for e in M.elemanlar if e.serbest)
              + "}   # uç serbestlikleri: eleman sırası -> serbest bırakılan yerel SD'ler (0'dan; j ucu +" + str(d) + ")"]
    s += [f"n = sd*len({koord})"]
    if kesin:
        s += ["",
              "# sayıları sympy'a çevir: bölmeler kesirli kalır, yuvarlama olmaz",
              f"{koord} = [tuple(sp.sympify(c) for c in p) for p in {koord}]",
              "elemanlar = [e[:2] + tuple(sp.sympify(v) for v in e[2:]) for e in elemanlar]",
              "F_dugum = [sp.sympify(v) for v in F_dugum]"]
        if M.yay_sd:
            s += ["yaylar = [(p, sp.sympify(v)) for p, v in yaylar]"]
        if M.cokme:
            s += ["cokme = {p: sp.sympify(v) for p, v in cokme.items()}"]
    kod = _py_eleman_kodu(M, sablon, kesin)
    if t in _EGILME:
        if kesin:
            gauss = ("[(-sp.sqrt(sp.Rational(3, 5)), sp.Rational(5, 9)), (0, sp.Rational(8, 9)), "
                     "(sp.sqrt(sp.Rational(3, 5)), sp.Rational(5, 9))]")
            donus = "[sp.expand(v) for v in f]   # köklü Gauss düğümleri birbirini götürür: sonuç kesirli"
        else:
            gauss = "[(-kok(0.6), 5/9), (0.0, 8/9), (kok(0.6), 5/9)]"
            donus = "f"
        s += ["", "# --- yayılı yük: eşdeğer düğüm yükleri (parçalı doğrusal q1→q2, [x1, x2]; 3 noktalı Gauss) ---"]
        s += _PY_FEQ.replace("{GAUSS}", gauss).replace("{DONUS}", donus).rstrip("\n").split("\n")
        if _py_eksenel_var(M):
            s += [""] + _PY_EKSENEL.rstrip("\n").split("\n")
    if M.serbest_var:
        s += ["", "# --- uç serbestlikleri: eleman düzeyinde statik yoğunlaştırma ---"]
        s += (_PY_YOGUN_KESIN if kesin else _PY_YOGUN_SAYI).rstrip("\n").split("\n")
    s += ["", "# --- eleman matrisleri ---"] + kod.rstrip("\n").split("\n")
    s += ["",
          "# --- birleştirme: K ve F ---",
          "K = sifirlar(n, n)",
          "F = sifirlar(n)",
          "for no, e in enumerate(elemanlar):",
          "    kl, Te, dofs, feq = eleman_matrisleri(e)"]
    if M.serbest_var:
        s += ["    if no in uc_serbest:                   # mafsal/serbest uç: yoğunlaştırılmış k* ve f*",
              "        kl, feq = yogunlastir(kl, feq, uc_serbest[no])"]
    s += ["    ke = kl if Te is None else Te.T @ kl @ Te",
          "    for a, p in enumerate(dofs):",
          "        for b, r in enumerate(dofs):",
          "            K[p, r] += ke[a, b]",
          "    if feq is not None:",
          "        fg = feq if Te is None else Te.T @ feq",
          "        for a, p in enumerate(dofs):",
          "            F[p] += fg[a]",
          "for p, v in enumerate(F_dugum):",
          "    F[p] += v"]
    if M.yay_sd:
        s += ["for p, kk in yaylar:                      # yay rijitliği köşegene eklenir",
              "    K[p, p] += kk"]
    if kesin:
        s += ["K = K.applyfunc(sp.cancel)                  # pay/payda sadeleştirme (simplify büyük matriste yavaş)"]
    if M.diyaframlar:
        # rijit diyafram (yalnız sayısal kip): aynı T dönüşümü, indirgenmiş sistemde çözüm, u = T u_r
        s += ["", "# --- rijit kat diyaframı: köle SD'leri efendi SD'lerine bağlanır, u = T u_r ---",
              "bag = {}                                   # köle SD -> [(efendi SD, katsayı)]",
              "for efendi, koleler in diyaframlar:",
              "    xm, ym, zm = dugum_xyz[efendi]",
              "    for kole in koleler:",
              "        xs, ys, zs = dugum_xyz[kole]",
              "        bag[sd*kole + 0] = [(sd*efendi + 0, 1.0), (sd*efendi + 4, zs - zm)]     # u_s = u_m + θy_m (z_s - z_m)",
              "        bag[sd*kole + 2] = [(sd*efendi + 2, 1.0), (sd*efendi + 4, -(xs - xm))]  # w_s = w_m - θy_m (x_s - x_m)",
              "        bag[sd*kole + 4] = [(sd*efendi + 4, 1.0)]                               # θy_s = θy_m",
              "ind = [p for p in range(n) if p not in bag and p not in sifir_sd]   # indirgenmiş (bağımsız) SD'ler",
              "kol = {p: a for a, p in enumerate(ind)}",
              "T = sifirlar(n, len(ind))",
              "for p in ind:",
              "    T[p, kol[p]] = 1.0",
              "for p, terimler in bag.items():",
              "    for q, c in terimler:",
              "        T[p, kol[q]] += c",
              "K_r = T.T @ K @ T                          # K_r = Tᵀ K T",
              "F_r = T.T @ F                              # F_r = Tᵀ F",
              "",
              "# --- sınır koşulları ve çözüm (indirgenmiş sistemde) ---",
              "sabit_r = [kol[p] for p in sabit if p in kol]",
              "serbest_r = [a for a in range(len(ind)) if a not in sabit_r]",
              "u_r = sifirlar(len(ind))"]
        if M.cokme:
            s += ["for p, v in cokme.items():                # bilinen (sıfır olmayan) yer değiştirmeler",
                  "    u_r[kol[p]] = v"]
        s += ["if serbest_r:"]
        if M.cokme:
            s += ["    Fs = F_r[serbest_r] - K_r[np.ix_(serbest_r, sabit_r)] @ u_r[sabit_r]   # F_f - K_fs u_s",
                  "    u_r[serbest_r] = np.linalg.solve(K_r[np.ix_(serbest_r, serbest_r)], Fs)"]
        else:
            s += ["    u_r[serbest_r] = np.linalg.solve(K_r[np.ix_(serbest_r, serbest_r)], F_r[serbest_r])"]
        s += ["u = T @ u_r                                # tam yer değiştirme vektörü",
              "artik = K @ u - F                          # köle SD'lerinde diyafram kuvveti, ötekilerde tepki",
              "F_diyafram = {p: artik[p] for p in bag}    # diyaframın köle düğüme uyguladığı kuvvet (iç kuvvet)",
              "R = sifirlar(n)",
              "R[ind] = T.T @ artik                       # tepkiler R_r = Tᵀ (K u - F): efendi, köle kuvvetlerini toplar"]
    else:
        s += ["", "# --- sınır koşulları ve çözüm ---",
              "serbest = [p for p in range(n) if p not in sabit]",
              "u = sifirlar(n)"]
    if M.cokme and not M.diyaframlar:
        s += ["for p, v in cokme.items():                # bilinen (sıfır olmayan) yer değiştirmeler",
              "    u[p] = v"]
    if M.diyaframlar:
        pass
    elif kesin:
        s += ["if serbest:",
              "    Ks = K.extract(serbest, serbest)",
              "    Fs = sp.Matrix([F[p] for p in serbest])"]
        if M.cokme:
            s += ["    Fs = Fs - K.extract(serbest, sabit)*sp.Matrix([u[p] for p in sabit])   # F_f - K_fs u_s"]
        s += ["    (us,) = sp.linsolve((Ks, Fs))        # kesin çözüm (LUsolve + simplify köklü/harfli girdide şişer)",
              "    for a, p in enumerate(serbest):",
              "        u[p] = sp.cancel(us[a])",
              "R = (K*u - F).applyfunc(sp.cancel)       # tepkiler R = K u - F"]
    else:
        s += ["if serbest:"]
        if M.cokme:
            s += ["    Fs = F[serbest] - K[np.ix_(serbest, sabit)] @ u[sabit]   # F_f - K_fs u_s",
                  "    u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], Fs)"]
        else:
            s += ["    u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], F[serbest])"]
        s += ["R = K @ u - F                            # tepkiler R = K u - F"]
    s += ["", "# --- sonuçlar ---",
          "print('u =', " + ("list(u))" if kesin else "u)"),
          "print('Mesnet tepkileri (tutulu SD, 1 tabanlı):')",
          "for p in sabit:",
          "    print(f'  R[{p + 1}] = {R[p]}')",
          "print('Eleman kuvvetleri:')",
          "for no, e in enumerate(elemanlar, start=1):",
          "    kl, Te, dofs, feq = eleman_matrisleri(e)",
          "    ue = mat([u[p] for p in dofs])",
          "    de = ue if Te is None else Te @ ue      # eleman eksenindeki yer değiştirme"]
    if M.serbest_var:
        s += ["    if no - 1 in uc_serbest:                # serbest uçtaki yer değiştirme geri kazanılır (o uçta iç kuvvet 0)",
              "        de = geri_kazan(kl, feq, de, uc_serbest[no - 1])"]
    s += [
          "    f = kl @ de",
          "    if feq is not None:",
          "        f = f - feq                         # f = k d - f_eq"]
    if kesin:
        s += ["    f = f.applyfunc(sp.cancel)"]
    if t in _EKSENEL:
        s += ["    N = f[1]                                # eksenel kuvvet (çekme +)",
              ("    print(f'  Eleman {no}: N = {N}')" if kesin else "    print(f'  Eleman {no}: N = {float(N):.6g}')")]
    else:
        s += [("    print(f'  Eleman {no}: f = {list(f)}')" if kesin
               else "    print(f'  Eleman {no}: f = {[round(float(x), 6) for x in f]}')")]
    return s


def _adim_python(M, anl):
    _basla(anl, 11, "Aynı hesap Python'da",
           "Elle yaptığımız bütün işlemleri (eleman matrisi, birleştirme, sınır koşulu, çözüm, tepkiler, eleman kuvvetleri) "
           "tek bir betikte topluyoruz. Betik kendi başına çalışır; çıktısı yukarıdaki sonuçlarla aynı olmalıdır. "
           + ("Kesin modda `sympy` (kesirli/harfli sonuç), sayısal modda `numpy` kullanılır."))
    kod, cikti = mo._python_bolumu(anl, _py_betik(M))
    return kod, cikti


# ============================================================================
# Yapılı sonuç verisi ve genel işlev
# ============================================================================
def _yayili_veri(parcalar):
    """Elemanın yayılı yük parçaları (veri çıktısı): [{q1, q2, x1, x2}, ...] (x2 eleman sonuysa L değeri yazılır)."""
    V = _veri_sayi
    return [{"q1": V(q1), "q2": V(q2), "x1": V(x1), "x2": V(x2)} for q1, q2, x1, x2 in parcalar]


def _diyafram_veri(M, V):
    """Veri çıktısı için (diyaframlar, diyafram_kuvvetleri) listeleri. ``diyafram_kuvvetleri``: diyaframın köle düğüme
    uyguladığı düzlem içi kuvvetler (Fx, Fz, My; global eksen yönünde +), tepkilerden ayrı (iç kuvvet)."""
    d = M.d
    diyaframlar = [{"ad": dy.ad, "ana": M.dugumler[dy.ana].no, "sanal": dy.sanal,
                    "dugumler": [M.dugumler[i].no for i in dy.koleler]} for dy in M.diyaframlar]
    kuvvetler = []
    for dy in M.diyaframlar:
        for i in dy.koleler:
            kuvvetler.append({"dugum": M.dugumler[i].no, "diyafram": dy.ad, "Fx": V(M.F_diyafram[d * i]),
                              "Fz": V(M.F_diyafram[d * i + 2]), "My": V(M.F_diyafram[d * i + 4])})
    return diyaframlar, kuvvetler


def _veri_olustur(M):
    """Sonuc.veri: JSON'a uygun, yapılı sonuçlar (sembolik çözümde sayı yerine ifade metni)."""
    t, d = M.tip, M.d
    V = _veri_sayi
    nmax = _en_buyuk_N(M)
    dugumler = []
    for i, dg in enumerate(M.dugumler):
        dugumler.append({"no": dg.no, "x": V(dg.x), "y": V(dg.y), "z": V(dg.z),
                         "sd": [d * i + j + 1 for j in range(d)],
                         "u": [V(M.u[d * i + j]) for j in range(d)], "sanal": dg.sanal})
    elemanlar = []
    for e in M.elemanlar:
        uc = [V(-e.N), V(e.N)] if e.f is None else [V(x) for x in e.f]
        kayit = {
            "no": e.no, "dugumler": list(e.dno), "L": V(e.L), "c": V(e.c), "s": V(e.s),
            "uc_kuvvetleri": uc, "N": V(e.N), "durum": _durum(M, e, nmax),
            "zemin": (None if e.zemin is None else V(e.zemin)),
            "zemin_kuvvetleri": (None if e.f_zemin is None else [V(x) for x in e.f_zemin_g]),
            "diyagram": {"x": [V(x) for x in e.dx], "N": [V(x) for x in e.dN],
                         "V": [V(x) for x in e.dV], "M": [V(x) for x in e.dM]}}
        if t in _EGILME:
            kayit["yayili"] = _yayili_veri(e.parcalar)
        if t == "cerceve3b":
            kayit["yayili_z"] = _yayili_veri(e.parcalar_z)
        if t in ("cerceve", "cerceve3b"):
            kayit["yayili_x"] = _yayili_veri(e.parcalar_x)
        if t in _SERBEST_ADLAR:
            adlar = _SERBEST_ADLAR[t]
            kayit["serbest"] = {"i": [adlar[k] for k in e.serbest if k < M.d],
                                "j": [adlar[k - M.d] for k in e.serbest if k >= M.d]}
        if t == "cerceve3b":
            kayit["aci"] = V(e.eksen_aci)
        if t in _YALNIZ_CEKME_TIP:
            kayit["yalniz_cekme"] = bool(e.yalniz_cekme)
        if M.uc:
            kayit["yon"] = [V(x) for x in e.yon]
            if e.lam is not None:
                kayit["lam"] = [[V(x) for x in satir] for satir in e.lam]
        if t == "cerceve3b":
            kayit["diyagram"]["Vz"] = [V(x) for x in e.dVz]
            kayit["diyagram"]["My"] = [V(x) for x in e.dMy]
            kayit["diyagram"]["T"] = [V(x) for x in e.dT]
        elemanlar.append(kayit)
    tepkiler = []
    for i, dg in enumerate(M.dugumler):
        if not any(M.mesnet[i]):
            continue
        if M.uc:
            r = {"dugum": dg.no, "Fx": 0.0, "Fy": 0.0, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": 0.0}
        else:
            r = {"dugum": dg.no, "Fx": 0.0, "Fy": 0.0, "M": 0.0}
        for j, ad in enumerate(_BILESEN[t]):
            if M.mesnet[i][j]:
                r[ad] = V(M.R_tam[d * i + j])
        tepkiler.append(r)
    yaylar = []
    for k, kk in M.yay_sd.items():
        i, j = divmod(k, d)
        yaylar.append({"dugum": M.dugumler[i].no, "sd": M.sd_et[k], "bilesen": _BILESEN[t][j], "k": V(kk),
                       "kuvvet": V(M.F_yay[k])})
    cokmeler = [{"dugum": M.dugumler[k // d].no, "sd": M.sd_et[k], "deger": V(v)} for k, v in M.cokme.items()]
    olcek = None
    if not M.sembolik:
        try:
            olcek = float(_olcek_bul(M))
        except (TypeError, ValueError, ArithmeticError):  # pragma: no cover
            olcek = None
    diyaframlar, diyafram_kuvvetleri = _diyafram_veri(M, V)
    veri = {
        "tip": t, "baslik": M.baslik, "birim": {"kuvvet": M.kuvvet, "uzunluk": M.uzunluk},
        "mod": M.mod, "sd_sayisi": M.n, "serbest_sd": len(M.serbest_r), "sd_etiketleri": list(M.sd_et),
        "boyut": 3 if M.uc else 2,
        "dugumler": dugumler, "elemanlar": elemanlar, "tepkiler": tepkiler,
        "yaylar": yaylar, "cokmeler": cokmeler,
        "diyaframlar": diyaframlar, "diyafram_kuvvetleri": diyafram_kuvvetleri,
        "u": [V(M.u[i]) for i in range(M.n)], "F": [V(M.F[i]) for i in range(M.n)],
        "denge": {k: V(v) for k, v in M.denge.items()},
        "olcek": olcek, "uyarilar": list(M.uyarilar),
        "K": ([[V(M.K[i, j]) for j in range(M.n)] for i in range(M.n)] if M.n <= 60 else None),
    }
    return veri


def se_coz(model, *, goster=None, anlat=True):
    """Bir sonlu eleman modelini (sözlük ya da JSON metni) doğrudan rijitlik yöntemiyle çözer.

    Dönüş: ``Sonuc`` — ``.deger`` global yer değiştirme vektörü u (sympy Matrix), ``.veri`` yapılı sonuçlar,
    ``.anlatim`` adım adım anlatım, ``.python_kodu`` / ``.python_ciktisi`` çalıştırılmış bağımsız betik.
    ``anlat=False`` hızlı yoldur: anlatım, şema ve betik üretilmez; yalnız ``.deger`` ve ``.veri`` dolar
    (``.anlatim`` boş, ``.python_kodu`` boş metin)."""
    M = _model_oku(model)
    _hazirla(M)
    _coz(M)
    _eleman_kuvvetleri(M)
    _denge_hesapla(M)
    _diyagram_hazirla(M)
    anl = mo.Anlatim()
    if not anlat:
        deger = sp.Matrix([float(v) for v in M.u]) if M.sayisal else sp.Matrix(M.u)
        sonuc = mo.Sonuc(deger, anl, "u", "", "")
        sonuc.veri = _veri_olustur(M)
        return sonuc
    _adim_model(M, anl)
    _adim_sema_model(M, anl)
    _adim_sd(M, anl)
    _adim_elemanlar(M, anl)
    _adim_birlestirme(M, anl)
    _adim_yukler(M, anl)
    _adim_cozum(M, anl)
    _adim_eleman_kuvvetleri(M, anl)
    _adim_sema_sonuc(M, anl)
    _adim_denge(M, anl)
    kod, cikti = _adim_python(M, anl)
    if M.sayisal:
        deger = sp.Matrix([float(v) for v in M.u])
    else:
        deger = sp.Matrix(M.u)
    sonuc = mo.Sonuc(deger, anl, "u", kod, cikti)
    sonuc.veri = _veri_olustur(M)
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc


# ============================================================================
# Çok yük durumlu çözüm (anlatımsız; yapı modülü ve kombinasyonlar için)
# ============================================================================
def _yuk_durumu_yukle(M, yuk, yayili, yayili_z, yayili_x=None):
    """Bir yük durumunu hazır modele yerleştirir: M.yuk, eleman parçaları ve f_eq, F vektörü."""
    M.yuk = yuk
    for e in M.elemanlar:
        _eleman_yuku(M, e, yayili[e.idx], yayili_z[e.idx], yayili_x[e.idx] if yayili_x is not None else ())
    _F_kur(M)


def _kisa_veri(M):
    """coz_coklu'nun bir yük durumu için kısa, JSON'a uygun sonucu (motor koordinatında, ondalık)."""
    t, d = M.tip, M.d
    tepkiler = []
    for i, dg in enumerate(M.dugumler):
        if not any(M.mesnet[i]):
            continue
        r = {"dugum": dg.no, "Fx": 0.0, "Fy": 0.0, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": 0.0}
        for j, ad in enumerate(_BILESEN[t]):
            if M.mesnet[i][j]:
                r["Mz" if ad == "M" else ad] = float(M.R_tam[d * i + j])
        tepkiler.append(r)
    elemanlar = []
    for e in M.elemanlar:
        uc = [float(-e.N), float(e.N)] if e.f is None else [float(x) for x in e.f]
        kayit = {"no": e.no, "uc_kuvvetleri": uc, "N": float(e.N),
                 "x": [float(x) for x in e.dx], "V": [float(x) for x in e.dV], "M": [float(x) for x in e.dM],
                 "Vz": None, "My": None, "T": None}
        if t == "cerceve3b":
            kayit["Vz"] = [float(x) for x in e.dVz]
            kayit["My"] = [float(x) for x in e.dMy]
            kayit["T"] = [float(x) for x in e.dT]
        kayit["Nx"] = [float(x) for x in e.dN]       # N(x) istasyonlarda (eksenel yayılı yükte değişken)
        enb = {"N": max(abs(v) for v in kayit["Nx"]), "V": max(abs(v) for v in kayit["V"]),
               "M": max(abs(v) for v in kayit["M"])}
        kayit["ekst"] = None
        if e.ekst is not None:                        # V = 0 kökündeki kesin M (istasyonlarda olmayabilir)
            kayit["ekst"] = [float(e.ekst[0]), float(e.ekst[1])]
            enb["M"] = max(enb["M"], abs(float(e.ekst[1])))
        if t == "cerceve3b":
            enb.update({"Vz": max(abs(v) for v in kayit["Vz"]), "My": max(abs(v) for v in kayit["My"]),
                        "T": max(abs(v) for v in kayit["T"])})
        kayit["enb"] = enb
        elemanlar.append(kayit)
    denge = {"Fx": 0.0, "Fy": 0.0, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": 0.0}
    for k, v in M.denge.items():
        denge["Mz" if k == "M" else k] = float(v)
    yaylar = []
    for k, kk in M.yay_sd.items():
        i, j = divmod(k, d)
        yaylar.append({"dugum": M.dugumler[i].no, "sd": M.sd_et[k], "bilesen": _BILESEN[t][j], "k": float(kk),
                       "kuvvet": float(M.F_yay[k])})
    _, diyafram_kuvvetleri = _diyafram_veri(M, float)
    return {"u": [float(v) for v in M.u], "F": [float(v) for v in M.F], "tepkiler": tepkiler,
            "elemanlar": elemanlar, "denge": denge, "yaylar": yaylar,
            "n": M.n, "serbest_sd": len(M.serbest_r), "diyafram_kuvvetleri": diyafram_kuvvetleri, "uyarilar": []}


def _coklu_hazirla(model, durumlar, diyagram_nokta, ad="coz_coklu"):
    """coz_coklu / coz_yalniz_cekme ortak girişi: model (yükleri atılmış, sayısal kip), hazır M, durum adları ve her
    durumun okunmuş yükleri {ad: (yuk, yayili, yayili_z, yayili_x)}, diyagram aralık sayısı."""
    model = dict(_model_sozluk(model))
    model.pop("yukler", None)
    model.pop("yayili", None)
    model["hesap"] = "sayisal"
    if isinstance(durumlar, (list, tuple)):
        durumlar = {str(k): durum for k, durum in enumerate(durumlar, start=1)}
    if not isinstance(durumlar, dict) or not durumlar:
        raise MatrisHatasi(f'{ad}: yük durumları {{ad: {{"yukler": [...], "yayili": [...]}}}} biçiminde, en az bir '
                           'durum içeren bir sözlük olmalı.')
    try:
        adet = max(1, int(diyagram_nokta) - 1)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"{ad}: diyagram_nokta tam sayı olmalı (girilen: {diyagram_nokta!r}).") from None
    M = _model_oku(model)
    _hazirla(M)
    yukler = {}
    for ad_, durum in durumlar.items():
        if isinstance(durum, (list, tuple)):
            durum = {"yukler": list(durum)}
        if not isinstance(durum, dict):
            raise MatrisHatasi(f'Yük durumu {ad_!r} bir sözlük olmalı: {{"yukler": [...], "yayili": [...]}}.')
        fazla = sorted(set(durum) - {"yukler", "yayili"})
        if fazla:
            raise MatrisHatasi(f"Yük durumu {ad_!r}: yalnız 'yukler' ve 'yayili' anahtarları kullanılabilir "
                               f"(bilinmeyen: {', '.join(repr(k) for k in fazla)}). Durumların doğrusal birleşimi "
                               "(kombinasyon, ölçek) motorda yapılmaz; sonuçlar istasyon-istasyon ölçeklenip toplanır.")
        try:
            yuk, yayili, yayili_z, yayili_x, semb = _yukleri_oku(M, durum)
        except MatrisHatasi as e:
            raise MatrisHatasi(f"Yük durumu {ad_!r}: {e}") from None
        if semb:
            raise MatrisHatasi(f"Yük durumu {ad_!r}: {ad} harfli (sembolik) yük kabul etmez; sayı girin.")
        yukler[str(ad_)] = ([[float(v) for v in satir] for satir in yuk], _parcalari_floata_cevir(yayili),
                            _parcalari_floata_cevir(yayili_z), _parcalari_floata_cevir(yayili_x))
    return M, list(yukler), yukler, adet


def _cok_sagli_coz(M, Fcok):
    """K_ff U_f = F_f − K_fs U_s (sütunlar yük durumları; diyafram varsa indirgenmiş sistemde). Dönüş U_r."""
    U = np.zeros((M.n_r, Fcok.shape[1]))
    for i, v in M.cokme.items():
        U[M.kol[i], :] = v
    if M.serbest_r:
        rhs = Fcok[M.serbest_r, :]
        if M.cokme:
            rhs = rhs - M.K_r[np.ix_(M.serbest_r, M.sabit_r)] @ U[M.sabit_r, :]
        U[M.serbest_r, :] = np.linalg.solve(M.K_r[np.ix_(M.serbest_r, M.serbest_r)], rhs)
    return U


def _durum_sonuclari(M, u_r, adet, sabit_x):
    """Çözülmüş bir durum için tepkiler, eleman kuvvetleri, denge ve diyagramlar (ortak istasyonlarda) → KISA."""
    M.u_r = u_r.copy()
    M.u = M.u_r.copy() if M.T is None else M.T @ M.u_r
    _tepki_hesapla(M)
    _eleman_kuvvetleri(M)
    _denge_hesapla(M)
    _diyagram_hazirla(M, adet=adet, sabit_x=sabit_x)
    return _kisa_veri(M)


def coz_coklu(model, durumlar, *, diyagram_nokta=11):
    """Aynı modeli birden çok yük durumu için tek seferde çözer (anlatım üretilmez; her zaman sayısal/numpy).

    ``model``: se_coz ile aynı şema; **modeldeki ``yukler`` ve ``yayili`` yoksayılır**, yükler yalnız ``durumlar``dan
    gelir (geometri, özellikler, mesnetler, yaylar, zemin ve çökmeler modelden). ``durumlar``: ``{ad: durum}`` sözlüğü
    (ya da durum listesi; adlar "1", "2", …); her durum ``{"yukler": [...], "yayili": [...]}`` (se_coz ile aynı
    kayıt biçimi: düğüm yükleri, düzgün ``q``/``qz``/``qx`` ya da parçalı doğrusal ``q1, q2, x1, x2`` / ``qz1, qz2`` /
    ``qx1, qx2``; global yönlü ``"yon": "gx"|"gy"|"gz"`` ve ``"izdusum"``).
    Rijitlik matrisi, mesnet listeleri ve mekanizma denetimi bir kez kurulur; bütün sağ taraflar tek
    ``np.linalg.solve`` çağrısıyla çözülür. Harfli (sembolik) girdi kabul edilmez.

    Dönüş ``{ad: kisa}``; ``kisa`` motor koordinatında (X sağa, Y yukarı, Z dışa) ve ondalık::

        u [n], F [n],
        tepkiler  [{dugum, Fx, Fy, Fz, Mx, My, Mz}]        # yalnız mesnetli düğümler (2B'de M → Mz)
        elemanlar [{no, uc_kuvvetleri [yerel, SE işareti], N (i ucunda), Nx [N(x) istasyonlarda], x, V, M, Vz, My, T
                    (2B'de None), enb {N, V, M[, Vz, My, T]} (mutlak en büyükler), ekst [x, M] | None (V = 0 kökündeki M)}]
        denge {Fx, Fy, Fz, Mx, My, Mz}   # ≈ 0
        yaylar [{dugum, sd, bilesen, k, kuvvet}]
        uyarilar [metin]                 # örn. yalnız-çekme çubuğu varken "doğrusal ön çözüm" uyarısı

    ``diyagram_nokta``: her elemanın eşit aralıklı diyagram istasyonu sayısı. İstasyon kümesi bütün durumlar için
    ORTAKTIR: eşit aralıklı noktalar + bütün durumların yayılı yük parça sınırları; V = 0 kökleri istasyona eklenmez
    (kombinasyonlar istasyon-istasyon toplanabilsin diye), kökteki kesin M ``ekst`` ve ``enb.M`` içinde verilir.

    Modelde ``yalniz_cekme`` çubuk varsa çözüm **doğrusal ön çözümdür** (bütün çubuklar etkin): her durumun
    ``uyarilar`` listesine not düşülür ve ``warnings.warn`` verilir; basınca düşen çubuğu çıkaran çözüm için
    ``coz_yalniz_cekme`` kullanın (doğrusal olmayan davranışta süperpozisyon geçersizdir)."""
    M, adlar, yukler, adet = _coklu_hazirla(model, durumlar, diyagram_nokta)
    # --- bütün sağ taraflar bir kez: K_ff U_f = F_f − K_fs U_s (diyafram varsa indirgenmiş sistemde, u = T u_r) ---
    Fcok = np.zeros((M.n_r, len(adlar)))
    for k, ad in enumerate(adlar):
        _yuk_durumu_yukle(M, *yukler[ad])
        Fcok[:, k] = _F_indirgenmis(M)
    U = _cok_sagli_coz(M, Fcok)
    uyarilar = []
    if M.yalniz_cekme_var:
        ycs = [e.no for e in M.elemanlar if e.yalniz_cekme]
        uyarilar.append(f"Yalnız çekme çubukları var (eleman {', '.join(str(n) for n in ycs)}): coz_coklu sonucu doğrusal "
                        "ön çözümdür (bütün çubuklar etkin). Basınca düşen yalnız-çekme çubuğu olan yapıda doğrusal "
                        "süperpozisyon yanlış olur; her yük birleşimini coz_yalniz_cekme ile doğrudan çözün.")
        warnings.warn(uyarilar[0], stacklevel=2)
    # --- her durum için tepkiler, eleman kuvvetleri, denge, diyagramlar (ortak istasyonlarda) ---
    sabit_x = _ortak_istasyonlar(M, adet, [yukler[ad][1:] for ad in adlar])
    sonuc = {}
    for k, ad in enumerate(adlar):
        _yuk_durumu_yukle(M, *yukler[ad])
        sonuc[ad] = _durum_sonuclari(M, U[:, k], adet, sabit_x)
        sonuc[ad]["uyarilar"] = list(uyarilar)
    return sonuc


def _etkinlik_uygula(M, pasif):
    """Yalnız-çekme yinelemesi: ``pasif`` (eleman sıraları) devre dışı, ötekiler etkin; K yeniden kurulur (diyafram
    dönüşümü ve mekanizma denetimi dahil). Mekanizma oluşursa MatrisHatasi."""
    for e in M.elemanlar:
        e.etkin = e.idx not in pasif
    _K_kur(M)
    _diyafram_kur(M)
    _mekanizma_kontrol(M)


def coz_yalniz_cekme(model, yukler_listesi_ya_da_durumlar, *, en_fazla_yineleme=10, diyagram_nokta=11):
    """Yalnız çekme çubuklu (``"yalniz_cekme": true``; kafes, kafes3b, cerceve, cerceve3b) yapıyı her yük durumu için
    AYRI AYRI ve yinelemeli çözer (doğrusal olmayan çözüm: yalnız çekme çalışan çubuk + doğrusal olmayan statik durum).

    Her durumda: (1) bütün çubuklar etkinken çöz; (2) basınçta kalan (N < −tol) yalnız-çekme çubuklarını rijitlikten
    çıkar, devre dışı çubuklardan uzaması yeniden çekmeye dönenleri (N_sanal = EA/L·δ > tol) geri al; (3) etkin küme
    değişmeyene dek yeniden çöz (en çok ``en_fazla_yineleme`` çözüm). tol = 1e-9 · max(1, max|N|). Devre dışı çubuğun
    kendi yayılı yükü düğümlere eşdeğer yük olarak gitmeye devam eder; uç kuvvetleri −f_eq, N = 0 raporlanır.

    ``yukler_listesi_ya_da_durumlar``: coz_coklu ile aynı (``{ad: {"yukler", "yayili"}}`` ya da liste). Durumlar
    birbirinden bağımsız çözülür; **sonuçlar süperpoze edilemez**, her kombinasyon ayrı bir durum olarak verilmelidir.

    Dönüş ``{ad: kisa}``: coz_coklu KISA biçimi + ``etkin_degil`` [devre dışı eleman no'ları], ``yineleme`` (çözüm
    sayısı; 1 = ilk doğrusal çözüm yeterli) ve ``uyarilar`` [metin] (yakınsamama/salınım ya da mekanizma: bu durumda
    son kararlı etkin kümenin çözümü döner)."""
    try:
        en_fazla = max(1, int(en_fazla_yineleme))
    except (TypeError, ValueError):
        raise MatrisHatasi(f"coz_yalniz_cekme: en_fazla_yineleme tam sayı olmalı (girilen: {en_fazla_yineleme!r}).") from None
    M, adlar, yukler, adet = _coklu_hazirla(model, yukler_listesi_ya_da_durumlar, diyagram_nokta, ad="coz_yalniz_cekme")
    yc = [e for e in M.elemanlar if e.yalniz_cekme]
    sabit_x = _ortak_istasyonlar(M, adet, [yukler[ad][1:] for ad in adlar])
    sonuc = {}
    for ad in adlar:
        _yuk_durumu_yukle(M, *yukler[ad])
        pasif, gecmis, uyarilar, yineleme = set(), [], [], 0
        kararli = None              # son başarılı çözümün (pasif kümesi, u_r)
        while True:
            try:
                _etkinlik_uygula(M, pasif)
            except MatrisHatasi as hata:
                if kararli is None:
                    raise
                uyarilar.append(f"Mekanizma: basınçtaki yalnız-çekme çubukları (eleman "
                                f"{', '.join(str(M.elemanlar[i].no) for i in sorted(pasif))}) çıkarılınca yapı kararsız "
                                f"kalıyor; son kararlı etkin kümenin çözümü verildi (doğrusal olmayan çözüm yakınsamadı). "
                                f"Ayrıntı: {hata}")
                pasif = kararli[0]
                _etkinlik_uygula(M, pasif)
                break
            yineleme += 1
            u_r = _cok_sagli_coz(M, _F_indirgenmis(M).reshape(-1, 1))[:, 0]
            M.u_r = u_r
            M.u = u_r.copy() if M.T is None else M.T @ u_r
            _eleman_kuvvetleri(M)
            kararli = (set(pasif), u_r)
            olcek = max([1.0] + [abs(float(e.N)) for e in M.elemanlar])
            tol = 1e-9 * olcek
            yeni = set()
            for e in yc:
                if e.etkin:
                    if float(e.N) < -tol:
                        yeni.add(e.idx)
                elif float(e.N_sanal) <= tol:
                    yeni.add(e.idx)
            if yeni == pasif:
                break
            if yineleme >= en_fazla:
                uyarilar.append(f"Yakınsamadı: {en_fazla} yinelemede etkin çubuk kümesi kararlı hale gelmedi; son çözüm "
                                "verildi (bazı yalnız-çekme çubukları basınçta ya da devre dışı çubuklar çekmede olabilir).")
                break
            if yeni in gecmis:
                uyarilar.append("Salınım: etkin çubuk kümesi daha önce denenmiş bir kümeye döndü (kararsızlık); son çözüm "
                                "verildi. Yükleri ya da çapraz düzenini denetleyin.")
                break
            gecmis.append(set(pasif))
            pasif = yeni
        kisa = _durum_sonuclari(M, kararli[1], adet, sabit_x)   # etkin küme = kararli[0] = pasif
        kisa["etkin_degil"] = sorted(M.elemanlar[i].no for i in pasif)
        kisa["yineleme"] = yineleme
        kisa["uyarilar"] = uyarilar
        sonuc[ad] = kisa
    # model nesnesi sonraki kullanım için bütün çubuklar etkin hale getirilir
    for e in M.elemanlar:
        e.etkin = True
    return sonuc
