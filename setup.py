#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'certifi==2020.12.5',
    'chardet==4.0.0',
    'click==7.1.2',
    'idna==2.10',
    'Jinja2==2.11.3',
    'MarkupSafe==1.1.1',
    'requests==2.25.1',
    'urllib3==1.26.3',
]

setup(
    name='lenmay',
    version='0.1.4',
    description="CLI tool to len may!",
    long_description=readme,
    author="KhanhIceTea",
    author_email='khanhicetea@gmail.com',
    url='https://github.com/khanhicetea/lenmay',
    packages=find_packages(include=['lenmay']),
    package_data={
        "lenmay/templates": ["init/*.twig"],
    },
    entry_points={
        'console_scripts': [
            'lenmay=lenmay:cli'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='lenmay',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ]
)