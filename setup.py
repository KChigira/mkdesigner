#!/usr/bin/env python
from setuptools import setup, find_packages # type: ignore
from mkdesigner.__init__ import __version__

setup(name='mkdesigner',
      version=__version__,
      description='Genome-wide design of markers for PCR-based genotyping from NGS data.',
      author='Koki Chigira',
      author_email='s211905s@st.go.tuat.ac.jp',
      url='https://github.com/KChigira/mkdesigner/',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        'pandas',
        'matplotlib',
      ],
      entry_points={'console_scripts': [
            'mkvcf = mkdesigner.mkvcf:main',
            'mkprimer = mkdesigner.mkprimer:main',
            'mkselect = mkdesigner.mkselect:main',
            ]
      }
    )
