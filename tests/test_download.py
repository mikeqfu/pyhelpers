# download.py

import Image

from pyhelpers.dir import cd
from pyhelpers.download import download

url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
path_to_python_logo = cd("tests", "picture", "python-logo.png")
download(url, path_to_python_logo)

image = Image.open(path_to_python_logo)
image.show()
