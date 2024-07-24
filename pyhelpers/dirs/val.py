"""
Directory/file validation.
"""

import errno
import os
import pathlib
import re

from .nav import cd
from .._cache import _check_rel_pathname


def path2linux(path):
    """
    Convert a path to a standardized Linux file path format for cross-platform compatibility.

    This function:

        - Formats the file path to ensure compatibility across Windows, Linux and macOS.
        - Converts an OS-specific path to a standard Linux path.

    :param path: Absolute or relative pathname.
    :type path: str | bytes | os.PathLike
    :return: Standard Linux pathname.
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
    Convert a pathname to a standard Linux file path format.

    This function serves as an alternative to :func:`~pyhelpers.dirs.path2linux`.

    :param pathname: Absolute or relative pathname.
    :type pathname: str | pathlib.Path
    :return: Standard Linux pathname.
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
    Check whether a string represents a valid directory path.

    This function verifies whether the input string is a valid directory path. See also
    [`DIRS-IVD-1 <https://stackoverflow.com/questions/9532499/>`_] and [`DIRS-IVD-2
    <https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499->`_].

    :param path_to_dir: Pathname of a directory.
    :type path_to_dir: str | bytes
    :return: ``True`` if the input string is a valid directory path, ``False`` otherwise.
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

    :param path_to_dir: Pathname of a data directory;
        if ``path_to_dir=None`` (default),
        it examines ``subdir`` to construct a valid directory path.
    :type path_to_dir: str | os.PathLike[str] | bytes | os.PathLike[bytes] | None
    :param subdir: Name of a subdirectory to be examined if ``path_to_dir=None``;
        defaults to ``""``.
    :type subdir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param msg: Error message if `path_to_dir` is not a valid full pathname;
        defaults to ``"Invalid input!"``.
    :type msg: str
    :param kwargs: [Optional] Additional parameters for the function :func:`pyhelpers.dirs.cd`.
    :return: Valid full pathname of a directory.
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
            data_dir_ = _check_rel_pathname(path_to_dir_.lstrip('.\\.'))

    else:
        data_dir_ = cd(subdir, **kwargs) if subdir else cd()

    return data_dir_


def validate_filename(file_pathname, suffix_num=1):
    """
    Validate the filename and create a new filename with a suffix if the original exists.

    If the file specified by ``file_pathname`` exists, this function generates a new filename
    by appending a suffix such as ``"(1)"``, ``"(2)"``, etc., to make it unique.

    :param file_pathname: Pathname of a file.
    :type file_pathname: str
    :param suffix_num: Number to use as a suffix if the filename exists; defaults to ``1``.
    :type suffix_num: int
    :return: Validated file name (with a unique suffix if necessary).
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
        >>> # When "test(1).txt" exists, it returns a pathname of a file named "test(2).txt"
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
    Get paths of files in a directory matching the specified file extension.

    This function retrieves paths of files within the directory specified by ``path_to_dir``.
    Optionally, it filters files by the exact ``file_ext`` specified.
    If ``file_ext=None``, it returns paths for all files.
    If ``incl_subdir=True``, it traverses subdirectories recursively.

    :param path_to_dir: Path to the directory.
    :type path_to_dir: str | os.PathLike
    :param file_ext: Exact file extension to filter files; defaults to `None`.
    :type file_ext: str | None
    :param incl_subdir: Whether to include files from subdirectories;
        when ``incl_subdir=True``, it includes files from all subdirectories recursively;
        defaults to `False`.
    :type incl_subdir: bool
    :return: List of file paths matching the criteria.
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
        >>> # Get absolute pathnames of all files contained in the folder (incl. all subdirectories)
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
    Check if specified files exist within a given directory.

    :param filenames: Filenames to check for existence.
    :type filenames: typing.Iterable
    :param path_to_dir: Path to the directory where files are to be checked.
    :type path_to_dir: str | os.PathLike
    :return: ``True`` if all queried files exist in the directory, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import check_files_exist
        >>> test_dir_name = "tests/data"
        >>> # Check if all required files exist in the directory
        >>> check_files_exist(["dat.csv", "dat.txt"], test_dir_name)
        True
        >>> # If not all required files exist, print the missing files
        >>> check_files_exist(("dat.csv", "dat.txt", "dat_0.txt"), test_dir_name)
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
