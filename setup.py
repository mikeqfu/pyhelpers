import json
import pkgutil

import setuptools

metadata = json.loads(pkgutil.get_data(__name__, "data/metadata").decode())

__pkgname__ = metadata['Package']
__version__ = metadata['Version']
__homepage__ = f"https://github.com/mikeqfu/{__pkgname__}"

setuptools.setup(
    name=__pkgname__,
    version=__version__,
    description=metadata['Description'],
    url=__homepage__,
    author=metadata['Author'],
    author_email=metadata['Email'],
    license=metadata['License'],
    project_urls={
        'Documentation': f'https://{__pkgname__}.readthedocs.io/en/{__version__}/',
        'Source': __homepage__,
        'Bug Tracker': f'{__homepage__}/issues',
    },
)
