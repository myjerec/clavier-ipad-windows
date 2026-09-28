# Développer et compiler

## Prérequis

Windows x64, Python 3.11 ou plus récent avec Tcl/Tk, Git, Node.js pour les tests JavaScript. La compilation publiée a été réalisée avec Python 3.11, PyInstaller 6.22.3 et Inno Setup 6.7.3. Les versions des bibliothèques du binaire sont indiquées dans THIRD_PARTY_NOTICES.md.

```powershell
git clone https://github.com/myjerec/clavier-ipad-windows.git
cd clavier-ipad-windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python companion.py --start
```

`DEMARRER.bat` constitue une alternative : il vérifie les dépendances, les installe si nécessaire puis lance le compagnon. Internet est nécessaire à leur téléchargement, pas à la saisie locale.

## Tests

```powershell
python -m unittest -v test_companion.py
node test_native.js
node test_extras.js
```

Les tests du protocole utilisent un récepteur simulé pour ne pas taper dans les fenêtres ouvertes. Un test ne certifie pas le comportement tactile de Safari.

## Construire le .exe

```powershell
.\CONSTRUIRE_EXE.ps1
```

Résultat : `dist/Clavier-iPad/Clavier-iPad.exe`, avec l’interface web, Tcl/Tk, cryptographie, QR code et icône de notification dans le dossier `_internal` adjacent. Distribuer le dossier complet. Ne lance pas le binaire cible pendant sa reconstruction. Le script installe PyInstaller et les dépendances dans l’environnement Python actif ; utilise de préférence l’environnement virtuel.

Pour vérifier le binaire sans saisir de touches :

```powershell
$p = Start-Process .\dist\Clavier-iPad\Clavier-iPad.exe -ArgumentList '--self-test', "$PWD\dist\self-test.json" -Wait -PassThru
Get-Content .\dist\self-test.json
```

Attendre `ok: true`. Cette vérification initialise une vraie fenêtre Tk puis couvre TLS, les ressources intégrées, l’authentification et la persistance d’appairage.

## Construire le Setup

Installe le compilateur [Inno Setup](https://jrsoftware.org/), puis compile avec [ISCC](https://jrsoftware.org/ishelp/topic_compilercmdline.htm) :

```powershell
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' .\installer.iss
```

Adapte le chemin si Inno Setup est installé ailleurs. Résultat : `dist/Clavier-iPad-Setup.exe`. Le script n’intègre que l’exécutable, le guide et les licences, jamais `private/`.

Les notices de `third_party/` correspondent au binaire publié : actualise-les si tu changes les dépendances. Les contraintes de requirements.txt ne verrouillent pas toutes les dépendances transitives ; la compilation n’est pas garantie identique octet par octet.

## Publier une nouvelle version

1. Mettre à jour AppVersion dans installer.iss, CHANGELOG et les guides.
2. Lancer les tests, compiler, vérifier le binaire puis tester installation/désinstallation dans un dossier séparé.
3. Vérifier masquage/restauration et HTTPS pendant le masquage ; tester la saisie réelle avec un document sans importance.
4. Contrôler les fichiers suivis : aucun private/, certificat, clé, jeton, donnée utilisateur ou chemin personnel.
5. Publier les binaires dans une GitHub Release, pas dans l’historique Git. Fournir le ZIP portable avec licences et SHA256SUMS.txt.

## Organisation

`companion.py` : serveur, appairage, commandes et injection Windows. `companion_ui.py` : fenêtre, QR et icône. `index.html`, `style.css`, `app.js`, `extras.js`, `native-draft.js` : interface Safari. `packaging_check.py` : autodiagnostic du binaire. `ios/` : sources expérimentales SwiftUI/UIKit.
