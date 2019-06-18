import setuptools

with open("README.md", 'r') as readme:
    long_description = readme.read()

setuptools.setup(

    name='pyhelpers',
    version='1.0.8',

    author='Qian Fu',
    author_email='qian.fu@outlook.com',

    description="A small toolkit of helper functions to facilitate trivial data manipulations",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/mikeqfu/pyhelpers',

    install_requires=[
        'fuzzywuzzy',
        'matplotlib',
        'nltk',
        'numpy',
        'openpyxl',
        'pandas',
        'pdfkit',
        # 'progressbar2',
        'python-rapidjson',
        'requests',
        'tqdm',
        'xlrd',
        # 'xlwt',
        'XlsxWriter'
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "tests.*", "tests"]),

    classifiers=[
        'License :: OSI Approved :: MIT License',
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
