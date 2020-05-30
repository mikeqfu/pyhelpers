# download.py

from PIL import Image

from pyhelpers.dir import cd
from pyhelpers.download import download

url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
path_to_python_logo = cd("tests", "images", "python-logo.png")
download(url, path_to_python_logo)

path_to_python_logo = "python-logo.png"
download(url, path_to_python_logo)

image = Image.open(path_to_python_logo)
image.show()
