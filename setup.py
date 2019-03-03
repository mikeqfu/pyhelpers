import setuptools

with open("README.md", 'r') as readme:
    long_description = readme.read()

setuptools.setup(

    name='pyutils',
    version='0.0.1',

    author='Qian Fu',
    author_email='qian.fu@outlook.com',

    description="Download, parse and store OSM data extracts",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/mikeqfu/pyutils',

    install_requires=[
        'matplotlib',
        'nltk',
        'pandas',
        'pkg_resources',
        'progressbar2',
        'requests',
        'tqdm'
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
