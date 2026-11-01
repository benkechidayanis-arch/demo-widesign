# Modèle de démo v9 : guide de construction

Le modèle v9 a été validé par Yanis sur la démo Oriol (« effet wow, moderne, un site vendable 1 500 € »). Chaque démo doit sortir au même niveau : même structure, même design, mêmes animations, mais tout le contenu, les photos, le logo et la couleur sont ceux du prospect. Le fichier gabarit-v9.html est la démo Oriol écrite avec des jetons (LOGO_CLIENT, PICTO_GRAND, PICTO_SMALL, CHK, TICK, PHONE, CLOCK, PIN, STARS, CARTE_SVG, CITYROWS, PLACE_ID, AVIS_CLE) : c'est l'exemple à suivre, section par section. Rien d'Oriol ni de MATCH ne doit rester.

Principe du modèle : un seul moment sombre (le hero), puis du blanc et du crème, de grandes photos, des grilles plutôt que des carrousels, des chiffres géants, une barre d'appel collée en bas sur mobile. La page est pensée d'abord pour le téléphone.

Outils (dans $O) : gabarit-v9.html, assembler_v9.py, photos_site.py, recadrer.py, couleur_site.py (+ palette.py), logo_blanc.py, carte_ville.py, empreinte.py.

## Règles absolues
- Vérité : uniquement ce que l'entreprise annonce elle-même (son site, ses pages) et les données du prompt (SIRENE, Google). Aucun chiffre, nom, date, montant, certification, client ou chantier inventé. Une section sans contenu vrai est retirée en entier (avec ses liens dans le menu, le menu mobile et le pied de page), jamais remplie au hasard.
- Interdit : avis ou témoignages écrits à la main, adresse mail, superlatifs invérifiables (« le meilleur », « n°1 », « leader »), tiret cadratin, emoji, nom d'un concurrent.
- Avis : jamais de texte d'avis dans le fichier. La section « Avis clients » charge les vrais avis Google en direct à chaque visite (règles de Google) ; la liste <ul class="avs" id="avs"> reste vide dans le source.
- La seule note affichée est la note Google réelle du prompt. Sans note dans le prompt, supprime le bloc <a class="note"> du hero et la section avis.
- Photos : aucune photo où l'on voit une femme (même au second plan, même en partie, même floue), aucun enfant, aucune photo d'animal ou d'illustration sans rapport, aucun visuel avec un gros texte incrusté, aucune capture d'écran, aucune image floue ou pixelisée, aucun filigrane. Chaque photo n'est utilisée qu'une fois, sauf dans la bande de photos qui défile (elle reprend des photos déjà placées).
- Design : ne touche jamais au CSS (sauf le bloc de couleurs ci-dessous), ni au JavaScript (sauf la date d'expiration), ni à l'ordre des sections, ni aux classes. Les attributs data-gif servent au GIF avant/après : garde-les sur les sections gardées.
- Ton : français, phrases courtes et concrètes, orientées vers l'appel et la demande de devis.

## 1. Les faits
Lis le site actuel (WebFetch : accueil, entreprise ou histoire, chaque page de service, réalisations ou références, moyens, certifications, contact, mentions légales). Note pour chaque fait la page où il est écrit. Commentaire <!-- sources : ... --> en haut du fichier.

## 2. Les photos du prospect (priorité absolue)
- python3 $O/photos_site.py <site> $D/<id>/photos-site : il garde les vraies photos (700 px de large au moins, sans doublon) et fait des planches numérotées. Regarde chaque planche avec Read, puis ouvre en grand chaque photo envisagée.
- Pour chaque photo retenue, écris ce qu'elle montre, puis place-la dans la section dont c'est exactement le sujet.
- Photos de groupe : regarde chaque personne. S'il y a une femme, recadrage net seulement s'il la retire entièrement et que l'image reste belle (python3 $O/recadrer.py photo.jpg photo-recadree.jpg gauche haut droite bas), rouvre le résultat et vérifie bord par bord ; sinon la photo est écartée.
- Le hero prend la photo la plus forte : des gens au travail sur un vrai chantier ou une belle installation, en paysage, nette. Jamais une façade ou un logo.
- Le modèle demande beaucoup de photos (environ 20). Il manque des photos : banque du métier (les moins utilisées d'abord), puis Unsplash gratuit selon les règles de l'agent démo. Les photos du prospect passent toujours avant.
- Copie les photos dans $D/<id>/img/ avec des noms parlants.

## 3. La couleur et le logo
- python3 $O/couleur_site.py <site> $D/<id>/img/logo-client.png : remplace dans le bloc :root du gabarit les valeurs de --acc, --acc-ring, --acc-ink, --acc-txt (= acc2) et --accd par celles données. Ne touche pas aux autres couleurs.
- Logo : la barre d'en-tête est anthracite. Logo SVG du site s'il est lisible sur fond sombre, sinon la version claire faite par logo_blanc.py (PNG). Le symbole seul (picto), s'il existe en fichier séparé, va dans « picto » de config.json : il sert au grand symbole de la section de marque et au centre du sceau tournant. Sinon rien.

## 4. Le contenu, section par section (longueurs maximales pour que tout tienne sur mobile)
- <title> : « Nom, métier à Ville » ; garde la balise robots noindex.
- En-tête, menu mobile, pied de page : liens seulement vers les sections gardées ; téléphone réel partout (tel:+33...).
- Hero : pastille h1 « Métier(s) à Ville » (55 caractères) ; note Google réelle (« Noté X/5 sur Google, N avis ») ; grand titre de 7 mots au plus, fort et vrai ; ligne des métiers (3 ou 4, séparés par <i>/</i>) ; accroche de 140 caractères ; 4 pastilles d'atouts vrais de 32 caractères (escalier, ordinateur).
- Bandeau qui défile sous le hero : 5 ou 6 certifications et engagements vrais (32 caractères). Pas de note Google ici (elle est déjà dans le hero). Moins de 4 éléments vrais : retire la section .proofs.
- Chiffres (carte arrondie) : 4 chiffres publiés (année de création, effectif, puissance, nombre de chantiers ou d'interventions, ancienneté...) avec une légende de 30 caractères. data-n = le nombre ; data-brut="1" et data-from pour une année. Avec 2 chiffres vrais seulement, garde 2 blocs ; avec moins, retire la section.
- Métiers (mosaïque) : 6 cartes photo numérotées 01 à 06 dans l'ordre des classes du gabarit (big, tall, normale, normale, wide, normale) + la carte de couleur « Un autre projet ? ». La carte big et la carte wide ont un sous-titre de 45 caractères. Titre de carte de 24 caractères. Si l'entreprise a moins de 6 métiers, découpe ses vraies prestations (installation, entretien, dépannage d'un même métier) ; jamais de métier inventé. Titre de section adapté (« Six métiers, une seule équipe » seulement si c'est vrai).
- Réalisations (cartes empilées) : 3 à 5 chantiers publiés, avec seulement les faits écrits (lieu, année, puissance, quantités, montant en étiquette de couleur s'il est publié). Compteur « 01 / 0N » juste. Sans référence publiée : section retirée.
- Section de marque (fond de couleur) : la promesse la plus forte et vraie de l'entreprise (bureau d'études, dépannage rapide annoncé, entreprise familiale, fabrication maison...) : pastille, titre de 6 à 8 mots dont la fin en <em>, 3 puces vraies de 60 caractères, bouton, une photo qui montre exactement cette promesse.
- Bande de photos qui défile : 6 photos de chantiers ou d'installations du prospect (les mêmes 6 dans les deux rangées du gabarit). Moins de 6 photos du prospect : retire la section .strip (pas de photo de banque ici).
- Avis clients : garde la section telle quelle si le prompt donne une note Google d'au moins 4 et au moins 3 avis. Mets la note réelle dans .score (« X/5 », « N avis sur Google »). Ne touche pas au script : il affiche en direct jusqu'à 4 vrais avis de 4 ou 5 étoiles et retire la section s'il en trouve moins de 2. Sinon retire la section.
- L'entreprise (collage) : sceau tournant avec un texte vrai en capitales de 36 caractères terminé par « · » (« ENTREPRISE FAMILIALE · DEPUIS 1943 · ») ; grande photo des dirigeants ou d'une équipe d'hommes (sinon véhicule ou chantier), prénoms seulement s'ils sont publiés dans .tagn, une pastille vraie ; petite photo de chantier ; titre ; un paragraphe de 230 caractères ; frise de 3 ou 4 dates publiées (moins de 3 dates : retire la frise).
- Méthode : 4 étapes adaptées au métier et aux services réellement proposés, chacune avec sa photo (la même série si possible), titre de 30 caractères, phrase de 100 caractères.
- Zone : titre avec la ville et le département, une phrase. Carte : trouve la commune avec https://geo.api.gouv.fr/communes?nom=<ville>&fields=code,codeEpci,centre&format=json (bon département), télécharge les contours autour d'elle (environ 0,35 degré de chaque côté) : https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=ADMINEXPRESS-COG-CARTO.LATEST:commune&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326&BBOX=<lon_min>,<lat_min>,<lon_max>,<lat_max>,EPSG:4326 dans $D/<id>/communes.json, puis python3 $O/carte_ville.py communes.json <code INSEE> <code EPCI> $D/<id>/carte.svg. Étiquette .lab : le nom de la ville, avec style="left:L%;top:T%" où L = cx/9 + 4 et T = cy/9 - 4 (cx et cy du cercle r="6" du SVG). Légende .leg : « Siège » + la rue réelle. Si l'IGN ne répond pas, retire le bloc <div class="mapv">...</div> et garde les villes. « villes » de config.json : les communes citées par l'entreprise (aucune : liste vide, l'assembleur retire le bandeau ; moins de 6 : une ligne fixe ; 6 et plus : lignes qui défilent).
- Questions : 4 à 6 questions dont la réponse est écrite sur leur site ou dans les données (zone, horaires, particuliers ou professionnels, certifications, dépannage, entretien).
- Appel à l'action (.fin) : photo réelle (véhicule, chantier), « Contactez <nom> à <ville> », titre, deux boutons, 3 pastilles vraies.
- Contact : trois blocs (téléphone, adresse avec lien Google Maps de recherche, horaires écrits en clair) ; options du formulaire = leurs services.
- Pied de page : logo, une phrase de présentation, navigation, métiers, contact, et la mention exacte « Démo Widesign : un aperçu de ce que pourrait être le site de <nom>, visible jusqu'au <date d'expiration>. Démo non cédée, reproduction interdite. » avec le lien widesign.fr.
- JavaScript : remplace la date 2026-11-30T23:59:59 par la date d'expiration du prompt.

## 5. Assembler
Écris $D/<id>/config.json : {"logo": "img/...", "nom": "...", "picto": "img/..." ou absent, "villes": [...], "carte": "carte.svg" ou absent, "note": X ou absent, "place_id": "<id de la démo>", "avis_cle": "<champ google_avis_cle de reglages/moteur, ou vide>"}. Puis python3 $O/assembler_v9.py $D/<id>/source.html $D/<id>/index.html $D/<id>/config.json. Il refuse tout jeton restant, mention Oriol ou MATCH, tiret cadratin, image absente, avis écrit en dur : corrige et relance jusqu'à ce qu'il passe. Il retire lui-même la section avis s'il n'y a pas de clé. La clé des avis est une clé publique limitée au domaine des démos : elle est faite pour être dans la page.

## 6. Regarder vraiment
Captures Playwright pleine page en mobile 390 x 844 (is_mobile) et en ordinateur 1440 x 900, après avoir fait défiler toute la page lentement (les blocs apparaissent au défilement). En local, la section avis disparaît (Google refuse les pages hors du domaine des démos) : c'est normal ; elle se vérifie sur la démo en ligne. Ouvre les captures avec Read et vérifie, sur mobile d'abord :
- l'en-tête tient sur une ligne (logo, téléphone, Devis, menu) ; si le logo est trop large, réduis sa hauteur dans l'en-tête avec un style en ligne ;
- le hero montre la photo, le titre ne déborde pas, les boutons sont en bas ;
- aucun mot de titre ne dépasse de l'écran (raccourcis le titre plutôt que de changer la taille) ;
- la mosaïque des métiers n'a pas de trou, chaque carte a sa photo ;
- chaque photo illustre sa section, aucune femme, aucune photo répétée hors de la bande qui défile ;
- contraste lisible partout, aucune section vide, aucun texte d'Oriol.
Corrige et recapture, deux fois au plus. Après la mise en ligne, capture « <url>?moi » en mobile, descends jusqu'à la section avis et vérifie qu'elle affiche de vrais avis ou qu'elle a disparu proprement.
