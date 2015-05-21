#!/usr/bin/env python

import sys

try:
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup


is_py3 = sys.version_info.major == 3
readme_file = 'README.md'


def read_long_description(readme_file):
    """ Read package long description from README file """
    try:
        import pypandoc
    except (ImportError, OSError) as e:
        print('No pypandoc or pandoc: %s' % (e,))
        if is_py3:
            fh = open(readme_file, encoding='utf-8')
        else:
            fh = open(readme_file)
        long_description = fh.read()
        fh.close()
        return long_description
    else:
        return pypandoc.convert(readme_file, 'rst')


def read_version():
    """ Read package version """
    with open('./ciex/version.py') as fh:
        for line in fh:
            if line.startswith('VERSION'):
                return line.split('=')[1].strip().strip("'")
setup(
    name='ciex',
    version=read_version(),
    packages=['ciex', 'ciex.contrib', 'ciex.contrib.workers'],
    author='Tony Walker',
    author_email='walkr.walkr@gmail.com',
    url='https://github.com/walkr/ciex',
    license='MIT',
    description='A simple, lightweight and modular CI system',
    long_description=read_long_description(readme_file),
    install_requires=[
        'oi',
        'nose',
        'gitpython',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'ciexd = ciex.ciexd:main',
            'ciexctl = ciex.ciexctl:main',
        ],
    },
)
