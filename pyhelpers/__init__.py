"""Package initialization."""

import datetime
import json
import pkgutil

from . import dbms, dirs, geom, ops, settings, store, text

metadata = json.loads(pkgutil.get_data(__name__, "data/metadata.json").decode())

__project__ = metadata['Project']
__pkgname__ = metadata['Package']

__author__ = metadata['Author']
__affiliation__ = metadata['Affiliation']
__author_email__ = metadata['Email']

__description__ = metadata['Description']

__copyright__ = f'2019-{datetime.datetime.now().year}, {__author__}'

__version__ = metadata['Version']
__license__ = metadata['License']

__first_release_date__ = metadata['First release']

__all__ = [
    'dbms',
    'dirs',
    'geom',
    'ops',
    'settings',
    'store',
    'text',
]
