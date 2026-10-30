"""animasyon.sablon.html + kontur.json -> animasyon.html (tek dosya)."""
import os
KOK = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(KOK, 'animasyon.sablon.html'), encoding='utf-8').read()
k = open(os.path.join(KOK, 'kontur.json'), encoding='utf-8').read().strip()
open(os.path.join(KOK, 'animasyon.html'), 'w', encoding='utf-8').write(s.replace('__KONTUR__', k))
print('animasyon.html yazıldı')
