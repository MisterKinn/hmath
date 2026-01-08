from setuptools import setup

APP = ['gui/app.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': [],
    'includes': ['PIL', 'PIL.ImageFilter'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
