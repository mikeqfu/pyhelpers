"""
Directory/file navigation.
"""

import importlib.resources
import os
import re

from .._cache import _check_file_pathname


def cd(*subdir, mkdir=False, cwd=None, back_check=False, **kwargs):
    """
    Specifies the pathname of a directory (or file).

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike | bytes
    :param mkdir: Whether to create the directory; defaults to ``False``.
    :type mkdir: bool
    :param cwd: Current working directory; defaults to ``None``.
    :type cwd: str | os.PathLike | bytes | | None
    :param back_check: Whether to check if a parent directory exists; defaults to ``False``.
    :type back_check: bool
    :param kwargs: [Optional] Additional parameters (e.g. ``mode=0o777``) for the function
        `os.makedirs`_.
    :return: Pathname of the directory or file.
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
        >>> path_to_tests_dir = cd("tests\\folder1/folder2")
        >>> os.path.relpath(path_to_tests_dir)
        'tests\\folder1\\folder2'
    """

    # Current working directory
    if cwd in {None, "."}:
        path = os.getcwd()
    else:
        path = cwd.decode() if isinstance(cwd, bytes) else str(cwd)

    if back_check:
        while not os.path.exists(path) and path != os.path.sep:
            path = os.path.dirname(path)

    for x in subdir:
        x = x.decode() if isinstance(x, bytes) else str(x)
        if x == "..":
            path = os.path.dirname(path)
        else:
            path = os.path.join(path, re.sub(r"[\\/]+", re.escape(os.path.sep), x))

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


def cdd(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Specifies the pathname of a directory (or file) under `data_dir`.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike | bytes
    :param data_dir: Name of the directory where data is (or will be) stored;
        defaults to ``"data"``.
    :type data_dir: str | os.PathLike | bytes
    :param mkdir: Whether to create the directory if it does not exist; defaults to ``False``.
    :type mkdir: bool
    :param kwargs: [Optional] Additional parameters for the function :func:`~pyhelpers.dirs.cd`.
    :return: Pathname of a directory or file under ``data_dir``.
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
        To delete the directory ".\\test_cdd\\"
        ? [No]|Yes: yes
        Deleting ".\\test_cdd\\" ... Done.
        >>> # Set `data_dir` to be `"tests"`
        >>> path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
        >>> os.path.relpath(path_to_dat_dir)
        'test_cdd\\data'
        >>> # Delete the "test_cdd" folder and the sub-folder "data"
        >>> test_cdd = os.path.dirname(path_to_dat_dir)
        >>> delete_dir(test_cdd, verbose=True)
        To delete the directory ".\\test_cdd\\" (Not empty)
        ? [No]|Yes: yes
        Deleting ".\\test_cdd\\" ... Done.
        >>> # # Alternatively,
        >>> # import shutil
        >>> # shutil.rmtree(test_cdd)
    """

    kwargs.update({'mkdir': mkdir})
    path = cd(data_dir, *subdir, **kwargs)

    return path


def cd_data(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Specifies the pathname of a directory (or file) under ``data_dir`` of a package.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike | bytes
    :param data_dir: Name of the directory to store data; defaults to ``"data"``.
    :type data_dir: str | os.PathLike | bytes
    :param mkdir: Whether to create the directory if it does not exist; defaults to ``False``.
    :type mkdir: bool
    :param kwargs: [Optional] Additional parameters (e.g. ``mode=0o777``) for the function
        `os.makedirs`_.
    :return: Pathname of a directory or file under ``data_dir`` of a package.
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
    path = importlib.resources.files(__package__).joinpath(f"../{data_dir_}")

    for x in subdir:
        x = re.sub(
            r"[\\/]+", re.escape(os.path.sep), x.decode() if isinstance(x, bytes) else str(x))
        path = os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '' or ext == b'':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


def find_executable(name, options=None, target=None):
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
        >>> python_exe_exists, path_to_python_exe = find_executable(
        ...     python_exe, target=possible_paths[0])
        >>> python_exe_exists
        False
        >>> python_exe_exists, path_to_python_exe = find_executable(
        ...     python_exe, target=possible_paths[1])
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

    return _check_file_pathname(name=name, options=options, target=target)
