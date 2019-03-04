import setuptools

with open("README.md", 'r') as readme:
    long_description = readme.read()

setuptools.setup(

    name='pyhelpers',
    version='1.0.0',

    author='Qian Fu',
    author_email='qian.fu@outlook.com',

    description="A small toolkit of helper functions to facilitate trivial processes",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/mikeqfu/pyhelpers',

    install_requires=[
        'matplotlib',
        'nltk',
        'openpyxl',
        'pandas',
        'progressbar2',
        'requests',
        'tqdm',
        'XlsxWriter'
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: Microsoft :: Windows :: Windows 8',
        'Operating System :: Microsoft :: Windows :: Windows 8.1',
        'Operating System :: Microsoft :: Windows :: Windows 10',
    ],
)
