"""Recadre une photo (par exemple pour retirer d'une photo de groupe les personnes qui ne doivent pas apparaître).
Usage : python3 recadrer.py entree.jpg sortie.jpg gauche haut droite bas
Les quatre valeurs sont des fractions de 0 à 1 de la largeur et de la hauteur (ex. 0 0 0.55 1 = moitié gauche).
Refuse un résultat de moins de 700 px de large : dans ce cas la photo ne doit pas être utilisée."""
import sys
from PIL import Image
e, s, *b = sys.argv[1:7]
g, h, d, ba = map(float, b)
im = Image.open(e).convert('RGB'); W, H = im.size
box = (round(g * W), round(h * H), round(d * W), round(ba * H))
c = im.crop(box)
if c.width < 700 or c.height < 380:
    sys.exit(f'REFUS : recadrage trop petit ({c.width} x {c.height}), photo à écarter')
c.save(s, quality=88); print(s, c.size)
