; op4 kurulum betiği (Inno Setup 6). UTF-8 (BOM'lu) kaydedilmelidir; Türkçe metinler için gereklidir.
; Derleme (CI):  ISCC.exe /DSurum=0.0.1 /DPaket=<paket> /DCikti=<çıktı> [/DSihirbaz=<klasör>] op4\kurulum\op4.iss
; Paket klasörü: op4.exe, kimlik\, python\ (gömülü CPython + numpy/sympy), motor\ (hesap motoru .py + .pyc).
; Sürüm X.Y.Z: CI'da "op4-vX.Y.Z" etiketinden, etiketsiz derlemede op4/CMakeLists.txt OP4_TABAN_SURUM'dan gelir.
; Çıktı: op4-setup-<sürüm>.exe.
; Sihirbaz: op4/araclar/kimlik_uret.py --sihirbaz <klasör> ile Opus Fortis kimliğinden üretilen BMP'ler (yedi DPI
; ölçeği); verilmezse kurulum aracının varsayılan görselleri kullanılır.

#ifndef Surum
  #define Surum "0.0.1"
#endif
#ifndef Paket
  #define Paket "..\..\paket"
#endif
#ifndef Cikti
  #define Cikti "..\..\dagitim"
#endif
#ifndef Simge
  #define Simge "..\kimlik\op4_simge_placeholder.ico"
#endif

[Setup]
AppId={{6F2B9C4E-0D3A-4E7B-9C1F-0A4D5E6B7C81}
AppName=op4
AppVersion={#Surum}
AppVerName=op4 {#Surum}
AppPublisher=Opus Fortis
AppCopyright=Opus Fortis
VersionInfoVersion={#Surum}.0
VersionInfoCompany=Opus Fortis
VersionInfoDescription=op4 kurulumu
VersionInfoProductName=op4
DefaultDirName={autopf}\Opus Fortis\op4
DefaultGroupName=Opus Fortis
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\op4.exe
UninstallDisplayName=op4 {#Surum}
OutputDir={#Cikti}
OutputBaseFilename=op4-setup-{#Surum}
SetupIconFile={#Simge}
WizardStyle=modern
; Karşılama sayfası açık: sol paneldeki kimlik görseli kurulumun başında görünür.
DisableWelcomePage=no
#ifdef Sihirbaz
WizardImageFile={#Sihirbaz}\sihirbaz-buyuk-100.bmp,{#Sihirbaz}\sihirbaz-buyuk-125.bmp,{#Sihirbaz}\sihirbaz-buyuk-150.bmp,{#Sihirbaz}\sihirbaz-buyuk-175.bmp,{#Sihirbaz}\sihirbaz-buyuk-200.bmp,{#Sihirbaz}\sihirbaz-buyuk-225.bmp,{#Sihirbaz}\sihirbaz-buyuk-250.bmp
WizardSmallImageFile={#Sihirbaz}\sihirbaz-kucuk-100.bmp,{#Sihirbaz}\sihirbaz-kucuk-125.bmp,{#Sihirbaz}\sihirbaz-kucuk-150.bmp,{#Sihirbaz}\sihirbaz-kucuk-175.bmp,{#Sihirbaz}\sihirbaz-kucuk-200.bmp,{#Sihirbaz}\sihirbaz-kucuk-225.bmp,{#Sihirbaz}\sihirbaz-kucuk-250.bmp
#endif
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Yönetici değilse kullanıcıya özel kurulum seçilebilir (%LOCALAPPDATA%\Programs).
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
; DirectX 12 + PerMonitorV2: Windows 10 1809 ve sonrası.
MinVersion=10.0.17763
ChangesAssociations=yes
CloseApplications=yes

[Languages]
Name: "turkce"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ingilizce"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "masaustu"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek kısayollar:"; Flags: unchecked
Name: "iliskilendir"; Description: ".op4 proje dosyalarını op4 ile aç"; GroupDescription: "Dosya ilişkilendirme:"

[Files]
Source: "{#Paket}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Opus Fortis\op4"; Filename: "{app}\op4.exe"; WorkingDir: "{app}"; Comment: "op4 — yapısal modelleme ve analiz"
Name: "{autoprograms}\Opus Fortis\op4 kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\op4"; Filename: "{app}\op4.exe"; WorkingDir: "{app}"; Tasks: masaustu

[Registry]
Root: HKA; Subkey: "Software\Classes\.op4"; ValueType: string; ValueName: ""; ValueData: "OpusFortis.op4.Proje"; Flags: uninsdeletevalue; Tasks: iliskilendir
Root: HKA; Subkey: "Software\Classes\OpusFortis.op4.Proje"; ValueType: string; ValueName: ""; ValueData: "op4 projesi"; Flags: uninsdeletekey; Tasks: iliskilendir
Root: HKA; Subkey: "Software\Classes\OpusFortis.op4.Proje\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\op4.exe,0"; Tasks: iliskilendir
Root: HKA; Subkey: "Software\Classes\OpusFortis.op4.Proje\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\op4.exe"" ""%1"""; Tasks: iliskilendir

[Run]
Filename: "{app}\op4.exe"; Description: "op4'ü başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Python'un çalışma anında yazabileceği önbellekler (kurulum dosyası olmayanlar).
Type: filesandordirs; Name: "{app}\motor\__pycache__"
Type: filesandordirs; Name: "{app}\python\Lib\site-packages\__pycache__"
