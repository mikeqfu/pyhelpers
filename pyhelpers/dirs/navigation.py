"""
Utilities for directory/file navigation.
"""

import importlib.resources
import os
from pathlib import Path

from .._cache import _add_slashes, _check_file_pathname, _normalize_pathname


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
        return _normalize_pathname(path) if normalized else str(path)

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


def find_executable(name, options=None, target=None, normalized=True):
    # noinspection PyShadowingNames
    """
    Finds the pathname of an executable file for a specified application.

    :param name: Name or filename of the application that is to be called.
    :type name: str
    :param options: Possible pathnames or directories to search for the executable;
        defaults to ``None``.
    :type options: list | set | None
    :param target: Specific pathname of the executable file (if already known);
        defaults to ``None``.
    :type target: str | None
    :param normalized: Whether to normalize the returned pathname; defaults to ``True``.
    :type normalized: bool
    :return: Whether the specified executable file exists (i.e. a boolean indicating existence),
        together with its pathname.
    :rtype: tuple[bool, str]

    **Examples**::

        >>> from pyhelpers.dirs import find_executable
        >>> import os
        >>> import sys
        >>> python_exe = "python.exe"
        >>> python_exe_exists, path_to_python_exe = find_executable(python_exe)
        >>> python_exe_exists
        True
        >>> possible_paths = [os.path.dirname(sys.executable), sys.executable]
        >>> target = possible_paths[0]
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
        >>> os.path.relpath(path_to_test_exe)
        'pyhelpers.exe'
    """

    file_exists, file_pathname = _check_file_pathname(name=name, options=options, target=target)

    if file_exists and normalized:
        file_pathname = _add_slashes(file_pathname, normalized=normalized, surrounded_by="")

    return file_exists, file_pathname
