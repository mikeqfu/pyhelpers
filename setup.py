import setuptools

from pyhelpers import __author__, __description__, __email__, __package_name__, __version__

with open("README.rst", 'r', encoding='utf-8') as readme:
    long_description = readme.read()

setuptools.setup(

    name=__package_name__,

    version=__version__,

    description=__description__,
    long_description=long_description,
    long_description_content_type="text/x-rst",

    url='https://github.com/mikeqfu/pyhelpers',

    author=__author__,
    author_email=__email__,

    license='GPLv2',

    classifiers=[
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',

        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',

        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',

        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
    ],

    keywords=['python', 'helper functions', 'utilities'],

    project_urls={
        'Documentation': 'https://pyhelpers.readthedocs.io/en/latest/',
        'Source': 'https://github.com/mikeqfu/pyhelpers',
        'Tracker': 'https://github.com/mikeqfu/pyhelpers/issues',
    },

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    install_requires=[
        'XlsxWriter',
        'Shapely',
        'SQLAlchemy',
        'fake-useragent',
        'fuzzywuzzy',
        'joblib',
        'numpy',
        'openpyxl',
        'pandas',
        'psycopg2',
        'pyproj',
        'orjson',
        'requests',
        'scipy',
        'xlrd',
        # 'python-rapidjson',
        # 'python-Levenshtein'
        # 'gdal',
        # 'matplotlib',
        # 'nltk',
        # 'pdfkit',
        # 'pyxlsb',
        # 'tqdm',
    ],

    package_data={"": ["requirements.txt", "LICENSE"]},
    include_package_data=True,

)
