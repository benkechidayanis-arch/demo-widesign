"""Publie les démos protégées sur Cloudflare Pages (projet demo-widesign, domaine demo.widesign.fr).
Le site entier est reconstruit à chaque envoi : on récupère la liste des fichiers en ligne (_widesign/fichiers.json),
on retélécharge ceux des démos encore valides (les démos expirées disparaissent d'elles-mêmes), on ajoute les nouveaux,
puis wrangler envoie le tout (il n'envoie réellement que les fichiers nouveaux ou modifiés).

Usage :
  CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... python3 publier_cloudflare.py \
     [--amorce-github] [--essai] \
     [--demo dossier=chemin_local_du_dossier_en-ligne:AAAA-MM-JJ ...] \
     [--fichier chemin/sur/le/site=chemin_local ...] \
     [--fin dossier=AAAA-MM-JJ ...]
  --amorce-github : premier envoi, part du dépôt GitHub benkechidayanis-arch/demo-widesign (lecture seule).
  --demo : remplace (ou crée) le dossier public de la démo, avec sa date de fin.
  --fichier : fichier isolé (GIF, image du GIF, vignette) : g/<hex>.gif=/tmp/demos/x/gif.gif
  --fin : date de fin d'une démo déjà en ligne (utile pour l'amorce).
  --essai : prépare le site dans /tmp/site-demos sans rien envoyer.
Affiche « OK » avec l'adresse pages.dev et l'état du domaine, ou « ÉCHEC : cause ». Les clés ne sont jamais affichées."""
import datetime, json, os, shutil, subprocess, sys, urllib.request, urllib.error

PROJET, DOMAINE, BRANCHE = 'demo-widesign', 'demo.widesign.fr', 'main'
DEPOT = 'https://github.com/benkechidayanis-arch/demo-widesign.git'
SITE = '/tmp/site-demos'
args = sys.argv[1:]
essai = '--essai' in args
amorce = '--amorce-github' in args
tok = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
acc = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '').strip()
if not essai and (not tok or not acc):
    sys.exit('ÉCHEC : CLOUDFLARE_API_TOKEN ou CLOUDFLARE_ACCOUNT_ID absent')

def valeurs(nom):
    out, i = [], 0
    while i < len(args):
        if args[i] == nom and i + 1 < len(args):
            out.append(args[i + 1]); i += 2
        else:
            i += 1
    return out

def api(meth, chemin, data=None):
    req = urllib.request.Request('https://api.cloudflare.com/client/v4/accounts/' + acc + chemin, method=meth,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corps = e.read().decode(errors='replace')[:400].replace(tok, '***') if tok else ''
        return {'success': False, 'status': e.code, 'body': corps}

def telecharger(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'widesign-agent-demo'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)

aujourd = datetime.date.today().isoformat()
shutil.rmtree(SITE, ignore_errors=True)
os.makedirs(SITE)
fins = {}                     # dossier de démo -> date de fin
for v in valeurs('--fin'):
    d, f = v.split('=', 1); fins[d.strip('/')] = f

# 1. Projet et adresse pages.dev
sous_domaine = None
if not essai:
    p = api('GET', f'/pages/projects/{PROJET}')
    if not p.get('success'):
        if p.get('status') == 404 or 'not found' in json.dumps(p).lower():
            p = api('POST', '/pages/projects', {'name': PROJET, 'production_branch': BRANCHE})
        if not p.get('success'):
            sys.exit('ÉCHEC : projet Cloudflare Pages : ' + json.dumps(p)[:400])
    sous_domaine = p['result'].get('subdomain') or f'{PROJET}.pages.dev'

# 2. Base du site
if amorce:
    tmp = '/tmp/depot-demos'
    shutil.rmtree(tmp, ignore_errors=True)
    r = subprocess.run(['git', 'clone', '--depth', '1', DEPOT, tmp], capture_output=True, text=True)
    if r.returncode:
        sys.exit('ÉCHEC : lecture du dépôt GitHub : ' + r.stderr[-300:])
    for n in os.listdir(tmp):
        if n in ('.git', 'CNAME', 'diag', '.github', '_moteur', 'README.md', '.nojekyll'):
            continue
        src = os.path.join(tmp, n)
        (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, os.path.join(SITE, n))
else:
    base = f'https://{sous_domaine}' if sous_domaine else f'https://{DOMAINE}'
    try:
        man = json.loads(urllib.request.urlopen(urllib.request.Request(base + '/_widesign/fichiers.json', headers={'User-Agent': 'widesign-agent-demo'}), timeout=30).read())
    except Exception as e:
        sys.exit('ÉCHEC : liste des fichiers en ligne introuvable (' + str(e)[:120] + ') ; lance une amorce avec --amorce-github')
    for d, f in man.get('dossiers', {}).items():
        fins.setdefault(d, f)
    for chemin in man.get('fichiers', []):
        tete = chemin.split('/')[0]
        if tete in man.get('dossiers', {}) and fins.get(tete, '9999') < aujourd:
            continue
        try:
            telecharger(base + '/' + chemin, os.path.join(SITE, chemin))
        except Exception as e:
            sys.exit('ÉCHEC : téléchargement de ' + chemin + ' : ' + str(e)[:120])

# 3. Nouvelles démos et fichiers
for v in valeurs('--demo'):
    d, reste = v.split('=', 1)
    loc, fin = reste.rsplit(':', 1)
    d = d.strip('/')
    if not os.path.isfile(os.path.join(loc, 'index.html')):
        sys.exit('ÉCHEC : ' + loc + '/index.html absent')
    html = open(os.path.join(loc, 'index.html'), encoding='utf-8', errors='replace').read()
    if 'crypto.subtle' not in html:
        sys.exit('ÉCHEC : la démo ' + d + " n'est pas protégée (crypto.subtle absent)")
    shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)
    shutil.copytree(loc, os.path.join(SITE, d))
    fins[d] = fin
for v in valeurs('--fichier'):
    cible, loc = v.split('=', 1)
    if not os.path.isfile(loc):
        sys.exit('ÉCHEC : fichier local absent ' + loc)
    os.makedirs(os.path.dirname(os.path.join(SITE, cible)) or SITE, exist_ok=True)
    shutil.copy2(loc, os.path.join(SITE, cible))

# 4. Démos expirées retirées, liste des fichiers écrite
for d, f in list(fins.items()):
    if f < aujourd:
        shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)
        del fins[d]
dossiers = {d: f for d, f in fins.items() if os.path.isdir(os.path.join(SITE, d))}
fichiers = []
for racine, _, fs in os.walk(SITE):
    for f in fs:
        rel = os.path.relpath(os.path.join(racine, f), SITE).replace(os.sep, '/')
        if not rel.startswith('_widesign/'):
            fichiers.append(rel)
os.makedirs(os.path.join(SITE, '_widesign'), exist_ok=True)
json.dump({'genere_le': datetime.datetime.now().isoformat(timespec='seconds'), 'dossiers': dossiers, 'fichiers': sorted(fichiers)},
          open(os.path.join(SITE, '_widesign', 'fichiers.json'), 'w'), ensure_ascii=False, indent=1)
with open(os.path.join(SITE, '_headers'), 'w') as f:
    f.write('/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n')
taille = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(SITE) for f in fs)
if essai:
    print(f'ESSAI : {len(fichiers)} fichiers, {len(dossiers)} démos ({", ".join(sorted(dossiers))}), {taille // 1024} Ko dans {SITE}')
    sys.exit(0)

# 5. Envoi
env = dict(os.environ, CLOUDFLARE_API_TOKEN=tok, CLOUDFLARE_ACCOUNT_ID=acc, WRANGLER_SEND_METRICS='false', CI='1')
r = subprocess.run(['npx', '--yes', 'wrangler@4', 'pages', 'deploy', SITE, '--project-name', PROJET, '--branch', BRANCHE, '--commit-dirty=true'],
                   capture_output=True, text=True, env=env, timeout=900)
sortie = (r.stdout + r.stderr).replace(tok, '***')
if r.returncode:
    sys.exit('ÉCHEC : envoi wrangler : ' + sortie[-600:])

# 6. Domaine demo.widesign.fr rattaché au projet
dom = api('GET', f'/pages/projects/{PROJET}/domains')
noms = [x.get('name') for x in (dom.get('result') or [])]
if DOMAINE not in noms:
    dom2 = api('POST', f'/pages/projects/{PROJET}/domains', {'name': DOMAINE})
    etat = 'ajouté' if dom2.get('success') else 'non ajouté : ' + json.dumps(dom2)[:300]
else:
    etat = next((x.get('status') for x in dom['result'] if x.get('name') == DOMAINE), 'inconnu')
print(f'OK : {len(fichiers)} fichiers, {len(dossiers)} démos en ligne, adresse https://{sous_domaine} , domaine {DOMAINE} : {etat}')
