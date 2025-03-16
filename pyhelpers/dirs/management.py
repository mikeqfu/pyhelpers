"""
Utilities for directory/file management.
"""

import collections.abc
import os
import shutil

from .._cache import _add_slashes, _check_relative_pathname, _confirmed, _print_failure_message


def add_slashes(pathname, normalized=True, surrounded_by='"'):
    """
    Adds leading and/or trailing slashes to a given pathname for formatting or display purposes.

    :param pathname: The pathname of a file or directory.
    :type pathname: str | bytes | os.PathLike
    :param normalized: Whether to normalize the returned pathname; defaults to ``True``.
    :type normalized: bool
    :param surrounded_by: A string by which the returned pathname is surrounded;
        defaults to ``'"'``.
    :type surrounded_by: str
    :return: A formatted pathname with added slashes.
    :rtype: str

    **Examples**::

        >>> from pyhelpers._cache import _add_slashes
        >>> _add_slashes("pyhelpers\\data")
        '"./pyhelpers/data/"'
        >>> _add_slashes("pyhelpers\\data", normalized=False)  # on Windows
        '".\\pyhelpers\\data\\"'
        >>> _add_slashes("pyhelpers\\data\\pyhelpers.dat")
        '"./pyhelpers/data/pyhelpers.dat"'
        >>> _add_slashes("C:\\Windows")  # on Windows
        '"C:/Windows/"'
    """

    return _add_slashes(pathname, normalized=normalized, surrounded_by=surrounded_by)


def _delete_dir(path_to_dir, confirmation_required=True, verbose=False, raise_error=True, **kwargs):
    """
    Deletes a directory.

    :param path_to_dir: Pathname of the directory.
    :type path_to_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes]
    :param confirmation_required: Whether to prompt for confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False``, the error will be suppressed; defaults to ``True``.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `shutil.rmtree`_ or
        `os.rmdir`_.

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
    .. _`os.rmdir`: https://docs.python.org/3/library/os.html#os.rmdir

    **Tests**::

        >>> from pyhelpers.dirs.management import _delete_dir
        >>> from pyhelpers._cache import _add_slashes
        >>> from pyhelpers.dirs import cd
        >>> import os
        >>> dir_path = cd("tests", "test_dir", mkdir=True)
        >>> rel_dir_path = _add_slashes(os.path.relpath(dir_path))
        >>> print(f'The directory {rel_dir_path} exists? {os.path.exists(dir_path)}')
        The directory ".\\tests\\test_dir\\" exists? True
        >>> _delete_dir(dir_path, verbose=True)
        To delete the directory ".\\tests\\test_dir\\"
        ? [No]|Yes: yes
        Deleting ".\\tests\\test_dir\\" ... Done.
        >>> print(f'The directory {rel_dir_path} exists? {os.path.exists(dir_path)}')
        The directory ".\\tests\\test_dir\\" exists? False
        >>> dir_path = cd("tests", "test_dir", "folder", mkdir=True)
        >>> rel_dir_path = _add_slashes(os.path.relpath(dir_path))
        >>> print(f'The directory {rel_dir_path} exists? {os.path.exists(dir_path)}')
        The directory ".\\tests\\test_dir\\folder\\" exists? True
        >>> _delete_dir(cd("tests", "test_dir"), verbose=True)
        The directory ".\\tests\\test_dir\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting ".\\tests\\test_dir\\" ... Done.
        >>> print(f'The directory {rel_dir_path} exists? {os.path.exists(dir_path)}')
        The directory ".\\tests\\test_dir\\folder\\" exists? False
    """

    rel_path_to_dir = _check_relative_pathname(path_to_dir)

    try:
        path_to_dir_ = _add_slashes(rel_path_to_dir)

        if os.listdir(rel_path_to_dir):
            cfm_msg = f"The directory {path_to_dir_} is not empty.\nConfirmed to delete it\n?"
            func = shutil.rmtree
        else:
            cfm_msg = f"To delete the directory {path_to_dir_}\n?"
            func = os.rmdir

        if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                print(f"Deleting {path_to_dir_}", end=" ... ")

            func(rel_path_to_dir, **kwargs)

        if verbose:
            if not os.path.exists(path_to_dir):
                print("Done.")
            else:
                print("Cancelled.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def delete_dir(path_to_dir, confirmation_required=True, verbose=False, raise_error=False, **kwargs):
    """
    Deletes a directory or directories.

    :param path_to_dir: Pathname(s) of the directory (or directories).
    :type path_to_dir: str | bytes | os.PathLike | collections.abc.Sequence
    :param confirmation_required: Whether to prompt for confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `shutil.rmtree`_ or
        `os.rmdir`_.

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
            ".\\tests\\test_dir0\\" (Not empty)
            ".\\tests\\test_dir1\\" (Not empty)
            ".\\tests\\test_dir2\\"
        ? [No]|Yes: yes
        Deleting ".\\tests\\test_dir0\\" ... Done.
        Deleting ".\\tests\\test_dir1\\" ... Done.
        Deleting ".\\tests\\test_dir2\\" ... Done.
    """

    if (isinstance(path_to_dir, collections.abc.Sequence) and
            not isinstance(path_to_dir, (str, bytes))):
        dir_pathnames = [_check_relative_pathname(p) for p in path_to_dir]
    else:
        dir_pathnames = [_check_relative_pathname(path_to_dir)]

    pn = [_add_slashes(p) + (" (Not empty)" if os.listdir(p) else "") for p in dir_pathnames]
    if len(pn) == 1:
        cfm_msg = f"To delete the directory {pn[0]}\n?"
    else:
        temp = "\n\t".join(pn)
        cfm_msg = f"To delete the following directories:\n\t{temp}\n?"

    if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
        for dir_pathname in dir_pathnames:
            _delete_dir(
                dir_pathname, confirmation_required=False, verbose=verbose, raise_error=raise_error,
                **kwargs)
