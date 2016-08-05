from setuptools import setup

setup(name='gi',
      version='0.0.4',
      description='Git wrapper to perform Mercurial-like short unique abbreviation searching for commands',
      maintainer='Kirill Gagarski',
      maintainer_email='kirill.gagarski [at] gmail.com',
      url='http://bitbucket.org/gagarski/gi/',
      license='WTFPL',
      scripts=['bin/gi'],
      packages=['gi4git'],
      install_requires=[
          'marisa_trie',
      ],
)