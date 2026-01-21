# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['claude_usage.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rumps', 'requests', 'urllib3', 'certifi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL', 'scipy'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClaudeWatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='ClaudeWatch.app',
    icon=None,
    bundle_identifier='com.gitwithuli.claudewatch',
    info_plist={
        'LSUIElement': True,
        'CFBundleName': 'ClaudeWatch',
        'CFBundleDisplayName': 'ClaudeWatch',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
