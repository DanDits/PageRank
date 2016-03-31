from distutils.core import setup

setup(
    name='pyoogle',
    version='1.1',
    packages=['pyoogle', 'pyoogle.search', 'pyoogle.preprocessing', 'pyoogle.preprocessing.web', 'pyoogle.preprocessing.crawl', 'pyoogle.preprocessing.ranking'],
    url='',
    license='Apache License Version 2.0',
    author='daniel',
    author_email='dans.ditt@gmail.com',
    description='Google in python: a crawler, page rank and small search engine', requires=['scipy', 'numpy', 'bs4']
)
