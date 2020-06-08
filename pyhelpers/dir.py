""" Helper functions for manipulating directories """

import os

import pkg_resources

from pyhelpers.ops import confirmed


def cd(*sub_dir, mkdir=False, **kwargs):
    """
    Change directory.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional arguments of `os.makedirs <https://docs.python.org/3/library/os.html#os.makedirs>`_,
        e.g. ``mode=0o777``
    :return: a full path to a directory (or a file)
    :rtype: str

    Examples::

        cd()  # Current working directory

        mkdir = True
        cd("test_cd", mkdir=mkdir)  # [working directory]/test_cd/
    """

    path = os.getcwd()  # Current working directory
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(os.path.dirname(path), exist_ok=True, **kwargs)
    return path


def cdd(*sub_dir, data_dir="data", mkdir=False, **kwargs):
    """
    Change directory to "[working directory]/[data_dir]/" and sub-directories.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param data_dir: name of a directory to store data, defaults to ``"data"``
    :type data_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional arguments of `os.makedirs <https://docs.python.org/3/library/os.html#os.makedirs>`_,
        e.g. ``mode=0o777``
    :return path: a full path to a directory (or a file) under ``data_dir``
    :rtype: str

    Examples::

        data_dir = "Data"
        mkdir = False

        cdd()  # [working directory]/data

        cdd("test_cdd")  # [working directory]/Data/test_cdd

        cdd("test_cdd", data_dir="test_cdd", mkdir=True)  # [working directory]/test_cdd/test_cdd
    """

    path = cd(data_dir)
    for x in sub_dir:
        path = os.path.join(path, x)
    if mkdir:
        os.makedirs(os.path.dirname(path), exist_ok=True, **kwargs)
    return path


def cd_dat(*sub_dir, dat_dir="dat", mkdir=False, **kwargs):
    """
    Change directory to "dat" and sub-directories within a package.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param dat_dir: name of a directory to store data, defaults to ``"dat"``
    :type dat_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional arguments of `os.makedirs <https://docs.python.org/3/library/os.html#os.makedirs>`_,
        e.g. ``mode=0o777``
    :return: a full path to a directory (or a file) under ``data_dir``
    :rtype: str

    Example::

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


def is_dirname(x):
    """
    Check if a string is a path or just a string.

    :param x: a string-type variable to be checked
    :type x: str
    :return: whether or not ``x`` is a path-like variable
    :rtype: bool

    Examples::

        x = "test_is_dirname"
        is_dirname(x)  # False

        x = "\\\\test_is_dirname"
        is_dirname(x)  # True

        x = cd("test_is_dirname")
        is_dirname(x)  # True
    """

    if os.path.dirname(x):
        return True
    else:
        return False


def regulate_input_data_dir(data_dir=None, msg="Invalid input!"):
    """
    Regulate the input data directory.

    :param data_dir: data directory as input, defaults to ``None``
    :type data_dir: str, None
    :param msg: an error message if ``data_dir`` is not an absolute path, defaults to ``"Invalid input!"``
    :type msg: str
    :return: a full path to a regulated data directory
    :rtype: str

    Example::

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


def rm_dir(path, confirmation_required=True, verbose=False, **kwargs):
    """
    Remove a directory.

    :param path: a full path to a directory
    :type path: str
    :param confirmation_required: whether to prompt a message for confirmation to proceed, defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
    :type verbose: bool
    :param kwargs: optional arguments of `shutil.rmtree <https://docs.python.org/3/library/shutil.html#shutil.rmtree>`_

    Example::

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
