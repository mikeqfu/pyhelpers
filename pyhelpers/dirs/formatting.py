"""
Utilities for formatting, normalizing and standardizing file and directory paths.
"""

from pathlib import Path

from .._cache import _format_display_path, _get_relative_path, _normalize_path, _normalize_token


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
