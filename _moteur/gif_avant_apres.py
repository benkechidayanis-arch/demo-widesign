"""GIF avant/après pour le mail de prospection : deux téléphones côte à côte,
le site actuel du prospect à gauche, la démo Widesign à droite, qui défilent ensemble au rythme de lecture\n(arrêt de 1,8 s sur chaque écran, défilement d'environ 1 s).
Usage : python3 gif_avant_apres.py <url_site_actuel> <chemin_ou_url_demo> <sortie.gif> "<légende ou vide>" [couleur_accent]
Le premier plan du GIF montre les deux pages d'accueil (c'est ce que voit Outlook ordinateur).
Vise moins de 700 Ko sans perte visible (256 couleurs gardées, tramage fin, compression gifsicle) ; gifsicle est installé avec npm s'il manque."""
import os, subprocess, sys, shutil, tempfile, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from playwright.sync_api import sync_playwright

site, demo, sortie, legende = sys.argv[1:5]
if site.startswith('http://'):
    site = 'https://' + site[7:]   # le proxy refuse le http simple ; les sites des prospects répondent presque tous en https
accent = sys.argv[5] if len(sys.argv) > 5 else '#E8601F'
if not demo.startswith(('http://', 'https://', 'file://')):
    demo = 'file://' + os.path.abspath(demo)

W, H = 540, 540
S = 2                          # tout est dessiné en double taille puis réduit : bords nets, ombres propres
PH_W, PH_H = 214, 440          # écran affiché dans chaque téléphone (taille finale)
VIEW_W, VIEW_H = 390, 747      # fenêtre mobile capturée (même rapport que l'écran sous la barre d'état)
ARRETS = [0, 760, 1520]        # positions de défilement (3 écrans : le poids reste sous 900 Ko)
PAUSE, PAUSE_1 = 180, 240      # durée de chaque arrêt, en centièmes de seconde (le premier plan reste plus longtemps)
PAS, PAS_D = 8, 12             # défilement : 8 images de 12 centièmes, soit environ 1 s par écran
# Mode moments forts : si la démo marque ses sections avec data-gif, le GIF saute de moment en moment
# (5 arrêts au plus, transition rapide de 0,4 s, arrêt de 1,7 s) et le site actuel avance à la même proportion de sa hauteur.
M_PAS, M_PAS_D, M_PAUSE = 4, 13, 170
TMP = tempfile.mkdtemp(prefix='gifaa-')

def ease(t):
    return 4 * t * t * t if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def positions(arrets, h, pas=PAS, pas_d=PAS_D, pause=PAUSE):
    """Liste de (position de défilement, durée d'affichage en centièmes)."""
    arrets = [min(a, max(0, h - VIEW_H)) for a in arrets]
    out = []
    for i, a in enumerate(arrets):
        out.append((a, PAUSE_1 if i == 0 else (200 if i == len(arrets) - 1 and pause != PAUSE else pause)))
        if i < len(arrets) - 1:
            b = arrets[i + 1]
            out += [(round(a + (b - a) * ease(k / pas)), pas_d) for k in range(1, pas)]
    return out

UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 '
      '(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

def capturer(pw, url, dossier, ratios=None):
    """Capture les images du défilement. Renvoie (positions, ratios des moments forts ou None)."""
    os.makedirs(dossier, exist_ok=True)
    proxy = {'server': os.environ['HTTPS_PROXY']} if os.environ.get('HTTPS_PROXY') and url.startswith('http') else None
    b = pw.chromium.launch(proxy=proxy)
    ctx = b.new_context(viewport={'width': VIEW_W, 'height': VIEW_H}, device_scale_factor=1.5,
                        is_mobile=True, has_touch=True, user_agent=UA, locale='fr-FR')
    p = ctx.new_page()
    try:
        p.goto(url, wait_until='networkidle', timeout=45000)
    except Exception:
        pass
    p.wait_for_timeout(2500)
    # bandeaux cookies : on refuse ou on ferme, puis on force l'affichage des blocs animés
    p.evaluate("""()=>{const m=/^(tout refuser|refuser|continuer sans accepter|refuser et fermer|fermer|j'ai compris|ok)$/i;
      const b=[...document.querySelectorAll('button,a,[role=button]')].filter(x=>m.test((x.innerText||'').trim()));if(b[0])b[0].click();
      document.querySelectorAll('.rv').forEach(e=>e.classList.add('on'))}""")
    p.wait_for_timeout(800)
    h = p.evaluate('document.documentElement.scrollHeight')
    for y in range(0, min(h, 16000), 450):
        p.evaluate(f'scrollTo(0,{y})'); p.wait_for_timeout(120)
    p.evaluate('scrollTo(0,0)'); p.wait_for_timeout(700)
    moments = None
    if ratios is None:
        tops = p.evaluate("""()=>[...document.querySelectorAll('[data-gif]')].slice(0,4).map(e=>Math.round(e.getBoundingClientRect().top+scrollY))""")
        if tops:
            moments = [0] + [max(0, t - 70) for t in tops]
    else:
        moments = [0] + [round(r * max(0, h - VIEW_H)) for r in ratios]
    if moments:
        pos = positions(moments, h, M_PAS, M_PAS_D, M_PAUSE)
    else:
        pos = positions(ARRETS, h)
    for i, (y, _) in enumerate(pos):
        p.evaluate(f"window.scrollTo({{top:{y},behavior:'instant'}})")
        p.wait_for_timeout(50)
        p.screenshot(path=f'{dossier}/{i:03d}.png')
    b.close()
    rat = [min(1, m / max(1, h - VIEW_H)) for m in moments[1:]] if (moments and ratios is None) else None
    return pos, rat

def police(taille, gras=False):
    for f in (['/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', '/usr/share/fonts/opentype/inter/Inter-Bold.otf'] if gras else
              ['/usr/share/fonts/opentype/inter/Inter-Medium.otf', '/usr/share/fonts/opentype/inter/Inter-Regular.otf']) + \
             ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if gras else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, taille)
    return ImageFont.load_default()

def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def fond():
    im = Image.new('RGB', (W * S, H * S), (243, 240, 235))
    d = ImageDraw.Draw(im)
    f = police(15 * S, True)
    for cx, txt, col in ((W * 0.27, "Votre site aujourd'hui", (160, 150, 140)), (W * 0.73, 'Démo Widesign', hexrgb(accent))):
        tw = d.textlength(txt, font=f) / S
        x = cx - (tw + 16) / 2
        d.ellipse((x * S, 22 * S, (x + 9) * S, 31 * S), fill=col)
        d.text(((x + 16) * S, 18 * S), txt, fill=(28, 24, 20), font=f)
    if legende.strip():
        f2 = police(12 * S)
        tw = d.textlength(legende, font=f2)
        d.text(((W * S - tw) / 2, (H - 22) * S), legende, fill=(120, 112, 104), font=f2)
    return im

B = 6                           # épaisseur du bord du téléphone
BARRE = 30                      # hauteur de la barre d'état
FW, FH = PH_W + 2 * B, PH_H + 2 * B
R_EXT, R_INT = 34, 28

def rr(taille, rayon, fill, mode='L'):
    m = Image.new(mode, taille, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, taille[0] - 1, taille[1] - 1), rayon, fill=fill)
    return m

def cadre_telephone():
    """Téléphone vide en double taille : liseré métal, bord noir, îlot en haut."""
    c = Image.new('RGBA', (FW * S, FH * S), (0, 0, 0, 0))
    c.paste((70, 70, 74), (0, 0), rr((FW * S, FH * S), R_EXT * S, 255))
    e = int(1.2 * S)
    c.paste((12, 12, 14), (e, e), rr((FW * S - 2 * e, FH * S - 2 * e), R_EXT * S - e, 255))
    return c

def ombre():
    """Ombre en deux couches (diffuse + contact), sur une toile assez grande pour que le flou ne soit jamais coupé."""
    M = 60 * S
    t = (FW * S + 2 * M, FH * S + 2 * M)
    o = Image.new('L', t, 0)
    l1 = Image.new('L', t, 0)
    ImageDraw.Draw(l1).rounded_rectangle((M + 10 * S, M + 22 * S, M + (FW - 10) * S, M + (FH + 8) * S), R_EXT * S, fill=60)
    l1 = l1.filter(ImageFilter.GaussianBlur(20 * S))
    l2 = Image.new('L', t, 0)
    ImageDraw.Draw(l2).rounded_rectangle((M + 4 * S, M + 6 * S, M + (FW - 4) * S, M + (FH + 2) * S), R_EXT * S, fill=70)
    l2 = l2.filter(ImageFilter.GaussianBlur(5 * S))
    o = Image.fromarray(__import__('numpy').maximum(__import__('numpy').array(l1), __import__('numpy').array(l2)))
    return o, M

def composer(pos_a, pos_b):
    base = fond()
    om, M = ombre()
    cadre = cadre_telephone()
    masque = rr((PH_W * S, PH_H * S), R_INT * S, 255)
    y0 = 52
    xs = (int(W * 0.27 - FW / 2), int(W * 0.73 - FW / 2))
    for k in range(2):
        base.paste((38, 30, 24), (xs[k] * S - M, y0 * S - M), om)
        base.paste(cadre, (xs[k] * S, y0 * S), cadre)
    n = min(len(pos_a), len(pos_b))
    for i in range(n):
        im = base.copy()
        for k, dos in enumerate(('a', 'b')):
            cap = Image.open(f'{TMP}/{dos}/{i:03d}.png').convert('RGB').resize((PH_W * S, (PH_H - BARRE) * S), Image.LANCZOS)
            # barre d'état façon iPhone (couleur du haut de la page, îlot noir) : le site commence en dessous, rien n'est caché
            haut = cap.crop((0, 0, cap.width, 3 * S)).resize((1, 1), Image.BOX).getpixel((0, 0))
            ecran = Image.new('RGB', (PH_W * S, PH_H * S), haut)
            ecran.paste(cap, (0, BARRE * S))
            de = ImageDraw.Draw(ecran)
            de.rounded_rectangle(((PH_W / 2 - 30) * S, 7 * S, (PH_W / 2 + 30) * S, 24 * S), 8.5 * S, fill=(8, 8, 10))
            clair = sum(haut) / 3 < 140
            fh = police(9 * S, True)
            de.text((20 * S, 10 * S), '9:41', fill=(255, 255, 255) if clair else (20, 20, 22), font=fh)
            im.paste(ecran, ((xs[k] + B) * S, (y0 + B) * S), masque)
        im.resize((W, H), Image.LANCZOS).save(f'{TMP}/c{i:03d}.png')
    return [d for _, d in pos_a[:n]]

def encoder(durees):
    brut = f'{TMP}/brut.gif'
    with open(f'{TMP}/liste.txt', 'w') as f:
        for i, d in enumerate(durees):
            f.write(f"file 'c{i:03d}.png'\nduration {d / 100:.2f}\n")
        f.write(f"file 'c{len(durees) - 1:03d}.png'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{TMP}/liste.txt',
                    '-vf', 'split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
                    '-fps_mode', 'vfr', '-loop', '0', brut], check=True)
    trouver = lambda: shutil.which('gifsicle') or next(iter(glob.glob('/tmp/gs/node_modules/gifsicle/vendor/gifsicle')), None)
    gs = trouver()
    if not gs:
        os.makedirs('/tmp/gs', exist_ok=True)
        subprocess.run(['npm', 'i', 'gifsicle@5', '--silent'], cwd='/tmp/gs', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gs = trouver()
    if gs:
        for lossy, cols in ((40, 256), (60, 256), (80, 256), (100, 224)):
            subprocess.run([gs, '-O3', '--colors', str(cols), f'--lossy={lossy}', brut, '-o', sortie], check=True,
                           stderr=subprocess.DEVNULL)
            if os.path.getsize(sortie) < 700_000:
                break
    else:
        print('ATTENTION : gifsicle introuvable, GIF non compressé', file=sys.stderr)
        shutil.copy(brut, sortie)
    return os.path.getsize(sortie)

with sync_playwright() as pw:
    pb, rat = capturer(pw, demo, f'{TMP}/b')
    pa, _ = capturer(pw, site, f'{TMP}/a', rat)
durees = composer(pa, pb)
taille = encoder(durees)
n = len(durees)
Image.open(f'{TMP}/c000.png').convert('RGB').save(os.path.splitext(sortie)[0] + '-premiere.jpg', quality=82)
print(sortie, n, 'images', taille, 'octets')
shutil.rmtree(TMP, ignore_errors=True)
