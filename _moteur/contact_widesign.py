"""Bandeau « Écrivez-moi » de Widesign, ajouté à toutes les démos (assembler_v9.py et retoucher_demo.py).
- une pastille discrète apparaît après un tiers de la page (ou 20 s) : un toucher ouvre une petite fiche avec mail et WhatsApp
- une bande en bas de page reprend le même contact ; la pastille se cache quand cette bande est à l'écran
- l'adresse mail n'est jamais écrite en clair dans la page (lien construit au clic)
- rien ne s'affiche pour les navigateurs automatisés (captures et GIF)
Le bloc est entre <!--wsx--> et <!--/wsx--> : il est remplacé à chaque retouche."""
import html as _h
import json
import re

TEL_WA = '33756844985'
MAIL = ('yanis', 'widesign.fr')

CSS = """<style>
.wsx-p,.wsx-f,.wsx-b{font-family:inherit;-webkit-font-smoothing:antialiased;box-sizing:border-box}
.wsx-p *,.wsx-f *,.wsx-b *{box-sizing:border-box}
.wsx-p{position:fixed;z-index:95;left:50%;bottom:88px;transform:translate(-50%,24px);opacity:0;visibility:hidden;pointer-events:none;display:flex;align-items:center;gap:9px;padding:7px 15px 7px 7px;border-radius:999px;background:rgba(17,17,16,.9);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);color:#fff;font-size:13.5px;font-weight:500;line-height:1;white-space:nowrap;border:1px solid rgba(255,255,255,.12);box-shadow:0 10px 30px rgba(0,0,0,.25);cursor:pointer;transition:transform .5s cubic-bezier(.2,.8,.2,1),opacity .4s}
.wsx-p.on{transform:translate(-50%,0);opacity:1;visibility:visible;pointer-events:auto}
.wsx-p .wsx-w{flex:none;width:26px;height:26px;border-radius:50%;background:#fff;color:#111;display:grid;place-items:center;font-weight:800;font-size:13px;letter-spacing:-.04em}
.wsx-p .wsx-d{width:7px;height:7px;border-radius:50%;background:#3DDC84;box-shadow:0 0 0 3px rgba(61,220,132,.22);margin-left:2px}
.wsx-f{position:fixed;z-index:96;left:12px;right:12px;bottom:12px;max-width:400px;margin:0 auto;padding:22px 20px 18px;border-radius:20px;background:#111110;color:#fff;box-shadow:0 20px 60px rgba(0,0,0,.4);transform:translateY(calc(100% + 30px));visibility:hidden;transition:transform .5s cubic-bezier(.2,.8,.2,1),visibility 0s .5s}
.wsx-f.on{transform:none;visibility:visible;transition:transform .5s cubic-bezier(.2,.8,.2,1)}
.wsx-f .wsx-x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;border-radius:50%;background:rgba(255,255,255,.08);color:#fff;font-size:20px;line-height:1;cursor:pointer}
.wsx-f p{margin:0 36px 4px 0;font-size:17px;font-weight:600;line-height:1.3;letter-spacing:-.01em}
.wsx-f small{display:block;margin:0 0 16px;font-size:13.5px;line-height:1.45;color:rgba(255,255,255,.62)}
.wsx-a{display:flex;gap:8px}
.wsx-a a{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;padding:12px 10px;border-radius:12px;font-size:14.5px;font-weight:600;text-decoration:none;line-height:1.2;transition:filter .2s}
.wsx-a a:hover{filter:brightness(1.08)}
.wsx-a svg{flex:none;width:18px;height:18px}
.wsx-a .wsx-m{background:#fff;color:#111}
.wsx-a .wsx-g{background:#25D366;color:#06301A}
.wsx-b{background:#0E0E0D;color:#fff;padding:26px 6% 100px}
.wsx-b .wsx-i{max-width:1180px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
.wsx-b p{margin:0;font-size:15px;line-height:1.5;color:rgba(255,255,255,.72)}
.wsx-b p b{color:#fff;font-weight:600}
.wsx-b .wsx-a{max-width:400px}
@media(min-width:900px){
.wsx-p{left:24px;bottom:24px;transform:translateY(24px)}
.wsx-p.on{transform:none}
.wsx-f{left:24px;right:auto;bottom:24px;width:380px;margin:0}
.wsx-b .wsx-i{flex-direction:row;align-items:center;justify-content:space-between}
.wsx-b{padding-bottom:30px}.wsx-b .wsx-a{flex:none;width:400px}}
@media print{.wsx-p,.wsx-f{display:none}}
</style>"""

ICO_M = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 6.5 12 13l8.5-6.5"/></svg>'
ICO_W = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.2A9.8 9.8 0 0 0 3.6 17l-1.4 4.8 5-1.3A9.8 9.8 0 1 0 12 2.2Zm0 17.9a8.1 8.1 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.1 8.1 0 1 1 12 20.1Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.3.8 3.2.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.2-.2-.5-.3Z"/></svg>'


def bloc(nom):
    n = _h.escape(nom.strip())
    sujet = f'Démo du site {nom.strip()}'
    wa = f'Bonjour Yanis, j\'ai vu la démo du site {nom.strip()}.'
    actions = (f'<div class="wsx-a"><a class="wsx-m" href="#" data-wsx="m">{ICO_M}Écrivez-moi</a>'
               f'<a class="wsx-g" href="#" data-wsx="w" target="_blank" rel="noopener">{ICO_W}WhatsApp</a></div>')
    js = ("<script>(function(){var u=" + json.dumps(list(MAIL)) + ",s=" + json.dumps(sujet) + ",w=" + json.dumps(wa) + ",t='" + TEL_WA + "';"
          "[].forEach.call(document.querySelectorAll('[data-wsx]'),function(a){a.addEventListener('click',function(e){"
          "if(a.dataset.wsx==='m'){e.preventDefault();location.href='mailto:'+u[0]+'@'+u[1]+'?subject='+encodeURIComponent(s)}"
          "});if(a.dataset.wsx==='w')a.href='https://wa.me/'+t+'?text='+encodeURIComponent(w)});"
          "if(navigator.webdriver)return;"
          "var p=document.getElementById('wsx-p'),f=document.getElementById('wsx-f'),b=document.getElementById('wsx-b'),vu=false,bas=false,ouvert=false;"
          "if(!document.getElementById('callbar')){p.style.bottom='20px';b.style.paddingBottom='30px'}"
          "function maj(){p.classList.toggle('on',vu&&!bas&&!ouvert)}"
          "function voir(){if(!vu){vu=true;maj()}}"
          "setTimeout(voir,20000);"
          "addEventListener('scroll',function(){var h=document.documentElement;if(scrollY>(h.scrollHeight-innerHeight)/3)voir()},{passive:true});"
          "if('IntersectionObserver' in window)new IntersectionObserver(function(es){bas=es[0].isIntersecting;maj()}).observe(b);"
          "p.addEventListener('click',function(){ouvert=true;f.classList.add('on');maj()});"
          "document.getElementById('wsx-x').addEventListener('click',function(){ouvert=false;f.classList.remove('on');maj()})"
          "})();</script>")
    return ('<!--wsx-->' + CSS +
            f'<section class="wsx-b" id="wsx-b" aria-label="Contact Widesign"><div class="wsx-i"><p>Démo préparée pour <b>{n}</b> par Yanis, de Widesign. Elle vous plaît ?</p>{actions}</div></section>'
            f'<button class="wsx-p" id="wsx-p" type="button"><span class="wsx-w">W</span>Démo Widesign · Elle vous plaît ?<span class="wsx-d"></span></button>'
            f'<div class="wsx-f" id="wsx-f" role="dialog" aria-label="Contact Widesign"><button class="wsx-x" id="wsx-x" type="button" aria-label="Fermer">×</button>'
            f'<p>Cette démo vous plaît ?</p><small>Préparée pour {n} par Yanis, de Widesign. Une question, une envie : je vous réponds vite.</small>{actions}</div>'
            + js + '<!--/wsx-->')


def inserer(h, nom):
    """Ajoute (ou remplace) le bandeau juste avant </body>."""
    h = re.sub(r'<!--wsx-->.*?<!--/wsx-->', '', h, flags=re.S)
    b = bloc(nom)
    i = h.rfind('</body>')
    return h[:i] + b + h[i:] if i >= 0 else h + b


def nom_depuis_page(h):
    m = re.search(r"site (?:d'|d’|de |du |des )(.+?)(?:,| ·) visible jusqu", h)
    return _h.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else None
