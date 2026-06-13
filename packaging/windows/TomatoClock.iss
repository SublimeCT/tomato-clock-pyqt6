#define AppName "TomatoClock"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "dist\TomatoClock"
#endif

[Setup]
AppId={{7A2811A8-D4D7-4B59-A4E8-EB1A0A630D3D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=SublimeCT
AppPublisherURL=https://github.com/SublimeCT/tomato-clock-pyqt6
AppSupportURL=https://github.com/SublimeCT/tomato-clock-pyqt6/issues
AppUpdatesURL=https://github.com/SublimeCT/tomato-clock-pyqt6/releases
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=TomatoClock-Setup-{#AppVersion}-Windows
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\TomatoClock.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\TomatoClock.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\TomatoClock.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TomatoClock.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
