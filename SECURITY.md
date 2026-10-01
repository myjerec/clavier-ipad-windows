# Sécurité et données locales

## Périmètre

Projet destiné à un réseau local de confiance, pas à une exposition Internet. HTTPS avec certificat propre au PC, code d’appairage de cinq minutes et dix essais maximum, un appareil appairé à la fois. Les commandes vérifient le jeton, l’adresse locale, Host et Origin. TLS 1.2 minimum.

Le Setup n’ouvre pas de port sur le routeur et ne modifie pas le pare-feu. Ne pas publier de tunnel ni de redirection Internet vers ce serveur. Le QR contient uniquement l’adresse locale ; il ne contient pas le jeton ni le code.

## Données

- PC : certificat, clé privée, empreinte du jeton et choix réseau dans private/, à côté de l’exécutable. Ces fichiers restent sur le PC et sont préservés par les mises à jour dans le même dossier.
- Safari : cookie Secure/HttpOnly/SameSite Strict, durée renouvelée d’un an, et favoris locaux. La suppression des données du site les efface.
- Le texte traverse le réseau local pour être envoyé à Windows. Le compagnon ne journalise pas le contenu saisi ; ses gardes conservent un compteur d’activité physique et l’état nécessaire au suivi de saisie.
- Aucune télémétrie applicative ni compte distant n’est requis. Le bouton Navigateur ouvre Google dans le navigateur du PC ; les applications tierces ont leurs propres communications réseau.

Ne partage jamais private/, server-key.pem, pairing.json ou un cookie. Le seul certificat à transférer volontairement sur ton propre iPad est Clavier-iPad.cer. La licence publique du code n’autorise aucun accès à tes appareils.

## Limites

L’application injecte des touches dans la fenêtre active de la session utilisateur : elle ne doit pas être exécutée en administrateur. Un appareil appairé peut agir sur les applications de cette session. Révoque son accès avec Nouvel appairage s’il est perdu ou partagé.

Ce projet n’a pas subi d’audit indépendant. Les tests automatisés et vérifications locales ne garantissent pas l’absence de vulnérabilité.

## Signalement

Ne publie pas de clés, cookies, certificats privés ou documents personnels dans les issues. Pour une faille exploitable, utilise le signalement privé GitHub s’il est disponible ; sinon ouvre uniquement une demande de contact sans détail d’exploitation ni donnée sensible.

## Presse-papiers

Les commandes clipboard read/write exigent le même appairage, le contrôle d’origine et un compagnon non pausé. Transferts explicites de texte brut uniquement, limités à 2 000 caractères. Pas de surveillance ni d’historique. Le panneau affiche le texte reçu en mémoire pendant l’utilisation ; il n’est pas conservé dans localStorage.
