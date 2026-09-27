# Clavier PC — projet natif iPad (iOS 17+)

**Sources initiales, non compilées et non testées sur iPad. Aucun IPA installable n’est fourni.**

Application SwiftUI/UIKit, pas une page Safari encapsulée. Elle utilise le compagnon Windows existant et conserve le clavier Apple, ses prédictions et ses compositions.

Inclus : saisie directe, Ctrl/Alt/Maj/Windows, raccourcis, pavé de chiffres, navigation/F1–F12, applications autorisées, touches multimédia, création de phrases et de raccourcis favoris. Les favoris sont propres à cette application ; ils ne sont pas importés de Safari. Appui prolongé sur un favori pour le supprimer. La modification/réorganisation de favoris et une icône définitive restent à ajouter avant diffusion.

## Depuis Windows aujourd’hui

Conserver ces sources et continuer à utiliser la version web fonctionnelle. Aucun logiciel Apple ni compte payant n’a été installé ou acheté. Le compagnon Windows n’a pas été modifié pour ce projet.

## Sur un Mac plus tard

1. Installer Xcode depuis Apple, l’ouvrir une fois et installer les composants iOS.
2. Installer [XcodeGen](https://github.com/yonaskolb/XcodeGen) selon son guide officiel (`brew install xcodegen` si Homebrew est déjà installé).
3. Dans ce dossier : `xcodegen generate` puis ouvrir `ClavierIPad.xcodeproj`.
4. Dans Signing & Capabilities, choisir ton équipe Apple et remplacer `com.example.clavieripad` par ton identifiant unique.
5. Sélectionner un iPad connecté au Mac, puis compiler et lancer. Corriger les erreurs éventuelles de compilation avant toute distribution : ce projet n’a pas pu être compilé sur Windows.
6. Autoriser l’accès au réseau local lors de la demande iPadOS.

## Connexion au PC

Le compagnon doit être la version avec appairage mémorisé, applications et multimédia. PC et iPad sont sur le même réseau.

- Installer sur l’iPad le certificat `Clavier-iPad.cer` du compagnon, puis activer sa confiance SSL dans les réglages. Ne jamais transférer la clé privée. L’application utilise la validation TLS normale, sans exception de certificat.
- Dans l’application : Connexion → adresse HTTPS affichée sur le PC.
- Safari et l’application native n’ont pas le même stockage. Pour passer à l’application, renouveler le code sur le PC puis l’entrer dans l’application. Cela révoque la session Safari puisque le compagnon n’accepte qu’un appareil/appairage actif.
- Le jeton est conservé dans le trousseau iOS, accessible uniquement lorsque l’appareil est déverrouillé et non transférable à un autre appareil. Les favoris sont conservés dans les préférences locales.
- Sélectionner un champ sur le PC, puis toucher la zone de saisie de l’application. Après un raccourci, un retour depuis l’arrière-plan ou un changement de cible, toucher Reprendre ici.
- Les frappes incertaines ne sont pas automatiquement renvoyées. L’application n’agit pas en arrière-plan.

## Vérification à faire sur Mac / iPad

- Compiler avec le SDK iOS de Xcode, résoudre tout avertissement de concurrence/signature.
- Vérifier permission LAN, certificat, appairage et restauration du trousseau après fermeture.
- Tester lettres, accents, autocorrection, composition/dictée, focus du clavier après les boutons et changements d’orientation.
- Tester tous les panneaux, un favori texte et Ctrl+C/Coller dans un document de test.
- Débrancher le réseau pendant une frappe : aucun doublon après reconnexion.
- Avant TestFlight/App Store : icône, licence, politique de confidentialité, tests appareils, signature et compte développeur approprié.

GitHub et l’App Store sont deux publications distinctes. Ces sources sont publiées avec le projet Windows, mais ne constituent pas une version signée ou publiée sur l’App Store.

Références : [Xcode](https://developer.apple.com/xcode/), [accès au réseau local](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy), [XcodeGen](https://github.com/yonaskolb/XcodeGen).
