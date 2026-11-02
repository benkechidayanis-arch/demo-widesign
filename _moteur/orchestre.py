"""Chef d'orchestre de la prospection automatique (décisions seulement, aucune écriture en base).

  python3 orchestre.py scan <dossier>
      Lit <dossier>/scans.json (liste des documents scans, champ id + données) et <dossier>/plan.json
      (reglages/plan_auto). Affiche un JSON : {"scan": <document à créer> ou null, "raison": "..."}.
      plan.scans_par_jour scans par jour (heure de Paris), un à la fois, quota Google gratuit respecté, aucun scan si un autre tourne.

  python3 orchestre.py demos <dossier> [max]
      Lit <dossier>/scans.json, <dossier>/demos.json (liste des documents demos), <dossier>/plan.json
      et <dossier>/scan-<id>.json pour chaque scan terminé. Affiche un JSON :
      {"lancer": [ids déjà en statut demande à lancer], "creer": [documents demos à créer], "raison": "..."}.
      Rien si une démo est en cours de fabrication. Plafond de démos créées par jour : plan.demos_par_jour.

Les mails ne partent jamais d'ici : Yanis les valide et les envoie lui-même dans l'onglet Envois.
"""
import datetime, json, os, re, sys, unicodedata, zoneinfo

PARIS = zoneinfo.ZoneInfo('Europe/Paris')
QUOTA_JOUR, QUOTA_MOIS = 40, 1000
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


def lire(p, defaut=None):
    try:
        return json.load(open(p))
    except FileNotFoundError:
        return defaut


def docs(liste):
    """Accepte [{id, data:{...}}] (sortie de requête) ou [{...}] (données à plat)."""
    out = []
    for d in liste or []:
        x = dict(d.get('data') or d)
        x.setdefault('id', d.get('id'))
        out.append(x)
    return out


def quand(s):
    if not s:
        return None
    try:
        t = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def maintenant():
    return datetime.datetime.now(PARIS)


def cle_zone(lat, lng):
    try:
        return '%.2f,%.2f' % (float(lat), float(lng))
    except (TypeError, ValueError):
        return ''


def cle_metiers(noms):
    return '|'.join(sorted(noms))


def id_metier(fam, nom):
    s = unicodedata.normalize('NFD', fam + '-' + nom)
    return re.sub(r'[^\w-]', '', s).lower()


def appels(scans, depuis):
    t = 0
    for s in scans:
        c = quand(s.get('cree_le'))
        if c and c >= depuis:
            st = s.get('stats') or {}
            t += st['appels_places'] if st.get('appels_places') is not None else int(s.get('plafond_appels') or 15)
    return t


def scan_occupe(s):
    if s.get('statut') in ('demande', 'en_cours'):
        return 'scan ' + s['id'] + ' en cours'
    if (s.get('mails_agent') or {}).get('statut') in ('demande', 'en_cours'):
        return 'recherche de mails en cours pour ' + s['id']
    if (s.get('design') or {}).get('statut') in ('demande', 'en_cours'):
        return 'analyse des sites en cours pour ' + s['id']
    return None


def cmd_scan(d):
    scans, plan = docs(lire(os.path.join(d, 'scans.json'), [])), lire(os.path.join(d, 'plan.json'), {})
    if not plan.get('actif', True):
        return {'scan': None, 'raison': 'prospection automatique en pause'}
    now = maintenant()
    jour = now.replace(hour=0, minute=0, second=0, microsecond=0)
    du_jour = sum(1 for s in scans if s.get('auto') and (quand(s.get('cree_le')) or jour - datetime.timedelta(days=1)) >= jour)
    if du_jour >= int(plan.get('scans_par_jour', 1)):
        return {'scan': None, 'raison': 'scans du jour déjà lancés (' + str(du_jour) + ')'}
    for s in scans:
        o = scan_occupe(s)
        if o:
            return {'scan': None, 'raison': o}
    resteJ = QUOTA_JOUR - appels(scans, jour)
    resteM = QUOTA_MOIS - appels(scans, jour.replace(day=1))
    plaf = min(int(plan.get('plafond_appels', 15)), resteJ, resteM)
    if plaf < 3:
        return {'scan': None, 'raison': 'quota Google gratuit atteint'}
    faits = set()
    for s in scans:
        if s.get('statut') == 'erreur' and not s.get('auto'):
            continue
        faits.add((cle_zone(s.get('lat'), s.get('lng')), cle_metiers(m['nom'] for m in s.get('metiers') or [])))
    for z in plan.get('zones', []):
        for g in plan.get('groupes', []):
            k = (cle_zone(z['lat'], z['lng']), cle_metiers(n for _, n in g))
            if k in faits:
                continue
            metiers = []
            for fam, nom in g:
                info = (plan.get('metiers') or {}).get(nom)
                if not info:
                    return {'scan': None, 'raison': 'métier inconnu dans le plan : ' + nom}
                metiers.append({'id': id_metier(fam, nom), 'nom': nom, 'requete': info['requete'], 'naf': info['naf'], 'famille': fam})
            sid = 's' + base36(int(now.timestamp() * 1000))
            doc = {'id': sid, 'ville': z['ville'], 'lat': z['lat'], 'lng': z['lng'], 'cp': z['cp'],
                   'rayon_km': z.get('rayon_km', 4), 'metiers': metiers, 'activite_libre': None,
                   'plafond_appels': plaf, 'statut': 'demande', 'etape': 'En file', 'progression': 0,
                   'cree_le': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'), 'auto': True}
            return {'scan': doc, 'raison': z['ville'] + ' : ' + ', '.join(n for _, n in g)}
    return {'scan': None, 'raison': 'plan terminé : ajouter des zones ou des métiers'}


def base36(n):
    c = '0123456789abcdefghijklmnopqrstuvwxyz'
    r = ''
    while n:
        n, k = divmod(n, 36)
        r = c[k] + r
    return r


def date_fr(t):
    return ('1er' if t.day == 1 else str(t.day)) + ' ' + MOIS[t.month - 1] + ' ' + str(t.year)


def zone_de(e, scan):
    a = (e.get('territoire') or {}).get('agglo')
    if a:
        a = re.sub(r"^(Communauté (d'agglomération|de communes|urbaine)|Métropole|CA|CC)\s+(du |de la |des |de l'|d'|de )?", '', a, flags=re.I)
        a = re.sub(r'\s+(Métropole|Agglomération|Agglo|Communauté)$', '', a, flags=re.I).strip()
        if a:
            return a
    return scan.get('centre_nom') or scan.get('ville') or ''


def prompt_demo(e, scan, expire_txt):
    s = e.get('sirene') or {}
    av = e.get('avis_site') or {}
    zone = zone_de(e, scan)
    commune = (e.get('territoire') or {}).get('commune') or e.get('ville') or ''
    L = ['# DONNÉES · DÉMO « ' + e['nom'] + ' »', '',
         'Démo d\'une page construite avec le modèle « Version 9 » (_moteur/gabarit-v9.html, guide _moteur/guide-v9.md) selon les consignes de l\'agent démo.', '',
         '## Entreprise (seule source de vérité avec son site)', '- Nom : ' + e['nom'],
         '- Activité : ' + (e.get('metier') or '') + (' (' + s['naf_libelle'] + ')' if s.get('naf_libelle') else '')]
    if e.get('adresse'):
        L.append('- Adresse : ' + e['adresse'])
    L.append('- Ville : ' + commune + (' (zone de ' + zone + ')' if zone and commune and zone != commune else ''))
    if e.get('telephone'):
        L.append('- Téléphone : ' + e['telephone'])
    if s.get('date_creation'):
        L.append('- Entreprise créée en ' + str(s['date_creation'])[:4] + ' (SIRENE)')
    if e.get('horaires'):
        L.append('- Horaires : ' + ' ; '.join(re.sub(r':\s', ': ', re.sub(r'\s*[–-]\s*', ' à ', h), count=1) for h in e['horaires']))
    if e.get('note') and e.get('nb_avis'):
        L.append('- Note Google : ' + str(e['note']).replace('.', ',') + '/5, ' + str(e['nb_avis']) + ' avis')
    if e.get('site'):
        L.append('- Site actuel : ' + e['site'])
    if av.get('constats'):
        L += ['', '## Constats de l\'analyste sur le site actuel'] + ['- ' + c for c in av['constats']]
    L += ['', '## Expiration', '- Démo visible jusqu\'au ' + expire_txt + '.']
    return '\n'.join(L)


def cmd_demos(d, maxi):
    scans = docs(lire(os.path.join(d, 'scans.json'), []))
    demos = docs(lire(os.path.join(d, 'demos.json'), []))
    plan = lire(os.path.join(d, 'plan.json'), {})
    if not plan.get('actif', True):
        return {'lancer': [], 'creer': [], 'raison': 'prospection automatique en pause'}
    if any(x.get('statut') == 'en_cours' for x in demos):
        return {'lancer': [], 'creer': [], 'raison': 'une fabrication de démos est en cours'}
    attente = [x['id'] for x in demos if x.get('statut') == 'demande']
    if attente:
        return {'lancer': attente[:maxi], 'creer': [], 'raison': str(len(attente)) + ' démos en file'}
    now = maintenant()
    jour = now.replace(hour=0, minute=0, second=0, microsecond=0)
    faites = sum(1 for x in demos if (quand(x.get('cree_le')) or jour) > jour and x.get('auto'))
    reste = min(maxi, int(plan.get('demos_par_jour', 16)) - faites)
    if reste <= 0:
        return {'lancer': [], 'creer': [], 'raison': 'plafond de démos du jour atteint'}
    deja = {x['id'] for x in demos}
    ignorer = set(plan.get('scans_ignores', []))
    fichiers = []
    for s in sorted(scans, key=lambda x: x.get('cree_le') or ''):
        f = lire(os.path.join(d, 'scan-' + s['id'] + '.json'))
        if f:
            fichiers.append((s, f))
    # doublons : même fiche Google, même mail ou même SIREN qu'une démo déjà faite
    mails, sirens = set(), set()
    for _, f in fichiers:
        for e in f.get('entreprises', []):
            if e['id'] in deja:
                if e.get('mail'):
                    mails.add(e['mail'].strip().lower())
                if (e.get('sirene') or {}).get('siren'):
                    sirens.add(e['sirene']['siren'])
    cands = []
    for s, f in fichiers:
        if s['id'] in ignorer or s.get('statut') != 'termine' or scan_occupe(s):
            continue
        for e in f.get('entreprises', []):
            if e['id'] in deja or not e.get('mail') or e.get('ecarte') or e.get('attente_mail') or e.get('attente_avis'):
                continue
            m, sn = e['mail'].strip().lower(), (e.get('sirene') or {}).get('siren')
            if m in mails or (sn and sn in sirens):
                continue
            deja.add(e['id'])
            mails.add(m)
            if sn:
                sirens.add(sn)
            cands.append((0 if e.get('site') else 1, -(e.get('score') or 0), e, s))
    cands.sort(key=lambda c: (c[0], c[1]))
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    creer = []
    for _, _, e, s in cands[:reste]:
        creer.append({'id': e['id'], 'scan': s['id'], 'nom': e['nom'], 'metier': e.get('metier') or '',
                      'zone': zone_de(e, s), 'style': 'Version 9', 'modele': 'v9',
                      'statut': 'demande', 'prompt': prompt_demo(e, s, date_fr(exp.astimezone(PARIS))),
                      'cree_le': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
                      'expire_le': exp.isoformat().replace('+00:00', 'Z'), 'fichier': 'data/demos/' + e['id'] + '/index.html',
                      'vignette': None, 'url': None, 'message': None, 'auto': True})
    return {'lancer': [x['id'] for x in creer], 'creer': creer,
            'raison': str(len(creer)) + ' nouvelles démos' if creer else 'aucun prospect en attente de démo'}


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('scan', 'demos'):
        sys.exit(__doc__)
    if sys.argv[1] == 'scan':
        r = cmd_scan(sys.argv[2])
    else:
        r = cmd_demos(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
    json.dump(r, open(os.path.join(sys.argv[2], 'decision.json'), 'w'), ensure_ascii=False)
    print(json.dumps({k: (v if k != 'creer' else [x['nom'] for x in v]) for k, v in r.items()}, ensure_ascii=False))
