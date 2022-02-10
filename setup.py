import json

import setuptools

with open("src/pyhelpers/data/metadata.json", mode='r') as metadata_file:
    metadata = json.load(metadata_file)

__package__ = metadata['Package']
__author__ = metadata['Author']
__author_email__ = metadata['Email']
__description__ = metadata['Description']
__version__ = metadata['Version']
__license__ = metadata['License']

__home_page__ = 'https://github.com/mikeqfu/' + f'{__package__}'

setuptools.setup(
    name=__package__,
    version=__version__,
    description=__description__,
    url=__home_page__,
    author=__author__,
    author_email=__author_email__,
    license=__license__,
    project_urls={
        'Documentation': f'https://{__package__}.readthedocs.io/en/{__version__}/',
        'Source': __home_page__,
        'Tracker': __home_page__ + f'/issues',
    },
)
