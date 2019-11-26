""" Change directory """

import os
import shutil

import pkg_resources

from pyhelpers.ops import confirmed


# Change directory
def cd(*sub_dir, mkdir=False):
    """
    :param sub_dir: [str]
    :param mkdir: [bool] (default: False)
    :return: [str]

    Examples:
        cd()  # Current working directory
        mkdir = True
        cd("test_cd", mkdir=mkdir)  # Current working directory \\test_cd
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

    Examples:
        data_dir = "Data"
        mkdir = False
        cdd()  # \\Data
        cdd("test_cdd")  # \\Data\\test_cdd
        cdd("test_cdd", data_dir="test_cdd", mkdir=True)  # \\test_cdd\\test_cdd
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

    Example:
        dat_dir = "dat"
        mkdir = False
        cd_dat("test_cd_dat", dat_dir=dat_dir, mkdir=mkdir)
    """
    path = pkg_resources.resource_filename(__name__, dat_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(path, exist_ok=True)
    return path


# Check if a string is a path or just a string
def is_dirname(x):
    """
    :param x: [str]
    :return: [bool]

    Examples:
        x = "test_is_dirname"
        is_dirname(x)  # False

        x = "\\test_is_dirname"
        is_dirname(x)  # True

        x = cd("test_is_dirname")
        is_dirname(x)  # True

    """
    if os.path.dirname(x):
        return True
    else:
        return False


# Regulate the input data directory
def regulate_input_data_dir(data_dir, msg="Invalid input!"):
    """
    :param data_dir: [str] data directory as input
    :param msg: [str] (default: "Invalid input!")
    :return: [str] regulated data directory

    Example:
        data_dir = "test_regulate_input_data_dir"
        msg = "Invalid input!"
        regulate_input_data_dir(data_dir, msg)
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

    Example:
        path = cd("test_rm_dir", mkdir=True)
        confirmation_required = True
        verbose = False
        rm_dir(path, confirmation_required, verbose)
    """
    print("Removing \"{}\"".format(path), end=" ... ") if verbose else None
    try:
        if os.listdir(path):
            if confirmed("\"{}\" is not empty. Confirmed to continue removing the directory?".format(path),
                         confirmation_required=confirmation_required):
                shutil.rmtree(path)
        else:
            if confirmed("To remove the directory \"{}\"?".format(path), confirmation_required=confirmation_required):
                os.rmdir(path)
        if verbose:
            print("Successfully.") if not os.path.exists(path) else print("Failed.")
    except Exception as e:
        print("Failed. {}.".format(e))
