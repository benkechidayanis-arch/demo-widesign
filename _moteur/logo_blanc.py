"""Passe un logo en blanc (toutes les zones visibles deviennent blanches, la transparence est gardée).
Un fond plein (blanc ou uni) est d'abord retiré.
Usage : python3 logo_blanc.py logo.png sortie.png"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGBA')
w, h = im.size
px = im.load()
coins = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
fond = None
if all(c[3] > 250 for c in coins):
    r = sum(c[0] for c in coins) // 4; g = sum(c[1] for c in coins) // 4; b = sum(c[2] for c in coins) // 4
    if all(abs(c[0] - r) + abs(c[1] - g) + abs(c[2] - b) < 30 for c in coins):
        fond = (r, g, b)
out = Image.new('RGBA', (w, h))
po = out.load()
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if fond:
            d = abs(r - fond[0]) + abs(g - fond[1]) + abs(b - fond[2])
            a = min(a, max(0, min(255, (d - 20) * 4)))
        po[x, y] = (255, 255, 255, a)
bb = out.getbbox()
if bb:
    out = out.crop(bb)
out.save(sys.argv[2])
print(out.size)
