""" Change directory """

import os

import pkg_resources


# Change directory and sub-directories
def cd(*directories):
    # Current working directory
    path = os.getcwd()
    for directory in directories:
        path = os.path.join(path, directory)
    return path


# Change directory to "dat" and sub-directories
def cdd(*directories):
    path = pkg_resources.resource_filename(__name__, 'dat/')
    for directory in directories:
        path = os.path.join(path, directory)
    return path
