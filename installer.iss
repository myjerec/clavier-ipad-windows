; Build with ISCC.exe installer.iss. Only the public executable and guide are packaged.
#ifndef AppExe
  #define AppExe "dist\Clavier-iPad\Clavier-iPad.exe"
#endif
#ifndef SetupOutput
  #define SetupOutput "dist"
#endif
[Setup]
AppId={{E90241F3-A25C-4B3A-9DA5-67152DEB40B1}
AppName=Clavier iPad
AppVersion=1.2.1
AppPublisher=Clavier iPad
DefaultDirName={localappdata}\Programs\Clavier-iPad
DefaultGroupName=Clavier iPad
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#SetupOutput}
OutputBaseFilename=Clavier-iPad-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=app-icon.ico
UninstallDisplayIcon={app}\Clavier-iPad.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Clavier-iPad\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LIRE-MOI.md"; DestDir: "{app}"; Flags: ignoreversion

Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "third_party\*"; DestDir: "{app}\third_party"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Clavier iPad"; Filename: "{app}\Clavier-iPad.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Clavier iPad"; Filename: "{app}\Clavier-iPad.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Clavier-iPad.exe"; Description: "Lancer Clavier iPad"; Flags: nowait postinstall skipifsilent

; The private folder is generated locally by the app and preserved on update/uninstall.
