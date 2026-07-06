"""
Utilities for directory/file management.
"""

import collections.abc
import os
import shutil

from .._cache import _confirmed, _format_display_path, _get_relative_path, _print_failure_message


def format_display_path(path, normalized=True, surrounded_by='"', is_dir=None, prepend_dot=False):
    """
    Format a path string for display, logging or printing purposes.

    This function generates a visual representation of a path. It can optionally add
    trailing slashes for directories, wrap the output in quotes and prepend a dot-slash
    for relative paths (e.g. when preparing shell commands).

    :param path: The filesystem path to format for display.
    :type path: str | bytes | pathlib.Path | os.PathLike
    :param normalized: Whether to standardize slashes via :func:`~pyhelpers._cache._normalize_path`.
        Defaults to ``True``.
    :type normalized: bool
    :param surrounded_by: A string literal used to wrap the output. Defaults to ``'"'``.
    :type surrounded_by: str
    :param is_dir: Explicitly treat the path as a directory. If ``None``, the filesystem is checked
        first; when the path does not exist, this falls back to a heuristic that treats a path
        without a file extension as a directory (which can misclassify extensionless files such
        as ``"Makefile"`` or ``"LICENSE"``). Defaults to ``None``.
    :type is_dir: bool | None
    :param prepend_dot: If ``True``, prepends a ``./`` (or native OS equivalent) to
        paths that are not absolute. Defaults to ``False``.
    :type prepend_dot: bool
    :return: Formatted pathname with configured slashes and wrappers.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import format_display_path

        >>> format_display_path("pyhelpers\\data")
        '"pyhelpers/data/"'

        >>> format_display_path("pyhelpers\\data", normalized=False)  # on Windows
        '"pyhelpers\\data\\"'

        >>> format_display_path("pyhelpers\\data\\pyhelpers.dat", prepend_dot=True)
        '"./pyhelpers/data/pyhelpers.dat"'

        >>> format_display_path("C:\\Windows", prepend_dot=True)  # on Windows
        '"C:/Windows/"'
    """

    return _format_display_path(
        path=path,
        normalized=normalized,
        surrounded_by=surrounded_by,
        is_dir=is_dir,
        prepend_dot=prepend_dot
    )


def _delete_dir(dir_path, confirmation_required=True, verbose=False, indent=None, raise_error=True,
                verbose_label="Deleting", **kwargs):
    # noinspection PyShadowingNames,PyUnresolvedReferences
    """
    Delete a directory securely after optional confirmation.

    This internal helper verifies the existence of a target directory, checks whether it contains
    any files or subdirectories to customize the confirmation prompt message, and executes the
    deletion using `shutil.rmtree`_ to safely accept keyword configurations.

    :param dir_path: Pathname of the directory to be deleted.
    :type dir_path: str | bytes | os.PathLike
    :param confirmation_required: Whether to prompt for confirmation before proceeding.
        Defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print status messages to the console. Defaults to ``False``.
    :type verbose: bool | int
    :param indent: Indentation level for console output layout.
        If an integer, it represents the number of spaces (e.g. ``2`` means two spaces);
        if a string, it is used as the indentation character (e.g. ``'\\t'``).
        Defaults to ``None``.
    :type indent: int | str | None
    :param raise_error: Whether to raise exceptions if deletion fails;
        if ``raise_error=False``, the error will be suppressed. Defaults to ``True``.
    :type raise_error: bool
    :param verbose_label: The action word printed before the path in the ``verbose`` deletion
        message (e.g. ``"Deleting"``). Pass ``""`` to omit it -- useful when a caller has already
        printed a header (e.g. ``"Deleting:"``) and would otherwise repeat the word on every line.
        Defaults to ``"Deleting"``.
    :type verbose_label: str | None
    :param kwargs: Optional parameters passed directly to `shutil.rmtree`_
        (the underlying deletion function).

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree

    **Tests**::

        >>> from pyhelpers.dirs.management import _delete_dir
        >>> from pyhelpers._cache import _get_relative_path
        >>> from pyhelpers.dirs import cd
        >>> from pathlib import Path

        >>> dir_path = cd("tests", "test_dir", mkdir=True)
        >>> rel_dir_path = _get_relative_path(dir_path, as_str=True, quoted=True)
        >>> print(f'The directory {rel_dir_path} exists? {dir_path.is_dir()}')
        The directory "tests/test_dir/" exists? True

        >>> _delete_dir(dir_path, verbose=True)
        Confirm deletion of the directory "tests/test_dir/"?
         [No]|Yes: yes
        Deleting "tests/test_dir/" ... Done.

        >>> print(f'The directory {rel_dir_path} exists? {dir_path.is_dir()}')
        The directory "tests/test_dir/" exists? False

        >>> dir_path = cd("tests", "test_dir", "folder", mkdir=True)
        >>> rel_dir_path = _get_relative_path(dir_path, as_str=True, quoted=True)
        >>> print(f'The directory {rel_dir_path} exists? {dir_path.is_dir()}')
        The directory "tests/test_dir/folder/" exists? True

        >>> _delete_dir(cd("tests", "test_dir"), verbose=True)
        The directory "tests/test_dir/" is not empty.
        Proceed with deletion?
         [No]|Yes: yes
        Deleting "tests/test_dir/" ... Done.

        >>> print(f'The directory {rel_dir_path} exists? {dir_path.is_dir()}')
        The directory "tests/test_dir/folder/" exists? False
    """

    try:
        rel_dir_path = _get_relative_path(dir_path)
        display_path = _format_display_path(rel_dir_path)

        indent_str = " " * indent if isinstance(indent, int) else (indent or "")

        if not os.path.isdir(rel_dir_path):
            if verbose:
                print(f"{indent_str}The directory {display_path} does not exist.")
            return

        # Only build the confirmation message when a prompt will actually be shown
        if confirmation_required:
            if os.listdir(rel_dir_path):
                cfm_msg = f"The directory {display_path} is not empty.\nProceed with deletion?\n"
            else:
                cfm_msg = f"Confirm deletion of the directory {display_path}?\n"
        else:
            cfm_msg = None

        if _confirmed(prompt=cfm_msg, confirmation_required=confirmation_required):
            if verbose:
                prefix = f"{verbose_label} " if verbose_label else ""
                # Fallback pattern if explicit indentation is removed or zeroed
                print(f"{indent_str}{prefix}{display_path}", end=" ... ")

            # Use shutil.rmtree to safely absorb keyword arguments like ignore_errors
            shutil.rmtree(rel_dir_path, **kwargs)

            if verbose:
                # `shutil.rmtree` only reaches this point without raising if it either
                # succeeded outright, or `ignore_errors=True` silently suppressed a failure
                still_exists = os.path.isdir(rel_dir_path)
                print("Done." if not still_exists else "Not fully removed.")

    except Exception as e:
        _print_failure_message(e, "Failed. Error:", verbose=verbose, raise_error=raise_error)


def delete_dir(dir_path, confirmation_required=True, verbose=False, indent=2, raise_error=False,
               **kwargs):
    """
    Delete a directory or multiple directories.

    :param dir_path: Pathname(s) of the directory (or directories) to be deleted.
    :type dir_path: str | bytes | os.PathLike | collections.abc.Sequence
    :param confirmation_required: Whether to prompt for confirmation before proceeding.
        Defaults to ``True``.
    :type confirmation_required: bool
    :param verbose: Whether to print relevant information to the console. Defaults to ``False``.
    :type verbose: bool | int
    :param indent: Indentation level; if an integer, represents the number of spaces;
        if a string, used as the indentation character (e.g. ``'\\t'``).
        Defaults to ``2`` (two spaces).
    :type indent: int | str
    :param raise_error: Whether to raise an exception if deletion fails;
        if ``raise_error=False`` (default), the error will be suppressed. Defaults to ``False``.
    :type raise_error: bool
    :param kwargs: Optional parameters passed directly to `shutil.rmtree`_ (the underlying
        deletion function).

    .. _`shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree

    **Examples**::

        >>> from pyhelpers.dirs import cd, delete_dir, get_relative_path

        >>> test_dirs = []
        >>> for x in range(3):
        ...     test_dirs.append(cd("tests", f"test_dir{x}", mkdir=True))
        ...     if x == 0:
        ...         cd("tests", f"test_dir{x}", "a_folder", mkdir=True)
        ...     elif x == 1:
        ...         open(cd("tests", f"test_dir{x}", "file"), 'w').close()

        >>> for x in test_dirs:
        ...     print(get_relative_path(x))
        tests\test_dir0
        tests\test_dir1
        tests\test_dir2

        >>> delete_dir(test_dirs, verbose=True)
        Confirm deletion of the following directories:
          "tests/test_dir0/" (Not empty)
          "tests/test_dir1/" (Not empty)
          "tests/test_dir2/"
        ? [No]|Yes: yes
        Deleting:
          "tests/test_dir0/" ... Done.
          "tests/test_dir1/" ... Done.
          "tests/test_dir2/" ... Done.
    """

    if (isinstance(dir_path, collections.abc.Sequence) and
            not isinstance(dir_path, (str, bytes))):
        dir_paths = [_get_relative_path(p) for p in dir_path]
    else:
        dir_paths = [_get_relative_path(dir_path)]

    if not dir_paths or not any(os.path.isdir(d) for d in dir_paths):
        if verbose:
            print("No directory specified for deletion.")
        return

    # Formulate path descriptions safely
    disp_dir_paths = []
    for dir_path in dir_paths:
        p_str = _format_display_path(dir_path)
        if os.path.isdir(dir_path):
            if os.listdir(dir_path):
                p_str += " (Not empty)"
        else:
            p_str += " (Does not exist)"
        disp_dir_paths.append(p_str)

    if len(disp_dir_paths) == 1:
        cfm_msg = f"Confirm deletion of the directory {disp_dir_paths[0]}?\n"
    else:
        # Resolve indentation string
        indent_str = " " * indent if isinstance(indent, int) else (indent or "")
        temp = f"\n{indent_str}".join(disp_dir_paths)
        cfm_msg = f"Confirm deletion of the following directories:\n{indent_str}{temp}\n?"

    if _confirmed(cfm_msg, confirmation_required=confirmation_required):
        if len(dir_paths) == 1:
            # Single item: no header, no indent, for a clean single-line output
            _delete_dir(
                dir_paths[0],
                confirmation_required=False,
                verbose=verbose,
                indent=0,
                raise_error=raise_error,
                **kwargs
            )

        else:  # Multiple items: print header and use indentation for a list
            if verbose:
                print("Deleting:")  # Header for the progress list
            for dir_pathname in dir_paths:
                _delete_dir(
                    dir_pathname,
                    confirmation_required=False,
                    verbose=verbose,
                    indent=indent,
                    raise_error=raise_error,
                    verbose_label=None,
                    **kwargs
                )
