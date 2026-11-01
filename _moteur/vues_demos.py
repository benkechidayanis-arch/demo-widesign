"""Lit les visites des démos comptées sur demo.widesign.fr (stockage Cloudflare « demo-widesign-vues »).
Usage : CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... python3 vues_demos.py
Affiche un JSON { "dossier": {"n": 3, "premiere": "...", "derniere": "...", "duree_max": 95, "appareils": {...}}, ... }
ou « ÉCHEC : cause ». La clé n'est jamais affichée."""
import json, os, sys, urllib.parse, urllib.request, urllib.error

tok = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
acc = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '').strip()
if not tok or not acc:
    sys.exit('ÉCHEC : CLOUDFLARE_API_TOKEN ou CLOUDFLARE_ACCOUNT_ID absent')
BASE = 'https://api.cloudflare.com/client/v4/accounts/' + acc


def get(chemin, brut=False):
    req = urllib.request.Request(BASE + chemin, headers={'Authorization': 'Bearer ' + tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = r.read()
            return d.decode() if brut else json.loads(d)
    except urllib.error.HTTPError as e:
        if brut:
            return None
        return {'success': False, 'status': e.code, 'body': e.read().decode(errors='replace')[:300].replace(tok, '***')}


r = get('/storage/kv/namespaces?per_page=100')
if not r.get('success'):
    sys.exit('ÉCHEC : lecture du stockage refusée (autorisation Workers KV absente sur la clé) ' + json.dumps(r)[:200])
ns = next((n['id'] for n in r.get('result') or [] if n.get('title') == 'demo-widesign-vues'), None)
if not ns:
    print('{}')
    sys.exit(0)
out, curseur = {}, ''
while True:
    q = '/storage/kv/namespaces/' + ns + '/keys?prefix=v:&limit=1000' + ('&cursor=' + urllib.parse.quote(curseur) if curseur else '')
    k = get(q)
    if not k.get('success'):
        sys.exit('ÉCHEC : liste des visites : ' + json.dumps(k)[:200])
    for x in k.get('result') or []:
        v = get('/storage/kv/namespaces/' + ns + '/values/' + urllib.parse.quote(x['name'], safe=''), brut=True)
        try:
            out[x['name'][2:]] = json.loads(v or '{}')
        except Exception:
            pass
    curseur = (k.get('result_info') or {}).get('cursor') or ''
    if not curseur:
        break
print(json.dumps(out, ensure_ascii=False))
