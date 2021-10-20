import setuptools

from pyhelpers import __author__, __description__, __email__, __package__, __version__

with open("README.rst", 'r', encoding='utf-8') as readme:
    long_description = readme.read()

setuptools.setup(

    name=__package__,

    version=__version__,

    description=__description__,
    long_description=long_description,
    long_description_content_type="text/x-rst",

    url=f'https://github.com/mikeqfu/{__package__}',

    author=__author__,
    author_email=__email__,

    license='GPLv2',

    classifiers=[
        'Intended Audience :: Developers',
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

    keywords=['Python', 'Utilities', 'Helpers'],

    project_urls={
        'Documentation': f'https://{__package__}.readthedocs.io/en/{__version__}/',
        'Source': f'https://github.com/mikeqfu/{__package__}',
        'Tracker': f'https://github.com/mikeqfu/{__package__}/issues',
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

    package_data={"": ["dat/*", "requirements.txt", "LICENSE"]},
    include_package_data=True,

)
