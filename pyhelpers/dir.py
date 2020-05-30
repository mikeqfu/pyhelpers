""" Change directory """

import os

import pkg_resources

from pyhelpers.ops import confirmed


# Change directory
def cd(*sub_dir, mkdir=False, **kwargs):
    """
    :param sub_dir: [str] name of directory or names of directories (and/or a filename)
    :param mkdir: [bool] whether to create a directory (default: False)
    :param kwargs: [int] optional arguments for `os.makedirs()`: `mode=0o777`
    :return path: [str] a full path to a directory (or a file)

    Examples:
        cd()  # Current working directory
        mkdir = True
        cd("test_cd", mkdir=mkdir)  # Current working directory \\test_cd
    """
    path = os.getcwd()  # Current working directory
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(os.path.dirname(path), exist_ok=True, **kwargs)
    return path


# Change directory to "Data"
def cdd(*sub_dir, data_dir="data", mkdir=False, **kwargs):
    """
    :param sub_dir: [str] name of directory or names of directories (and/or a filename)
    :param data_dir: [str] name of a directory to store data (default: "Data")
    :param mkdir: [bool] whether to create a directory (default: False)
    :param kwargs: [int] optional arguments for `os.makedirs()`: `mode=0o777`
    :return path: [str] a full path to a directory (or a file) under `data_dir`

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
        os.makedirs(os.path.dirname(path), exist_ok=True, **kwargs)
    return path


# Change directory to "dat" and sub-directories for a Python package per se
def cd_dat(*sub_dir, dat_dir="dat", mkdir=False, **kwargs):
    """
    :param sub_dir: [str] name of directory or names of directories (and/or a filename)
    :param dat_dir: [str] name of a directory to store data (default: "dat")
    :param mkdir: [bool] whether to create a directory (default: False)
    :param kwargs: [int] optional arguments for `os.makedirs()`: `mode=0o777`
    :return path: [str] a full path to a directory (or a file) under `data_dir`

    Example:
        dat_dir = "dat"
        mkdir = False
        cd_dat("test_cd_dat", dat_dir=dat_dir, mkdir=mkdir)
    """
    path = pkg_resources.resource_filename(__name__, dat_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(os.path.dirname(path), exist_ok=True, **kwargs)
    return path


# Check if a string is a path or just a string
def is_dirname(x):
    """
    :param x: [str] a string-type variable to be checked
    :return: [bool] whether or not `x` is a path-like variable

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
def regulate_input_data_dir(data_dir=None, msg="Invalid input!"):
    """
    :param data_dir: [str; None (default)] data directory as input
    :param msg: [str] an error message if the input `data_dir` is not an absolute path (default: "Invalid input!")
    :return data_dir_: [str] a full path to a regulated data directory

    Example:
        data_dir = "test_regulate_input_data_dir"
        msg = "Invalid input!"
        regulate_input_data_dir(data_dir, msg)
    """
    if data_dir:
        assert isinstance(data_dir, str), msg
        if not os.path.isabs(data_dir):  # Use default file directory
            data_dir_ = cd(data_dir.strip('.\\.'))
        else:
            data_dir_ = os.path.realpath(data_dir.lstrip('.\\.'))
            assert os.path.isabs(data_dir), msg
    else:
        data_dir_ = cdd()
    return data_dir_


# Remove a directory
def rm_dir(path, confirmation_required=True, verbose=False, **kwargs):
    """
    :param path: [str] a full path to a directory
    :param confirmation_required: [bool] whether or not to impose a prompting message for confirmation to proceed
                                        (default: True)
    :param verbose: [bool] whether or not show illustrative messages (default: False)
    :param kwargs: optional arguments used by `shutil.rmtree()`

    Example:
        path = cd("test_rm_dir", mkdir=True)
        confirmation_required = True
        verbose = False
        rm_dir(path, confirmation_required, verbose)
    """
    print("Removing \"{}\"".format(path), end=" ... ") if verbose else None
    try:
        if os.listdir(path):
            if confirmed("\"{}\" is not empty. Confirmed to remove the directory?".format(path),
                         confirmation_required=confirmation_required):
                import shutil
                shutil.rmtree(path, **kwargs)
        else:
            if confirmed("To remove the directory \"{}\"?".format(path), confirmation_required=confirmation_required):
                os.rmdir(path)
        if verbose:
            print("Successfully.") if not os.path.exists(path) else print("Failed.")
    except Exception as e:
        print("Failed. {}.".format(e))
