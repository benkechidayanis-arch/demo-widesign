"""Couleur d'accent tirée du logo du client.
Usage : python3 palette.py logo.png  -> JSON {acc, acc2, accd, rgb, rgbd}
acc : couleur principale (boutons, bandeau), lisible avec du texte blanc
acc2 : version claire pour les accents sur fond sombre
accd : version foncée (survol, ombres)"""
import colorsys, json, sys
from collections import Counter
from PIL import Image

im = Image.open(sys.argv[1]).convert('RGBA')
im.thumbnail((400, 400))
c = Counter()
for r, g, b, a in im.getdata():
    if a < 200:
        continue
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s < 0.35 or l < 0.12 or l > 0.9:
        continue  # gris, noir, blanc : pas une couleur de marque
    c[(round(h * 36) % 36)] += 1
if not c:
    print(json.dumps(None)); sys.exit()
teinte = c.most_common(1)[0][0]
px = [(r, g, b) for r, g, b, a in im.getdata() if a >= 200]
sel = []
for r, g, b in px:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s >= 0.35 and 0.12 <= l <= 0.9 and round(h * 36) % 36 == teinte:
        sel.append((h, l, s))
h = sorted(x[0] for x in sel)[len(sel) // 2]
s = min(0.9, sorted(x[2] for x in sel)[len(sel) // 2])

def hexa(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#%02X%02X%02X' % (round(r * 255), round(g * 255), round(b * 255)), (round(r * 255), round(g * 255), round(b * 255))

def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

# acc : on fonce jusqu'à un contraste d'au moins 4,5 avec le blanc
l = 0.5
while l > 0.2:
    a, argb = hexa(h, l, s)
    if 1.05 / (lum(argb) + 0.05) >= 4.5:
        break
    l -= 0.01
acc2, _ = hexa(h, min(0.72, l + 0.2), min(1, s + 0.05))
accd, drgb = hexa(h, max(0.16, l - 0.12), s)
print(json.dumps({'acc': a, 'acc2': acc2, 'accd': accd, 'rgb': '%d,%d,%d' % argb, 'rgbd': '%d,%d,%d' % drgb}))
