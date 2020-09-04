""" A module for manipulation of directories. """

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
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return: a full path to a directory (or a file)
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        from pyhelpers.dir import cd

        path = cd()
        print(path)
        # <cwd>  # Current working directory

        mkdir = True
        path = cd("tests", mkdir=mkdir)
        print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
        # <cwd>\\tests. (This directory will be created if it does not exists.)
    """

    path = os.getcwd()  # Current working directory
    for x in sub_dir:
        path = os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        if ext == '':
            os.makedirs(path_to_file, exist_ok=True, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), exist_ok=True, **kwargs)

    return path


def cdd(*sub_dir, data_dir="data", mkdir=False, **kwargs):
    """
    Change directory to `data_dir/` and sub-directories.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param data_dir: name of a directory to store data, defaults to ``"data"``
    :type data_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return path: a full path to a directory (or a file) under ``data_dir``
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        from pyhelpers.dir import cdd

        path = cdd()
        print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
        # <cwd>\\data. (This directory will NOT be created if it does not exists).

        mkdir = True

        path = cdd(mkdir=mkdir)
        print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
        # <cwd>\\data. (This directory will be created if it does not exists.)

        path = cdd("data", data_dir="tests", mkdir=mkdir)
        print(".  ".join([path, "(This directory will be created if it does not exists.)"]))
        # <cwd>\\tests\\data. (This directory will be created if it does not exists.)
    """

    path = cd(data_dir, *sub_dir, mkdir=mkdir, **kwargs)

    return path


def cd_dat(*sub_dir, dat_dir="dat", mkdir=False, **kwargs):
    """
    Change directory to `dat_dir/` and sub-directories within a package.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param dat_dir: name of a directory to store data, defaults to ``"dat"``
    :type dat_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return: a full path to a directory (or a file) under ``data_dir``
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Example**::

        from pyhelpers.dir import cd_dat

        dat_dir = "dat"
        mkdir = False

        path = cd_dat("tests", dat_dir=dat_dir, mkdir=mkdir)
        print(".  ".join([path, "(This directory will NOT be created if it does not exists.)"]))
        # <package directory>\\dat\\tests. (This directory will NOT be created if it does not exists.)
    """

    path = pkg_resources.resource_filename(__name__, dat_dir)
    for x in sub_dir:
        path = os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        if ext == '':
            os.makedirs(path_to_file, exist_ok=True, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), exist_ok=True, **kwargs)

    return path


def is_dirname(dir_name):
    """
    Check if a string is a path or just a string.

    :param dir_name: a string-type variable to be checked
    :type dir_name: str
    :return: whether or not ``x`` is a path-like variable
    :rtype: bool

    **Examples**::

        from pyhelpers.dir import cd, is_dirname

        dir_name = "tests"
        print(is_dirname(dir_name))
        # False

        dir_name = "\\tests"
        print(is_dirname(dir_name))
        # True

        dir_name = cd("tests")
        print(is_dirname(dir_name))
    """

    if os.path.dirname(dir_name):
        return True
    else:
        return False


def validate_input_data_dir(data_dir=None, msg="Invalid input!"):
    """
    Validate the input data directory.

    :param data_dir: data directory as input, defaults to ``None``
    :type data_dir: str, None
    :param msg: an error message if ``data_dir`` is not an absolute path, defaults to ``"Invalid input!"``
    :type msg: str
    :return: full path to a valid data directory
    :rtype: str

    **Example**::

        from pyhelpers.dir import validate_input_data_dir

        data_dir = "tests"

        data_dir_ = validate_input_data_dir(data_dir)

        print(data_dir_)
        # <cwd>\\tests
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


def rm_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Remove a directory.

    :param path_to_dir: a full path to a directory
    :type path_to_dir: str
    :param confirmation_required: whether to prompt a message for confirmation to proceed, defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs, defaults to ``False``
    :type verbose: bool
    :param kwargs: optional parameters of `shutil.rmtree <https://docs.python.org/3/library/shutil.html#shutil.rmtree>`_

    **Example**::

        import os
        from pyhelpers.dir import cdd, rm_dir

        path_to_dir = cdd(mkdir=True)
        print("The directory \"{}\" exists? {}".format(path_to_dir, os.path.exists(path_to_dir)))
        # The directory "<cwd>\\data\\dat" exists? True

        rm_dir(path_to_dir, confirmation_required=True, verbose=True)
        # To remove the directory "<cwd>\\data\\dat"? [No]|Yes: yes
        # Done.

        print("The directory \"{}\" exists? {}".format(path_to_dir, os.path.exists(path_to_dir)))
        # The directory "<cwd>\\data\\dat" exists? False
    """

    try:
        if os.listdir(path_to_dir):
            if confirmed("\"{}\" is not empty. Confirmed to remove the directory?".format(path_to_dir),
                         confirmation_required=confirmation_required):
                import shutil
                shutil.rmtree(path_to_dir, **kwargs)

        else:
            if confirmed("To remove the directory \"{}\"?".format(path_to_dir),
                         confirmation_required=confirmation_required):
                os.rmdir(path_to_dir)

        if verbose:
            print("Done.") if not os.path.exists(path_to_dir) else print("Cancelled.")

    except Exception as e:
        print("Failed. {}.".format(e))
