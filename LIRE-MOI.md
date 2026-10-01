# Guide d’utilisation — ClaviGo 1.2.2

## Installer sur Windows

Télécharge `ClaviGo-Setup.exe` depuis les [versions GitHub](https://github.com/myjerec/clavier-ipad-windows/releases). Ferme l’ancien compagnon, y compris son icône près de l’horloge, puis lance le Setup. Le dossier proposé est `%LOCALAPPDATA%\Programs\Clavier-iPad`. Aucun Python n’est nécessaire.

Pour la version portable, extrais tout le ZIP dans un dossier où tu peux écrire. Ne déplace pas le .exe seul : le dossier `_internal` contient les composants de la fenêtre. Conserve le dossier `private` créé après le premier lancement : il contient l’identité de ce compagnon et l’appairage. Ne lance pas simultanément les versions portable et installée sur la même adresse/port.

Le Setup se désinstalle depuis les paramètres Applications de Windows. Les données générées dans `private/` sont conservées ; supprime-les manuellement seulement si tu souhaites effacer l’identité et l’appairage.

### Mise à jour ou passage du portable au Setup

Une mise à jour dans le même dossier garde `private/`. Une installation dans un autre dossier crée une nouvelle identité. Pour conserver ton appairage lors du passage du portable au Setup, ferme les deux compagnons, copie ton propre dossier `private` vers le nouveau dossier avant de lancer l’application installée, puis garde la même adresse réseau. Sinon, refais la confiance du certificat et l’appairage. Ne copie jamais ces données dans GitHub ou un dossier partagé.

## Certificat local — première utilisation

1. Lance le compagnon : il crée un certificat pour l’adresse locale choisie.
2. Dans le dossier de l’application, trouve `private/Clavier-iPad.cer`.
3. Transfère **uniquement ce fichier .cer** sur ton iPad par un moyen de confiance, puis installe le profil de certificat dans les réglages iPadOS. Ne transfère jamais `server-key.pem`.
4. Active la confiance SSL/TLS de ce certificat dans **Réglages > Général > Informations > Réglages des certificats**. Consulte la [procédure officielle Apple](https://support.apple.com/fr-fr/102390).
5. Vérifie l’identité du certificat avec l’empreinte SHA-256 affichée dans **Réseau et détails** sur le PC. N’approuve pas un certificat reçu d’une personne inconnue.

Cette opération concerne ton certificat local. Le QR code n’effectue pas ces étapes. Si l’adresse du PC change, un nouveau certificat peut être généré : il faudra refaire cette configuration.

## Connecter l’iPad

- PC et iPad doivent être sur le même réseau local ; un Wi-Fi invité peut isoler les appareils.
- Dans le compagnon, ouvre **Réseau et détails** si la mauvaise carte réseau est sélectionnée. Choisis l’adresse Wi-Fi/Ethernet utilisée, puis Appliquer.
- Clique sur **Connecter mon iPad avec un QR code** et scanne avec l’appareil photo de l’iPad. Ouvre le lien dans Safari, ou saisis l’adresse HTTPS affichée sur le PC.
- Entre les huit chiffres affichés. Le code est valable cinq minutes, avec dix essais maximum. Si nécessaire, clique sur **Nouvel appairage**.
- Quand l’appareil est mémorisé, le compagnon affiche **iPad mémorisé**. Cela indique un appairage enregistré, pas une preuve que Safari est actuellement ouvert.

Le cookie Safari est sécurisé et renouvelé lors de l’utilisation. L’appairage survit au redémarrage du compagnon, mais aucune page web ne peut garantir une connexion éternelle : mise en veille, réseau indisponible ou données Safari effacées peuvent nécessiter une reconnexion.

## Écrire avec le clavier Apple

1. Clique dans le champ ou le document cible sur le PC.
2. Dans Safari sur l’iPad, touche la zone de saisie ou **Clavier iPad**.
3. Écris : les lettres sont envoyées directement. Les compositions attendent leur validation par iPadOS.
4. Les corrections et suggestions de l’iPad remplacent la fin du texte suivi. Elles dépendent de tes réglages clavier iPadOS.

La zone suit au maximum 2 000 caractères de cette session. Le suivi recommence automatiquement au curseur courant après un clic, un changement de fenêtre ou un raccourci, sans réécrire l’ancien texte. La zone se renouvelle aussi automatiquement avant sa limite de longueur.

Après une erreur réseau, vérifie le document avant de reprendre : l’application ne renvoie pas automatiquement les frappes dont le résultat est incertain.

## Touches et panneaux

- Active Ctrl, Alt, Maj, Win ou AltGr, puis choisis une lettre du panneau **Lettres PC** pour une combinaison. **Relâcher** désactive les modificateurs. Les compositions complexes du clavier Apple sont moins adaptées aux raccourcis.
- Fais glisser la barre d’onglets pour accéder à **Raccourcis**, **Pavé numérique**, **Applications**, **Son & musique**, **Mes boutons**, **Navigation**, **F1–F12** et **Lettres PC**.
- Les applications sont limitées à une liste fixe. Discord doit être installé à son emplacement habituel. Aucune application n’est téléchargée automatiquement.
- Le volume agit sur Windows ; les commandes musicales dépendent du lecteur actif.
- **Mes boutons** conserve jusqu’à 40 favoris, avec un nom de 40 caractères et un texte de 2 000 caractères maximum. Gérer permet de modifier/supprimer ; la dernière suppression peut être annulée. Ces favoris restent dans Safari pour cette adresse. Effacer les données du site les supprime. N’y stocke pas de mots de passe.

## Pause, masquage et arrêt

**Mettre en pause** bloque les commandes sans effacer l’appairage. **Reprendre la saisie** les réactive.

**Masquer près de l’horloge** cache la fenêtre et garde le compagnon actif. Double-clique sur l’icône clavier, éventuellement dans le menu **^**, pour le réafficher. Le clic droit propose Afficher, Masquer et Quitter.

La croix de la fenêtre et **Quitter et couper la connexion** arrêtent complètement le compagnon. **Nouvel appairage** révoque l’iPad mémorisé et demande une confirmation s’il existe déjà un appairage.

## Dépannage

| Problème | À vérifier |
|---|---|
| Safari n’ouvre pas la page | Même réseau, bonne adresse, PC allumé, compagnon lancé ; absence d’isolation du Wi-Fi invité |
| Erreur de certificat | Installation et confiance du certificat de ce PC ; adresse inchangée |
| Page accessible, code refusé | Code actuel à huit chiffres ; cinq minutes non dépassées ; Nouvel appairage si nécessaire |
| Port déjà utilisé | Fermer l’autre compagnon, y compris sa version masquée ; ne lancer qu’une instance |
| Connexion bloquée par Windows | Autoriser le compagnon uniquement sur ton réseau privé ; limiter la règle TCP 18443 au réseau local |
| Les lettres n’arrivent pas | Compagnon non pausé, cible PC sélectionnée, aucune fenêtre administrateur/UAC, puis continue à écrire |
| Le texte ne correspond plus | Arrêter la saisie, corriger sur le PC, reprendre la saisie |
| L’iPad redemande un code | Données Safari effacées, adresse ou certificat changé, appareil révoqué, autre installation du compagnon |
| Icône introuvable | Regarder dans ^ près de l’horloge ; si l’application a été quittée, la relancer |

Aucune règle du routeur n’est nécessaire. Ne redirige pas le port sur Internet. Le Setup ne modifie pas automatiquement le pare-feu.

## Limites connues

Pas de Ctrl+Alt+Suppr, de contrôle de l’écran verrouillé, de fenêtre UAC, d’application administrateur ou de maintien de touches pour les jeux. Le compagnon s’exécute dans ta session utilisateur, ce n’est pas un service système Windows.

La suppression automatique d’emoji, caractères combinés, tabulations ou sauts de ligne peut être arrêtée, car leur effacement varie selon l’application cible. Les éditeurs qui réécrivent eux-mêmes le texte peuvent désynchroniser les corrections. Corrige ces situations sur le PC puis continue à écrire.

La version native iOS est un projet source non compilé : pas d’IPA, pas de TestFlight et pas d’App Store. La version utilisable sur iPad est actuellement celle de Safari. macOS reste une évolution possible, non implémentée.

## Presse-papiers iPad ↔ PC (1.2.0)

Dans l’onglet Presse-papiers, **iPad → PC** lit le texte copié sur l’iPad et le place dans le presse-papiers Windows. **PC → iPad** fait l’inverse. Le transfert remplace le texte du presse-papiers de destination ; il ne colle pas automatiquement dans un document. Limite : texte brut de 2 000 caractères, sans images ni fichiers, sans historique ni stockage de ce texte par l’application.

Safari peut demander une autorisation ou un geste Coller. Si l’accès direct est refusé, colle le texte dans la zone du panneau puis utilise les boutons de copie. Pour recevoir depuis le PC, le texte est également placé dans cette zone. Aucun échange n’a lieu en arrière-plan. [Règles du presse-papiers Safari](https://webkit.org/blog/10855/async-clipboard-api/).

La saisie est toujours automatique après appairage, sans option Direct ni bouton Reprendre. iPadOS peut encore imposer de toucher le champ pour afficher son clavier Apple : une page web ne peut pas forcer son ouverture sans interaction. Après une erreur réseau, les caractères au résultat incertain ne sont pas renvoyés : vérifie le document avant de continuer.

## Nouveau nom ClaviGo

Le programme est désormais ClaviGo.exe et le raccourci ClaviGo. Le dossier d’installation historique Clavier-iPad est conservé pour préserver les données locales ; c’est normal. Le dépôt GitHub garde son adresse existante.
