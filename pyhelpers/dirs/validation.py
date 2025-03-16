"""
Utilities for directory/file validation.
"""

import errno
import os
import pathlib
import re

from .navigation import cd
from .._cache import _check_relative_pathname, _normalize_pathname


def normalize_pathname(pathname, sep="/", add_slash=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Converts a pathname to a consistent file path format for cross-platform compatibility.

    This function formats a file (or an OS-specific) path to ensure compatibility across
    Windows and Ubuntu (and other Unix-like systems).

    :param pathname: A pathname.
    :type pathname: str | bytes | pathlib.Path | os.PathLike
    :param sep: File path separator used by the operating system; defaults to ``"/"``
        (forward slash) for both Windows and Ubuntu (and other Unix-like systems).
    :type sep: str
    :param add_slash: If ``True``, adds a leading slash (and, if appropriate, a trailing slash)
        to the returned pathname; defaults to ``False``.
    :type add_slash: bool
    :return: Pathname of a consistent file path format.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import normalize_pathname
        >>> import os
        >>> import pathlib
        >>> normalize_pathname("tests\\data\\dat.csv")
        'tests/data/dat.csv'
        >>> normalize_pathname("tests\\data\\dat.csv", add_slash=True)  # on Windows
        './tests/data/dat.csv'
        >>> normalize_pathname("tests//data/dat.csv")
        'tests/data/dat.csv'
        >>> pathname = pathlib.Path("tests\\data/dat.csv")
        >>> normalize_pathname(pathname, sep=os.path.sep)  # On Windows
        'tests\\data\\dat.csv'
        >>> normalize_pathname(pathname, sep=os.path.sep, add_slash=True)  # On Windows
        '.\\tests\\data\\dat.csv'
    """

    return _normalize_pathname(pathname=pathname, sep=sep, add_slash=add_slash, **kwargs)


def is_dir(path_to_dir):
    """
    Checks whether a string represents a valid directory path.

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
    Validates the pathname of a directory.

    :param path_to_dir: Pathname of a data directory;
        if ``path_to_dir=None`` (default),
        it examines ``subdir`` to construct a valid directory path.
    :type path_to_dir: str | os.PathLike | bytes | None
    :param subdir: Name of a subdirectory to be examined if ``path_to_dir=None``;
        defaults to ``""``.
    :type subdir: str | os.PathLike | bytes
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
            data_dir_ = _check_relative_pathname(path_to_dir_.lstrip('.\\.'))

    else:
        data_dir_ = cd(subdir, **kwargs) if subdir else cd()

    return data_dir_


def validate_filename(file_pathname, suffix_num=1):
    """
    Validates the filename and create a new filename with a suffix if the original exists.

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
        >>> os.path.exists(test_file_pathname)
        False
        >>> # If the file does not exist, the function returns the same filename
        >>> file_pathname_0 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_0)  # on Windows
        'tests\\data\\test.txt'
        >>> # Create a file named "test.txt"
        >>> open(test_file_pathname, 'w').close()
        >>> os.path.exists(test_file_pathname)
        True
        >>> # As "test.txt" exists, the function returns a new pathname ending with "test(1).txt"
        >>> file_pathname_1 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_1)  # on Windows
        'tests\\data\\test(1).txt'
        >>> # When "test(1).txt" exists, it returns a pathname of a file named "test(2).txt"
        >>> open(file_pathname_1, 'w').close()
        >>> os.path.exists(file_pathname_1)
        True
        >>> file_pathname_2 = validate_filename(test_file_pathname)
        >>> os.path.relpath(file_pathname_2)  # on Windows
        'tests\\data\\test(2).txt'
        >>> # Remove the created files
        >>> for x in [file_pathname_0, file_pathname_1]:
        ...     os.remove(x)
    """

    # Convert the path to standard linux path
    filename_abspath = os.path.normpath(file_pathname)

    # Get the file suffix
    file_suffix = filename_abspath.split(".")[-1]
    file_without_suffix = filename_abspath[:-len(file_suffix) - 1]

    # Remove the suffix if the file name contains "("
    if "(" in file_without_suffix:
        file_without_suffix = file_without_suffix.split("(")[0]

    # If the file does not exist, return the same file name
    if os.path.exists(filename_abspath):
        filename_update = f"{file_without_suffix}({suffix_num}).{file_suffix}"
        return validate_filename(filename_update, suffix_num + 1)

    return filename_abspath


def get_file_pathnames(path_to_dir, file_ext=None, incl_subdir=False, abs_path=False,
                       normalized=True, add_slash=False):
    """
    Gets paths of files in a directory matching the specified file extension.

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
    :param abs_path: Whether to return absolute pathname(s).
    :type abs_path: bool
    :param normalized: Whether to normalize the returned pathname; defaults to ``True``.
    :type normalized: bool
    :param add_slash: If ``True``, adds a leading slash (and, if appropriate, a trailing slash)
        to the returned pathname; defaults to ``False``.
    :type add_slash: bool
    :return: List of file paths matching the criteria.
    :rtype: list

    **Examples**::

        >>> from pyhelpers.dirs import get_file_pathnames, delete_dir
        >>> from pyhelpers.store import unzip
        >>> import os
        >>> test_dir_name = "tests/data"
        >>> # Get all files in the directory (without subdirectories) on Windows
        >>> get_file_pathnames(test_dir_name, add_slash=True)
        ['./tests/data/csr_mat.npz',
         './tests/data/dat.csv',
         './tests/data/dat.feather',
         './tests/data/dat.joblib',
         './tests/data/dat.json',
         './tests/data/dat.ods',
         './tests/data/dat.pickle',
         './tests/data/dat.pickle.bz2',
         './tests/data/dat.pickle.gz',
         './tests/data/dat.pickle.xz',
         './tests/data/dat.txt',
         './tests/data/dat.xlsx',
         './tests/data/zipped.7z',
         './tests/data/zipped.txt',
         './tests/data/zipped.zip']
        >>> get_file_pathnames(test_dir_name, file_ext=".txt")
        ['tests/data/dat.txt', 'tests/data/zipped.txt']
        >>> output_dir = unzip('tests/data/zipped.zip', ret_output_dir=True)
        >>> os.listdir(output_dir)
        ['zipped.txt']
        >>> # Get absolute pathnames of all files contained in the folder (incl. all subdirectories)
        >>> get_file_pathnames(test_dir_name, file_ext="txt", incl_subdir=True, abs_path=True)
        ['<Parent directories>/tests/data/dat.txt',
         '<Parent directories>/tests/data/zipped.txt',
         '<Parent directories>/tests/data/zipped/zipped.txt']
        >>> delete_dir(output_dir, confirmation_required=False)
    """

    if incl_subdir:
        file_pathnames = [
            os.path.normpath(os.path.join(root, file))
            for root, _, files in os.walk(path_to_dir)
            for file in files
        ]

    else:
        file_pathnames = [
            os.path.normpath(os.path.join(path_to_dir, file))
            for file in os.listdir(path_to_dir)
            if os.path.isfile(os.path.join(path_to_dir, file))
        ]

    if file_ext in {None, "*", "all"}:
        file_pathnames = [
            os.path.abspath(p) if abs_path else p for p in file_pathnames]
    elif file_ext:
        file_pathnames = [
            os.path.abspath(p) if abs_path else p for p in file_pathnames if p.endswith(file_ext)]

    file_pathnames = [
        normalize_pathname(p, add_slash=add_slash) if normalized else p for p in file_pathnames]

    return file_pathnames


def check_files_exist(filenames, path_to_dir, verbose=False, **kwargs):
    """
    Checks if specified files exist within a given directory.

    :param filenames: Filenames to check for existence.
    :type filenames: typing.Iterable
    :param path_to_dir: Path to the directory where files are to be checked.
    :type path_to_dir: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :return: ``True`` if all queried files exist in the directory, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import check_files_exist
        >>> test_dir_name = "tests/data"
        >>> # Check if all required files exist in the directory
        >>> check_files_exist(["dat.csv", "dat.txt"], path_to_dir=test_dir_name)
        True
        >>> # If not all required files exist, print the missing files
        >>> check_files_exist(("dat.csv", "dat.txt", "dat_0.txt"), test_dir_name, verbose=True)
        Error: Required files are not satisfied, missing files are: ['dat_0.txt']
        False
    """

    dir_files = get_file_pathnames(
        path_to_dir=path_to_dir, file_ext="*", normalized=False, **kwargs)

    # Format the required file name to standard linux path
    file_or_pathnames = [os.path.abspath(filename) for filename in filenames]

    required_files_short = [filename.split(os.path.sep)[-1] for filename in file_or_pathnames]
    dir_files_short = [filename.split(os.path.sep)[-1] for filename in dir_files]

    # `mask` have the same length as `filenames`
    mask = [file in dir_files_short for file in required_files_short]

    if all(mask):
        rslt = True

    else:
        err_prt_dat = [
            required_files_short[i] for i in range(len(required_files_short)) if not mask[i]]

        if verbose:
            print(f"Error: Required files are not satisfied, missing files are: {err_prt_dat}")
        rslt = False

    return rslt
