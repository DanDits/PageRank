from setuptools import setup, find_packages

setup(
    name='pyoogle',
    version='1.2.1',
    packages=find_packages(),
    url='https://github.com/DanDits/Pyoogle',
    license='Apache License Version 2.0',
    author='daniel',
    author_email='dans.ditt@gmail.com',
    description='Google in python: a crawler, page rank and small search engine',
    requires=['scipy', 'numpy', 'bs4', 'PyQt4'],
    installrequires=['scipy', 'numpy', 'bs4'],
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers'
    ],
    keywords=[
        'Search',
        'Google',
        'Crawler',
        'Web scraping'
    ]
)
