"""Envoi d'un mail de prospection par l'API Resend.
Usage : RESEND_KEY=re_xxx python3 envoyer.py mail.json
mail.json : {"a": "...", "objet": "...", "html": "...", "texte": "...",
             "expediteur": "yanis@widesign.fr", "nom_expediteur": "Yanis Benkechida",
             "repondre_a": "yanis@widesign.fr", "id": "<id envoi>",
             "in_reply_to": "<message-id du mail précédent>" (relance, facultatif),
             "references": ["<message-id 1>", "<message-id 2>"] (relance, facultatif)}
Affiche une ligne JSON : {"ok": true, "resend_id": "...", "message_id": "<...>" ou null} ou {"ok": false, "erreur": "..."}
message_id (lu juste après l'envoi) sert à faire tomber les relances dans le même fil ; il reste null si la clé
ne permet que l'envoi."""
import json, os, sys, time, urllib.request, urllib.error

m = json.load(open(sys.argv[1]))
cle = os.environ.get('RESEND_KEY', '')
if not cle.startswith('re_'):
    print(json.dumps({'ok': False, 'erreur': 'clé Resend absente'})); sys.exit(1)
for champ in ('a', 'objet', 'html', 'texte', 'expediteur'):
    if not m.get(champ):
        print(json.dumps({'ok': False, 'erreur': f'champ vide : {champ}'})); sys.exit(1)
for interdit in ('—', '\U0001F64F'):
    if interdit in m['objet'] + m['html'] + m['texte']:
        print(json.dumps({'ok': False, 'erreur': 'caractère interdit dans le mail'})); sys.exit(1)

stop = m.get('repondre_a') or m['expediteur']
corps = {
    'from': f"{m.get('nom_expediteur') or 'Yanis Benkechida'} <{m['expediteur']}>",
    'to': [m['a']],
    'subject': m['objet'],
    'html': m['html'],
    'text': m['texte'],
    'reply_to': stop,
    'headers': {},
    'tags': [{'name': 'campagne', 'value': 'prospection'}],
}
if m.get('in_reply_to'):
    corps['headers']['In-Reply-To'] = m['in_reply_to']
    refs = [r for r in (m.get('references') or []) if r] or [m['in_reply_to']]
    corps['headers']['References'] = ' '.join(refs)
req = urllib.request.Request('https://api.resend.com/emails', data=json.dumps(corps).encode(),
                             headers={'Authorization': f'Bearer {cle}', 'Content-Type': 'application/json',
                                      'Idempotency-Key': 'envoi-' + str(m.get('id', ''))[:200],
                                      'User-Agent': 'widesign-prospection/1.0'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read() or b'{}')
    mid = None
    for _ in range(4):
        time.sleep(3)
        try:
            g = urllib.request.Request('https://api.resend.com/emails/' + d.get('id', ''),
                                       headers={'Authorization': f'Bearer {cle}', 'User-Agent': 'widesign-prospection/1.0'})
            with urllib.request.urlopen(g, timeout=20) as r2:
                mid = json.loads(r2.read() or b'{}').get('message_id')
            if mid:
                break
        except Exception:
            break
    print(json.dumps({'ok': True, 'resend_id': d.get('id'), 'message_id': mid}))
except urllib.error.HTTPError as e:
    print(json.dumps({'ok': False, 'erreur': f'Resend {e.code} : {e.read().decode(errors="replace")[:300]}'})); sys.exit(1)
except Exception as e:
    print(json.dumps({'ok': False, 'erreur': f'réseau : {e}'})); sys.exit(1)
