import setuptools

import pyhelpers

with open("README.rst", 'r', encoding='utf-8') as readme:
    long_description = readme.read()

setuptools.setup(

    name=pyhelpers.__package_name__,
    version=pyhelpers.__version__,

    author=pyhelpers.__author__,
    author_email=pyhelpers.__email__,

    description=pyhelpers.__description__,
    long_description=long_description,
    long_description_content_type="text/x-rst",

    url='https://github.com/mikeqfu/pyhelpers',

    install_requires=[
        # 'gdal',
        'fuzzywuzzy',
        # 'matplotlib',
        # 'nltk',
        'numpy',
        'openpyxl',
        'pandas',
        # 'pdfkit',
        # 'psycopg2',
        'python-rapidjson',
        # 'python-Levenshtein',
        # 'pyproj',
        # 'pyxlsb',
        'requests',
        # 'shapely',
        'sqlalchemy',
        'sqlalchemy-utils',
        'tqdm',
        # 'xlrd',
        # 'xlwt',
        'XlsxWriter'
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    package_data={"": ["requirements.txt", "LICENSE"]},
    include_package_data=True,

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux'
    ],
)
