$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'Installation des outils impossible' }
$clavierBuild = @('--clean','--noconfirm','--onedir','--windowed','--name','Clavier-iPad')
foreach ($clavierAsset in @('index.html','app.js','style.css','native-draft.js','extras.js')) {
    $clavierBuild += @('--add-data', "$clavierAsset;.")
}
$clavierBuild += 'companion.py'
python -m PyInstaller @clavierBuild
if ($LASTEXITCODE -ne 0) { throw 'Compilation impossible' }
Write-Host 'Exécutable créé : dist\Clavier-iPad\Clavier-iPad.exe'
