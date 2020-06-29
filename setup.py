import setuptools

from pyhelpers import __version__, __author__, __email__

with open("README.rst", 'r') as readme:
    long_description = readme.read()

setuptools.setup(

    name='pyhelpers',
    version=__version__,

    author=__author__,
    author_email=__email__,

    description="A toolkit for facilitating data manipulation using Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",

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
        # 'pyproj',
        'pyxlsb',
        'requests',
        # 'shapely',
        'sqlalchemy',
        'sqlalchemy-utils',
        'tqdm',
        'xlrd',
        'xlwt',
        'XlsxWriter'
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    package_data={"": ["README.md", "requirements.txt", "LICENSE"]},
    include_package_data=True,

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux'
    ],
)
