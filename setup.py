from setuptools import setup

setup(name='sortest',
      version='0.0.1',
      description=('Continuous testing in Python with sorting by test speed '
                   'and auto-restart when files change'),
      url='https://github.com/eigenhombre/sortest',
      author='John Jacobsen',
      author_email='john@mail.npxdesigns.com',
      license='EPL',
      packages=['sortest'],
      install_requires=['nose'],
      zip_safe=False)
