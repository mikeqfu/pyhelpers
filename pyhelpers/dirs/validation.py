"""
Utilities for directory/file validation.
"""

import errno
import os
import re
from pathlib import Path

from .navigation import cd
from .._cache import _get_relative_path, _normalize_path, _normalize_token


def normalize_path(path, sep="/", as_str=True, prepend_dot=False):
    # noinspection PyShadowingNames
    """
    Convert a path into a consistent format for cross-platform compatibility.

    This function converts all path separators (``"\\"`` and ``"/"``) into a single,
    consistent separator and collapses consecutive separators, so that the resulting
    path is consistent across systems (e.g. Windows and Unix-like operating systems).

    .. note::

        A run of *leading* separators (e.g. a Windows UNC prefix such as ``"\\\\server\\share"``)
        is also collapsed to a single separator. This function does not preserve UNC-style
        double-slash prefixes; avoid it for network-share paths.

    :param path: The filesystem path to normalize.
    :type path: str | bytes | pathlib.Path | os.PathLike
    :param sep: Path separator used when the result is returned as a string; this is ignored when
        ``as_str=False``, in which case the separator is determined automatically by
        ``pathlib.Path`` based on the current platform. Defaults to ``"/"``.
    :type sep: str
    :param as_str: Whether to return the normalized path as a string; if ``False``,
        a ``pathlib.Path`` object is returned instead. Defaults to ``True``.
    :type as_str: bool
    :param prepend_dot: If ``True``, prepends ``"./"`` to a relative path that does not already
        begin with ``"./"``, ``"../"``, or a path that ``pathlib`` considers absolute *on the
        current platform*. Note that on Windows, a path with a leading separator but no drive
        letter (e.g. ``"/pyhelpers/data"``) is drive-relative, not absolute, and will have
        ``"./"`` prepended; on POSIX systems, that same path is absolute and is left untouched.
        Only takes effect when ``as_str=True``, since ``pathlib.Path`` normalizes away a leading
        ``"./"`` when constructing a ``Path`` object. Defaults to ``False``.
    :type prepend_dot: bool
    :return: Pathname formatted to a consistent standard, either as a string (default)
        or as a ``pathlib.Path`` object when ``as_str=False``.
    :rtype: str | pathlib.Path

    **Examples**::

        >>> from pyhelpers.dirs import normalize_path
        >>> from pathlib import Path
        >>> import os

        >>> path = "tests\\data\\dat.csv"
        >>> normalize_path(path)
        'tests/data/dat.csv'

        >>> normalize_path(path, prepend_dot=True)
        './tests/data/dat.csv'

        >>> path = "tests//data/dat.csv"
        >>> normalize_path(path)
        'tests/data/dat.csv'

        >>> path = Path("tests\\data/dat.csv")  # Assuming Windows OS
        >>> normalize_path(path, sep=os.sep)
        'tests\\data\\dat.csv'
        >>> normalize_path(path, sep=os.sep, as_str=False)
        WindowsPath('tests/data/dat.csv')

        >>> # on POSIX: absolute, untouched
        >>> normalize_path("/usr/bin", prepend_dot=True)
        '/usr/bin'
        >>> # on Windows: drive-relative, not absolute
        >>> normalize_path("/usr/bin", prepend_dot=True)
        './usr/bin'
    """

    return _normalize_path(path=path, as_str=as_str, sep=sep, prepend_dot=prepend_dot)


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


def resolve_dir_path(dir_path=None, subdir="", msg="Invalid input!", **kwargs):
    """
    Resolve a directory path into an absolute pathname.

    This function accepts a variety of input types and converts them into a standardized directory
    pathname via :func:`~pyhelpers.dirs.cd`. If ``dir_path`` is not given, ``subdir`` is
    used instead (or the current directory, if ``subdir`` is also not given).

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


def get_file_paths(dir_path, file_ext=None, incl_subdir=False, abs_path=False, normalized=True,
                   prepend_dot=False):
    """
    Get the paths of files in a directory, optionally filtered by file extension.

    This function retrieves paths of files within the directory specified by ``dir_path``.
    Files are optionally filtered by the exact ``file_ext`` given, matched against each
    file's actual extension (via ``os.path.splitext``) rather than a trailing-substring
    comparison. If ``file_ext`` is ``None``, ``"*"`` or ``"all"``, all files are returned.
    If ``incl_subdir=True``, subdirectories are traversed recursively.

    :param dir_path: Pathname of the directory to search.
    :type dir_path: str | os.PathLike
    :param file_ext: Exact file extension to filter files by, with or without the leading
        dot (e.g. ``".txt"`` or ``"txt"``). Defaults to ``None``, in which case all files
        are returned regardless of extension.
    :type file_ext: str | None
    :param incl_subdir: Whether to include files from subdirectories; when ``incl_subdir=True``,
        files from all subdirectories are included recursively. Defaults to ``False``.
    :type incl_subdir: bool
    :param abs_path: Whether to return absolute pathname(s). Defaults to ``False``.
    :type abs_path: bool
    :param normalized: Whether to normalize the returned pathname(s) via
        :func:`~pyhelpers._cache._normalize_path`. Defaults to ``True``.
    :type normalized: bool
    :param prepend_dot: If ``True``, prepends ``"./"`` to a relative pathname that doesn't
        already have a dot-relative or absolute prefix. Only takes effect when
        ``normalized=True``. Defaults to ``False``.
    :type prepend_dot: bool
    :return: List of file pathnames matching the criteria.
    :rtype: list[str]

    **Examples**::

        >>> from pyhelpers.dirs import get_file_paths, delete_dir
        >>> from pyhelpers.store import unzip
        >>> import os

        >>> test_dir_name = "tests/data"

        >>> # Get all files in the directory (without subdirectories) on Windows
        >>> get_file_paths(test_dir_name, prepend_dot=True)
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

        >>> get_file_paths(test_dir_name, file_ext=".txt")
        ['tests/data/dat.txt', 'tests/data/zipped.txt']

        >>> output_dir = unzip('tests/data/zipped.zip', ret_output_dir=True)
        >>> os.listdir(output_dir)
        ['zipped.txt']

        >>> # Get absolute paths of all files contained in the folder (incl. all subdirectories)
        >>> get_file_paths(test_dir_name, file_ext="txt", incl_subdir=True, abs_path=True)
        ['<Parent directories>/tests/data/dat.txt',
         '<Parent directories>/tests/data/zipped.txt',
         '<Parent directories>/tests/data/zipped/zipped.txt']

        >>> delete_dir(output_dir, confirmation_required=False, verbose=True)
        Deleting "tests/data/zipped/" ... Done.
    """

    if incl_subdir:
        file_pathnames = [
            os.path.normpath(os.path.join(root, file))
            for root, _, files in os.walk(dir_path)
            for file in files
        ]
    else:
        file_pathnames = [
            os.path.normpath(os.path.join(dir_path, file))
            for file in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, file))
        ]

    if file_ext not in {None, "*", "all"}:
        # Match against the actual extension, not just a trailing substring, so that e.g.
        # `file_ext="txt"` doesn't also match a file such as "notes.mytxt"
        target_ext = file_ext if file_ext.startswith(".") else f".{file_ext}"
        file_pathnames = [p for p in file_pathnames if os.path.splitext(p)[1] == target_ext]

    if abs_path:
        file_pathnames = [os.path.abspath(p) for p in file_pathnames]

    if normalized:
        file_pathnames = [_normalize_path(p, prepend_dot=prepend_dot) for p in file_pathnames]

    return file_pathnames


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


def get_relative_path(path, as_str=False, normalized=True, quoted=False, is_dir=None,
                      prepend_dot=False):
    """
    Check if the pathname is relative to the current working directory.

    If the specified ``path`` resides within the current working directory, this function
    returns its relative path counterpart. Otherwise, it returns the original absolute path.

    :param path: Pathname of a file or directory.
    :type path: str | bytes | pathlib.Path | os.PathLike
    :param as_str: Whether to return the path as a string; if ``False``, a ``pathlib.Path``
        object is returned instead and ``normalized``, ``quoted``, ``is_dir`` and
        ``prepend_dot`` are all ignored. Defaults to ``False``.
    :type as_str: bool
    :param normalized: Whether to run the path through
        :func:`~pyhelpers._cache._normalize_path` (or, when ``quoted=True``,
        :func:`~pyhelpers._cache._format_display_path`) before returning it as a string.
        If ``False``, the string is returned using the native OS separator, unnormalized.
        Only takes effect when ``as_str=True``. Defaults to ``True``.
    :type normalized: bool
    :param quoted: Whether to format and wrap the returned string via
        :func:`~pyhelpers._cache._format_display_path` (double-quoted, with a trailing
        separator for directories) instead of :func:`~pyhelpers._cache._normalize_path`.
        Only takes effect when ``as_str=True``. Defaults to ``False``.
    :type quoted: bool
    :param is_dir: Explicitly treat the path as a directory; passed through to
        :func:`~pyhelpers._cache._format_display_path`. Only takes effect when
        ``as_str=True`` and ``quoted=True``. Defaults to ``None``.
    :type is_dir: bool | None
    :param prepend_dot: Whether to prepend a dot-relative prefix to a relative path.
        Only takes effect when ``as_str=True``. Defaults to ``False``.
    :type prepend_dot: bool
    :return: A location relative to the current working directory if ``path`` is within
        the working space; otherwise, a resolved copy of the absolute ``path``.
    :rtype: pathlib.Path | str

    **Examples**::

        >>> from pyhelpers.dirs import get_relative_path, cd

        >>> get_relative_path(path=".")  # on Windows
        WindowsPath('.')

        >>> get_relative_path(path=cd(), as_str=True)
        '.'

        >>> get_relative_path(path="C:/Windows", as_str=True)
        'C:/Windows'

        >>> get_relative_path(path="C:\\Program Files", as_str=True, normalized=False)
        'C:\\Program Files'
    """

    return _get_relative_path(
        path=path,
        as_str=as_str,
        normalized=normalized,
        quoted=quoted,
        is_dir=is_dir,
        prepend_dot=prepend_dot
    )


def standardize_path(path, sep="-", parents=False):
    """
    Standardize file and directory paths.

    This function handles camelCase, spaces and special characters while preserving file extensions
    (``"."``) and operating system path anchors (``"/"`` or ``"C:\\"``).

    :param path: The target file or directory path ``str`` or ``pathlib.Path`` object to clean.
    :type path: str | pathlib.Path
    :param sep: The character used to separate words. Defaults to ``"-"``.
    :type sep: str
    :param parents: If ``True``, standardizes all parent directories in the path layout.
        If ``False`` (default), only standardizes the final file or folder name.
    :type parents: bool
    :return: A standardized operating system path object.
    :rtype: pathlib.Path

    **Examples**::

        >>> from pyhelpers.dirs import standardize_path
        >>> from pathlib import Path

        >>> standardize_path('Random Evaluation Name')  # On Windows
        WindowsPath('random-evaluation-name')

        >>> standardize_path("-license.txt")
        WindowsPath('-license.txt')

        >>> standardize_path('C:/Users/Username/ProjectData/schema-v2.json')
        WindowsPath('C:/Users/Username/ProjectData/schema-v2.json')

        >>> standardize_path(Path('/Archive/Old Folders/MyScript.py'), sep="_")
        WindowsPath('/Archive/Old Folders/my_script.py')

        >>> # Only standardize the filename, leave the directories alone
        >>> standardize_path('/Archive/Old Folders/MyScript.py', parents=True)
        WindowsPath('/archive/old-folders/my-script.py')
    """

    path_obj = Path(path)
    cleaned_parts = []

    for idx, part in enumerate(path_obj.parts):
        # Protect OS root anchors (e.g. "C:\\" or "/")
        if idx == 0 and (part.endswith(":\\") or part == "/" or part == "\\"):
            cleaned_parts.append(part)
            continue

        # Skip parent processing if explicitly requested by configuration
        if not parents and idx < len(path_obj.parts) - 1:
            cleaned_parts.append(part)
            continue

        # Clean the segment using the internal tracking normalizer
        name = _normalize_token(part, preserve_dot=True)

        # Substitute standard underscores with the designated connector
        if sep != "_":
            name = name.replace("_", sep)

        # Condense consecutive accidental separators along token boundaries
        if len(name) > 1:
            if name.startswith(sep * 2):
                name = f"{sep}{name.lstrip(sep)}"
            if name.endswith(sep * 2):
                name = f"{name.rstrip(sep)}{sep}"

        # Fallback safeguard to prevent returning empty path tokens
        if not name or name == "." or name == sep:
            name = f"name_{idx}"

        cleaned_parts.append(name)

    return Path(*cleaned_parts)
