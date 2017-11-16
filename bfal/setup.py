from setuptools import setup, find_packages

with open("README", 'r') as f:
    long_description = f.read()

setup(
   name             = 'bfal',
   version          = '0.1',
   description      = 'An assembly language for brainfuck',
   license          = "MIT",
   long_description = long_description,
   author           = 'MMarius Lambacher',
   author_email     = 'bfal@lmbchr.de',
   url              = "",
   packages         = find_packages(exclude=('tests', 'docs')),
   install_requires = [], #external packages as dependencies
)