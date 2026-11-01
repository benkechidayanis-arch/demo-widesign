"""Protège une démo avant mise en ligne.
Usage : python3 proteger.py demo.html dossier_sortie hote date_fin(AAAA-MM-JJ)
- le document est chiffré (AES-GCM) avec une clé dérivée du nom d'hôte : hors de cet hôte, il ne se déchiffre pas
- après la date de fin, la page affiche seulement que la démo a expiré
- un signal de visite est envoyé à /_v quand une vraie personne regarde la démo (page visible au moins 4 s avec un geste : défilement, toucher, souris) ; ouvrir la démo avec ?moi la retire du comptage sur cet appareil
- clic droit, sélection, glisser et raccourcis de code source bloqués
- les images sont renommées (noms sans signification)"""
import base64, hashlib, os, re, secrets, shutil, sys, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

src, out, hote, fin = sys.argv[1:5]
base = os.path.dirname(os.path.abspath(src))
html = open(src, encoding='utf-8').read()
os.makedirs(os.path.join(out, 'm'), exist_ok=True)

noms = {}
def ren(m):
    p = m.group(1)
    if p not in noms:
        ext = p.rsplit('.', 1)[1]
        n = 'm/' + secrets.token_hex(6) + '.' + ext
        shutil.copy(os.path.join(base, p), os.path.join(out, n))
        noms[p] = n
    return noms[p]
html = re.sub(r'(img/[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|svg|webp))', lambda m: ren(m), html)

garde = """<style>html,body{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}img{-webkit-user-drag:none;pointer-events:none}</style>
<script>(function(){var s=function(e){e.preventDefault()};['contextmenu','dragstart','selectstart','copy'].forEach(function(t){document.addEventListener(t,s)});document.addEventListener('keydown',function(e){var k=(e.key||'').toLowerCase();if(k==='f12'||((e.ctrlKey||e.metaKey)&&(k==='u'||k==='s'||k==='p'))||((e.ctrlKey||e.metaKey)&&e.shiftKey&&(k==='i'||k==='j'||k==='c'))||(e.metaKey&&e.altKey&&(k==='i'||k==='j'||k==='u'))){e.preventDefault()}})})();</script>"""
html = html.replace('</head>', garde + '</head>', 1)

vue = """<script>(function(){try{if(/[?&]moi(=|&|$)/.test(location.search))localStorage.setItem('wd_moi','1');if(localStorage.getItem('wd_moi'))return}catch(e){}
var d=(location.pathname.split('/')[1]||'').toLowerCase();if(!/^[a-z0-9-]{3,80}$/.test(d))return;var t0=Date.now(),geste=0,parti=0,fin=0;
function env(q){var u='/_v?d='+encodeURIComponent(d)+'&s='+Math.round((Date.now()-t0)/1000)+q;try{if(navigator.sendBeacon&&navigator.sendBeacon(u))return}catch(e){}try{fetch(u,{method:'POST',keepalive:true})}catch(e){}}
['scroll','pointerdown','touchstart','keydown','mousemove','wheel'].forEach(function(t){addEventListener(t,function(){geste=1},{passive:true,once:true})});
var it=setInterval(function(){if(!parti&&geste&&document.visibilityState==='visible'&&Date.now()-t0>4000){parti=1;clearInterval(it);env('')}},1000);
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden'&&parti&&!fin){fin=1;env('&f=1')}});
addEventListener('pagehide',function(){if(parti&&!fin){fin=1;env('&f=1')}})})();</script>"""
html = html.replace('</body>', vue + '</body>', 1) if '</body>' in html else html + vue

sel = secrets.token_bytes(16)
cle = hashlib.sha256(hote.encode() + sel).digest()
iv = secrets.token_bytes(12)
chiffre = AESGCM(cle).encrypt(iv, html.encode('utf-8'), None)
fin_ms = int(datetime.datetime.strptime(fin, '%Y-%m-%d').replace(hour=23, minute=59).timestamp() * 1000)
b = lambda x: base64.b64encode(x).decode()
titre = re.search(r'<title>(.*?)</title>', html, re.S)
titre = titre.group(1) if titre else 'Démo Widesign'

page = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow,noarchive"><title>{titre}</title>
<style>html,body{{margin:0;background:#120E0B;color:#fff;font:15px system-ui,sans-serif}}.x{{min-height:100vh;display:grid;place-items:center;text-align:center;padding:24px;opacity:.7}}</style></head><body>
<script>(async function(){{var d="{b(chiffre)}",v="{b(iv)}",g="{b(sel)}",f={fin_ms};
function u(s){{return Uint8Array.from(atob(s),function(c){{return c.charCodeAt(0)}})}}
function m(t){{document.body.innerHTML='<div class="x">'+t+'</div>'}}
if(Date.now()>f){{m('Cette démo a expiré.');return}}
try{{var h=new TextEncoder().encode(location.hostname),s=u(g),k=new Uint8Array(h.length+s.length);k.set(h);k.set(s,h.length);
var c=await crypto.subtle.digest('SHA-256',k),K=await crypto.subtle.importKey('raw',c,'AES-GCM',false,['decrypt']);
var p=await crypto.subtle.decrypt({{name:'AES-GCM',iv:u(v)}},K,u(d));
document.open();document.write(new TextDecoder().decode(p));document.close()}}catch(e){{m('Démo Widesign')}}}})();</script></body></html>"""
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)
print(out, len(page), len(noms), 'images')
