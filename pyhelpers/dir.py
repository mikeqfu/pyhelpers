"""
Manipulation of directories.
"""

import os
import shutil

import pkg_resources

from .ops import confirmed

""" == Change directories ==================================================================== """


def cd(*sub_dir, mkdir=False, **kwargs):
    """
    Change directory and get path to sub-directories / files.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return: an absolute path to a directory (or a file)
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> import os
        >>> from pyhelpers.dir import cd

        >>> cwd = cd()  # Current working directory
        >>> print(os.path.relpath(cwd))
        .

        # (The directory will be created if it does not exists.)
        >>> path_to_tests_dir = cd("tests", mkdir=True)
        >>> print(os.path.relpath(path_to_tests_dir))
        tests
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
    Get path to ``data_dir`` and/or sub-directories / files.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param data_dir: name of a directory to store data, defaults to ``"data"``
    :type data_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return path: an absolute path to a directory (or a file) under ``data_dir``
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> import os
        >>> import shutil
        >>> from pyhelpers.dir import cdd

        >>> path_to_dat_dir = cdd()
        >>> # As `mkdir=False`, `path_to_dat_dir` will NOT be created if it doesn't exist
        >>> print(os.path.relpath(path_to_dat_dir))
        data

        >>> path_to_dat_dir = cdd(data_dir="test_cdd", mkdir=True)
        >>> # As `mkdir=True`, `path_to_dat_dir` will be created if it doesn't exist
        >>> print(os.path.relpath(path_to_dat_dir))
        test_cdd

        >>> # Delete the "test_cdd" folder
        >>> os.rmdir(path_to_dat_dir)

        >>> # Set `data_dir` to be `"tests"`
        >>> path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
        >>> print(os.path.relpath(path_to_dat_dir))
        test_cdd\\data

        >>> # Delete the "test_cdd" folder and the sub-folder "data"
        >>> shutil.rmtree(os.path.dirname(path_to_dat_dir))
    """

    path = cd(data_dir, *sub_dir, mkdir=mkdir, **kwargs)

    return path


def cd_dat(*sub_dir, dat_dir="dat", mkdir=False, **kwargs):
    """
    Get path to ``dat_dir`` and sub-directories / files in a package.

    :param sub_dir: name of directory or names of directories (and/or a filename)
    :type sub_dir: str
    :param dat_dir: name of a directory to store data, defaults to ``"dat"``
    :type dat_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: optional parameters of `os.makedirs`_, e.g. ``mode=0o777``
    :return: an absolute path to a directory (or a file) under ``data_dir``
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Example**::

        >>> import os
        >>> from pyhelpers.dir import cd_dat

        >>> path_to_dat_dir = cd_dat("tests", dat_dir="dat", mkdir=False)

        >>> print(os.path.relpath(path_to_dat_dir))
        pyhelpers\\dat\\tests
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


""" == Validate directories ================================================================== """


def is_dirname(dir_name):
    """
    Check if a string is a path or just a string.

    :param dir_name: a string-type variable to be checked
    :type dir_name: str
    :return: whether or not ``x`` is a path-like variable
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dir import cd, is_dirname

        >>> x = "tests"
        >>> print(is_dirname(x))
        False

        >>> x = "\\tests"
        >>> print(is_dirname(x))
        True

        >>> x = cd("tests")
        >>> print(is_dirname(x))
        True
    """

    if os.path.dirname(dir_name):
        return True
    else:
        return False


def validate_input_data_dir(input_data_dir=None, msg="Invalid input!", sub_dir=""):
    """
    Validate the input data directory.

    :param input_data_dir: data directory as input, defaults to ``None``
    :type input_data_dir: str or None
    :param msg: error message if ``data_dir`` is not an absolute path, defaults to ``"Invalid input!"``
    :type msg: str
    :param sub_dir: name of a sub-directory for when ``input_data_dir`` is ``None``, defaults to ``""``
    :type sub_dir: str
    :return: an absolute path to a valid data directory
    :rtype: str

    **Example**::

        >>> import os
        >>> from pyhelpers.dir import validate_input_data_dir

        >>> dat_dir = validate_input_data_dir()
        >>> print(os.path.relpath(dat_dir))
        .

        >>> dat_dir = validate_input_data_dir("tests")
        >>> print(os.path.relpath(dat_dir))
        tests

        >>> dat_dir = validate_input_data_dir(sub_dir="data")
        >>> print(os.path.relpath(dat_dir))
        data
    """

    if input_data_dir:
        assert isinstance(input_data_dir, str), msg

        if not os.path.isabs(input_data_dir):  # Use default file directory
            data_dir_ = cd(input_data_dir.strip('.\\.'))

        else:
            data_dir_ = os.path.realpath(input_data_dir.lstrip('.\\.'))
            assert os.path.isabs(input_data_dir), msg

    else:
        data_dir_ = cd(sub_dir) if sub_dir else cd()

    return data_dir_


""" == Delete directories ==================================================================== """


def delete_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory.

    :param path_to_dir: an absolute path to a directory
    :type path_to_dir: str
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: optional parameters of `shutil.rmtree`_

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree

    **Examples**::

        >>> import os
        >>> from pyhelpers.dir import cd, delete_dir

        >>> dir_path = cd("test_dir", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? True
        >>> delete_dir(dir_path, verbose=True)
        To delete the directory "test_dir\\"? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? False

        >>> dir_path = cd("test_dir", "folder", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? True
        >>> delete_dir(cd("test_dir"), verbose=True)
        The directory "test_dir\\" is not empty.
        Confirmed to delete it? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? False
    """

    rel_path_to_dir = os.path.relpath(path_to_dir)

    def print_msg():
        if verbose:
            print("Deleting \"{}\\\"".format(rel_path_to_dir), end=" ... ")

    try:
        if os.listdir(path_to_dir):
            if confirmed("The directory \"{}\\\" is not empty.\nConfirmed to delete it?".format(
                    rel_path_to_dir), confirmation_required=confirmation_required):
                print_msg()
                shutil.rmtree(path_to_dir, **kwargs)

        else:
            if confirmed("To delete the directory \"{}\\\"?".format(rel_path_to_dir),
                         confirmation_required=confirmation_required):
                print_msg()
                os.rmdir(path_to_dir)

        if verbose:
            print("Done.") if not os.path.exists(path_to_dir) else print("Cancelled.")

    except Exception as e:
        print("Failed. {}.".format(e))
