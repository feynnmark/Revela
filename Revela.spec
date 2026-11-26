# Build with .venv\Scripts\python.exe -m PyInstaller --noconfirm Revela.spec
from PyInstaller.utils.hooks import collect_dynamic_libs

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=collect_dynamic_libs('rawpy') + collect_dynamic_libs('pillow_heif'),
    datas=[('ui', 'ui'), ('assets', 'assets'), ('VERSION', '.'), ('licenses/Microsoft-WebView2', 'licenses/Microsoft-WebView2'), ('build/licenses', 'licenses')],
    hiddenimports=['webview.platforms.edgechromium', 'webview.platforms.winforms', 'PIL.ImageCms', 'pillow_heif'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5','PyQt6','PySide2','PySide6','tkinter','matplotlib','scipy','IPython','pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Revela', debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False, icon='assets/revela.ico', version='build/version_info.txt')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Revela')
