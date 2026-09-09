# -*- mode: python ; coding: utf-8 -*-
a = Analysis(['main.py'], pathex=[], binaries=[], datas=[('templates', 'templates'), ('static', 'static')], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='教室檔案分享', debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False, disable_windowed_traceback=False)
