#define MyAppName "DSF GUI"
#define MyAppVersion "1.0.0"
#define MyAppExeName "DSF_GUI.exe"

[Setup]
AppId={{A5A5C7DB-7C30-4B9B-9FC8-0A18D7B3A7F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\DSF GUI
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=DSF_GUI_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent