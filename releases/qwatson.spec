# -*- mode: python -*-
import shutil
import subprocess
import os
from qwatson import __version__
from qwatson.utils.fileio import delete_folder_recursively

block_cipher = None

added_files = [('../qwatson/ressources/icons_png/*.png',
                'ressources/icons_png')]

a = Analysis(['../qwatson/mainwindow.py'],
             pathex=[],
             binaries=[],
             datas=added_files ,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PySide', 'PyQt4'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='qwatson',
          debug=False,
          strip=False,
          upx=True,
          console=False ,
          icon='qwatson.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='QWatson')

# Prepare the binary folder

shutil.copyfile("../LICENSE", "dist/LICENSE")
output_dirname = 'qwatson_'+__version__+'_win_amd64'
delete_folder_recursively(output_dirname, delroot=True)
os.rename('dist', output_dirname)

# Zip the binary folder

cmd = ['C:/Program Files/7-Zip/7z', 'a', output_dirname+'.zip',
       output_dirname, '-mx9']
sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# Prepare the installer

innosetp_scrip = (
    '[Setup]\n'
    'AppId={{73183705-C0D1-4A71-9A02-3509F6265F8A}\n'
    'AppName=QWatson\n'
    'AppVersion=%s\n'
    ';AppVerName=QWatson %s\n'
    'AppPublisher=Jean-S\u00e9bastien Gosselin\n'
    'AppPublisherURL=https://github.com/jnsebgosselin/qwatson\n'
    'AppSupportURL=https://github.com/jnsebgosselin/qwatson\n'
    'AppUpdatesURL=https://github.com/jnsebgosselin/qwatson\n'
    'DefaultDirName={pf}/QWatson\n'
    'DisableDirPage=auto\n'
    'DisableProgramGroupPage=yes\n'
    'LicenseFile=../LICENSE\n'
    'OutputBaseFilename=qwatson_%s_win_amd64\n'
    'SetupIconFile=./qwatson.ico\n'
    'Compression=lzma\n'
    'SolidCompression=yes\n'
    '\n'
    '[Languages]\n'
    'Name: "english"; MessagesFile: "compiler:Default.isl"\n'
    '\n'
    '[Tasks]\n'
    'Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; '
    'GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked\n'
    '\n'
    '[Files]\n'
    'Source: ".\qwatson_%s_win_amd64\QWatson\qwatson.exe"; '
    'DestDir: "{app}"; Flags: ignoreversion\n'
    'Source: ".\qwatson_%s_win_amd64\QWatson\*"; DestDir: "{app}"; '
    'Flags: ignoreversion recursesubdirs createallsubdirs\n'
    
    '; NOTE: Do not use "Flags: ignoreversion" on any shared system files\n'
    '\n'
    '[Icons]\n'
    'Name: "{commonprograms}\QWatson"; Filename: "{app}\qwatson.exe"\n'
    'Name: "{commondesktop}\QWatson"; Filename: "{app}\qwatson.exe"; '
    'Tasks: desktopicon\n'
    '\n'
    '[Run]\n'
    'Filename: "{app}\qwatson.exe"; '
    'Description: "{cm:LaunchProgram,QWatson}"; '
    'Flags: nowait postinstall skipifsilent\n'
) % (__version__, __version__, __version__, __version__, __version__)

with open('qwatson_innosetup_script.iss', 'w') as f:
    f.write(innosetp_scrip)
    
cmd = ['C:/Program Files (x86)/Inno Setup 5/compil32.exe', '/cc',
       'qwatson_innosetup_script.iss']
sp2 = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
