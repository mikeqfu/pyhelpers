"""
Utilities for validating paths, confirming file existence and sanitizing inputs.
"""

import errno
import os
import re

from .management import get_file_paths


def is_dir_path(dir_path):
    """
    Check whether a string is formatted as a directory path.

    This function performs a syntax-only check: it does not verify that the directory
    actually exists, only that the string is shaped like a directory path and does not
    contain characters or a length that the operating system would reject outright.
    See also `this discussion on Stack Overflow <https://stackoverflow.com/questions/9532499/>`_
    and the `Windows System Error Codes reference
    <https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499->`_.

    :param dir_path: Pathname of a directory.
    :type dir_path: str | bytes | pathlib.Path | os.PathLike
    :return: ``True`` if ``dir_path`` is formatted as a valid directory path, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import cd, is_dir_path

        >>> is_dir_path("tests")
        False

        >>> is_dir_path("/tests")
        True

        >>> is_dir_path(cd("tests"))
        True

        >>> is_dir_path(".\\tests/")
        True
    """

    if not dir_path:
        return False

    try:
        path_str = os.fsdecode(dir_path)

        try:
            os.lstat(path_str)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 123:  # ERROR_INVALID_NAME (Windows)
                return False
            if exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                return False

    except (TypeError, ValueError):
        return False

    else:  # Final heuristic: does it "look" like a directory?
        if path_str.endswith(("/", "\\")):  # Ends with a separator
            return True

        has_dir_structure = bool(os.path.dirname(path_str))  # e.g. "./tests" has a parent
        _, ext = os.path.splitext(path_str)

        return has_dir_structure and not ext


def validate_filename(file_path, suffix_num=1):
    """
    Validate a filename, generating a uniquely suffixed name if the file already exists.

    If the file specified by ``file_path`` already exists, this function appends a numeric
    suffix such as ``"(1)"``, ``"(2)"``, etc. to the filename (before its extension, if any)
    until it finds a pathname that doesn't already exist. A pre-existing numeric suffix on
    ``file_path`` itself (e.g. from a prior call) is stripped before a new one is generated,
    so repeated calls don't accumulate suffixes.

    :param file_path: Pathname of a file.
    :type file_path: str | os.PathLike
    :param suffix_num: Starting number to use as a suffix if the filename already exists.
        Defaults to ``1``.
    :type suffix_num: int
    :return: Validated pathname of a file (with a unique numeric suffix if necessary).
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
        >>> os.path.isfile(test_file_pathname)
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
    normalized_path = os.path.normpath(file_path)

    # Get the file suffix
    parent_dir, basename = os.path.split(normalized_path)
    stem, ext = os.path.splitext(basename)

    # Strip a pre-existing numeric "(N)" suffix so repeated calls don't accumulate them
    # (e.g. "test(1)" -> "test", so a second call produces "test(2)", not "test(1)(2)")
    stem = re.sub(r"\(\d+\)$", "", stem)

    candidate_path = normalized_path
    n = suffix_num

    while os.path.exists(candidate_path):
        candidate_path = os.path.join(parent_dir, f"{stem}({n}){ext}")
        n += 1

    return candidate_path


def check_files_exist(filenames, dir_path, verbose=False, **kwargs):
    """
    Check whether specified files exist within a given directory.

    This function compares files by basename only, not by their full relative path -- if
    ``filenames`` includes a path with subdirectory components, only the final filename
    portion is compared, so a same-named file located in a *different* subdirectory of
    ``dir_path`` (e.g. when ``incl_subdir=True`` is passed via ``kwargs``) would count as
    a match.

    :param filenames: Filenames to check for existence.
    :type filenames: typing.Iterable
    :param dir_path: Pathname of the directory in which to check for the files.
    :type dir_path: str | os.PathLike
    :param verbose: Whether to print relevant information to the console. Defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for
        :func:`~pyhelpers.dirs.validation.get_file_paths` (e.g. ``incl_subdir=True`` to also
        check files within subdirectories).
    :return: ``True`` if all queried files exist in the directory, ``False`` otherwise.
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.dirs import check_files_exist

        >>> test_dir_name = "tests/data"

        >>> # Check if all required files exist in the directory
        >>> check_files_exist(["dat.csv", "dat.txt"], dir_path=test_dir_name)
        True

        >>> # If not all required files exist, print the missing files
        >>> check_files_exist(("dat.csv", "dat.txt", "dat_0.txt"), test_dir_name, verbose=True)
        Error: Required files are not satisfied, missing files are: ['dat_0.txt']
        False
    """

    dir_files = get_file_paths(dir_path=dir_path, file_ext="*", normalized=False, **kwargs)

    # # `os.path.basename` isolates the filename regardless of which separator style the input uses
    required_base_names = [os.path.basename(filename) for filename in filenames]
    dir_base_names = set(os.path.basename(filename) for filename in dir_files)

    missing_files = [name for name in required_base_names if name not in dir_base_names]

    if missing_files:
        if verbose:
            print(f"Error: Required files are not satisfied, missing files are: {missing_files}")
        return False

    return True
