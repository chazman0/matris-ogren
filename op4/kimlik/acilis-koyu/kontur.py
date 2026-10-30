"""Simge PNG'sinin alfa kanalından kemer ve kilit taşı konturlarını çıkarır.

Çıktılar (simge PNG koordinatlarında, 1200x1397):
  kontur.json : kalem yolları (her biri nokta listesi) + yardımcı ölçüler
  katmanlar/kemer.png, katmanlar/kilit.png : renk maskesiyle ayrılmış katmanlar
"""
import json, math, os, sys
import numpy as np
from PIL import Image
import contourpy

KOK = os.path.dirname(os.path.abspath(__file__))
SIMGE = os.path.join(KOK, '..', 'kimlik', 'opus-fortis-simge-renkli.png')

im = np.array(Image.open(SIMGE).convert('RGBA')).astype(np.float64)
H, W = im.shape[:2]
a = im[..., 3] / 255.0
# kilit taşı payı: kırmızı kanal Kahve(138) -> Krem(237) arasında doğrusal
k = np.clip((im[..., 0] - 138.0) / (237.0 - 138.0), 0, 1)
k[a < 0.02] = 0
kemer_m = a * (1 - k)
kilit_m = a * k

# --- katmanlar (renk maskesi; logo yeniden çizilmez) ---
def katman(maske, renk):
    out = np.zeros((H, W, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = renk
    out[..., 3] = np.clip(np.round(maske * 255), 0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')
katman(kemer_m, (0x8A, 0x6B, 0x3C)).save(os.path.join(KOK, 'katmanlar', 'kemer.png'), optimize=True)
katman(kilit_m, (0xED, 0xE6, 0xD8)).save(os.path.join(KOK, 'katmanlar', 'kilit.png'), optimize=True)

# --- konturlar (marching squares, 0.5 seviyesi) ---
def konturlar(m):
    gen = contourpy.contour_generator(z=np.pad(m, 1), line_type='Separate')
    ls = gen.lines(0.5)
    return [np.array(l) - 0.5 for l in ls if len(l) > 50]  # (x, y)

def rdp(p, eps):
    if len(p) < 3:
        return p
    a_, b_ = p[0], p[-1]
    d = b_ - a_
    n = np.hypot(*d)
    if n == 0:
        dist = np.hypot(*(p - a_).T)
    else:
        dist = np.abs(d[0] * (p[:, 1] - a_[1]) - d[1] * (p[:, 0] - a_[0])) / n
    i = int(np.argmax(dist))
    if dist[i] > eps:
        return np.vstack([rdp(p[:i + 1], eps)[:-1], rdp(p[i:], eps)])
    return np.vstack([a_, b_])

kemer_k = konturlar(kemer_m)
kilit_k = konturlar(kilit_m)
print('kemer kontur sayisi', len(kemer_k), [len(c) for c in kemer_k])
print('kilit kontur sayisi', len(kilit_k), [len(c) for c in kilit_k])

ys, xs = np.nonzero(a > 0.5)
bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
cx = (bx0 + bx1) / 2.0
print('bbox', bx0, bx1, by0, by1, 'cx', cx)

# sol yarı: ortalama x'i cx'ten küçük olan kontur
sol = [c for c in kemer_k if c[:, 0].mean() < cx][0]
if sol[0].tolist() == sol[-1].tolist():
    sol = sol[:-1]

def yol_bol(loop, S, J):
    """Kapalı döngüyü S'den J'ye iki yola böler (ileri / geri)."""
    i = int(np.argmin(np.hypot(*(loop - S).T)))
    j = int(np.argmin(np.hypot(*(loop - J).T)))
    n = len(loop)
    ileri = [loop[(i + t) % n] for t in range(((j - i) % n) + 1)]
    geri = [loop[(i - t) % n] for t in range(((i - j) % n) + 1)]
    ileri, geri = np.array(ileri), np.array(geri)
    ileri[0] = geri[0] = S; ileri[-1] = geri[-1] = J
    return ileri, geri

# sol ayak alt kenarının ortası
taban_y = sol[:, 1].max()
ayak = sol[np.abs(sol[:, 1] - taban_y) < 1.0]
S_sol = np.array([(ayak[:, 0].min() + ayak[:, 0].max()) / 2, taban_y])
kil = kilit_k[0]
if kil[0].tolist() == kil[-1].tolist():
    kil = kil[:-1]


def cember(p):
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    b = (p ** 2).sum(1)
    xc, yc, c = np.linalg.lstsq(A, b, rcond=None)[0]
    return xc, yc, np.sqrt(c + xc ** 2 + yc ** 2)

_r = np.hypot(sol[:, 0] - cx, sol[:, 1] - 634)
xc, yc, R_DIS = cember(sol[(_r > 330) & (sol[:, 1] < 600) & (sol[:, 0] < 500)])
xi, yi, R_IC = cember(sol[(_r < 260) & (sol[:, 1] < 600) & (sol[:, 1] > 450)])
M = np.array([cx, (yc + yi) / 2])          # ortak yay merkezi (üzengi çizgisi)
print('dis', xc, yc, R_DIS, 'ic', xi, yi, R_IC)

# derz: kilit taşı ile sol kemer arasındaki kenar (sol konturun kilide değen noktaları)
yak = np.array([p for p in sol if np.min(np.hypot(*(kil - p).T)) < 1.5])
J_sol = yak[np.argsort(yak[:, 1])][len(yak) // 2]
u = (J_sol - M) / np.hypot(*(J_sol - M))
O_sol = M + u * R_DIS                     # dış yay ile derzin kesişimi
I_sol = M + u * R_IC                      # iç yay ile derzin kesişimi
TETA_J = math.atan2(M[1] - J_sol[1], M[0] - J_sol[0])   # derz açısı (yataydan)
print('J', J_sol, 'O', O_sol, 'I', I_sol, 'aci', math.degrees(TETA_J))


def yol_bol(loop, S, J):
    """Kapalı döngüyü S'den J'ye iki yola böler (ileri / geri)."""
    i = int(np.argmin(np.hypot(*(loop - S).T)))
    j = int(np.argmin(np.hypot(*(loop - J).T)))
    n = len(loop)
    ileri = np.array([loop[(i + t) % n] for t in range(((j - i) % n) + 1)])
    geri = np.array([loop[(i - t) % n] for t in range(((i - j) % n) + 1)])
    ileri[0] = geri[0] = S; ileri[-1] = geri[-1] = J
    return ileri, geri


d1, d2 = yol_bol(sol, S_sol, J_sol)
dis, ic = (d1, d2) if d1[:, 0].min() < d2[:, 0].min() else (d2, d1)

# --- ortak "yapım cephesi" parametresi g (0..1) ---
# evreler: ayak tabanı -> bacak (aynı yükseklik) -> yay (aynı açı: radyal derz gibi) -> derz
X_DIS, X_IC = sol[:, 0].min(), cx - R_IC
L_AYAK = (S_sol[0] - X_DIS + X_IC - S_sol[0]) / 2
L_BACAK = taban_y - M[1]
L_YAY = (R_DIS + R_IC) / 2 * (math.pi - TETA_J)
L_DERZ = np.hypot(*(O_sol - J_sol))
AG = np.array([L_AYAK, L_BACAK, L_YAY, L_DERZ]); AG = AG / AG.sum()
OF = np.concatenate([[0], np.cumsum(AG)])
print('evre agirliklari', AG.round(3))


SINIR = {}


def g_hesapla(p, kose_x, R, U, ad):
    """Kalem yolundaki her noktaya evre parametresini atar."""
    i1 = int(np.argmin(np.hypot(p[:, 0] - kose_x, p[:, 1] - taban_y)))
    i2 = int(np.argmin(np.hypot(p[:, 0] - kose_x, p[:, 1] - M[1])))
    i3 = int(np.argmin(np.hypot(*(p - U).T)))
    SINIR[ad] = (i1, i2, i3)
    g = np.zeros(len(p))
    for k, (x, y) in enumerate(p):
        if k <= i1:
            yerel, e = abs(x - S_sol[0]) / abs(kose_x - S_sol[0]), 0
        elif k <= i2:
            yerel, e = (taban_y - y) / L_BACAK, 1
        elif k <= i3:
            ac = math.atan2(M[1] - y, M[0] - x)
            yerel, e = ac / (math.pi - TETA_J) if ac >= 0 else 0, 2
        else:
            yerel, e = 1 - np.hypot(*(p[k] - J_sol)) / L_DERZ, 3
        g[k] = OF[e] + AG[e] * min(max(yerel, 0), 1)
    g = np.maximum.accumulate(g)
    g[0], g[-1] = 0, 1
    return g


g_dis = g_hesapla(dis, X_DIS, R_DIS, O_sol, 'dis')
g_ic = g_hesapla(ic, X_IC, R_IC, I_sol, 'ic')

# kilit taşı: dış derz ucundan tepeye (üst kalem), iç derz ucundan alt ortaya (alt kalem)
T = np.array([cx, kil[:, 1].min()])
alt = kil[np.abs(kil[:, 0] - cx) < 2]
B = np.array([cx, alt[:, 1].max()])


def kisa_yol(loop, a, b):
    y1, y2 = yol_bol(loop, a, b)
    return y1 if kumul(y1)[-1] < kumul(y2)[-1] else y2


def kumul(p):
    return np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])


k_ust = kisa_yol(kil, O_sol, T)
k_alt = kisa_yol(kil, I_sol, B)
g_kust = kumul(k_ust) / kumul(k_ust)[-1]
g_kalt = kumul(k_alt) / kumul(k_alt)[-1]


def ayna(p):
    q = p.copy(); q[:, 0] = 2 * cx - q[:, 0]; return q


def rdp_i(p, eps, i0=0):
    """RDP; korunan noktaların indislerini döndürür."""
    if len(p) < 3:
        return list(range(i0, i0 + len(p)))
    a_, b_ = p[0], p[-1]
    d = b_ - a_
    n = np.hypot(*d)
    dist = np.hypot(*(p - a_).T) if n == 0 else np.abs(d[0] * (p[:, 1] - a_[1]) - d[1] * (p[:, 0] - a_[0])) / n
    k = int(np.argmax(dist))
    if dist[k] > eps:
        return rdp_i(p[:k + 1], eps, i0)[:-1] + rdp_i(p[k:], eps, i0 + k)
    return [i0, i0 + len(p) - 1]


EPS = 0.2
def paket(p, g=None, sinirlar=()):
    """RDP ile sadeleştirir; evre sınırlarındaki noktalar her zaman korunur."""
    p = np.asarray(p)
    kes = sorted(set([0, len(p) - 1] + [int(i) for i in sinirlar]))
    idx = []
    for a_, b_ in zip(kes[:-1], kes[1:]):
        idx += rdp_i(p[a_:b_ + 1], EPS, a_)[:-1]
    idx.append(len(p) - 1)
    out = {'p': [[round(float(p[i][0]), 2), round(float(p[i][1]), 2)] for i in idx]}
    if g is not None:
        out['g'] = [round(float(g[i]), 5) for i in idx]
    return out


kalemler = {
    'kemer_sol_dis': paket(dis, g_dis, SINIR['dis']), 'kemer_sol_ic': paket(ic, g_ic, SINIR['ic']),
    'kemer_sag_dis': paket(ayna(dis), g_dis, SINIR['dis']), 'kemer_sag_ic': paket(ayna(ic), g_ic, SINIR['ic']),
    'kilit_sol_ust': paket(k_ust, g_kust), 'kilit_sag_ust': paket(ayna(k_ust), g_kust),
    'kilit_sol_alt': paket(k_alt, g_kalt), 'kilit_sag_alt': paket(ayna(k_alt), g_kalt),
}
for ad, v in kalemler.items():
    print(ad, len(v['p']), 'nokta', v['p'][0], '->', v['p'][-1])

hayalet = {
    'kemer_sol': paket(np.vstack([sol, sol[:1]]))['p'],
    'kemer_sag': paket(ayna(np.vstack([sol, sol[:1]])))['p'],
    'kilit': paket(np.vstack([kil, kil[:1]]))['p'],
}
olcu = {'png': [W, H], 'bbox': [int(bx0), int(by0), int(bx1), int(by1)], 'cx': float(cx),
        'merkez': [round(float(M[0]), 2), round(float(M[1]), 2)], 'uzengi_y': round(float(M[1]), 2),
        'taban_y': round(float(taban_y), 2), 'dis_r': round(float(R_DIS), 2), 'ic_r': round(float(R_IC), 2),
        'derz_aci_derece': round(math.degrees(TETA_J), 2), 'evre_agirlik': [round(float(v), 4) for v in AG]}
print(olcu)
json.dump({'kalemler': kalemler, 'hayalet': hayalet, 'olcu': olcu},
          open(os.path.join(KOK, 'kontur.json'), 'w'), separators=(',', ':'))
print('kontur.json', os.path.getsize(os.path.join(KOK, 'kontur.json')), 'bayt')
