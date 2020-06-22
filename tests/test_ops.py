# ops.py

from PIL import Image

from pyhelpers.dir import cd
from pyhelpers.ops import confirmed, download_file_from_url

# download_file_from_url()
url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
path_to_python_logo = cd("tests", "images", "python-logo.png")
download_file_from_url(url, path_to_python_logo)

path_to_python_logo = "python-logo.png"
download_file_from_url(url, path_to_python_logo)

image = Image.open(path_to_python_logo)
image.show()

# confirmed()
confirmed(prompt="Continue?...", confirmation_required=True)
