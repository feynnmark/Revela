"""Generate Windows version resources from the public VERSION file."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = (root / 'VERSION').read_text(encoding='utf-8').strip()
parts = version.split('.')
if len(parts) != 3 or not all(part.isdigit() and int(part) <= 65535 for part in parts):
    raise ValueError('VERSION must contain three numeric components.')
numbers = tuple(int(part) for part in parts) + (0,)
contents = f'''VSVersionInfo(ffi=FixedFileInfo(filevers={numbers},prodvers={numbers},mask=0x3f,flags=0x0,OS=0x40004,fileType=0x1,subtype=0x0,date=(0,0)),kids=[StringFileInfo([StringTable('040904B0',[StringStruct('CompanyName','Revela'),StringStruct('FileDescription','Revela - Conversor de imagenes'),StringStruct('FileVersion','{version}'),StringStruct('InternalName','Revela'),StringStruct('OriginalFilename','Revela.exe'),StringStruct('ProductName','Revela'),StringStruct('ProductVersion','{version}')])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])'''
(root / 'build').mkdir(exist_ok=True)
(root / 'build' / 'version_info.txt').write_text(contents, encoding='utf-8')
