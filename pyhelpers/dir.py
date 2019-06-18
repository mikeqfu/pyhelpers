""" Change directory """

import os

import pkg_resources


# Change directory
def cd(*sub_dir, mkdir=False):
    path = os.getcwd()  # Current working directory
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Change directory to ".\\Data"
def cdd(*sub_dir, data_dir="Data", mkdir=False):
    path = cd(data_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Change directory to "dat" and sub-directories
def cd_dat(*sub_dir, dat_dir="dat", mkdir=False):
    path = pkg_resources.resource_filename(__name__, dat_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path
