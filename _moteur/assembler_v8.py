"""Assemble une démo v8 : remplace les jetons du gabarit par les éléments graphiques.
Usage : python3 assembler_v8.py source.html index.html config.json
config.json : {
  "logo": "img/logo-client.svg" ou "img/logo-client.png"   (version lisible sur fond sombre),
  "nom": "Nom de l'entreprise",
  "picto": "img/picto.svg" (facultatif : symbole seul du logo, sinon rien),
  "villes": ["Saint-Étienne", "..."],
  "note": 4.3 (facultatif : note Google réelle, sinon la ligne de note doit être retirée du source)
}
Contrôles : aucun tiret cadratin, aucun jeton restant, aucune image http, aucune mention Oriol si le client n'est pas Oriol."""
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
    pref = cls + '-'
    t = re.sub(r'\.(cls|st)-?(\d+)', lambda m: '.' + pref + m.group(1) + m.group(2), t)
    t = re.sub(r'class="(cls|st)-?(\d+)"', lambda m: 'class="' + pref + m.group(1) + m.group(2) + '"', t)
    return t.replace('<svg ', f'<svg class="{cls}" {extra} ', 1)

def visuel(p, cls, alt):
    if p.lower().endswith('.svg'):
        return svg_inline(p, cls, f'role="img" aria-label="{alt}"')
    return f'<img class="{cls}" src="{p}" alt="{alt}">'

nom = c['nom']
s = s.replace('LOGO_CLIENT', visuel(c['logo'], 'lg', nom))
s = s.replace('PICTO_SMALL', visuel(c['picto'], 'ps', '') .replace('alt=""', 'alt="" aria-hidden="true"') if c.get('picto') else '')
star = '<svg viewBox="0 0 20 20"><path fill="#F5B301" d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 15l-5.2 2.7 1-5.9L1.5 7.7l5.9-.8Z"/></svg>'
stare = '<svg viewBox="0 0 20 20"><path fill="none" stroke="#F5B301" stroke-width="1.5" d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 15l-5.2 2.7 1-5.9L1.5 7.7l5.9-.8Z"/></svg>'
if 'STARS' in s:
    n = max(1, min(5, round(float(c.get('note') or 0))))
    s = re.sub(r'STARS\d?', star * n + stare * (5 - n), s)
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
s = s.replace('>PIN<', '>' + pin + '<').replace('CITIES', ''.join(f'<li>{cpin}{v}</li>' for v in c.get('villes', [])))
err = []
if '—' in s: err.append('tiret cadratin')
for k in ['CHK', 'TICK', 'PICTO_', 'LOGO_', 'STARS', 'ARW_', 'CHEV', 'CITIES', 'CLOCK']:
    if k in s: err.append('jeton restant ' + k)
if re.search(r'src="http:', s): err.append('image en http')
if 'oriol' not in nom.lower() and re.search(r'oriol', s, re.I): err.append('mention Oriol restante')
for m in re.findall(r'src="(img/[^"]+)"', s):
    if not os.path.exists(os.path.join(base, m)): err.append('image absente ' + m)
if err:
    sys.exit('ÉCHEC : ' + ' ; '.join(sorted(set(err))))
open(out, 'w', encoding='utf-8').write(s)
print(out, len(s) // 1024, 'Ko')
