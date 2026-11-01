"""Empreinte visuelle (dHash 64 bits) : deux images proches ont des empreintes à moins de 10 bits d'écart.
Usage : python3 empreinte.py image.jpg [image2.jpg]  -> empreinte, et l'écart si deux images"""
import sys
from PIL import Image
def dh(p):
    im = Image.open(p).convert('L').resize((9, 8), Image.LANCZOS)
    px = list(im.getdata())
    v = 0
    for y in range(8):
        for x in range(8):
            v = v << 1 | (px[y * 9 + x] > px[y * 9 + x + 1])
    return '%016x' % v
a = dh(sys.argv[1]); print(a)
if len(sys.argv) > 2:
    b = dh(sys.argv[2]); print(b, bin(int(a, 16) ^ int(b, 16)).count('1'))
