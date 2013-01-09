#!/usr/bin/env python

from setuptools import setup


setup(name='sortest',
      version='0.0.2',
      description=('Continuous testing in Python with sorting by test speed '
                   'and auto-restart when files change'),
      url='https://github.com/eigenhombre/sortest',
      author='John Jacobsen',
      author_email='john@mail.npxdesigns.com',
      license='EPL',
      packages=['sortest'],
      scripts=['bin/sortest'],
#      entry_points={'console_scripts': ['sortest = scripts/sortest.py:main']},
      install_requires=['nose'],
      zip_safe=False)
