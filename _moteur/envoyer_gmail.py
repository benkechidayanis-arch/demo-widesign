"""Envoi d'un mail de prospection par la boîte Google Workspace (script Google « Envoi prospection »).
Usage : GMAIL_URL=https://script.google.com/.../exec python3 envoyer_gmail.py mail.json
mail.json : mêmes champs que pour envoyer.py ("a", "objet", "html", "texte", "expediteur",
            "nom_expediteur", "repondre_a", "id", "in_reply_to", "references").
Affiche une ligne JSON : {"ok": true, "gmail_id": "...", "message_id": "<...>"} ou {"ok": false, "erreur": "..."}"""
import base64, json, os, sys, urllib.request, urllib.error
from email.message import EmailMessage
from email.utils import formataddr, make_msgid, formatdate

m = json.load(open(sys.argv[1]))
url = os.environ.get('GMAIL_URL', '')
if not url.startswith('https://script.google.com/') or not url.endswith('/exec'):
    print(json.dumps({'ok': False, 'erreur': 'lien Gmail absent'})); sys.exit(1)
for champ in ('a', 'objet', 'html', 'texte', 'expediteur'):
    if not m.get(champ):
        print(json.dumps({'ok': False, 'erreur': f'champ vide : {champ}'})); sys.exit(1)
for interdit in ('—', '\U0001F64F'):
    if interdit in m['objet'] + m['html'] + m['texte']:
        print(json.dumps({'ok': False, 'erreur': 'caractère interdit dans le mail'})); sys.exit(1)

e = EmailMessage()
e['From'] = formataddr((m.get('nom_expediteur') or 'Yanis Benkechida', m['expediteur']))
e['To'] = m['a']
e['Subject'] = m['objet']
e['Date'] = formatdate(localtime=True)
e['Message-ID'] = make_msgid(domain=m['expediteur'].split('@')[-1])
stop = m.get('repondre_a')
if stop and stop != m['expediteur']:
    e['Reply-To'] = stop
if m.get('in_reply_to'):
    e['In-Reply-To'] = m['in_reply_to']
    refs = [r for r in (m.get('references') or []) if r] or [m['in_reply_to']]
    e['References'] = ' '.join(refs)
e.set_content(m['texte'], charset='utf-8')
e.add_alternative(m['html'], subtype='html', charset='utf-8')

corps = {'raw': base64.urlsafe_b64encode(e.as_bytes()).decode(), 'in_reply_to': m.get('in_reply_to') or '',
         'id': str(m.get('id', ''))}
req = urllib.request.Request(url, data=json.dumps(corps).encode(),
                             headers={'Content-Type': 'application/json', 'User-Agent': 'widesign-prospection/1.0'},
                             method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        brut = r.read().decode(errors='replace')
    try:
        d = json.loads(brut)
    except Exception:
        print(json.dumps({'ok': False, 'erreur': 'réponse Google illisible : ' + brut[:200]})); sys.exit(1)
    if not d.get('ok'):
        print(json.dumps({'ok': False, 'erreur': d.get('erreur') or 'refus Google'})); sys.exit(1)
    print(json.dumps({'ok': True, 'gmail_id': d.get('id'), 'message_id': d.get('message_id') or e['Message-ID']}))
except urllib.error.HTTPError as x:
    print(json.dumps({'ok': False, 'erreur': f'Google {x.code} : {x.read().decode(errors="replace")[:300]}'})); sys.exit(1)
except Exception as x:
    print(json.dumps({'ok': False, 'erreur': f'réseau : {x}'})); sys.exit(1)
