"""
Directory/file navigation.
"""

import copy
import importlib.resources
import os

from .._cache import _check_file_pathname


def cd(*subdir, mkdir=False, cwd=None, back_check=False, **kwargs):
    """
    Get the full pathname of a directory (or file).

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param mkdir: Whether to create the directory; defaults to ``False``.
    :type mkdir: bool
    :param cwd: Current working directory; defaults to ``None``.
    :type cwd: str | os.PathLike[str] | bytes | os.PathLike[bytes] | None
    :param back_check: Whether to check if a parent directory exists; defaults to ``False``.
    :type back_check: bool
    :param kwargs: [Optional] additional parameters (e.g. ``mode=0o777``) for the function
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
    """

    # Current working directory
    path = os.getcwd() if cwd is None else copy.copy(cwd.decode() if isinstance(cwd, bytes) else cwd)

    if back_check:
        while not os.path.exists(path):
            path = os.path.dirname(path)

    for x in subdir:
        if isinstance(x, bytes):
            x = x.decode()
        path = os.path.dirname(path) if x == ".." else os.path.join(path, x)

    if mkdir:
        path_to_file, ext = os.path.splitext(path)

        kwargs.update({'exist_ok': True})
        if ext == '':
            os.makedirs(path_to_file, **kwargs)
        else:
            os.makedirs(os.path.dirname(path_to_file), **kwargs)

    return path


def ccd(*subdir, **kwargs):
    """
    Get the full pathname of a directory (or file) in an altered working directory.

    :param subdir: Name of a directory or file.
    :type subdir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param kwargs: [optional] Parameters for the function :func:`~pyhelpers.dirs.nav.cd`.
    :return: Pathname of a directory or file in the altered working directory.
    :rtype: str

    **Examples**::

        >>> from pyhelpers.dirs import ccd
        >>> import os
        >>> init_cwd = os.getcwd()
        >>> os.path.relpath(init_cwd)
        '.'
        >>> # Change the current working directory to "/new_cwd"
        >>> new_cwd = "tests/new_cwd"
        >>> os.makedirs(new_cwd, exist_ok=True)
        >>> os.chdir(new_cwd)
        >>> # Get the full path to a folder named "tests"
        >>> path_to_tests = ccd("tests")
        >>> os.path.relpath(path_to_tests)
        'tests'
        >>> path_to_tests_ = ccd("test1", "test2")
        >>> path_to_tests_ == os.path.join(os.getcwd(), "test1", "test2")
        True
        >>> os.chdir(init_cwd)
        >>> os.rmdir(new_cwd)
    """

    dir_names = [x.decode() if isinstance(x, bytes) else x for x in subdir]
    target = cd(*dir_names, **kwargs)

    if os.path.isdir(target):
        pathname = target

    else:
        original_cwd = os.path.dirname(target)
        pathname = os.path.join(original_cwd, *dir_names)

        if pathname == target:
            pass

        else:
            while not os.path.isdir(pathname):
                original_cwd = os.path.dirname(original_cwd)
                if original_cwd == cd():
                    break

            pathname = os.path.join(original_cwd, *dir_names)

    return pathname


def cdd(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under `data_dir`.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param data_dir: Name of the directory where data is (or will be) stored;
        defaults to ``"data"``.
    :type data_dir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param mkdir: Whether to create the directory if it does not exist; defaults to ``False``.
    :type mkdir: bool
    :param kwargs: [Optional] additional parameters for the function :func:`~pyhelpers.dirs.nav.cd`.
    :return: Pathname of a directory or file under `data_dir`.
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
        To delete the directory "test_cdd\\"
        ? [No]|Yes: yes
        Deleting "test_cdd\\" ... Done.

        >>> # Set `data_dir` to be `"tests"`
        >>> path_to_dat_dir = cdd("data", data_dir="test_cdd", mkdir=True)
        >>> os.path.relpath(path_to_dat_dir)
        'test_cdd\\data'

        >>> # Delete the "test_cdd" folder and the sub-folder "data"
        >>> test_cdd = os.path.dirname(path_to_dat_dir)
        >>> delete_dir(test_cdd, verbose=True)
        The directory "test_cdd\\" is not empty.
        Confirmed to delete it
        ? [No]|Yes: yes
        Deleting "test_cdd\\" ... Done.

        >>> # # Alternatively,
        >>> # import shutil
        >>> # shutil.rmtree(test_cdd)
    """

    kwargs.update({'mkdir': mkdir})
    path = cd(data_dir, *subdir, **kwargs)

    return path


def cd_data(*subdir, data_dir="data", mkdir=False, **kwargs):
    """
    Get the full pathname of a directory (or file) under `data_dir` of a package.

    :param subdir: Name of a directory or directories (and/or a filename).
    :type subdir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param data_dir: Name of the directory to store data; defaults to ``"data"``.
    :type data_dir: str | os.PathLike[str] | bytes | os.PathLike[bytes]
    :param mkdir: Whether to create the directory if it does not exist; defaults to ``False``.
    :type mkdir: bool
    :param kwargs: [Optional] additional parameters (e.g. ``mode=0o777``) for the function
        `os.makedirs`_.
    :return: Pathname of a directory or file under `data_dir` of a package.
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
        path = os.path.join(path, x.decode() if isinstance(x, bytes) else x)

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
    Get the pathname of an executable file for a specified application.

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
        >>> python_exe = "python.exe"
        >>> possible_paths = ["C:\\Program Files\\Python39", "C:\\Python39\\python.exe"]
        >>> python_exe_exists, path_to_python_exe = find_executable(python_exe, possible_paths)
        >>> python_exe_exists
        True
        >>> os.path.relpath(path_to_python_exe)
        'venv\\Scripts\\python.exe'
        >>> text_exe = "pyhelpers.exe"  # This file does not actually exist
        >>> test_exe_exists, path_to_test_exe = find_executable(text_exe, possible_paths)
        >>> test_exe_exists
        False
        >>> os.path.relpath(path_to_test_exe)
        'pyhelpers.exe'
    """

    return _check_file_pathname(name=name, options=options, target=target)
