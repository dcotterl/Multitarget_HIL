#define MyAppName "RDMA GUI"
#define MyAppVersion "1.0.0"
#define MyAppExeName "RDMA_GUI.exe"

[Setup]
AppId={{A5A5C7DB-7C30-4B9B-9FC8-0A18D7B3A7F1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\RDMA GUI
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=RDMA_GUI_Setup
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