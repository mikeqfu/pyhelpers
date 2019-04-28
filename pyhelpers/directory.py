""" Change directory """

import os

import pkg_resources


# Change directory
def cd(*sub_dir, mkdir=True):
    path = os.getcwd()  # Current working directory
    for d in sub_dir:
        path = os.path.join(path, d)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Change directory to "dat" and sub-directories
def cdd(*sub_dir):
    path = pkg_resources.resource_filename(__name__, 'dat/')
    for directory in sub_dir:
        path = os.path.join(path, directory)
    return path
