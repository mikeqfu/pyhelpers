"""
Package initialisation.
"""

import datetime
import importlib.resources
import json
import logging

from . import dbms, dirs, geom, ops, settings, store, text, viz

logging.getLogger(__name__).addHandler(logging.NullHandler())

metadata = json.loads(
    importlib.resources.files(__name__).joinpath("data/.metadata").read_text(encoding="utf-8"))

__project__ = metadata['Project']
__pkgname__ = metadata['Package']
__desc__ = metadata['Description']

__author__ = metadata['Author']
__affil__ = metadata['Affiliation']
__email__ = metadata['Email']

__version__ = metadata['Version']
__license__ = metadata['License']
__copyright__ = f'2019-{datetime.datetime.now().year} {__author__}'

__first_release__ = metadata['First release']

__all__ = ['dbms', 'dirs', 'geom', 'ops', 'settings', 'store', 'text', 'viz']
