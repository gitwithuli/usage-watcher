"""
Build standalone macOS app using py2app

Usage:
    python setup_app.py py2app
"""

from setuptools import setup

APP = ['claude_usage.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Claude Usage Monitor',
        'CFBundleDisplayName': 'Claude Usage Monitor',
        'CFBundleIdentifier': 'com.claudecode.usage-monitor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Hide from Dock (menu bar app)
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
    'packages': ['rumps', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna'],
    'includes': ['json', 'logging', 'subprocess', 'time'],
    # 'iconfile': 'icon.icns',  # Add later if desired
}

setup(
    name='Claude Usage Monitor',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
