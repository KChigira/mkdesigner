#!/usr/bin/env python

from distutils.core import setup
from mkdesigner.__init__ import __version__

setup(name='mkdesigner',
      version="0.0.1",
      description='Tools for designing DNA markers and their PCR primers from NGS data',
      author='Koki Chigira',
      author_email='s211905s@st.go.tuat.ac.jp',
      url='https://github.com/KChigira/mkdesigner/',
      license='GPL',
      packages=["mkdesigner"],
      entry_points={'console_scripts': [
            'mkvcf = mkdesigner.mkvcf:main',
            'mkprimer = mkdesigner.mkprimer:main',
            'mkselect = mkdesigner.mkselect:main',
            ]
      }
    )
