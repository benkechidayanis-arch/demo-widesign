"""Carte stylisée : vrai contour de la ville (IGN ADMIN EXPRESS), intégrée sur fond sombre.
Usage : python3 carte_ville.py communes.geojson CODE_INSEE SIREN_EPCI sortie.svg
Le SVG utilise currentColor pour l'accent (couleur héritée de la page)."""
import json, math, sys

src, insee, epci, out = sys.argv[1:5]
d = json.load(open(src))
ville = next(f for f in d['features'] if f['properties']['code_insee'] == insee)

def pts(g):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    return [p[0] for p in polys]

xs = [x for r in pts(ville['geometry']) for x, y in r]
ys = [y for r in pts(ville['geometry']) for x, y in r]
LON0, LAT0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
K = math.cos(math.radians(LAT0))
W = H = 900
# la ville occupe environ 46 % de la largeur, le reste montre le voisinage
span = max((max(xs) - min(xs)) * K, max(ys) - min(ys))
S = W * 0.46 / span

def P(lon, lat):
    return (W / 2 + (lon - LON0) * K * S, H / 2 - (lat - LAT0) * S)

def dp(p, tol):
    if len(p) < 3:
        return p
    (ax, ay), (bx, by) = p[0], p[-1]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    dm, ix = 0, 0
    for i in range(1, len(p) - 1):
        px, py = p[i]
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        dd = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
        if dd > dm:
            dm, ix = dd, i
    if dm > tol * tol:
        return dp(p[:ix + 1], tol)[:-1] + dp(p[ix:], tol)
    return [p[0], p[-1]]

def chemin(g, tol=0.8, marge=80):
    o = []
    for ring in pts(g):
        r = [P(x, y) for x, y in ring]
        if all(x < -marge or x > W + marge or y < -marge or y > H + marge for x, y in r):
            continue
        r = dp(r, tol)
        if len(r) >= 3:
            o.append('M' + 'L'.join('%.1f %.1f' % q for q in r) + 'Z')
    return ''.join(o)

autres, agglo = [], []
for f in d['features']:
    p = f['properties']
    if p['code_insee'] == insee:
        continue
    c = chemin(f['geometry'])
    if not c:
        continue
    (agglo if epci in (p.get('codes_siren_des_epci') or '') else autres).append(c)

v = chemin(ville['geometry'], 0.5)
cx, cy = P(4.3872, 45.4397) if insee == '42218' else (W / 2, H / 2)
svg = f'''<svg class="carte" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Contour de la commune">
<defs>
<radialGradient id="cf" cx="50%" cy="50%" r="50%"><stop offset="55%" stop-color="#fff"/><stop offset="100%" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="cm"><rect width="{W}" height="{H}" fill="url(#cf)"/></mask>
<filter id="cg" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<g mask="url(#cm)" fill="none" stroke-linejoin="round">
<path d="{''.join(autres)}" stroke="#fff" stroke-opacity=".07" stroke-width="1"/>
<path d="{''.join(agglo)}" stroke="#fff" stroke-opacity=".2" stroke-width="1.1"/>
</g>
<path d="{v}" fill="currentColor" fill-opacity=".35" filter="url(#cg)"/>
<path d="{v}" fill="currentColor" fill-opacity=".14"/>
<path class="trace" pathLength="1" d="{v}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="22" fill="currentColor" fill-opacity=".18" class="pouls"/>
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="6" fill="#fff"/>
</svg>'''
open(out, 'w').write(svg)
print(len(svg))
