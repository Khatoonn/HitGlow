; Script Inno Setup pour HitGlow — installeur Windows sans droits admin.
; Compilation : ISCC.exe installer\HitGlow.iss  (depuis la racine du projet,
; ou "iscc installer\HitGlow.iss" si ISCC.exe est dans le PATH)
; Prerequis : dist\HitGlow.exe doit deja exister (voir README, section Build).

#define MyAppName "HitGlow"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "Khatoonn"
#define MyAppURL "https://github.com/Khatoonn/HitGlow"
#define MyAppExeName "HitGlow.exe"

[Setup]
AppId={{E3E8953D-569B-4BD4-BFE9-CF4CBBE2C575}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Installation par utilisateur, sans necessiter les droits administrateur.
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=HitGlow-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis supplementaires :"; Flags: unchecked

[Files]
Source: "..\dist\HitGlow.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent
