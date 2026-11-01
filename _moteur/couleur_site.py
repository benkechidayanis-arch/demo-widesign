"""Couleur d'accent réellement utilisée par un site (titres, boutons, liens, fonds colorés), pondérée par la surface visible.
Usage : python3 couleur_site.py https://www.site.fr [logo.png]
Affiche un JSON : {"acc": "#E1001A", "acc_ink": "#FFFFFF", "rgb": "225,0,26", "acc2", "accd", "rgbd", "acc_ring", "classement": [...]}.
acc_ink = couleur du texte posé sur l'accent (blanc ou anthracite selon le contraste).
Si le site n'a aucune couleur saturée, essaie le logo (palette.py), sinon null."""
import os, sys, json, colorsys, subprocess
from playwright.sync_api import sync_playwright

url = sys.argv[1]
logo = sys.argv[2] if len(sys.argv) > 2 else None

JS = r"""() => {
  const out = {};
  const add = (c, w, kind) => {
    if (!c) return; const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return;
    const p = m[1].split(',').map(x => parseFloat(x)); if (p.length > 3 && p[3] < .6) return;
    const k = p.slice(0,3).map(Math.round).join(',');
    out[k] = out[k] || {w:0, kinds:{}}; out[k].w += w; out[k].kinds[kind] = (out[k].kinds[kind]||0) + w;
  };
  const H = innerHeight * 6;
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height || r.top > H) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity < .3) continue;
    const tag = el.tagName; const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (own) {
      const fs = parseFloat(cs.fontSize) || 14; const len = el.textContent.trim().length;
      let w = fs * fs * Math.min(len, 60) / 40; let kind = 'texte';
      if (/^H[1-4]$/.test(tag) || fs >= 24) { w *= 3; kind = 'titre'; }
      if (tag === 'A' || el.closest('a,button')) { w *= 1.6; kind = kind === 'titre' ? 'titre' : 'lien'; }
      add(cs.color, w, kind);
    }
    if (tag !== 'IMG' && tag !== 'VIDEO' && tag !== 'svg') {
      const area = Math.min(r.width * r.height, innerWidth * 400);
      const isBtn = tag === 'BUTTON' || (tag === 'A' && cs.backgroundColor !== 'rgba(0, 0, 0, 0)');
      add(cs.backgroundColor, area / (isBtn ? 40 : 400), isBtn ? 'bouton' : 'fond');
      if (parseFloat(cs.borderTopWidth) >= 2) add(cs.borderTopColor, r.width * 2 / 50, 'bordure');
    }
  }
  return out;
}"""

def sat_info(k):
    r, g, b = [int(x) / 255 for x in k.split(',')]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, l, s

def lum(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = rgb
    return .2126 * ch(r) + .7152 * ch(g) + .0722 * ch(b)

def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + .05) / (lb + .05)

proxy = {'server': os.environ['HTTPS_PROXY']} if os.environ.get('HTTPS_PROXY') else None
with sync_playwright() as p:
    b = p.chromium.launch(proxy=proxy)
    res = {}
    for vw, vh in ((1440, 900), (390, 844)):
        pg = b.new_page(viewport={'width': vw, 'height': vh})
        try:
            pg.goto(url, wait_until='networkidle', timeout=45000)
        except Exception:
            pass
        pg.wait_for_timeout(2000)
        for k, v in pg.evaluate(JS).items():
            res.setdefault(k, {'w': 0, 'kinds': {}})
            res[k]['w'] += v['w']
            for kk, vv in v['kinds'].items():
                res[k]['kinds'][kk] = res[k]['kinds'].get(kk, 0) + vv
        pg.close()
    b.close()

cand = []
for k, v in res.items():
    h, l, s = sat_info(k)
    if s < .38 or l < .16 or l > .86:
        continue  # gris, noirs, blancs, pastels trop clairs
    score = v['w'] * (0.5 + s)
    cand.append((score, k, v['kinds']))
cand.sort(reverse=True)

if not cand:
    if logo:
        out = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'palette.py'), logo], capture_output=True, text=True).stdout.strip()
        print(out or 'null')
    else:
        print('null')
    sys.exit(0)

top = cand[0][1]
rgb = tuple(int(x) for x in top.split(','))
white, ink = (255, 255, 255), (30, 31, 29)
acc_ink = '#FFFFFF' if contrast(rgb, white) >= 3.6 else '#1E1F1D'
h, l, sa = colorsys.rgb_to_hls(*[c / 255 for c in rgb])
def hx(h, l, s):
    c = tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, l, s)); return '#%02X%02X%02X' % c, '%d,%d,%d' % c
acc2, _ = hx(h, min(.72, l + .18), min(1, sa + .05))        # version claire : petits textes et icônes sur fond sombre
accd, rgbd = hx(h, max(.16, l - .12), sa)                    # version foncée : survol
_, ring = hx(h, max(.12, l * .5), sa)                        # bordure translucide des boutons
print(json.dumps({
    'acc': '#%02X%02X%02X' % rgb, 'acc_ink': acc_ink, 'rgb': top, 'acc2': acc2, 'accd': accd, 'rgbd': rgbd,
    'acc_ring': 'rgba(%s,.45)' % ring,
    'classement': [{'couleur': '#%02X%02X%02X' % tuple(int(x) for x in k.split(',')), 'poids': round(sc), 'usages': {a: round(b) for a, b in kd.items()}} for sc, k, kd in cand[:6]]
}, ensure_ascii=False, indent=1))
