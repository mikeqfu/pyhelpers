"""
Directory/file management.
"""

import collections.abc
import os
import shutil

from .._cache import _check_rel_pathname, _confirmed, _print_failure_msg


def _delete_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory.

    :param path_to_dir: Pathname of the directory.
    :type path_to_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes]
    :param confirmation_required: Whether to prompt for confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] additional parameters for the function `shutil.rmtree`_ or
        `os.rmdir`_.

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
    .. _`os.rmdir`: https://docs.python.org/3/library/os.html#os.rmdir

    **Tests**::

        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.dirs.mgmt import _delete_dir
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

        if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                print(f"Deleting \"{path_to_dir}\\\"", end=" ... ")

            func(dir_pathname, **kwargs)

        if verbose:
            if not os.path.exists(path_to_dir):
                print("Done.")
            else:
                print("Cancelled.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def delete_dir(path_to_dir, confirmation_required=True, verbose=False, **kwargs):
    """
    Delete a directory or directories.

    :param path_to_dir: Pathname(s) of the directory (or directories).
    :type path_to_dir: str | bytes | os.PathLike[str] | os.PathLike[bytes] | collections.abc.Sequence
    :param confirmation_required: Whether to prompt for confirmation before proceeding;
        defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] additional parameters for the function `shutil.rmtree`_ or
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
            "tests\\test_dir0\\" (Not empty)
            "tests\\test_dir1\\" (Not empty)
            "tests\\test_dir2\\"
        ? [No]|Yes: yes
        Deleting "tests\\test_dir0\\" ... Done.
        Deleting "tests\\test_dir1\\" ... Done.
        Deleting "tests\\test_dir2\\" ... Done.
    """

    if (isinstance(path_to_dir, collections.abc.Sequence) and
            not isinstance(path_to_dir, (str, bytes))):
        dir_pathnames = [_check_rel_pathname(p) for p in path_to_dir]
    else:
        dir_pathnames = [_check_rel_pathname(path_to_dir)]

    pn = ["\"" + p + ("\\\" (Not empty)" if os.listdir(p) else "\\\"") for p in dir_pathnames]
    if len(pn) == 1:
        cfm_msg = f"To delete the directory {pn[0]}\n?"
    else:
        temp = "\n\t".join(pn)
        cfm_msg = f"To delete the following directories:\n\t{temp}\n?"

    if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
        for dir_pathname in dir_pathnames:
            _delete_dir(dir_pathname, confirmation_required=False, verbose=verbose, **kwargs)
