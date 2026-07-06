"""
Utilities for directory navigation, context-switching and path resolution.
"""

import importlib.resources
import os
from pathlib import Path

from .._cache import _find_file_path, _normalize_path


def cd(*subdir, mkdir=False, cwd=None, back_check=False, as_str=False, normalized=True, **kwargs):
    # noinspection PyUnresolvedReferences
    """
    Specify and resolve the pathname of a directory or file.

    This function constructs an operating system-agnostic path object. Handles missing directories
    and resolves parent path traversal dynamically.

    :param subdir: Name of a directory or directories (and/or a filename).
        ``None`` values are safely ignored.
    :type subdir: str | bytes | pathlib.Path | os.PathLike | None
    :param mkdir: Whether to create the directory if it does not exist. Defaults to ``False``.
    :type mkdir: bool
    :param cwd: Current working directory fallback. Defaults to ``None``.
    :type cwd: str | bytes | pathlib.Path | os.PathLike | None
    :param back_check: Whether to check if a parent directory exists. Defaults to ``False``.
    :type back_check: bool
    :param as_str: If ``True``, forces the return type to be a standard string instead of
        a path object. Defaults to ``False``.
    :type as_str: bool
    :param normalized: Whether to normalize the returned pathname structurally.
        Defaults to ``True``.
    :type normalized: bool
    :param kwargs: Optional parameters (e.g. ``mode=0o777``) passed to `pathlib.Path.mkdir`_.
    :return: A standardized path object representing the target directory or file.
    :rtype: Path | str

    .. _`pathlib.Path.mkdir`: https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir

    **Examples**::

        >>> from pyhelpers.dirs import cd
        >>> from pathlib import Path

        >>> cur_dir = cd()  # Current working directory
        >>> cur_dir.name
        'pyhelpers'

        >>> cd(None).relative_to(cur_dir)  # On Windows OS
        WindowsPath('.')

        >>> # The directory will be created if it does not exist
        >>> test_path = cd("tests")
        >>> test_path.relative_to(cur_dir)
        WindowsPath('tests')

        >>> test_path = cd("tests\\folder1/folder2")
        >>> test_path.relative_to(cur_dir)
        WindowsPath('tests/folder1/folder2')

        >>> test_path = cd(Path("tests\\folder1"), as_str=True, normalized=False)
        >>> test_path  # On Windows OS
        'X:\\pyhelpers\\tests\\folder1'
    """

    # Current working directory
    path = Path.cwd() if cwd in {None, ".", ""} else Path(os.fsdecode(cwd)).resolve()

    if back_check:
        while not path.exists() and path.parent != path:
            path = path.parent

    for f in subdir:
        if f is None:
            continue

        # Replace backslashes dynamically to ensure cross-OS string injection works safely
        f_str = os.fsdecode(f).replace("\\", "/")
        path = path.parent if f_str == ".." else path.joinpath(f_str)

    if mkdir:
        kwargs.setdefault('exist_ok', True)
        kwargs.setdefault('parents', True)

        # Check if the path targets a file (contains an extension and is not hidden-only)
        if path.suffix and "." in path.name:
            path.parent.mkdir(**kwargs)
        else:
            path.mkdir(**kwargs)

    if as_str:
        return _normalize_path(path) if normalized else str(path)

    return path


def cdd(*subdir, mkdir=False, data_dir="data", **kwargs):
    # noinspection PyUnresolvedReferences
    """
    Specify and resolve the pathname of a directory (or file) under the designated ``data_dir``.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | bytes | pathlib.Path | os.PathLike | None
    :param mkdir: Whether to create the directory if it does not exist. Defaults to ``False``.
    :type mkdir: bool
    :param data_dir: Name of the directory where data is stored. Defaults to ``"data"``.
    :type data_dir: str | bytes | pathlib.Path | os.PathLike
    :param kwargs: Optional parameters passed to :func:`~pyhelpers.dirs.cd`.
    :return: Pathname of a directory or file under ``data_dir``.
    :rtype: pathlib.Path | str

    **Examples**::

        >>> from pyhelpers.dirs import cd, cdd, delete_dir
        >>> from pathlib import Path

        >>> cur_dir = cd()
        >>> cur_dir == Path.cwd()
        True

        >>> test_path = cdd()
        >>> # As `mkdir=False`, `test_path` will NOT be created if it doesn't exist
        >>> test_path.relative_to(cur_dir)
        WindowsPath('data')

        >>> test_path = cdd(data_dir="test_cdd", mkdir=True)
        >>> # As `mkdir=True`, `test_path` will be created if it doesn't exist
        >>> test_path.is_dir()
        True
        >>> test_path.relative_to(cur_dir)
        WindowsPath('test_cdd')

        >>> # Delete the "test_cdd" folder
        >>> delete_dir(test_path, verbose=True)
        To delete the directory "./test_cdd/"
        ? [No]|Yes: yes
        Deleting "./test_cdd/" ... Done.

        >>> # Set `data_dir` to be `"tests"`
        >>> test_path = cdd("data", data_dir="test_cdd", mkdir=True)
        >>> test_path.relative_to(cur_dir)
        WindowsPath('test_cdd/data')

        >>> # Delete the "test_cdd" folder and the sub-folder "data"
        >>> test_cdd = test_path.parent
        >>> delete_dir(test_cdd, verbose=True)
        To delete the directory "./test_cdd/" (Not empty)
        ? [No]|Yes: yes
        Deleting "./test_cdd/" ... Done.
        >>> # # Alternatively,
        >>> # import shutil
        >>> # shutil.rmtree(test_cdd)
    """

    return cd(data_dir, *subdir, mkdir=mkdir, **kwargs)


def cd_data(*subdir, data_dir="data", mkdir=False, as_str=False, **kwargs):
    # noinspection PyUnresolvedReferences
    """
    Specify and resolve the pathname of a directory (or file) under ``data_dir`` of a package.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike | bytes
    :param data_dir: Name of the directory to store data; defaults to ``"data"``.
    :type data_dir: str | os.PathLike | bytes
    :param mkdir: Whether to create the directory if it does not exist; defaults to ``False``.
    :type mkdir: bool
    :param as_str: If ``True``, forces the return type to be a standard string instead of
        a path object. Defaults to ``False``.
    :type as_str: bool
    :param kwargs: [Optional] Additional parameters (e.g. ``mode=0o777``) for the method
        `pathlib.Path.mkdir`_.
    :return: A normalized ``pathlib.Path`` object (or ``str``) of the requested target.
    :rtype: pathlib.Path | str

    .. _`os.makedirs`: https://docs.python.org/3/library/os.html#os.makedirs

    **Examples**::

        >>> from pyhelpers.dirs import cd_data
        >>> from pathlib import Path
        >>> test_path = cd_data("tests", mkdir=False)
        >>> test_path.relative_to(Path.cwd())  # on Windows
        WindowsPath('pyhelpers/data/tests')
    """

    data_dir_ = os.fsdecode(data_dir).replace("\\", "/")
    path = Path(importlib.resources.files(__package__)).joinpath("..", f"{data_dir_}").resolve()

    for x in subdir:
        if x is None:
            continue

        x_str = os.fsdecode(x).replace("\\", "/")
        path = path.parent if x_str == ".." else path / x_str

    if mkdir:
        kwargs.setdefault('exist_ok', True)
        kwargs.setdefault('parents', True)

        if path.suffix and "." in path.name:
            path.parent.mkdir(**kwargs)
        else:
            path.mkdir(**kwargs)

    return str(path) if as_str else path


def resolve_dir_path(dir_path=None, subdir="", msg="Invalid input!", **kwargs):
    """
    Resolve a directory path into an absolute pathname.

    This function accepts a variety of input types and converts them into a standardized directory
    pathname via :func:`~pyhelpers.dirs.cd`. If ``dir_path`` is not given, ``subdir`` is used
    instead (or the current directory, if ``subdir`` is also not given).

    .. note::

        Both a relative and an absolute ``dir_path`` are routed through the same call to
        :func:`~pyhelpers.dirs.cd`, on the assumption that ``cd`` (like ``os.path.join``) treats
        an absolute argument as replacing any preceding base directory, so ``**kwargs``
        (e.g. ``mkdir=True``) is applied consistently either way.
        If ``cd`` does not behave this way for absolute paths, this needs revisiting.

    :param dir_path: Pathname of a data directory; if ``dir_path=None`` (default), ``subdir``
        is examined instead to construct a valid directory path.
    :type dir_path: str | bytes | os.PathLike | None
    :param subdir: Name of a subdirectory to fall back on when ``dir_path=None``.
        Defaults to ``""``.
    :type subdir: str | bytes | os.PathLike
    :param msg: Error message used when ``dir_path`` cannot be decoded into a valid pathname.
        Defaults to ``"Invalid input!"``.
    :type msg: str
    :param kwargs: [Optional] Additional parameters for :func:`~pyhelpers.dirs.cd`
        (e.g. ``mkdir=True`` to create the directory if it does not already exist).
    :return: Valid pathname of a directory.
    :rtype: pathlib.Path

    **Examples**::

        >>> from pyhelpers.dirs import resolve_dir_path, get_relative_path
        >>> from pathlib import Path

        >>> data_dir = resolve_dir_path()
        >>> get_relative_path(data_dir)
        '.'

        >>> data_dir = resolve_dir_path("tests")
        >>> get_relative_path(data_dir)
        'tests'

        >>> data_dir = resolve_dir_path(subdir=Path("data"))
        >>> get_relative_path(data_dir)
        'data'
    """

    try:
        # Uniformly handle str, bytes, pathlib.Path, and os.PathLike
        path_to_dir_ = os.fsdecode(dir_path) if dir_path is not None else None
        subdir_ = os.fsdecode(subdir) if subdir else ""

    except (TypeError, ValueError):
        raise TypeError(msg)

    # Logic for path construction
    if path_to_dir_:
        # Normalize to remove redundant separators or dots safely
        normalized_path = os.path.normpath(path_to_dir_)
        data_dir_ = cd(normalized_path, **kwargs)

    else:  # Fallback to subdir or the current directory
        data_dir_ = cd(subdir_, **kwargs) if subdir_ else cd(**kwargs)

    return data_dir_


def find_executable(name, options=None, target=None, normalized=True, as_str=True):
    # noinspection PyShadowingNames
    """
    Find the pathname of an executable file for a specified application.

    This function relies on :func:`~pyhelpers._cache._find_file_path` to check a known
    ``target`` pathname, search through ``options``, and fall back to the system's PATH, in
    that order.

    :param name: Name or filename of the application that is to be called.
    :type name: str
    :param options: Possible pathnames or directories to search for the executable;
        defaults to ``None``.
    :type options: list | set | None
    :param target: Specific pathname of the executable file (if already known); this is
        checked first and, if it does not resolve to a valid match, the function stops
        and does not search ``options`` or the system PATH. Defaults to ``None``.
    :type target: str | None
    :param normalized: Whether to format the returned pathname for display via
        :func:`~pyhelpers._cache._format_display_path`. If ``True``, the pathname is
        returned as a formatted ``str``; if ``False``, it is returned unformatted as
        a ``pathlib.Path``. Defaults to ``True``.
    :type normalized: bool
    :param as_str: Whether to return the path as a string;
        if ``False``, a ``pathlib.Path`` object is returned instead. Defaults to ``True``.
    :type as_str: bool
    :return: Whether the specified executable file exists (i.e. a boolean indicating existence),
        together with its pathname, or ``None`` if it was not found.
    :rtype: tuple[bool, pathlib.Path | str | None]

    **Examples**::

        >>> from pyhelpers.dirs import find_executable
        >>> import os
        >>> import sys

        >>> python_exe = "python.exe"
        >>> python_exe_exists, path_to_python_exe = find_executable(python_exe)
        >>> python_exe_exists
        True

        >>> possible_paths = [os.path.dirname(sys.executable), sys.executable]
        >>> target = possible_paths[0]  # a directory, not a file - not a valid target
        >>> python_exe_exists, path_to_python_exe = find_executable(python_exe, target=target)
        >>> python_exe_exists
        False

        >>> target = possible_paths[1]
        >>> python_exe_exists, path_to_python_exe = find_executable(python_exe, target=target)
        >>> python_exe_exists
        True

        >>> python_exe_exists, path_to_python_exe = find_executable(possible_paths[1])
        >>> python_exe_exists
        True

        >>> text_exe = "pyhelpers.exe"  # This file does not actually exist
        >>> test_exe_exists, path_to_test_exe = find_executable(text_exe, possible_paths)
        >>> test_exe_exists
        False
        >>> path_to_test_exe is None
        True
    """

    file_exists, file_pathname = _find_file_path(
        name=name,
        options=options,
        target=target,
        as_str=as_str
    )

    if file_exists and normalized:
        file_pathname = _normalize_path(file_pathname, as_str=as_str)

    return file_exists, file_pathname
