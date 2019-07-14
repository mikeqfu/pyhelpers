""" Change directory """

import os
import shutil

import pkg_resources

from pyhelpers.misc import confirmed


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


# Regulate the input data directory
def regulate_input_data_dir(data_dir, msg="Invalid input!"):
    """
    :param data_dir: [str] data directory as input
    :param msg: [str]
    :return: [str] regulated data directory
    """
    if data_dir is None:
        data_dir = cdd()
    else:
        assert isinstance(data_dir, str)
        if not os.path.isabs(data_dir):  # Use default file directory
            data_dir = cd(data_dir.strip('.\\.'))
        else:
            data_dir = os.path.realpath(data_dir.lstrip('.\\.'))
            assert os.path.isabs(data_dir), msg
    return data_dir


# Remove a directory
def rm_dir(path, confirmation_required=True):
    if os.listdir(path):
        if confirmed("\"{}\" is not empty. Confirmed to continue removing the directory?".format(path),
                     confirmation_required=confirmation_required):
            shutil.rmtree(path)
    else:
        os.rmdir(path)
