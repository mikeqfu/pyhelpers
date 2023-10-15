"""
Directory/file validation.
"""

import errno
import os
import pathlib
import re

from .nav import cd
from .._cache import _get_rel_pathname


def path2linux(path):
    """
    Convert path to an uniformat (Linux) file path, which is executable in Windows, Linux and macOS.

    - Format the file path to be used for cross-platform compatibility;
    - Convert OS path to standard Linux path.

    :param path: absolute or relative pathname
    :type path: str | os.PathLike | bytes
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
    An alternative to the function :func:`~pyhelpers.dirs.path2linux`.

    :param pathname: absolute or relative pathname
    :type pathname: str | pathlib.Path
    :return: standard linux pathname
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import uniform_pathname
        >>> import pathlib

        >>> uniform_pathname("tests\\data\\dat.csv")
        'tests/data/dat.csv'

        >>> uniform_pathname("tests//data/dat.csv")
        'tests/data/dat.csv'

        >>> uniform_pathname(pathlib.Path("tests\\data/dat.csv"))
        'tests/data/dat.csv'
    """

    pathname_ = re.sub(r"\\|\\\\|//", "/", str(pathname))

    return pathname_


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

        dir_names = re.split(r'[\\/]', validate_dir(pathname_))

        for i in range(len(dir_names)):
            try:
                os.lstat(os.path.join(root_dirname, *dir_names[:i+1]))
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == 123:  # ERROR_INVALID_NAME
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False

    except TypeError:
        return False

    else:
        path_to_dir_, ext = os.path.splitext(path_to_dir)
        return bool(os.path.dirname(path_to_dir_)) and not ext


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
        >>> import pathlib

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
            data_dir_ = _get_rel_pathname(path_to_dir_.lstrip('.\\.'))

    else:
        data_dir_ = cd(subdir, **kwargs) if subdir else cd()

    return data_dir_


def validate_filename(file_pathname, suffix_num=1):
    """
    If the filename exist, then create new filename with a suffix such as "(1)", "(2)", and so on.

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


def get_file_pathnames(path_to_dir, file_ext=None, incl_subdir=False):
    """
    Get all files in the folder with the specified file type.

    :param path_to_dir: a folder path
    :type path_to_dir: str | os.PathLike
    :param file_ext: exact file type to specify, if file_type is ``"*"`` or ``"all"``,
        return all files in the folder; defaults to ``None``
    :type file_ext: str | None
    :param incl_subdir: whether to get files inside the subfolder, defaults to ``False``;
        when ``incl_subdir=True``, the function traverses all subfolders
    :type incl_subdir: bool
    :return: a list of file paths
    :rtype: list

    **Examples**::

        >>> from pyhelpers.dirs import get_file_pathnames

        >>> test_dir_name = "tests/data"

        >>> # Get all files in the folder (without sub-folders)
        >>> get_file_pathnames(test_dir_name)
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

        >>> get_file_pathnames(test_dir_name, file_ext=".txt")
        ['tests/data/dat.txt', 'tests/data/zipped.txt']

        >>> # Get absolute pathnames of all files contained in the folder (incl. all sub-folders)
        >>> get_file_pathnames(test_dir_name, file_ext="txt", incl_subdir=True)
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

    # noinspection PyTypeChecker
    return [
        path2linux(os.path.join(path_to_dir, file)) for file in os.listdir(path_to_dir)
        if file.endswith(file_ext)]


def check_files_exist(filenames, path_to_dir):
    """
    Check if queried files exist in a given directory.

    :param filenames: a list of filenames
    :type filenames: list
    :param path_to_dir: a list of filenames in the directory
    :type path_to_dir: str | os.PathLike
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

    dir_files = get_file_pathnames(path_to_dir, file_ext="*")

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
