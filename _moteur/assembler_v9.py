"""Assemble une démo v9 : remplace les jetons du gabarit par les éléments graphiques.
Usage : python3 assembler_v9.py source.html index.html config.json
config.json : {
  "logo": "img/logo-client.svg" ou "img/logo-client.png"   (version lisible sur fond sombre),
  "nom": "Nom de l'entreprise",
  "picto": "img/picto.svg" (facultatif : symbole seul du logo ; sans lui, le grand symbole de la section marque et le centre du sceau sont vides),
  "villes": ["Saint-Étienne", "..."]   (communes citées par l'entreprise ; liste vide = pas de bandeau de villes),
  "carte": "carte.svg" (facultatif : sortie de carte_ville.py ; sans elle, le bloc carte doit être retiré du source),
  "note": 4.3 (facultatif : note Google réelle du prompt),
  "place_id": "ChIJ..." (identifiant Google de l'entreprise = id de la démo),
  "avis_cle": "AIza..." (clé Google des avis, champ google_avis_cle de reglages/moteur ; sans elle la section avis est retirée)
}
Contrôles : aucun tiret cadratin, aucun jeton restant, aucune image http, aucune mention Oriol si le client n'est pas Oriol,
aucun avis écrit en dur dans la page (les avis se chargent en direct depuis Google)."""
import json, os, re, sys
src, out, cfg = sys.argv[1:4]
s = open(src, encoding='utf-8').read()
c = json.load(open(cfg, encoding='utf-8'))
base = os.path.dirname(os.path.abspath(src))


def svg_inline(p, cls, extra=''):
    t = open(os.path.join(base, p), encoding='utf-8').read()
    t = t[t.find('<svg'):]
    t = re.sub(r'<\?xml.*?\?>', '', t)
    t = re.sub(r'\sid="[^"]*"', '', t)
    t = re.sub(r'<defs>\s*</defs>', '', t)
    pref = cls + '-'
    t = re.sub(r'\.(cls|st)-?(\d+)', lambda m: '.' + pref + m.group(1) + m.group(2), t)
    t = re.sub(r'class="(cls|st)-?(\d+)"', lambda m: 'class="' + pref + m.group(1) + m.group(2) + '"', t)
    return t.replace('<svg ', f'<svg class="{cls}" {extra} ', 1)


def visuel(p, cls, alt):
    if p.lower().endswith('.svg'):
        return svg_inline(p, cls, f'role="img" aria-label="{alt}"' if alt else 'aria-hidden="true"')
    return f'<img class="{cls}" src="{p}" alt="{alt}"' + ('' if alt else ' aria-hidden="true"') + '>'


nom = c['nom']
s = s.replace('LOGO_CLIENT', visuel(c['logo'], 'lg', nom))
pic = c.get('picto')
s = s.replace('PICTO_GRAND', visuel(pic, 'pg', '') if pic else '')
s = s.replace('PICTO_SMALL', visuel(pic, 'ps', '') if pic else '')

star = '<svg viewBox="0 0 20 20"><path fill="#F5B301" d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 15l-5.2 2.7 1-5.9L1.5 7.7l5.9-.8Z"/></svg>'
stare = '<svg viewBox="0 0 20 20"><path fill="none" stroke="#F5B301" stroke-width="1.5" d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 15l-5.2 2.7 1-5.9L1.5 7.7l5.9-.8Z"/></svg>'
if 'STARS' in s:
    n = max(1, min(5, round(float(c.get('note') or 0))))
    s = re.sub(r'STARS\d?', star * n + stare * (5 - n), s)
s = s.replace('ETOILE_P_JS', json.dumps(star)).replace('ETOILE_V_JS', json.dumps(stare))

chk = '<svg class="chk" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="18" style="fill:var(--acc)"/><path d="M11 18.5l4.6 4.6L25.5 13" fill="none" style="stroke:var(--acc-ink)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
tick = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8.6c1.6 1 2.8 2.4 3.8 4.2C7.6 8.4 10.2 5 14 2.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
arl = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>'
arr = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
phone = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
pin = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s7-6.4 7-12a7 7 0 1 0-14 0c0 5.6 7 12 7 12Z"/><circle cx="12" cy="10" r="2.5"/></svg>'
clock = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
chev = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>'
cpin = '<svg viewBox="0 0 18 23" aria-hidden="true"><path style="fill:var(--acc)" d="M9 0a9 9 0 0 1 9 9c0 6.3-9 14-9 14S0 15.3 0 9a9 9 0 0 1 9-9Z"/><circle cx="9" cy="9" r="3.4" fill="#fff"/></svg>'
s = s.replace('CHK', chk).replace('TICK', tick).replace('ARW_L', arl).replace('ARW_R', arr).replace('PHONE', phone).replace('CLOCK', clock).replace('CHEV', chev)
s = s.replace('>PIN<', '>' + pin + '<')

# villes : 1 ligne fixe sous 6 villes, sinon 2 ou 3 lignes qui défilent
v = c.get('villes') or []
if not v:
    s = re.sub(r'<div class="vrows"[^>]*>CITYROWS</div>', '', s)
elif len(v) < 6:
    s = s.replace('CITYROWS', '<div class="vrow" style="animation:none;flex-wrap:wrap;width:auto;padding:0 18px"><ul style="flex-wrap:wrap">' + ''.join(f'<li>{cpin}{x}</li>' for x in v) + '</ul></div>')
else:
    n = 2 if len(v) < 16 else 3
    rows = ''
    for r in [v[i::n] for i in range(n)]:
        li = ''.join(f'<li>{cpin}{x}</li>' for x in r)
        rows += f'<div class="vrow"><ul>{li}</ul><ul aria-hidden="true">{li}</ul></div>'
    s = s.replace('CITYROWS', rows)

if c.get('carte'):
    car = open(os.path.join(base, c['carte']), encoding='utf-8').read()
    car = car[car.find('<svg'):]
    s = s.replace('CARTE_SVG', car)

# avis en direct
cle, pid = c.get('avis_cle') or '', c.get('place_id') or ''
if re.fullmatch(r'AIza[0-9A-Za-z_-]{35}', cle) and pid:
    s = s.replace('AVIS_CLE', cle).replace('PLACE_ID', pid)
else:
    s = re.sub(r'<section class="lt sec" id="avis".*?</section>\s*', '', s, flags=re.S)
    s = s.replace('AVIS_CLE', '').replace('PLACE_ID', '')

import contact_widesign
s = contact_widesign.inserer(s, nom)

err = []
if '—' in s: err.append('tiret cadratin')
for k in ['CHK', 'TICK', 'PICTO_', 'LOGO_', 'STARS', 'ARW_', 'CHEV', 'CITYROWS', 'CITIES', 'CLOCK', 'CARTE_SVG', 'ETOILE_', 'AVIS_CLE', 'PLACE_ID']:
    if k in s: err.append('jeton restant ' + k)
if re.search(r'src="http:', s): err.append('image en http')
if 'oriol' not in nom.lower() and (re.search(r'oriol', s, re.I) or re.search(r'\bMATCH\b', s)): err.append('mention Oriol ou MATCH restante')
m = re.search(r'<ul class="avs" id="avs">(.*?)</ul>', s, re.S)
if m and m.group(1).strip(): err.append('avis écrits en dur dans la page (la liste #avs doit rester vide)')
if re.search(r'témoignage', s, re.I): err.append('mot témoignage')
for m in re.findall(r'src="(img/[^"]+)"', s):
    if not os.path.exists(os.path.join(base, m)): err.append('image absente ' + m)
if err:
    sys.exit('ÉCHEC : ' + ' ; '.join(sorted(set(err))))
open(out, 'w', encoding='utf-8').write(s)
print(out, len(s) // 1024, 'Ko', '(avis en direct)' if 'id="avis"' in s else '(sans avis)')
