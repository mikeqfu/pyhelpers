"""Manipulation of directories and/or file paths."""

import collections.abc
import copy
import errno
import os
import pathlib
import re
import shutil

import pkg_resources
from typing import Union  # Python version <= 3.9

from ._cache import _check_rel_pathname
from .ops import confirmed


# ==================================================================================================
# Directory navigation
# ==================================================================================================


def cd(*subdir, mkdir=False, cwd=None, back_check=False, **kwargs):
    """
    Get the full pathname of a directory (or file).

    :param subdir: name of a directory or names of directories (and/or a filename)
    :type subdir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param cwd: current working directory, defaults to ``None``
    :type cwd: str or os.PathLike[str] or bytes or os.Path[bytes] or None
    :param back_check: whether to check if a parent directory exists, defaults to ``False``
    :type back_check: bool
    :param kwargs: [optional] parameters (e.g. ``mode=0o777``) of `os.makedirs`_
    :return: full pathname of a directory or that of a file
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> from pyhelpers.dirs import cd
        >>> import os
        >>> import pathlib

        >>> current_wd = cd()  # Current working directory
        >>> os.path.relpath(current_wd)
        '.'

        >>> # The directory will be created if it does not exist
        >>> path_to_tests_dir = cd("tests")
        >>> os.path.relpath(path_to_tests_dir)
        'tests'

        >>> path_to_tests_dir = cd(pathlib.Path("tests"))
        >>> os.path.relpath(path_to_tests_dir)
        'tests'
    """

    # Current working directory
    path = os.getcwd() if cwd is None else copy.copy(cwd.decode() if isinstance(cwd, bytes) else cwd)

    if back_check:
        while not os.path.exists(path):
            path = os.path.dirname(path)

    for x in subdir:
        if isinstance(x, bytes):
            x = x.decode()
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
    :type dir_name: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return: full pathname of an altered working directory (changed from the directory ``dir_name``)
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import go_from_altered_cwd
        >>> import os

        >>> init_cwd = os.getcwd()
        >>> init_cwd
        '<cwd>'

        >>> # Change the current working directory to "/new_cwd"
        >>> new_cwd = "\\new_cwd"
        >>> os.mkdir(new_cwd)
        >>> os.chdir(new_cwd)

        >>> # Get the full path to a folder named "tests"
        >>> path_to_tests = go_from_altered_cwd(dir_name="tests")
        >>> path_to_tests
        '<new_cwd>\\tests'

        >>> # Get the full path to a directory one level above the current working directory
        >>> path_to_tests_ = go_from_altered_cwd(dir_name="\\tests")
        >>> path_to_tests_ == os.path.join(os.path.dirname(os.getcwd()), "tests")
        True

        >>> os.chdir(init_cwd)
        >>> os.rmdir(new_cwd)
    """

    dir_name_ = dir_name.decode() if isinstance(dir_name, bytes) else dir_name
    target = cd(dir_name_, **kwargs)

    if os.path.isdir(target):
        altered_cwd = target

    else:
        original_cwd = os.path.dirname(target)
        altered_cwd = os.path.join(original_cwd, dir_name_)

        if altered_cwd == target:
            pass

        else:
            while not os.path.isdir(altered_cwd):
                original_cwd = os.path.dirname(original_cwd)
                if original_cwd == cd():
                    break
                else:
                    altered_cwd = os.path.join(original_cwd, dir_name_)

    return altered_cwd


def cdd(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under ``data_dir``.

    :param subdir: name of directory or names of directories (and/or a filename)
    :type subdir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param data_dir: name of a directory where data is (or will be) stored, defaults to ``"data"``
    :type data_dir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return path: full pathname of a directory (or a file) under ``data_dir``
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import cdd, delete_dir
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


def cd_data(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under ``data_dir`` of a package.

    :param subdir: name of directory or names of directories (and/or a filename)
    :type subdir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param data_dir: name of a directory to store data, defaults to ``"data"``
    :type data_dir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: [optional] parameters (e.g. ``mode=0o777``) of `os.makedirs`_
    :return: full pathname of a directory or that of a file under ``data_dir`` of a package
    :rtype: str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> from pyhelpers.dirs import cd_data
        >>> import os

        >>> path_to_dat_dir = cd_data("tests", mkdir=False)

        >>> os.path.relpath(path_to_dat_dir)
        'pyhelpers\\data\\tests'
    """

    data_dir_ = data_dir.decode() if isinstance(data_dir, bytes) else str(data_dir)
    path = pkg_resources.resource_filename(__name__, data_dir_)

    for x in subdir:
        path = os.path.join(path, x.decode() if isinstance(x, bytes) else x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '' or ext == b'':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


# ==================================================================================================
# Directory validation
# ==================================================================================================


def is_dir(path_to_dir):
    """
    Check whether a directory-like string is a (valid) directory name.

    See also [`DIRS-IVD-1 <https://stackoverflow.com/questions/9532499/>`_] and
    [`DIRS-IVD-2 <https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499->`_].

    :param path_to_dir: pathname of a directory
    :type path_to_dir: str or bytes
    :return: whether the input is a path-like string that describes a directory name
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import cd, is_dir

        >>> x = "tests"
        >>> is_dir(x)
        False

        >>> x = "/tests"
        >>> is_dir(x)
        True

        >>> x = cd("tests")
        >>> is_dir(x)
        True
    """

    try:
        root_dirname_, pathname_ = os.path.splitdrive(path_to_dir)

        root_dirname = root_dirname_ if root_dirname_ else '.'
        root_dirname += os.path.sep

        for pathname_part in re.split(r'[\\/]', pathname_):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == 123:  # ERROR_INVALID_NAME
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False

    except TypeError:
        return False

    else:
        return bool(os.path.dirname(path_to_dir))


def validate_dir(path_to_dir=None, subdir="", msg="Invalid input!", **kwargs):
    """
    Validate the pathname of a directory.

    :param path_to_dir: pathname of a data directory, defaults to ``None``
    :type path_to_dir: str or os.PathLike[str] or bytes or os.Path[bytes] or None
    :param subdir: name of a subdirectory to be examined if ``directory=None``, defaults to ``""``
    :type subdir: str or os.PathLike[str] or bytes or os.Path[bytes]
    :param msg: error message if ``data_dir`` is not a full pathname, defaults to ``"Invalid input!"``
    :type msg: str
    :param kwargs: [optional] parameters of the function :py:func:`pyhelpers.dir.cd`
    :return: valid full pathname of a directory
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import validate_dir
        >>> import os

        >>> dat_dir = validate_dir()
        >>> os.path.relpath(dat_dir)
        '.'

        >>> dat_dir = validate_dir("tests")
        >>> os.path.relpath(dat_dir)
        'tests'

        >>> dat_dir = validate_dir(subdir="data")
        >>> os.path.relpath(dat_dir)
        'data'
    """

    if path_to_dir:
        if isinstance(path_to_dir, pathlib.Path):
            path_to_dir_ = str(path_to_dir)
        elif isinstance(path_to_dir, bytes):
            path_to_dir_ = path_to_dir.decode()
        else:
            path_to_dir_ = path_to_dir
            assert isinstance(path_to_dir_, str), msg

        if not os.path.isabs(path_to_dir_):  # Use default file directory
            data_dir_ = cd(path_to_dir_.strip('.\\.'), **kwargs)

        else:
            assert os.path.isabs(path_to_dir_), msg
            data_dir_ = os.path.realpath(path_to_dir_.lstrip('.\\.'))

    else:
        data_dir_ = cd(subdir, **kwargs) if subdir else cd()

    return data_dir_


# ==================================================================================================
# Directory removal
# ==================================================================================================


def _delete_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory.

    :param path_to_dir: pathname of a directory
    :type path_to_dir: str or bytes or os.PathLike[str] or os.PathLike[bytes]
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `shutil.rmtree`_ or `os.rmdir`_

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
    .. _`os.rmdir`: https://docs.python.org/3/library/os.html#os.rmdir

    **Tests**::

        >>> from pyhelpers.dirs import cd, _delete_dir
        >>> import os

        >>> dir_path = cd("test_dir", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? True
        >>> _delete_dir(dir_path, verbose=True)
        To delete the directory "test_dir\\"
        ? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\" exists? False

        >>> dir_path = cd("test_dir", "folder", mkdir=True)
        >>> rel_dir_path = os.path.relpath(dir_path)

        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? True
        >>> _delete_dir(cd("test_dir"), verbose=True)
        The directory "test_dir\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "test_dir\\" ... Done.
        >>> print('The directory "{}\\" exists? {}'.format(rel_dir_path, os.path.exists(dir_path)))
        The directory "test_dir\\folder\\" exists? False
    """

    dir_pathname = _check_rel_pathname(path_to_dir)

    try:
        if os.listdir(dir_pathname):
            cfm_msg = f"The directory \"{dir_pathname}\\\" is not empty.\nConfirmed to delete it\n?"
            func = shutil.rmtree
        else:
            cfm_msg = f"To delete the directory \"{dir_pathname}\\\"\n?"
            func = os.rmdir

        if confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                print("Deleting \"{}\\\"".format(path_to_dir), end=" ... ")

            func(dir_pathname, **kwargs)

        if verbose:
            if not os.path.exists(path_to_dir):
                print("Done.")
            else:
                print("Cancelled.")

    except Exception as e:
        print("Failed. {}.".format(e))


def delete_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory or directories.

    :param path_to_dir: pathname (or pathnames) of a directory (or directories)
    :type path_to_dir: str or bytes or os.PathLike[str] or os.PathLike[bytes] or collections.abc.Sequence
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `shutil.rmtree`_ or `os.rmdir`_

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
    .. _`os.rmdir`: https://docs.python.org/3/library/os.html#os.rmdir

    **Examples**::

        >>> from pyhelpers.dirs import cd, delete_dir
        >>> import os

        >>> test_dirs = []
        >>> for x in range(3):
        ...     test_dirs.append(cd("tests", f"test_dir{x}", mkdir=True))
        ...     if x == 0:
        ...         cd("tests", f"test_dir{x}", "a_folder", mkdir=True)
        ...     elif x == 1:
        ...         open(cd("tests", f"test_dir{x}", "file"), 'w').close()

        >>> delete_dir(path_to_dir=test_dirs, verbose=True)
        To delete the following directories:
            "tests\\test_dir0\\" (Not empty)
            "tests\\test_dir1\\" (Not empty)
            "tests\\test_dir2\\"
        ? [No]|Yes: yes
        Deleting "tests\\test_dir0\\" ... Done.
        Deleting "tests\\test_dir1\\" ... Done.
        Deleting "tests\\test_dir2\\" ... Done.
    """

    if isinstance(path_to_dir, collections.abc.Sequence) and not isinstance(path_to_dir, (str, bytes)):
        dir_pathnames = [_check_rel_pathname(p) for p in path_to_dir]
    else:
        dir_pathnames = [_check_rel_pathname(path_to_dir)]

    pn = ["\"" + p + ("\\\" (Not empty)" if os.listdir(p) else "\\\"") for p in dir_pathnames]
    if len(pn) == 1:
        cfm_msg = f"To delete the directory {pn[0]}\n?"
    else:
        temp = "\n\t".join(pn)
        cfm_msg = f"To delete the following directories:\n\t{temp}\n?"

    if confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
        for dir_pathname in dir_pathnames:
            _delete_dir(dir_pathname, confirmation_required=False, verbose=verbose, **kwargs)


# ==================================================================================================
# Directory
# ==================================================================================================

# Format the file path to be used for cross-platform compatibility
# convert OS path to standard linux path
def path2linux(path: Union[str, pathlib.Path]) -> str:
    """Convert path to a linux path, linux path is executable in windows, linux and mac

    Args:
        path (Union[str, pathlib.Path]): a string or pathlib.Path object

    Returns:
        str: standard linux path

    Examples:
        >>> from pyhelpers.dirs import path2linux
        >>> path2linux("C:\\Users\\user\\Desktop\\test.txt")
        'C:/Users/user/Desktop/test.txt'
    """

    try:
        return path.replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def get_filenames_from_folder_by_type(dir_name: str, file_type: str = "txt", isTraverseSubdirectory: bool = False) -> list:
    """Get all files in the folder with the specified file type

    Args:
        dir_name (str)                         : the folder path
        file_type (str, optional)              : the exact file type to specify, if file_type is "*" or "all", return all files in the folder. Defaults to "txt".
        isTraverseSubdirectory (bool, optional): get files inside the subfolder or not, if True, will traverse all subfolders. Defaults to False.

    Returns:
        list: a list of file paths

    Examples:
        # get all files in the folder without traversing subfolder
        >>> from pyhelpers.dirs import get_filenames_from_folder_by_type
        >>> get_filenames_from_folder_by_type("C:/Users/user/Desktop", "txt")
        ['C:/Users/user/Desktop/test.txt']

        # get all files in the folder with traversing subfolder
        >>> from pyhelpers.dirs import get_filenames_from_folder_by_type
        >>> get_filenames_from_folder_by_type("C:/Users/user/Desktop", "txt", isTraverseSubdirectory=True)
        ['C:/Users/user/Desktop/test.txt', 'C:/Users/user/Desktop/sub_folder/test2.txt']
    """

    if isTraverseSubdirectory:
        files_list = []
        for root, dirs, files in os.walk(dir_name):
            files_list.extend([os.path.join(root, file) for file in files])
        if file_type in {"*", "all"}:
            return [path2linux(file) for file in files_list]
        return [path2linux(file) for file in files_list if file.split(".")[-1] == file_type]

    # files in the first layer of the folder
    if file_type in {"*", "all"}:
        return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name)]
    return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name) if file.split(".")[-1] == file_type]


def check_required_files_exist(required_files: list, dir_name: str) -> bool:
    """Check if all required files exist in the directory

    Args:
        required_files (list): a list of required file names
        dir_files (list)     : a list of file names in the directory

    Returns:
        bool: True if all required files exist, False otherwise

    Examples:
        # check if all required files exist in the directory
        >>> from pyhelpers.dirs import check_required_files_exist
        >>> check_required_files_exist(["test.txt", "test2.txt"], "C:/Users/user/Desktop")
        True

        # if not all required files exist, print the missing files
        >>> from pyhelpers.dirs import check_required_files_exist
        >>> check_required_files_exist(["test.txt", "test2.txt", "test3.txt"], "C:/Users/user/Desktop")
        Error: Required files are not satisfied, missing files are: ['test3.txt']
    """

    dir_files = get_filenames_from_folder_by_type(dir_name, file_type="*")

    # format the required file name to standard linux path
    required_files = [path2linux(os.path.abspath(filename)) for filename in required_files]

    required_files_short = [filename.split("/")[-1] for filename in required_files]
    dir_files_short = [filename.split("/")[-1] for filename in dir_files]

    # mask have the same length as required_files
    mask = [file in dir_files_short for file in required_files_short]
    if all(mask):
        return True

    print(f"Error: Required files are not satisfied, \
          missing files are: {[required_files_short[i] for i in range(len(required_files_short)) if not mask[i]]}")

    return False


def validate_filename(path_filename: str, suffix_num: int = 1) -> str:
    """If the filename exist, then create new filename with suffix _1, _2, ...

    Args:
        path_filename (str): the file path

    Returns:
        str: a validated file name

    Examples:
        # if the file does not exist, return the same file name
        >>> from pyhelpers.dirs import validate_filename
        >>> validate_filename("C:/Users/user/Desktop/test.txt")
        'C:/Users/user/Desktop/test.txt'

        # if the file exist, return the new file name with suffix _1
        >>> from pyhelpers.dirs import validate_filename
        >>> validate_filename("C:/Users/user/Desktop/test.txt")
        'C:/Users/user/Desktop/test_1.txt'

        # if the file exist, return the new file name with suffix _2
        >>> from pyhelpers.dirs import validate_filename
        >>> validate_filename("C:/Users/user/Desktop/test.txt")
        'C:/Users/user/Desktop/test_2.txt'
    """

    # convert the path to standard linux path
    filename_abspath = path2linux(os.path.abspath(path_filename))

    # get the file suffix
    file_suffix = filename_abspath.split(".")[-1]
    file_without_suffix = filename_abspath[:-len(file_suffix) - 1]

    # if the file does not exist, return the same file name
    if os.path.exists(filename_abspath):
        filename_update = f"{file_without_suffix}_{suffix_num}.{file_suffix}"
        return validate_filename(filename_update, suffix_num + 1)
    return filename_abspath
