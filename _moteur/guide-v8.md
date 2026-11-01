# Modèle de démo v8 : guide de construction

Le modèle v8 a été validé par Yanis sur la démo Oriol. Chaque démo doit sortir au même niveau : même structure, même design, mêmes animations, mais tout le contenu, les photos, le logo et la couleur sont ceux du prospect. Le fichier gabarit-v8.html est la démo Oriol écrite avec des jetons (LOGO_CLIENT, CHK, TICK, PHONE, CITIES, STARS4...) : c'est l'exemple à suivre, section par section. Rien d'Oriol ne doit rester.

Outils (dans $O) : gabarit-v8.html, assembler_v8.py, photos_site.py, recadrer.py, couleur_site.py (+ palette.py), logo_blanc.py, empreinte.py.

## Règles absolues
- Vérité : uniquement ce que l'entreprise annonce elle-même (son site, ses pages) et les données du prompt (SIRENE, Google). Aucun chiffre, nom, date, montant, certification, client ou chantier inventé. Une section sans contenu vrai est retirée en entier (avec son lien dans les menus), jamais remplie au hasard.
- Interdit : avis ou témoignages inventés, adresse mail, superlatifs invérifiables (« le meilleur », « n°1 », « leader »), tiret cadratin, emoji, nom d'un concurrent.
- La seule note affichée est la note Google réelle du prompt (« Noté X/5 sur Google, N avis »). Sans note dans le prompt, supprime le bloc <a class="note">.
- Photos : aucune photo où l'on voit une femme (même au second plan, même en partie, même floue), aucun enfant, aucune photo d'animal ou d'illustration sans rapport, aucun visuel avec un gros texte incrusté, aucune capture d'écran, aucune image floue ou pixelisée, aucun filigrane. Chaque photo n'est utilisée qu'une fois.
- Design : ne touche jamais au CSS (sauf le bloc de couleurs ci-dessous), ni au JavaScript (sauf la date d'expiration), ni à l'ordre des sections, ni aux classes. Jamais de motif de traits ou de logo en fond.
- Ton des textes : français, phrases courtes et concrètes, orientées vers l'appel et la demande de devis. Le site doit donner envie de contacter l'entreprise.

## 1. Les faits
Lis le site actuel (WebFetch : accueil, entreprise ou histoire, chaque page de service, réalisations ou références, moyens, certifications, contact, mentions légales). Note pour chaque fait la page où il est écrit. Commentaire <!-- sources : ... --> en haut du fichier.

## 2. Les photos du prospect (priorité absolue)
- python3 $O/photos_site.py <site> $D/<id>/photos-site : il parcourt le site, garde les vraies photos (700 px de large au moins, sans doublon) et fait des planches numérotées. Regarde chaque planche avec Read, puis ouvre en grand chaque photo que tu envisages.
- Pour chaque photo retenue, écris pour toi ce qu'elle montre, puis place-la dans la section dont c'est exactement le sujet (une centrale de traitement d'air dans « Ventilation », la façade dans « Questions » ou « L'entreprise », un véhicule devant un chantier dans l'appel à l'action, une équipe d'hommes dans « L'entreprise »).
- Photos de groupe (toute l'équipe devant les locaux ou les véhicules) : elles contiennent presque toujours des femmes. Regarde chaque personne une par une. S'il y a une femme, tu ne peux garder la photo que si un recadrage net la retire entièrement (aucun bras, aucune épaule, aucune silhouette au bord) et que l'image recadrée reste belle et assez grande : python3 $O/recadrer.py photo.jpg photo-recadree.jpg gauche haut droite bas (fractions de 0 à 1), puis rouvre le résultat avec Read et vérifie bord par bord. Si ce n'est pas possible, la photo est écartée, sans exception.
- Le hero prend la photo la plus forte : des gens au travail sur un vrai chantier ou une belle installation, en paysage, nette. Jamais une façade de bureaux ou un logo.
- Il manque des photos : complète avec la banque d'images du métier (les moins utilisées d'abord), puis Unsplash gratuit selon les règles de l'agent démo. Les photos du prospect passent toujours avant.
- Copie les photos choisies dans $D/<id>/img/ avec des noms parlants (hero-chantier.jpg, ventilation-toiture.jpg...).

## 3. La couleur et le logo
- python3 $O/couleur_site.py <site> $D/<id>/img/logo-client.png : remplace dans le bloc :root du gabarit les valeurs de --acc, --acc-ring, --acc-ink, --acc-txt (= acc2) et --accd par celles données. C'est la couleur dominante de leur site, elle fait la ressemblance avec leur charte. Ne touche pas aux autres couleurs.
- Logo : la barre d'en-tête est anthracite. Prends le logo SVG du site s'il existe et s'il est lisible sur fond sombre ; sinon la version claire faite par logo_blanc.py (PNG). Le symbole seul (picto), s'il existe en fichier séparé, va dans « picto » de config.json ; sinon rien.

## 4. Le contenu, section par section (longueurs maximales pour que tout tienne sur mobile)
- <title> : « Nom, métier à Ville » ; garde la balise robots noindex.
- En-tête et menu mobile : liens seulement vers les sections gardées ; téléphone réel partout (tel:+33...).
- Hero : pastille h1 « Métier(s) à Ville » (55 caractères) ; note Google si connue ; grand titre de 7 mots au plus, fort et vrai (l'année de création s'il y en a une) ; ligne des métiers (3 ou 4, séparés par <i>/</i>) ; phrase d'accroche de 140 caractères ; 4 pastilles d'atouts vrais de 32 caractères (affichées sur ordinateur).
- Pourquoi nous : pastille de contexte, titre en question, 3 cartes avec 3 vrais atouts tirés du site (bureau d'études, ancienneté, certification, dépannage rapide s'il est annoncé, entreprise familiale...), un fait clé en gras par carte. Garde les tuiles d'icône ; tu peux changer le pictogramme blanc à l'intérieur pour qu'il colle à l'atout (traits simples, même épaisseur).
- Métiers (carrousel) : une carte par service réellement proposé (4 à 8), titre de 24 caractères, photo du service ; garde la dernière carte « Votre projet n'est pas dans la liste ? ».
- L'entreprise (carte à cheval) : photo d'équipe (hommes seulement) ou de dirigeants, sinon façade ou véhicule ; nom des dirigeants seulement s'il est publié ; 3 pastilles de faits ; 2 paragraphes d'histoire de 260 caractères chacun (création, évolution, effectif s'il est publié) ; bouton téléphone.
- Zone : titre avec la ville et le département ; une phrase ; les communes citées par l'entreprise. Si elle n'en cite aucune, garde la ville seule dans le titre et retire la liste.
- Réalisations : 3 à 6 chantiers publiés par l'entreprise, avec seulement les faits écrits (lieu, année, puissance, quantités, montant). Sans référence publiée : section retirée.
- Méthode : 4 étapes adaptées au métier et aux services réellement proposés (pas d'étape « contrat d'entretien » si l'entreprise n'en propose pas). Photos de la même série si possible.
- Bureau d'études : seulement si l'entreprise en a un ou présente ses moyens (équipe, atelier, véhicules, logiciels). Chiffres seulement s'ils sont publiés. Sinon section retirée.
- Questions : 4 à 6 questions dont la réponse est écrite sur leur site ou dans les données (zone, horaires, particuliers ou professionnels, certifications, dépannage, entretien) ; photo de façade, de locaux ou d'équipe ; phrase courte en bas de photo (leur slogan s'ils en ont un, sinon leurs métiers).
- Appel à l'action : photo réelle (véhicule, chantier), « Contactez <nom> à <ville> », titre, deux boutons, 3 pastilles vraies.
- Contact : téléphone, adresse, horaires écrits en clair (« Du lundi au vendredi, de 8 h à 18 h ») ; options du formulaire = leurs services.
- Pied de page : logo, une phrase de présentation, navigation, métiers, contact, et la mention exacte « Démo Widesign : un aperçu de ce que pourrait être le site de <nom>, visible jusqu'au <date d'expiration>. Démo non cédée, reproduction interdite. » avec le lien widesign.fr.
- JavaScript : remplace la date 2026-11-30T23:59:59 par la date d'expiration du prompt.

## 5. Assembler
Écris $D/<id>/config.json : {"logo": "img/...", "nom": "...", "picto": "img/..." ou absent, "villes": [...], "note": X ou absent}. Puis python3 $O/assembler_v8.py $D/<id>/source.html $D/<id>/index.html $D/<id>/config.json. Il refuse tout jeton restant, mention Oriol, tiret cadratin, image absente : corrige et relance jusqu'à ce qu'il passe.

## 6. Regarder vraiment
Captures Playwright pleine page en mobile 390 x 844 (is_mobile) et en ordinateur 1440 x 900, après avoir fait défiler toute la page lentement (les blocs apparaissent au défilement). Ouvre-les avec Read et vérifie, sur mobile d'abord :
- l'en-tête tient sur une ligne (logo, téléphone, Devis, menu) ; si le logo est trop large, réduis sa hauteur dans l'en-tête avec un style en ligne ;
- le hero montre la photo, le titre ne déborde pas, les boutons sont en bas ;
- aucun mot de titre ne dépasse de l'écran (raccourcis le titre plutôt que de changer la taille) ;
- chaque photo illustre sa section, aucune femme, aucune photo répétée ;
- contraste lisible partout, aucune section vide, aucun texte d'Oriol.
Corrige et recapture, deux fois au plus.
