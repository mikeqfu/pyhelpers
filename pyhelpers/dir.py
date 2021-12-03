"""
Manipulation of directories and/or file paths.
"""

import copy
import os
import shutil

import pkg_resources

from .ops import confirmed

""" == Change directories ==================================================================== """


def cd(*subdir, mkdir=False, cwd=None, back_check=False, **kwargs):
    """
    Get the full pathname of a directory (or file).

    :param subdir: name of a directory or names of directories (and/or a filename)
    :type subdir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param cwd: current working directory, defaults to ``None``
    :type cwd: str or None
    :param back_check: whether to check if a parent directory exists, defaults to ``False``
    :type back_check: bool
    :param kwargs: [optional] parameters (e.g. ``mode=0o777``) of `os.makedirs`_
    :return: full pathname of a directory or that of a file
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> from pyhelpers.dir import cd
        >>> import os

        >>> current_wd = cd()  # Current working directory
        >>> os.path.relpath(current_wd)
        '.'

        >>> # The directory will be created if it does not exist
        >>> path_to_tests_dir = cd("tests", mkdir=True)
        >>> os.path.relpath(path_to_tests_dir)
        'tests'
    """

    # Current working directory
    path = os.getcwd() if cwd is None else copy.copy(cwd)

    if back_check:
        while not os.path.exists(path):
            path = os.path.dirname(path)

    for x in subdir:
        path = os.path.dirname(path) if x == ".." else os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


def go_from_altered_cwd(dir_name, **kwargs):
    """
    Get the full pathname of an altered working directory.

    :param dir_name: name of a directory
    :type dir_name: str
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return: full pathname of an altered working directory (changed from the directory ``dir_name``)
    :rtype: str

    **Example**::

        >>> from pyhelpers.dir import go_from_altered_cwd
        >>> import os

        >>> cwd = os.getcwd()
        >>> cwd
        '<cwd>'

        >>> # If the current working directory has been altered to "<cwd>\\test", and
        >>> # we'd like to set it to be "<cwd>\\target"
        >>> a_cwd = go_from_altered_cwd(dir_name="target")
        >>> a_cwd
        '<cwd>\\target'
    """

    target = cd(dir_name, **kwargs)

    if os.path.isdir(target):
        altered_cwd = target

    else:
        original_cwd = os.path.dirname(target)
        altered_cwd = os.path.join(original_cwd, dir_name)

        if altered_cwd == target:
            pass

        else:
            while not os.path.isdir(altered_cwd):
                original_cwd = os.path.dirname(original_cwd)
                if original_cwd == cd():
                    break
                else:
                    altered_cwd = os.path.join(original_cwd, dir_name)

    return altered_cwd


def cdd(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under ``data_dir``.

    :param subdir: name of directory or names of directories (and/or a filename)
    :type subdir: str
    :param data_dir: name of a directory where data is (or will be) stored, defaults to ``"data"``
    :type data_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return path: full pathname of a directory (or a file) under ``data_dir``
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dir import cdd, delete_dir
        >>> import os

        >>> path_to_dat_dir = cdd()
        >>> # As `mkdir=False`, `path_to_dat_dir` will NOT be created if it doesn't exist
        >>> os.path.relpath(path_to_dat_dir)
        'data'

        >>> path_to_dat_dir = cdd(data_dir="test_cdd", mkdir=True)
        >>> # As `mkdir=True`, `path_to_dat_dir` will be created if it doesn't exist
        >>> os.path.relpath(path_to_dat_dir)
        'test_cdd'

        >>> # Delete the "test_cdd" folder
        >>> delete_dir(path_to_dat_dir, verbose=True)
        To delete the directory "test_cdd\\"
        ? [No]|Yes: yes
        Deleting "test_cdd\\" ... Done.

        >>> # Set `data_dir` to be `"tests"`
        >>> path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
        >>> os.path.relpath(path_to_dat_dir)
        'test_cdd\\data'

        >>> # Delete the "test_cdd" folder and the sub-folder "data"
        >>> test_cdd = os.path.dirname(path_to_dat_dir)
        >>> delete_dir(test_cdd, verbose=True)
        The directory "test_cdd\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "test_cdd\\" ... Done.

        >>> # # Alternatively,
        >>> # import shutil
        >>> # shutil.rmtree(test_cdd)
    """

    kwargs.update({'mkdir': mkdir})
    path = cd(data_dir, *subdir, **kwargs)

    return path


def cd_dat(*subdir, dat_dir="dat", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under ``dat_dir`` of a package.

    :param subdir: name of directory or names of directories (and/or a filename)
    :type subdir: str
    :param dat_dir: name of a directory to store data, defaults to ``"dat"``
    :type dat_dir: str
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: [optional] parameters (e.g. ``mode=0o777``) of `os.makedirs`_
    :return: full pathname of a directory or that of a file under ``data_dir`` of a package
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Example**::

        >>> from pyhelpers.dir import cd_dat
        >>> import os

        >>> path_to_dat_dir = cd_dat("tests", dat_dir="dat", mkdir=False)

        >>> os.path.relpath(path_to_dat_dir)
        'pyhelpers\\dat\\tests'
    """

    path = pkg_resources.resource_filename(__name__, dat_dir)
    for x in subdir:
        path = os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


""" == Validate directories ================================================================== """


def is_dir(dir_pathname):
    """
    Check whether ``path_to_dir`` is a directory name.

    :param dir_pathname: name of a directory
    :type dir_pathname: str
    :return: whether ``path_to_dir`` is a path-like string that describes a directory name
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dir import cd, is_dir

        >>> x = "tests"
        >>> is_dir(x)
        False

        >>> x = "\\tests"
        >>> is_dir(x)
        True

        >>> x = cd("tests")
        >>> is_dir(x)
        True
    """

    if os.path.dirname(dir_pathname):
        return True
    else:
        return False


def validate_dir(dir_pathname=None, sub_dir="", msg="Invalid input!", **kwargs):
    """
    Validate the pathname of a directory.

    :param dir_pathname: pathname of a data directory, defaults to ``None``
    :type dir_pathname: str or None
    :param sub_dir: name of a subdirectory to be examined if ``directory=None``, defaults to ``""``
    :type sub_dir: str
    :param msg: error message if ``data_dir`` is not a full pathname, defaults to ``"Invalid input!"``
    :type msg: str
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return: valid full pathname of a directory
    :rtype: str

    **Example**::

        >>> from pyhelpers.dir import validate_dir
        >>> import os

        >>> dat_dir = validate_dir()
        >>> os.path.relpath(dat_dir)
        '.'

        >>> dat_dir = validate_dir("tests")
        >>> os.path.relpath(dat_dir)
        'tests'

        >>> dat_dir = validate_dir(sub_dir="data")
        >>> os.path.relpath(dat_dir)
        'data'
    """

    if dir_pathname:
        assert isinstance(dir_pathname, str), msg

        if not os.path.isabs(dir_pathname):  # Use default file directory
            data_dir_ = cd(dir_pathname.strip('.\\.'), **kwargs)

        else:
            data_dir_ = os.path.realpath(dir_pathname.lstrip('.\\.'))
            assert os.path.isabs(dir_pathname), msg

    else:
        data_dir_ = cd(sub_dir, **kwargs) if sub_dir else cd()

    return data_dir_


""" == Delete directories ==================================================================== """


def _print_deleting_msg(verbose, dir_relpath):
    if verbose:
        print("Deleting \"{}\\\"".format(dir_relpath), end=" ... ")


def delete_dir(dir_pathname, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory.

    :param dir_pathname: pathname of a directory
    :type dir_pathname: str
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `shutil.rmtree`_

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree

    **Examples**::

        >>> from pyhelpers.dir import cd, delete_dir
        >>> import os

        >>> dir_path = cd("test_dir", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? True
        >>> delete_dir(dir_path, verbose=True)
        To delete the directory "test_dir\\"
        ? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? False

        >>> dir_path = cd("test_dir", "folder", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? True
        >>> delete_dir(cd("test_dir"), verbose=True)
        The directory "test_dir\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? False
    """

    dir_relpath = os.path.relpath(dir_pathname)

    try:
        if os.listdir(dir_pathname):
            if confirmed("The directory \"{}\\\" is not empty.\nConfirmed to delete it\n?".format(
                    dir_relpath), confirmation_required=confirmation_required):
                _print_deleting_msg(verbose=verbose, dir_relpath=dir_relpath)
                shutil.rmtree(dir_pathname, **kwargs)

        else:
            if confirmed("To delete the directory \"{}\\\"\n?".format(dir_relpath),
                         confirmation_required=confirmation_required):
                _print_deleting_msg(verbose=verbose, dir_relpath=dir_relpath)
                os.rmdir(dir_pathname)

        if verbose:
            print("Done.") if not os.path.exists(dir_pathname) else print("Cancelled.")

    except Exception as e:
        print("Failed. {}.".format(e))
