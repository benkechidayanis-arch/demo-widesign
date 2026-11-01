"""Récupère les vraies photos du site d'un prospect pour sa démo.
Usage : python3 photos_site.py <url du site> <dossier de sortie> [nombre max de pages, défaut 14]
Parcourt l'accueil puis les pages internes les plus utiles (réalisations, chantiers, galerie, entreprise, services...),
rend chaque page avec Chromium (images chargées en différé comprises), relève les images des balises img
(plus grande version du srcset), des fonds CSS et de og:image, télécharge celles d'au moins 700 px de large,
écarte les doublons (empreinte visuelle) et les logos ou icônes.
Écrit dans le dossier : p01.jpg, p02.jpg... (JPEG de 1600 px au plus), inventaire.json
(fichier, source, page, largeur, hauteur, alt, texte autour) et planche-1.jpg, planche-2.jpg...
(vignettes numérotées, 20 par planche) à regarder avec Read pour choisir et placer chaque photo."""
import io, json, os, re, sys, hashlib, urllib.parse
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

site, out = sys.argv[1], sys.argv[2]
maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 14
if site.startswith('http://'):
    site = 'https://' + site[7:]
os.makedirs(out, exist_ok=True)
host = urllib.parse.urlparse(site).netloc.replace('www.', '')
UTILE = re.compile(r'realis|r%C3%A9alis|chantier|galer|photo|projet|reference|r%C3%A9f|entreprise|societe|soci%C3%A9t|equipe|%C3%A9quipe|qui-sommes|histoire|about|service|prestation|metier|activit|solution|expertise|moyens|savoir', re.I)
EXCLU = re.compile(r'mention|legal|cgv|cgu|confidential|cookie|privacy|plan-du-site|sitemap|login|panier|cart|wp-admin|\.pdf$|\.jpg$|\.png$|tel:|mailto:', re.I)

JS = r"""() => {
  const out = [];
  const best = (img) => { let u = img.currentSrc || img.src; let w = img.naturalWidth || 0;
    const ss = img.getAttribute('srcset') || img.getAttribute('data-srcset') || '';
    ss.split(',').forEach(p => { const m = p.trim().match(/^(\S+)\s+(\d+)w$/); if (m && +m[2] > w) { w = +m[2]; u = m[1]; } });
    const lz = img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || img.getAttribute('data-original');
    if (lz && (!u || u.startsWith('data:'))) u = lz;
    return u; };
  const ctx = (el) => { const s = el.closest('section,article,figure,li,div'); return s ? s.innerText.replace(/\s+/g, ' ').trim().slice(0, 160) : ''; };
  document.querySelectorAll('img').forEach(img => { const r = img.getBoundingClientRect();
    out.push({u: best(img), alt: img.alt || '', ctx: ctx(img), inHeader: !!img.closest('header,nav,.logo,[class*=logo]'), dw: r.width}); });
  document.querySelectorAll('*').forEach(el => { const b = getComputedStyle(el).backgroundImage;
    if (b && b.startsWith('url(')) { const m = b.match(/url\(["']?([^"')]+)/); if (m) out.push({u: m[1], alt: '', ctx: ctx(el), inHeader: !!el.closest('header,nav'), dw: el.getBoundingClientRect().width}); } });
  const og = document.querySelector('meta[property="og:image"]'); if (og) out.push({u: og.content, alt: 'og:image', ctx: '', inHeader: false, dw: 0});
  const links = [...document.querySelectorAll('a[href]')].map(a => ({h: a.href, t: (a.innerText || '').trim().slice(0, 60)}));
  return {imgs: out, links};
}"""

def dhash(im):
    g = im.convert('L').resize((9, 8))
    px = list(g.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])

proxy = {'server': os.environ['HTTPS_PROXY']} if os.environ.get('HTTPS_PROXY') else None
vus, cand, pages, faites = set(), [], [site], []
with sync_playwright() as p:
    b = p.chromium.launch(proxy=proxy)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, locale='fr-FR', ignore_https_errors=True)
    pg = ctx.new_page()
    while pages and len(faites) < maxp:
        url = pages.pop(0)
        if url in faites:
            continue
        faites.append(url)
        try:
            pg.goto(url, wait_until='networkidle', timeout=35000)
        except Exception:
            try:
                pg.wait_for_timeout(1500)
            except Exception:
                continue
        try:
            h = pg.evaluate('document.documentElement.scrollHeight')
            for y in range(0, min(h, 9000), 700):
                pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(150)
            pg.wait_for_timeout(800)
            r = pg.evaluate(JS)
        except Exception:
            continue
        for im in r['imgs']:
            u = (im['u'] or '').strip()
            if not u or u.startswith('data:') or re.search(r'\.svg(\?|$)|\.gif(\?|$)|logo|icon|favicon|sprite|picto', u, re.I):
                continue
            u = urllib.parse.urljoin(url, u)
            if u not in vus:
                vus.add(u); cand.append(dict(im, u=u, page=url))
        if len(faites) == 1 or len(faites) < maxp:
            liens = []
            for l in r['links']:
                h2 = l['h'].split('#')[0]
                if host in urllib.parse.urlparse(h2).netloc and not EXCLU.search(h2) and h2 not in faites and h2 not in pages:
                    liens.append(h2)
            liens.sort(key=lambda x: 0 if UTILE.search(x) else 1)
            pages += liens[:40]
    # téléchargement par le navigateur (mêmes en-têtes et cookies que la page)
    gardees, empreintes = [], []
    for c in cand:
        try:
            resp = ctx.request.get(c['u'], timeout=20000)
            if not resp.ok:
                continue
            im = Image.open(io.BytesIO(resp.body()))
            im.load()
        except Exception:
            continue
        w, h = im.size
        if w < 700 or h < 380 or w / h > 4 or h / w > 2.2:
            continue
        im = im.convert('RGB')
        d = dhash(im)
        if any(bin(d ^ e).count('1') < 8 for e in empreintes):
            continue
        empreintes.append(d)
        im.thumbnail((1600, 1600))
        n = len(gardees) + 1
        f = f'p{n:02d}.jpg'
        im.save(os.path.join(out, f), quality=84)
        gardees.append({'fichier': f, 'source': c['u'], 'page': c['page'], 'largeur': w, 'hauteur': h, 'alt': c['alt'], 'texte_autour': c['ctx']})
    b.close()

json.dump({'site': site, 'pages_lues': faites, 'photos': gardees}, open(os.path.join(out, 'inventaire.json'), 'w'), ensure_ascii=False, indent=1)
# planches de vignettes numérotées
try:
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
except Exception:
    f = ImageFont.load_default()
for k in range(0, len(gardees), 20):
    lot = gardees[k:k + 20]
    pl = Image.new('RGB', (5 * 300, ((len(lot) + 4) // 5) * 220), (30, 30, 30))
    d = ImageDraw.Draw(pl)
    for i, g in enumerate(lot):
        im = Image.open(os.path.join(out, g['fichier']))
        im.thumbnail((290, 200))
        x, y = (i % 5) * 300 + 5, (i // 5) * 220 + 5
        pl.paste(im, (x, y))
        d.rectangle((x, y, x + 64, y + 30), fill=(0, 0, 0))
        d.text((x + 6, y + 3), g['fichier'][1:3], fill=(255, 255, 0), font=f)
    pl.save(os.path.join(out, f'planche-{k // 20 + 1}.jpg'), quality=80)
print(len(faites), 'pages lues,', len(cand), 'images vues,', len(gardees), 'photos gardées dans', out)
