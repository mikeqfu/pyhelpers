import datetime
import json

import pkg_resources

f = open(pkg_resources.resource_filename(__name__, "dat\\metadata"), mode='r')
metadata = json.load(f)
f.close()

__project__ = metadata['Project']
__package__ = metadata['Package']

__author__ = metadata['Author']
__affiliation__ = metadata['Affiliation']
__email__ = metadata['Email']

__description__ = metadata['Description']

__copyright__ = f'2019-{datetime.datetime.now().year}, {__author__}'

__version__ = '1.3.0a4'
