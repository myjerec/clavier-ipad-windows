# Historique

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
