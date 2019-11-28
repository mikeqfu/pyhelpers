import setuptools

with open("README.md", 'r') as readme:
    long_description = readme.read()

setuptools.setup(

    name='pyhelpers',
    version='1.0.19',

    author='Qian Fu',
    author_email='qian.fu@outlook.com',

    description="A toolkit of helper functions to facilitate data manipulation.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/mikeqfu/pyhelpers',

    install_requires=[
        # 'gdal',
        # 'feather-format',
        'fuzzywuzzy',
        # 'matplotlib',
        # 'nltk',
        'numpy',
        'openpyxl',
        # 'pandas',
        # 'pdfkit',
        'python-rapidjson',
        # 'pyproj',
        'requests',
        'tqdm',
        'xlrd',
        'xlwt',
        'XlsxWriter'
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: Microsoft :: Windows :: Windows 10'
    ],
)
