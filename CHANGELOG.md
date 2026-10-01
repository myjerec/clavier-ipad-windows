# Historique

## 1.2.1 — 1 octobre 2026

- Nouvelle icône fournie par le créateur du projet : programme Windows, fenêtre, zone de notification et Setup.
- Icône Safari et écran d’accueil iPad. Le nom Clavier iPad reste inchangé.


## 1.2.0 — 1 octobre 2026

- Saisie toujours directe, sans boutons Reprendre ici, Direct ou Synchroniser.
- Reprise automatique après raccourci/changement de cible, sans réécriture de l’ancien texte.
- Presse-papiers texte iPad ↔ PC, sur action explicite, avec zone de secours Safari.
- Échanges authentifiés et limités à 2 000 caractères ; aucun historique.


## 1.1.1 — 28 septembre 2026

- Correction du démarrage « Can’t find a usable init.tcl » : Tcl/Tk est installé dans `_internal` à côté du programme, sans extraction temporaire du .exe.
- Le Setup et le ZIP portable contiennent désormais le dossier complet. Le .exe ne doit plus être déplacé seul.
- L’autodiagnostic vérifie aussi la création réelle d’une fenêtre Tk.

## 1.1.0 — 28 septembre 2026

Première publication GitHub regroupant les travaux du prototype :

- clavier Apple dans Safari, saisie directe et corrections ;
- touches PC, raccourcis, pavé numérique, applications, multimédia et favoris ;
- appairage mémorisé et connexion HTTPS locale ;
- compagnon Windows sombre, QR code et état de connexion ;
- masquage dans la zone de notification et restauration ;
- exécutable autonome et installateur français ;
- documentation, licence MIT et sources iOS expérimentales.

Les anciennes mentions V1.2 dans les notes de développement désignaient une itération du prototype ; la première version publiée utilise le numéro 1.1.0 de l’installateur.
