"""Manipulation of directories and/or file paths."""

import collections.abc
import copy
import errno
import importlib.resources
import os
import pathlib
import re
import shutil

from ._cache import _check_rel_pathname
from .ops import confirmed


# ==================================================================================================
# Directory navigation
# ==================================================================================================


def cd(*subdir, mkdir=False, cwd=None, back_check=False, **kwargs):
    """
    Get the full pathname of a directory (or file).

    :param subdir: name of a directory or names of directories (and/or a filename)
    :type subdir: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param cwd: current working directory, defaults to ``None``
    :type cwd: str | os.PathLike[str] | bytes | os.Path[bytes] | None
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
    :type dir_name: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param kwargs: [optional] parameters of the function :func:`pyhelpers.dirs.cd`
    :return: full pathname of an altered working directory (changed from the directory ``path_to_dir``)
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
        >>> path_to_tests = go_from_altered_cwd(path_to_dir="tests")
        >>> path_to_tests
        '<new_cwd>\\tests'

        >>> # Get the full path to a directory one level above the current working directory
        >>> path_to_tests_ = go_from_altered_cwd(path_to_dir="\\tests")
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
    :type subdir: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param data_dir: name of a directory where data is (or will be) stored, defaults to ``"data"``
    :type data_dir: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param mkdir: whether to create a directory, defaults to ``False``
    :type mkdir: bool
    :param kwargs: [optional] parameters of the function :func:`pyhelpers.dirs.cd`
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
    :type subdir: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param data_dir: name of a directory to store data, defaults to ``"data"``
    :type data_dir: str | os.PathLike[str] | bytes | os.Path[bytes]
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
    path = importlib.resources.files(__package__).joinpath(data_dir_)

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
    :type path_to_dir: str | bytes
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
    :type path_to_dir: str | os.PathLike[str] | bytes | os.Path[bytes] | None
    :param subdir: name of a subdirectory to be examined if ``directory=None``, defaults to ``""``
    :type subdir: str | os.PathLike[str] | bytes | os.Path[bytes]
    :param msg: error message if ``data_dir`` is not a full pathname, defaults to ``"Invalid input!"``
    :type msg: str
    :param kwargs: [optional] parameters of the function :func:`pyhelpers.dirs.cd`
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
    :type path_to_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes]
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool | int
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
    :type path_to_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes] | collections.abc.Sequence
    :param confirmation_required: whether to prompt a message for confirmation to proceed,
        defaults to ``True``
    :type confirmation_required: bool
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool | int
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
# Directory/file check
# ==================================================================================================


def path2linux(path):
    """
    Convert path to an uniformat (Linux) file path, which is executable in Windows, Linux and macOS.

    - Format the file path to be used for cross-platform compatibility;
    - Convert OS path to standard Linux path.

    :param path: absolute or relative pathname
    :type path: str | pathlib.Path
    :return: standard linux pathname
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import path2linux
        >>> import pathlib

        >>> path2linux("tests\\data\\dat.csv")
        'tests/data/dat.csv'

        >>> path2linux(pathlib.Path("tests\\data\\dat.csv"))
        'tests/data/dat.csv'
    """

    # noinspection PyBroadException
    try:
        return path.replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def uniform_pathname(pathname):
    """
    An alternative to the function :func:`pyhelpers.dirs.path2linux`.

    :param pathname: absolute or relative pathname
    :type pathname: str | pathlib.Path
    :return: standard linux pathname
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import uniform_pathname
        >>> import pathlib

        >>> uniform_pathname("tests\\data\\dat.csv")
        'tests/data/dat.csv'

        >>> uniform_pathname(pathlib.Path("tests\\data\\dat.csv"))
        'tests/data/dat.csv'
    """

    pathname_ = re.sub(r"\\|\\\\|//", "/", str(pathname))

    return pathname_


def get_rel_pathnames(path_to_dir, file_ext=None, incl_subdir=False):
    """
    Get all files in the folder with the specified file type.

    :param path_to_dir: a folder path
    :type path_to_dir: str
    :param file_ext: exact file type to specify, if file_type is ``"*"`` or ``"all"``,
        return all files in the folder; defaults to ``None``
    :type file_ext: str | None
    :param incl_subdir: whether to get files inside the subfolder, defaults to ``False``;
        when ``incl_subdir=True``, the function traverses all subfolders
    :type incl_subdir: bool
    :return: a list of file paths
    :rtype: list

    **Examples**::

        >>> from pyhelpers.dirs import get_rel_pathnames

        >>> test_dir_name = "tests/data"

        >>> # Get all files in the folder (without sub-folders)
        >>> get_rel_pathnames(test_dir_name)
        ['tests/data/csr_mat.npz',
         'tests/data/dat.csv',
         'tests/data/dat.feather',
         'tests/data/dat.joblib',
         'tests/data/dat.json',
         'tests/data/dat.pickle',
         'tests/data/dat.txt',
         'tests/data/dat.xlsx',
         'tests/data/zipped',
         'tests/data/zipped.7z',
         'tests/data/zipped.txt',
         'tests/data/zipped.zip']

        >>> get_rel_pathnames(test_dir_name, file_ext=".txt")
        ['tests/data/dat.txt', 'tests/data/zipped.txt']

        >>> # Get absolute pathnames of all files contained in the folder (incl. all sub-folders)
        >>> get_rel_pathnames(test_dir_name, file_ext="txt", incl_subdir=True)
        ['tests/data/dat.txt', 'tests/data/zipped.txt', 'tests/data/zipped/zipped.txt']

    """

    if incl_subdir:
        files_list = []
        for root, _, files in os.walk(path_to_dir):
            files_list.extend([os.path.join(root, file) for file in files])

        if file_ext in {None, "*", "all"}:
            return [path2linux(file) for file in files_list]

        return [path2linux(file) for file in files_list if file.endswith(file_ext)]

    # Files in the first layer of the folder
    if file_ext in {None, "*", "all"}:
        return [path2linux(os.path.join(path_to_dir, file)) for file in os.listdir(path_to_dir)]

    return [
        path2linux(os.path.join(path_to_dir, file)) for file in os.listdir(path_to_dir)
        if file.endswith(file_ext)]


def check_files_exist(filenames, path_to_dir):
    """
    Check if queried files exist in a given directory.

    :param filenames: a list of filenames
    :type filenames: list
    :param path_to_dir: a list of filenames in the directory
    :type path_to_dir: str
    :return: ``True`` if all the queried files exist, ``False`` otherwise
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import check_files_exist

        >>> test_dir_name = "tests/data"

        >>> # Check if all required files exist in the directory
        >>> check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
        True

        >>> # If not all required files exist, print the missing files
        >>> check_files_exist(["dat.csv", "dat.txt", "dat_0.txt"], test_dir_name)
        Error: Required files are not satisfied, missing files are: ['dat_0.txt']
        False
    """

    dir_files = get_rel_pathnames(path_to_dir, file_ext="*")

    # Format the required file name to standard linux path
    filenames = [path2linux(os.path.abspath(filename)) for filename in filenames]

    required_files_short = [filename.split("/")[-1] for filename in filenames]
    dir_files_short = [filename.split("/")[-1] for filename in dir_files]

    # `mask` have the same length as `filenames`
    mask = [file in dir_files_short for file in required_files_short]

    if all(mask):
        rslt = True
    else:
        err_prt_dat = [required_files_short[i] for i in range(len(required_files_short)) if not mask[i]]
        err_msg = f"Error: Required files are not satisfied, missing files are: {err_prt_dat}"
        print(err_msg)
        rslt = False

    return rslt


def validate_filename(file_pathname, suffix_num=1):
    """
    If the filename exist, then create new filename with a suffix e.g. (1), (2) and so on.

    :param file_pathname: pathname of a file
    :type file_pathname: str
    :param suffix_num: a number as a suffix appended to the filename, defaults to ``1``
    :type suffix_num: int
    :return: a validated file name
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import validate_filename
        >>> import os

        >>> test_file_pathname = "tests/data/test.txt"

        >>> # When the file does not exist, return the same file name
        >>> os.path.exists(test_file_pathname)
        False
        >>> file_pathname_0 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_0)
        'tests\\data\\test.txt'

        >>> # Create a file named "test.txt"
        >>> open(test_file_pathname, 'w').close()
        >>> os.path.exists(test_file_pathname)
        True
        >>> # As "test.txt" exists, the function returns a new pathname ending with "test(1).txt"
        >>> file_pathname_1 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_1)
        'tests\\data\\test(1).txt'

        >>> # When "test(1).txt" exists, the function returns a pathname of a file named "test(2).txt"
        >>> open(file_pathname_1, 'w').close()
        >>> os.path.exists(file_pathname_1)
        True
        >>> file_pathname_2 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_2)
        'tests\\data\\test(2).txt'

        >>> # Remove the created files
        >>> for x in [file_pathname_0, file_pathname_1]:
        ...     os.remove(x)
    """

    # convert the path to standard linux path
    filename_abspath = path2linux(os.path.abspath(file_pathname))

    # get the file suffix
    file_suffix = filename_abspath.split(".")[-1]
    file_without_suffix = filename_abspath[:-len(file_suffix) - 1]

    # remove the suffix if the file name contains "("
    if "(" in file_without_suffix:
        file_without_suffix = file_without_suffix.split("(")[0]

    # if the file does not exist, return the same file name
    if os.path.exists(filename_abspath):
        filename_update = f"{file_without_suffix}({suffix_num}).{file_suffix}"
        return validate_filename(filename_update, suffix_num + 1)

    return filename_abspath
