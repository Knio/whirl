import whirl
from setuptools import setup

setup(
    name        = 'whirl',
    version     = whirl.__version__,
    url         = 'https://github.com/Knio/whirl',
    author      = 'Tom Flanagan',
    author_email= 'tom@zkpq.ca',
    description = '''A collection of tools for making websites in Python''',
    long_description = open('README.md').read(),
    license = 'MIT',
    packages=['whirl'],
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
