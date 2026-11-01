"""GIF avant/après pour le mail de prospection : deux téléphones côte à côte,
le site actuel du prospect à gauche, la maquette Widesign à droite, qui défilent ensemble.
Usage : python3 gif_avant_apres.py <url_site_actuel> <chemin_ou_url_demo> <sortie.gif> "<légende ou vide>" [couleur_accent]
Le premier plan du GIF montre les deux pages d'accueil (c'est ce que voit Outlook ordinateur).
Vise moins de 900 Ko (256 couleurs : en dessous, les photos du site actuel se dégradent et le comparatif devient injuste) ; utilise ffmpeg et gifsicle s'ils sont présents."""
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
PH_W, PH_H = 214, 440          # écran affiché dans chaque téléphone
VIEW_W, VIEW_H = 390, 802      # fenêtre mobile capturée (même rapport que l'écran)
ARRETS = [0, 780, 1560, 2340]  # positions de défilement
TMP = tempfile.mkdtemp(prefix='gifaa-')

def ease(t):
    return 4 * t * t * t if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def positions(arrets, h):
    arrets = [min(a, max(0, h - VIEW_H)) for a in arrets]
    out = []
    for i, a in enumerate(arrets):
        out += [a] * 4
        if i < len(arrets) - 1:
            b = arrets[i + 1]
            out += [round(a + (b - a) * ease(k / 6)) for k in range(1, 7)]
    return out + [arrets[-1]] * 4

UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 '
      '(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

def capturer(pw, url, dossier):
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
    for y in range(0, min(h, 4200), 400):
        p.evaluate(f'scrollTo(0,{y})'); p.wait_for_timeout(120)
    p.evaluate('scrollTo(0,0)'); p.wait_for_timeout(700)
    pos = positions(ARRETS, h)
    for i, y in enumerate(pos):
        p.evaluate(f"window.scrollTo({{top:{y},behavior:'instant'}})")
        p.wait_for_timeout(50)
        p.screenshot(path=f'{dossier}/{i:03d}.png')
    b.close()
    return len(pos)

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
    im = Image.new('RGB', (W, H), (242, 239, 234))
    d = ImageDraw.Draw(im)
    f = police(15, True)
    for cx, txt, col in ((W * 0.27, "Votre site aujourd'hui", (170, 160, 150)), (W * 0.73, 'Démo Widesign', hexrgb(accent))):
        tw = d.textlength(txt, font=f)
        x = cx - (tw + 16) / 2
        d.ellipse((x, 22, x + 9, 31), fill=col)
        d.text((x + 16, 18), txt, fill=(28, 24, 20), font=f)
    if legende.strip():
        f2 = police(12)
        tw = d.textlength(legende, font=f2)
        d.text(((W - tw) / 2, H - 22), legende, fill=(120, 112, 104), font=f2)
    return im

def telephone(capture, sombre=True):
    ecran = capture.resize((PH_W, PH_H), Image.LANCZOS)
    cadre = Image.new('RGBA', (PH_W + 14, PH_H + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(cadre)
    d.rounded_rectangle((0, 0, PH_W + 13, PH_H + 13), 30, fill=(18, 16, 14) if sombre else (30, 28, 26))
    masque = Image.new('L', (PH_W, PH_H), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, PH_W - 1, PH_H - 1), 24, fill=255)
    cadre.paste(ecran, (7, 7), masque)
    return cadre

def composer(n_a, n_b):
    base = fond()
    # ombre douce sur une toile agrandie : sans marge, le flou est coupé net en rectangle sous le téléphone
    M = 30
    ombre = Image.new('L', (PH_W + 14 + 2 * M, PH_H + 14 + 2 * M), 0)
    ImageDraw.Draw(ombre).rounded_rectangle((M + 6, M, M + PH_W + 7, M + PH_H + 13), 30, fill=70)
    ombre = ombre.filter(ImageFilter.GaussianBlur(9))
    n = min(n_a, n_b)
    y0 = 50 if legende.strip() else 54
    xs = (int(W * 0.27 - (PH_W + 14) / 2), int(W * 0.73 - (PH_W + 14) / 2))
    for i in range(n):
        im = base.copy()
        for k, dos in enumerate(('a', 'b')):
            cap = Image.open(f'{TMP}/{dos}/{i:03d}.png').convert('RGB')
            im.paste((40, 34, 28), (xs[k] - M, y0 - M + 7), ombre)
            t = telephone(cap)
            im.paste(t, (xs[k], y0), t)
        im.save(f'{TMP}/c{i:03d}.png')
    return n

def encoder(n):
    brut = f'{TMP}/brut.gif'
    if shutil.which('ffmpeg'):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '9', '-i', f'{TMP}/c%03d.png',
                        '-vf', 'split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
                        '-loop', '0', brut], check=True)
    else:
        imgs = [Image.open(f'{TMP}/c{i:03d}.png').convert('P', palette=Image.ADAPTIVE, colors=256) for i in range(n)]
        imgs[0].save(brut, save_all=True, append_images=imgs[1:], duration=111, loop=0, optimize=True)
    gs = shutil.which('gifsicle') or next(iter(glob.glob('/tmp/gs/node_modules/gifsicle/vendor/gifsicle')), None)
    if gs:
        for lossy, cols in ((30, 256), (60, 256), (90, 220), (120, 180)):
            subprocess.run([gs, '-O3', f'--lossy={lossy}', '--colors', str(cols), brut, '-o', sortie], check=True)
            if os.path.getsize(sortie) < 900_000:
                break
    else:
        shutil.copy(brut, sortie)
    return os.path.getsize(sortie)

with sync_playwright() as pw:
    na = capturer(pw, site, f'{TMP}/a')
    nb = capturer(pw, demo, f'{TMP}/b')
n = composer(na, nb)
taille = encoder(n)
Image.open(f'{TMP}/c000.png').convert('RGB').save(os.path.splitext(sortie)[0] + '-premiere.jpg', quality=82)
print(sortie, n, 'images', taille, 'octets')
shutil.rmtree(TMP, ignore_errors=True)
