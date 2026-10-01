# Validation de la publication 1.1.0

## Vérifié sur Windows

- 10 tests Python : protocole HTTPS, appairage et révocation persistants, refus de jetons/commandes invalides, saisie différentielle et garde de cible, applications autorisées et multimédia simulés.
- Suites JavaScript test_native.js et test_extras.js : saisie/composition et commandes/favoris avec doubles de test.
- Véritable injection Windows dans une fenêtre de test lors du développement : B → Bonjor → Bonjour → Bonjour été → Bonjour ét, avec comparaison du résultat.
- Interface du compagnon observée dans le .exe : mise en page, appairage mémorisé et fenêtre QR.
- Test de fenêtre réelle : icône visible, masquage, requête HTTPS réussie pendant le masquage, restauration par l’action par défaut de l’icône et arrêt propre.
- Autodiagnostic du .exe empaqueté : ressources intégrées, certificat/TLS vérifié, authentification, saisie simulée et appairage persistant.
- Setup : installation dans un dossier isolé, comparaison du hash de l’exécutable installé, entrée de désinstallation, autodiagnostic et désinstallation.

## Restant à valider

Scan avec un iPad physique, prédictions selon langue et version iPadOS, toutes les combinaisons et lecteurs multimédia, comportement dans chaque éditeur, changements d’adresse, veille et reconnexion dans plusieurs réseaux. L’usage de base a été confirmé pendant le développement, sans constituer une campagne exhaustive sur appareils.

Le projet iOS natif n’a pas été compilé sur Mac ni testé sur iPad. Pas de binaire iOS fourni. Les exécutables Windows ne sont pas signés par un certificat d’éditeur. Aucun audit indépendant de sécurité n’a été réalisé.

## Correctif 1.1.1

Le test de la version 1.1.0 n’initialisait pas Tk et ne détectait donc pas l’erreur init.tcl signalée. L’autodiagnostic du correctif crée et ferme maintenant une vraie fenêtre avant de tester HTTPS.

## Version 1.2.0

12 tests Python et suites JavaScript réussis : reprise automatique sans suppression sur une nouvelle cible, transferts presse-papiers HTTPS authentifiés et limites, boutons de transfert et copie de secours. Aller-retour réel dans le presse-papiers Windows avec accents/emoji/retour à la ligne réussi ; texte précédent restauré. Le fonctionnement physique des autorisations Safari et du clavier Apple reste à essayer sur iPad.
