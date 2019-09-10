""" Change directory """

import os
import shutil

import pkg_resources

from pyhelpers.misc import confirmed


# Change directory
def cd(*sub_dir, mkdir=False):
    """
    :param sub_dir: [str]
    :param mkdir: [bool] (default: False)
    :return: [str]

    Testing e.g.
        mkdir = False

        cd()
        cd("test")
    """
    path = os.getcwd()  # Current working directory
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Change directory to "Data"
def cdd(*sub_dir, data_dir="Data", mkdir=False):
    """
    :param sub_dir: [str]
    :param data_dir: [str] (default: "Data")
    :param mkdir: [bool] (default: False)
    :return: [str]

    Testing e.g.
        data_dir = "Data"
        mkdir = False

        cdd()
        cdd("test")
        cdd("test", data_dir="dat")
    """
    path = cd(data_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Change directory to "dat" and sub-directories
def cd_dat(*sub_dir, dat_dir="dat", mkdir=False):
    """
    :param sub_dir: [str]
    :param dat_dir: [str] (default: "dat")
    :param mkdir: [bool] (default: False)
    :return: [str]

    Testing e.g.
        dat_dir = "dat"
        mkdir = False
    """
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
    :param msg: [str] (default: "Invalid input!")
    :return: [str] regulated data directory

    Testing e.g.
        data_dir = "test"
        msg = "Invalid input!"
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
def rm_dir(path, confirmation_required=True, verbose=False):
    """
    :param path: [str]
    :param confirmation_required: [bool] (default: False)
    :param verbose: [bool]

    Testing e.g.
        confirmation_required = True
        verbose = False
    """
    print("Removing \"{}\"".format(path), end=" ... ") if verbose else None
    try:
        if os.listdir(path):
            if confirmed("\"{}\" is not empty. Confirmed to continue removing the directory?".format(path),
                         confirmation_required=confirmation_required):
                shutil.rmtree(path)
        else:
            os.rmdir(path)
        if verbose:
            print("Successfully.") if not os.path.exists(path) else print("Failed.")
    except Exception as e:
        print("Failed. {}.".format(e))
