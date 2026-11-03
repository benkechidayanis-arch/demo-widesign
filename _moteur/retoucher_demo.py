"""Retouche d'une démo déjà en ligne, et copie d'aperçu pour l'application.

  python3 retoucher_demo.py source <dossier> <sortie> [--fin AAAA-MM-JJ]
      Récupère https://demo.widesign.fr/<dossier>/, la déchiffre, retire les ajouts de proteger.py
      et remet les images en img/ : <sortie>/source.html + <sortie>/img/. Applique les retouches
      du modèle (carte resserrée). Ensuite : proteger.py <sortie>/source.html <sortie>/en-ligne demo.widesign.fr <fin>
      puis publier_cloudflare.py --demo <dossier>=<sortie>/en-ligne:<fin>.
      --fin : nouvelle date de fin (prolongation) ; met à jour la date du pied de page et le contrôle d'expiration de la page.

  python3 retoucher_demo.py apercu <source.html> <sortie> [vignette.jpg]
      Copie d'aperçu pour l'application (dossier data/apercus/<dossier>/ de l'artefact) :
      <sortie>/index.html + <sortie>/img/ (seulement les images utilisées) + <sortie>/v.jpg (vignette 480 px).
      Les avis Google n'y chargent pas (règles de l'artefact) : la section se retire d'elle-même.
"""
import contact_widesign, base64, hashlib, io, os, re, shutil, sys, urllib.request
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HOTE = 'demo.widesign.fr'

CARTE_CSS = ('.mapc .mapv{aspect-ratio:4/3;overflow:hidden}'
             '.mapc .mapz{position:absolute;left:-15%;width:130%;aspect-ratio:1/1;top:50%;transform:translateY(-50%)}'
             '.mapc .mapz .carte{position:absolute;inset:0}'
             '@media(min-width:900px){.mapc .mapv{aspect-ratio:16/11}.mapc .mapz{left:-10%;width:120%}}')
CARTE_JS = ('<script>(function(){var v=document.querySelector(".mapc .mapv"),l=v&&v.querySelector(".lab");if(!l)return;'
            'var L0=parseFloat(l.style.left),T0=parseFloat(l.style.top);function f(){l.style.left=L0+"%";l.style.top=T0+"%";l.style.marginLeft="";'
            'var a=v.getBoundingClientRect(),b=l.getBoundingClientRect(),w=b.width;if(b.right<=a.right-12)return;'
            'l.style.left=(L0-8)+"%";l.style.marginLeft=(-w)+"px";var c=l.getBoundingClientRect();if(c.left>=a.left+12)return;'
            'l.style.left=(L0-4)+"%";l.style.top=(T0+10)+"%";l.style.marginLeft=(-w/2)+"px";c=l.getBoundingClientRect();'
            'if(c.right>a.right-12)l.style.marginLeft=(-w/2-(c.right-a.right+12))+"px";else if(c.left<a.left+12)l.style.marginLeft=(-w/2+(a.left+12-c.left))+"px"}'
            'f();addEventListener("resize",f)})();</script>')


POLICE = 'Archivo:wght@400;500;600;700;800'


def police(h):
    """Police du modèle : Archivo (remplace Bricolage Grotesque)."""
    h = re.sub(r'family=Bricolage\+Grotesque[^"&]*', 'family=' + POLICE, h)
    return h.replace('"Bricolage Grotesque"', '"Archivo"').replace("'Bricolage Grotesque'", "'Archivo'")


HERO_CSS = ('<style id="v9-hero">@media(max-width:1023px){.hero .bg:after{background:linear-gradient(180deg,rgba(14,15,13,.9) 0%,rgba(14,15,13,.8) 38%,rgba(14,15,13,.66) 64%,rgba(14,15,13,.3) 82%,rgba(14,15,13,.6) 100%)}}'
            '.hero .lead{color:rgba(255,255,255,.94);text-shadow:0 1px 12px rgba(0,0,0,.6)}</style>')


BUREAU_CSS = '<style id="v9-bureau">@media(min-width:1024px){.h2[style*="max-width"]{max-width:18ch!important}.h2{line-height:.86}.stk{height:min(580px,70vh)}.stp .ph{aspect-ratio:4/3}.stp .tx{padding:22px 22px 24px}.stp h3{font-size:23px}}</style>'


AVIS_JS = [('var rv=(p.reviews||[]).filter(function(r){return r.rating>=4&&r.text&&r.text.length>=40}).slice(0,4);', 'var rv=(p.reviews||[]).filter(function(r){return r.rating>=4&&r.text&&r.text.length>=40}).sort(function(a,b){return a.text.length-b.text.length}).slice(0,4).sort(function(a,b){return b.text.length-a.text.length});\n  var tr=function(t,L){t=String(t).trim();if(t.length<=L+40)return esc(t);var s=t.slice(0,L),j=s.lastIndexOf(" ");if(j>L*.6)s=s.slice(0,j);return \'<span>\'+esc(s.replace(/[\\s,;:.!?-]+$/,""))+\'… </span><button class="plus" type="button" data-t="\'+esc(t)+\'">Lire la suite</button>\'};'), ("<q>'+esc(r.text)+'</q>", "<q>'+tr(r.text,i?170:260)+'</q>"), ('sec.style.display="";ul.querySelectorAll', 'ul.onclick=function(e){var b=e.target.closest&&e.target.closest(".plus");if(b)b.parentNode.textContent=b.getAttribute("data-t")};sec.style.display="";ul.querySelectorAll')]
AVIS_CSS = '<style id="v9-avis">.av .plus{background:none;border:0;padding:0;font:inherit;font-weight:600;color:var(--acc);text-decoration:underline;text-underline-offset:3px;cursor:pointer;white-space:nowrap}.av.one .plus{color:var(--acc-ink)}</style>'


def avis(h):
    """Avis Google : les plus courts d'abord, textes longs coupés avec « Lire la suite »."""
    if 'id="avs"' not in h or 'Lire la suite' in h:
        return h
    for a, b in AVIS_JS:
        if a not in h:
            return h
    for a, b in AVIS_JS:
        h = h.replace(a, b, 1)
    i = h.find('</head>')
    return h[:i] + AVIS_CSS + h[i:]


def retouches(h):
    """Retouches du modèle v9 appliquées aux démos déjà assemblées (sans effet si déjà présentes)."""
    h = police(h)
    nom = contact_widesign.nom_depuis_page(h)
    if not nom:
        sys.exit("ÉCHEC : nom de l'entreprise introuvable dans le pied de page")
    h = contact_widesign.inserer(h, nom)
    if 'class="hero"' in h and 'id="v9-hero"' not in h and 'rgba(14,15,13,.66) 64%' not in h:
        i = h.find('</head>')
        h = h[:i] + HERO_CSS + h[i:]
    if 'steps2' in h and 'id="v9-bureau"' not in h:
        i = h.find('</head>')
        h = h[:i] + BUREAU_CSS + h[i:]
    if 'class="mapz"' not in h:
        h, n = re.subn(r'(<svg class="carte".*?</svg>)\s*(<span class="lab"[^>]*>.*?</span>)',
                       r'<div class="mapz">\1\2</div>', h, count=1, flags=re.S)
        if n:
            i = h.find('</style>')
            h = h[:i] + CARTE_CSS + h[i:]
            h = h.replace('</body>', CARTE_JS + '</body>', 1)
    return avis(h)


MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


def changer_fin(h, fin):
    a, m, j = (int(x) for x in fin.split('-'))
    txt = f"{j}{'er' if j == 1 else ''} {MOIS[m - 1]} {a}"
    h, n1 = re.subn(r'new Date\("\d{4}-\d{2}-\d{2}T23:59:59"\)', f'new Date("{fin}T23:59:59")', h)
    h, n2 = re.subn(r"(visible jusqu'au )\d{1,2}(?:er)? [a-zéû]+ \d{4}", lambda m_: m_.group(1) + txt, h)
    if not n2:
        sys.exit("ÉCHEC : date du pied de page introuvable")
    return h


def lire(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()


def source(dossier, out, fin=None):
    base = f'https://{HOTE}/{dossier}/'
    s = lire(base).decode('utf-8')
    d = re.search(r'var d="([^"]+)"', s).group(1)
    m = re.search(r',v="([^"]+)",g="([^"]+)",f=(\d+)', s)
    cle = hashlib.sha256(HOTE.encode() + base64.b64decode(m.group(2))).digest()
    h = AESGCM(cle).decrypt(base64.b64decode(m.group(1)), base64.b64decode(d), None).decode('utf-8')
    # retire les ajouts de proteger.py (ils seront remis à la prochaine protection)
    h = re.sub(r'<style>html,body\{-webkit-user-select:none.*?</script>', '', h, count=1, flags=re.S)
    h = re.sub(r'<script>\(function\(\)\{try\{if\(/\[\?&\]moi.*?</script>', '', h, count=1, flags=re.S)
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)
    for p in sorted(set(re.findall(r'm/([0-9a-f]+\.(?:jpg|jpeg|png|svg|webp))', h))):
        open(os.path.join(out, 'img', p), 'wb').write(lire(base + 'm/' + p))
    h = re.sub(r'\bm/([0-9a-f]+\.(?:jpg|jpeg|png|svg|webp))', r'img/\1', h)
    h = retouches(h)
    if fin:
        h = changer_fin(h, fin)
    open(os.path.join(out, 'source.html'), 'w', encoding='utf-8').write(h)
    print('OK', dossier, len(h), 'octets', len(os.listdir(os.path.join(out, 'img'))), 'images')


def apercu(src, out, vignette=None):
    base = os.path.dirname(os.path.abspath(src))
    h = retouches(open(src, encoding='utf-8').read())
    # un seul fichier : les images sont intégrées (data URI), l'application garde ainsi peu de fichiers
    os.makedirs(out, exist_ok=True)
    types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'svg': 'image/svg+xml', 'webp': 'image/webp'}
    def integrer(m):
        p = os.path.join(base, m.group(0))
        if not os.path.exists(p):
            return m.group(0)
        return 'data:%s;base64,%s' % (types[m.group(1).lower()], base64.b64encode(open(p, 'rb').read()).decode())
    h = re.sub(r'img/[A-Za-z0-9_.-]+\.(jpg|jpeg|png|svg|webp)', integrer, h)
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(h)
    if vignette:
        from PIL import Image
        data = lire(vignette) if vignette.startswith('http') else open(vignette, 'rb').read()
        im = Image.open(io.BytesIO(data)).convert('RGB')
        im.thumbnail((480, 480))
        im.save(os.path.join(out, 'v.jpg'), quality=80, optimize=True)
    print('OK apercu', out)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['source'] and len(a) in (3, 5) and (len(a) == 3 or a[3] == '--fin'):
        source(a[1], a[2], a[4] if len(a) == 5 else None)
    elif a[:1] == ['apercu'] and len(a) in (3, 4):
        apercu(a[1], a[2], a[3] if len(a) == 4 else None)
    else:
        sys.exit(__doc__)
