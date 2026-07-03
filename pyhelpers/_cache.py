"""
Cached functions and constants.
"""

import collections.abc
import copy
import functools
import importlib.metadata
import importlib.resources
import importlib.util
import json
import logging
import os
import pathlib
import re
import shutil
import string
import sys
import urllib.parse

import requests.adapters
import shapely.geometry
import urllib3


@functools.lru_cache(maxsize=None)
def _load_package_data(filename):
    """
    Loads data from the package's internal data directory.

    Supported formats are primarily JSON. Returns an empty dictionary if the file
    cannot be parsed or the extension is unsupported.

    :param filename: Name of the data file.
    :type filename: str
    :return: Parsed data from the file.
    :rtype: dict
    """

    filepath = importlib.resources.files(__package__).joinpath(f"data/{filename}")

    if filepath.suffix.endswith(".json"):  # noqa
        return json.loads(filepath.read_text(encoding='utf-8'))

    return {}


def _resolve_dependency_info(name):
    """
    Resolves the actual import path and the corresponding PyPI package name.

    This helper maps common user-friendly package names (e.g. 'beautifulsoup4')
    to their actual top-level import names (e.g. 'bs4') to prevent ``ModuleNotFoundError``
    due to naming discrepancies.

    :param name: Required package or module name.
    :type name: str
    :return: A tuple of ``(<actual_import_path>, <pip_install_name>)``.
    :rtype: tuple[str, str]

    **Tests**::

        >>> from pyhelpers._cache import _resolve_dependency_info
        >>> _resolve_dependency_info('beautifulsoup4')
        ('bs4', 'beautifulsoup4')
        >>> _resolve_dependency_info('pillow')
        ('PIL', 'Pillow')
        >>> _resolve_dependency_info('gdal')
        ('osgeo', 'gdal')
    """

    _install_name_mapping = {
        # Data Science & Arrays
        "beautifulsoup4": ("bs4", "beautifulsoup4"),
        "bs4": ("bs4", "beautifulsoup4"),
        "scikit-learn": ("sklearn", "scikit-learn"),
        "sklearn": ("sklearn", "scikit-learn"),

        # Images & CV
        "cv2": ("cv2", "opencv-python"),
        "opencv-python": ("cv2", "opencv-python"),
        "opencv": ("cv2", "opencv-python"),
        "pil": ("PIL", "Pillow"),
        "pillow": ("PIL", "Pillow"),

        # File Formats
        "odfpy": ("odf", "odfpy"),
        "odf": ("odf", "odfpy"),
        "python-rapidjson": ("rapidjson", "python-rapidjson"),
        "pyyaml": ("yaml", "PyYAML"),
        "rapidjson": ("rapidjson", "python-rapidjson"),
        "yaml": ("yaml", "PyYAML"),

        # Geospatial
        "gdal": ("osgeo.gdal", "gdal"),
    }

    name_ = name.lower()
    if name_ in _install_name_mapping:
        return _install_name_mapping[name_]

    # Default heuristic for standard packages
    return name.replace('-', '_'), name


def _check_dependencies(*names):
    """
    Imports one or multiple optional dependency packages/modules.

    This function attempts to import modules by their resolved names.
    It provides descriptive error messages upon failure.

    :param names: Names of packages/modules; can be strings (e.g. ``'pandas'``)
        or tuples for submodules (e.g. ``('osgeo', 'gdal')``).
    :type names: str | tuple[str, str]
    :return: Module object(s). Returns a single object if one name is passed,
        else a tuple.
    :rtype: Any | tuple[Any, ...]
    :raises ModuleNotFoundError: If the package is not installed.
    :raises ImportError: If the package exists but fails to load correctly.

    **Tests**::

        >>> from pyhelpers._cache import _check_dependencies
        >>> psycopg2 = _check_dependencies('psycopg2')
        >>> psycopg2.__name__
        'psycopg2'
        >>> psycopg2, pyodbc = _check_dependencies('pyodbc', 'psycopg2')
        >>> (psycopg2.__name__, pyodbc.__name__)
        ('pyodbc', 'psycopg2')
        >>> sqlalchemy_dialects = _check_dependencies(('sqlalchemy', 'dialects'))
        >>> sqlalchemy_dialects.__name__
        'sqlalchemy.dialects'
        >>> pd, plt = _check_dependencies('pandas', 'matplotlib.pyplot')
        >>> (pd.__name__, plt.__name__)
        ('pandas', 'matplotlib.pyplot')
        >>> # Handling GDAL specifically
        >>> gdal = _check_dependencies('gdal')  # Tries osgeo first, then legacy gdal
        >>> gdal.__name__
        'osgeo.gdal'
    """

    results = []

    for item in names:
        # Normalize name
        if isinstance(item, str):
            query_name = item
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            query_name = f"{item[0]}.{item[1]}"
        else:
            raise TypeError("Dependency must be a string or (package, name) tuple.")

        import_path, pip_name = _resolve_dependency_info(query_name)

        # 1. Fast path: Cache check
        if import_path in sys.modules:
            results.append(sys.modules[import_path])
            continue

        # 2. Attempt import
        try:
            # We use import_module on the full path (e.g. 'osgeo.gdal')
            module = importlib.import_module(import_path)
            results.append(module)
        except (ModuleNotFoundError, ImportError) as e:
            # Handle GDAL legacy fallback: try 'import gdal' if 'osgeo.gdal' fails
            if query_name.lower() == 'gdal':
                try:
                    legacy_gdal = importlib.import_module('gdal')
                    results.append(legacy_gdal)
                    continue
                except ImportError:
                    pass

            # If the module is actually missing from the environment
            if isinstance(e, ModuleNotFoundError):
                # Specific rich error for GDAL
                if 'gdal' in query_name.lower():
                    raise ModuleNotFoundError(
                        "'GDAL' not found. Try: `import osgeo.gdal`.\n  "
                        "If that fails, install via: `conda install -c conda-forge gdal` "
                        "(or `pip install <gdal-wheel-file>`)."
                    ) from None

                raise ModuleNotFoundError(
                    f"Missing optional dependency '{query_name}' (import as '{import_path}').\n"
                    f"  Install it via: `pip install {pip_name}` "
                    f"(or `pip install <{pip_name}-wheel-file>`)."
                ) from None

            # If the module exists but failed to load (e.g. DLL issues, syntax errors)
            raise ImportError(
                f"Failed to import '{import_path}' from installed package '{pip_name}': {e}"
            ) from e

    return results[0] if len(results) == 1 else tuple(results)


class _LazyModule:
    """
    Proxy object that defers module importation until an attribute is accessed.

    This reduces overhead for optional dependencies that may not be used in
    every session.
    """

    __slots__ = ['_name', '_module']

    def __init__(self, name):
        """
        :param name: The name of the module to load lazily.
        :type name: str
        """
        self._name = name
        self._module = None

    def _load(self):
        if self._module is None:
            # Delegate to the robust checker function
            self._module = _check_dependencies(self._name)
        return self._module

    def __getattr__(self, attr):
        module = self._load()
        try:
            return getattr(module, attr)
        except AttributeError:
            # Check if 'attr' is a submodule that needs explicit loading
            submodule_path = f"{self._name}.{attr}"
            try:
                # Attempt to import the subpackage dynamically
                submodule = importlib.import_module(submodule_path)
                # Cache the submodule on the parent to avoid repeated imports
                setattr(module, attr, submodule)
                return submodule
            except (ImportError, ModuleNotFoundError):
                # Re-raise the original error if it's truly not a submodule
                raise AttributeError(f"module '{self._name}' has no attribute '{attr}'") from None

    def __dir__(self):
        return dir(self._load())


def _lazy_check_dependencies(*args, **kwargs):
    """
    Decorator to inject lazy-loading modules into a function's global namespace.

    This allows functions to use optional dependencies internally without triggering top-level
    imports. The actual import occurs only when the injected variable is accessed inside the
    function.

    :param args: Package names where the variable name equals the package name.
    :type args: str
    :param kwargs: Mapping of ``alias='package_name'``. Submodules can be represented using
        dots in the string or underscores in the key.
    :type kwargs: str
    :return: A decorated function with lazy modules injected into its globals.
    :rtype: typing.Callable

    **Examples**::

        >>> from pyhelpers._cache import _lazy_check_dependencies
        >>> @_lazy_check_dependencies('numpy', 'pandas')  # No aliases
        >>> @_lazy_check_dependencies(np='numpy', pd='pandas')  # Aliases
        >>> @_lazy_check_dependencies('scipy', plt='matplotlib.pyplot')  # Mixed
        >>> @_lazy_check_dependencies(**{'sp': 'scipy.sparse'})  # (Alternative)
        >>> @_lazy_check_dependencies('scipy', 'scipy.sparse')  # Both package and its subpackage
    """

    # Build mapping: {'alias': 'package_name'}
    package_mapping = {}

    # Handle positional arguments (no alias, so alias == package_name)
    for package in args:
        if isinstance(package, str):
            package_mapping[package] = package
        else:
            raise TypeError("Package names must be strings.")

    # Handle keyword arguments (alias provided)
    for alias, import_name in kwargs.items():
        # If any, take the 'dot' version as the primary guess
        package_mapping[alias] = import_name.replace('_', '.')

    def decorator(func):
        # Inject the LazyModule into the function's global namespace
        for pkg_alias, pkg_name in package_mapping.items():
            func.__globals__[pkg_alias] = _LazyModule(pkg_name)
        return func

    return decorator


def example_dataframe(osgb36=False):
    """
    Returns an example dataframe.

    This functions creates and returns a pandas DataFrame with geographical coordinates either in
    OSGB36 National Grid format (default) or in longitude and latitude format.

    :param osgb36: Whether to use data based on OSGB36 National Grid; defaults to ``True``.
    :type osgb36: bool
    :return: An example dataframe with geographical coordinates.
    :rtype: pandas.DataFrame

    **Tests**::

        >>> from pyhelpers._cache import example_dataframe
        >>> example_dataframe()
                          Easting       Northing
        City
        London      530039.558844  180371.680166
        Birmingham  406705.887014  286868.166642
        Manchester  383830.039036  398113.055831
        Leeds       430147.447354  433553.327117
        >>> example_dataframe(osgb36=False)
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    pd = _check_dependencies('pandas')

    if osgb36:
        _columns = ['Easting', 'Northing']
        _example_df = [
            (530039.5588445, 180371.6801655),  # London
            (406705.8870136, 286868.1666422),  # Birmingham
            (383830.0390357, 398113.0558309),  # Manchester
            (430147.4473539, 433553.3271173),  # Leeds
        ]
    else:
        _columns = ['Longitude', 'Latitude']
        _example_df = [
            (-0.1276474, 51.5073219),  # London
            (-1.9026911, 52.4796992),  # Birmingham
            (-2.2451148, 53.4794892),  # Manchester
            (-1.5437941, 53.7974185),  # Leeds
        ]

    _index = ['London', 'Birmingham', 'Manchester', 'Leeds']

    _example_dataframe = pd.DataFrame(data=_example_df, index=_index, columns=_columns)

    _example_dataframe.index.name = 'City'

    return _example_dataframe


def _confirmed(prompt=None, confirmation_required=True, resp=False):
    """
    Prompts the user for confirmation to proceed.

    This function prompts the user with a Yes/No message specified by ``prompt``.
    If ``confirmation_required=True``, the user must confirm to proceed.
    The function returns ``True`` if the user confirms (either by typing ``'y'`` or ``'yes'``),
    otherwise ``False``.

    See also [`OPS-C-1 <https://code.activestate.com/recipes/541096/>`_].

    :param prompt: Message prompting a response (Yes/No); defaults to ``None``.
    :type prompt: str | None
    :param confirmation_required: Whether confirmation is mandatory; defaults to ``True``.
    :type confirmation_required: bool
    :param resp: Default response if no input is provided; defaults to ``False``.
    :type resp: bool
    :return: ``True`` if confirmed, ``False`` otherwise.
    :rtype: bool

    **Tests**::

        >>> from pyhelpers._cache import _confirmed
        >>> if _confirmed(prompt="Testing if the function works?", resp=True):
        ...     print("Passed.")
        Testing if the function works? [Yes]|No: yes
        Passed.
    """

    if confirmation_required:
        if prompt is None:
            prompt_ = "Confirmed?"
        else:
            prompt_ = copy.copy(prompt)

        if resp:  # meaning that default response is True
            prompt_ = f"{prompt_} [Yes]|No: "
        else:
            prompt_ = f"{prompt_} [No]|Yes: "

        ans = input(prompt_)
        if not ans:
            return resp

        if re.match('[Yy](es)?', ans):
            return True
        if re.match('[Nn](o)?', ans):
            return False
        return None

    else:
        return True


def _normalize_token(text, preserve_dot=False):
    """
    Normalize a single string token to ``snake_case`` format.

    This function handles ``camelCase`` and ``PascalCase`` structural splits, forces lowercase,
    swaps common spacing symbols to underscores and strips out illegal punctuation characters.

    :param text: The raw ``str`` token or name segment to clean.
    :type text: str
    :param preserve_dot: If ``True``, protects the dot character (``.``) from being stripped to
        safeguard file extensions. Defaults to ``False``.
    :type preserve_dot: bool
    :return: A cleaned, lowercase snake_case representation of the ``text`` parameter.
    :rtype: str
    """

    if not text:
        return ''

        # Isolate leading and trailing hyphens, underscores and spaces immediately
    leading_match = re.match(r'^[\s\-_]+', text)
    trailing_match = re.search(r'[\s\-_]+$', text)

    leading_prefix = leading_match.group(0) if leading_match else ''
    trailing_suffix = trailing_match.group(0) if trailing_match else ''

    # Strip boundaries off the core text so conversions can run safely
    core_text = text[len(leading_prefix):]
    if trailing_suffix:
        core_text = core_text[:-len(trailing_suffix)]

    # If the entire token is boundary characters (e.g. "_", "  "), `leading_prefix` and
    # `trailing_suffix` overlap the same span; without this guard the reattachment logic
    # below would double-count that span (e.g. "_" would incorrectly become "__")
    if not core_text:
        return '_' if (leading_prefix or trailing_suffix) else ''

    # Handle camelCase and PascalCase splitting transformations cleanly
    txt = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', core_text)
    txt = re.sub(r'([A-Z]+)(?=[A-Z][a-z])', r'\1_', txt)
    txt = txt.lower()  # Cast everything to lowercase

    # Convert spaces, hyphens and slashes to underscores
    txt = re.sub(r'[\s\-/\\]+', '_', txt)

    # Strip punctuation (conditionally keeping the dot for file extensions)
    if preserve_dot and '.' in core_text:
        txt = re.sub(r'[^\w.]', '', txt)
        txt = re.sub(r'\.+', '.', txt)  # Condense duplicate consecutive dots if present
    else:
        txt = re.sub(r'\W', '', txt)

    # Condense duplicate consecutive underscores and strip interior edges
    txt = re.sub(r'_+', '_', txt).strip('_')

    # Re-attach raw boundaries using underscores as placeholder flags
    if leading_prefix:
        txt = f'_{txt}'
    if trailing_suffix and not (preserve_dot and '.' in txt):
        # Do not append past a preserved extension
        txt = f'{txt}_'

    return txt


def _normalize_path(path, sep="/", as_str=True, add_slash=False):
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
        a ``pathlib.Path`` object is returned instead. Defaults to ``False``.
    :type as_str: bool
    :param add_slash: Whether to prepend ``"./"`` to a relative path that does not already begin
        with ``"./"``, ``"../"`` or an absolute path prefix (e.g. ``"/"`` or a Windows drive letter
        such as ``"C:/"``). This only takes effect when ``as_str=True``, since ``pathlib.Path``
        normalizes away a leading ``"./"`` when constructing a ``Path`` object.
        Defaults to ``False``.
    :type add_slash: bool
    :return: Pathname formatted to a consistent standard,
        either as a ``pathlib.Path`` object (default) or as a string when ``as_str=True``.
    :rtype: str | pathlib.Path

    **Examples**::

        >>> from pyhelpers._cache import _normalize_path
        >>> from pathlib import Path
        >>> import os

        >>> path = "tests\\data\\dat.csv"
        >>> _normalize_path(path)
        'tests/data/dat.csv'

        >>> _normalize_path(path, add_slash=True)
        './tests/data/dat.csv'

        >>> path = "tests//data/dat.csv"
        >>> _normalize_path(path)
        'tests/data/dat.csv'

        >>> path = Path("tests\\data/dat.csv")  # Assuming Windows OS
        >>> _normalize_path(path, sep=os.sep)
        'tests\\data\\dat.csv'
        >>> _normalize_path(path, sep=os.sep, as_str=False)
        WindowsPath('tests/data/dat.csv')
    """

    path_str = os.fsdecode(path)

    # Normalize any mix of "\" and "/" to a single "/" in one pass
    path_str = re.sub(r"[\\/]+", "/", path_str)

    if not as_str:  # `add_slash` and `sep` are string-only concerns
        # `Path` strips a leading "./" and normalizes separators itself,
        # so both `add_slash` and `sep` would be discarded here
        return pathlib.Path(path_str)

    if add_slash and not re.match(r"^(\.{1,2}/|/|[A-Za-z]:/)", path_str):
        path_str = f"./{path_str}"

    return path_str if sep == "/" else path_str.replace("/", sep)


def _format_display_path(path, normalized=True, surrounded_by='"', is_dir=None, prepend_dot=False):
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

        >>> from pyhelpers._cache import _format_display_path

        >>> _format_display_path("pyhelpers\\data")
        '"./pyhelpers/data/"'

        >>> _format_display_path("pyhelpers\\data", normalized=False)  # on Windows
        '"pyhelpers\\data\\"'

        >>> _format_display_path("pyhelpers\\data\\pyhelpers.dat", prepend_dot=True)
        '"./pyhelpers/data/pyhelpers.dat"'

        >>> _format_display_path("C:\\Windows", prepend_dot=True)  # on Windows
        '"C:/Windows/"'
    """

    path_str = os.fsdecode(path)

    if is_dir is None:
        if os.path.exists(path_str):
            is_dir = os.path.isdir(path_str)
        else:  # Heuristic fallback: assume no extension means a directory
            is_dir = os.path.splitext(path_str)[1] == ''

    # Handle leading slash/dot (for relative paths)
    if prepend_dot and not os.path.isabs(path_str) and not path_str.startswith((".", os.sep, "/")):
        path_str = f".{os.sep}{path_str}"

    # Handle trailing slash
    if not path_str.endswith((os.sep, "/")) and is_dir:
        path_str += os.sep

    if normalized:
        path_str = _normalize_path(path_str)

    s = surrounded_by or ""

    return f"{s}{path_str}{s}"


def _get_relative_path(path, normalized=True):
    """
    Check if the pathname is relative to the current working directory.

    If the specified ``pathname`` resides within the current working directory, this function
    returns its relative path counterpart. Otherwise, it returns the original absolute path.

    :param path: Pathname (of a file or directory).
    :type path: str | bytes | pathlib.Path | os.PathLike
    :param normalized: Whether to normalize the returned pathname. Defaults to ``True``.
    :type normalized: bool
    :return: A location relative to the current working directory
        if ``pathname`` is within the current working directory; otherwise, a copy of ``pathname``.
    :rtype: str | pathlib.Path

    **Tests**::

        >>> from pyhelpers._cache import _get_relative_path
        >>> from pyhelpers.dirs import cd

        >>> _get_relative_path(path=".")
        '.'

        >>> _get_relative_path(path=cd())
        '.'

        >>> _get_relative_path(path="C:/Windows")
        'C:/Windows'

        >>> _get_relative_path(path="C:\\Program Files", normalized=False)
        WindowsPath('C:/Program Files')
    """

    path_str = os.fsdecode(path)

    path_obj = pathlib.Path(path_str).resolve()
    cwd_obj = pathlib.Path.cwd()

    if path_obj.is_relative_to(cwd_obj):
        rel_path = path_obj.relative_to(cwd_obj)
    else:
        rel_path = path_obj  # Return original absolute path if outside CWD

    return _normalize_path(rel_path) if normalized else rel_path


def _find_file_path(name, options=None, target=None, as_str=False):
    # noinspection PyShadowingNames
    """
    Check the pathname of a specified file given its name or filename.

    This function determines if a specified executable or file exists by verifying an explicit
    target path, searching through a provided list of options, or checking the system's PATH.
    The checks run in order (``target``, direct lookup of ``name`` itself, ``options``, PATH),
    and a failed ``target`` check falls through to the remaining checks rather than aborting
    the search.

    :param name: Name or filename of the file/executable.
    :type name: str
    :param options: Possible pathnames or directories to search for ``name``; defaults to ``None``.
    :type options: list | set | None
    :param target: Specific known pathname to validate first; defaults to ``None``.
    :type target: str | None
    :param as_str: If ``True``, returns the output path as a string instead of a ``pathlib.Path``
        object. Defaults to ``False``.
    :type as_str: bool
    :return: Tuple containing a boolean indicating existence, and the resolved path if found.
    :rtype: tuple[bool, pathlib.Path | str | None]

    **Tests**::

        >>> from pyhelpers._cache import _find_file_path
        >>> from pathlib import Path
        >>> import sys

        >>> python_exe = "python.exe"
        >>> python_exe_exists, path_to_python_exe = _find_file_path(python_exe)
        >>> python_exe_exists
        True

        >>> possible_paths = [Path(sys.executable).parent, sys.executable]
        >>> target = possible_paths[0]
        >>> python_exe_exists, path_to_python_exe = _find_file_path(python_exe, target=target)
        >>> python_exe_exists
        False

        >>> target = possible_paths[1]
        >>> python_exe_exists, path_to_python_exe = _find_file_path(python_exe, target=target)
        >>> python_exe_exists
        True

        >>> python_exe_exists, path_to_python_exe = _find_file_path(possible_paths[1])
        >>> python_exe_exists
        True

        >>> text_exe = "pyhelpers.exe"  # This file does not actually exist
        >>> test_exe_exists, path_to_test_exe = _find_file_path(text_exe, possible_paths)
        >>> test_exe_exists
        False
    """

    name_str = str(name)

    # Target priority path
    if target:  # Check `target` if provided
        target_path = pathlib.Path(target).resolve()

        # Verify it's a file and the name matches (case-insensitive for safety)
        if target_path.is_file() and name_str.lower() in target_path.name.lower():
            return True, (str(target_path) if as_str else target_path)

    # Direct absolute/relative path lookup
    direct_path = pathlib.Path(name).resolve()
    if direct_path.is_file():  # Check if `name` itself is already a valid direct path
        return True, (str(direct_path) if as_str else direct_path)

    # Dynamic search pipeline
    search_paths = []
    if options:
        search_paths.extend(list(options))

    # Add system PATH lookup
    system_match = shutil.which(name_str)  # noqa
    if system_match:
        search_paths.append(system_match)

    # Iterate and validate
    for p in search_paths:
        if p is None:
            continue

        p_obj = pathlib.Path(p).resolve()
        # If the option is a directory, look for 'name' inside it
        potential_file = (p_obj / name_str) if p_obj.is_dir() else p_obj

        if potential_file.is_file():
            # Validate substring match to prevent spoofed/random file resolutions
            if name_str.lower() in potential_file.name.lower():
                return True, (str(potential_file) if as_str else potential_file)

    return False, None


def _format_exception_message(exception=None, prefix=""):
    """
    Formats a consolidated error message string.

    This function combines a prefix with an error description (string or ``Exception``), ensuring
    proper spacing and terminal punctuation.

    :param exception: Error message or ``Exception`` object. Defaults to ``None``.
    :type exception: BaseException | Exception | str | None
    :param prefix: Text to prepend to the error description. Defaults to ``""``.
    :type prefix: str
    :return: Formatted error message.
    :rtype: str

    **Tests**::

        >>> from pyhelpers._cache import _format_exception_message
        >>> _format_exception_message("test")
        'Failed. Error: test.'
        >>> _format_exception_message("test", prefix="Failed.")
        'Failed. test.'
        >>> _format_exception_message(ValueError('There is a value error.'))
        'There is a value error.'
    """

    # Convert exception to string and clean it up
    msg_str = str(exception).strip() if exception is not None else ""

    # Add terminal punctuation if content exists and isn't already punctuated
    if msg_str and not msg_str.endswith((".", "!", "?")):
        msg_str += "."

    # Clean join to handle empty prefix or empty message
    return " ".join(filter(None, [prefix.strip(), msg_str]))


def _print_failure_message(e, prefix="Error:", verbose=True, raise_error=False):
    # noinspection PyShadowingNames
    """
    Prints an error message associated with the occurrence of an ``Exception``.

    Prints the error message ``msg`` along with details of ``e`` (if provided).
    If ``verbose=True``, additional relevant information is printed to the console.

    :param e: ``Exception`` or any of its subclasses, indicating the error message;
        defaults to ``None``.
    :type e: Exception | BaseException | str | None
    :param prefix: A text string to prepend to the details of ``e``; defaults to ``"Error:"``.
    :type prefix: str
    :param verbose: Whether to print additional information to the console; defaults to ``True``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :return: None.
    :rtype: None

    **Tests**::

        >>> from pyhelpers._cache import _print_failure_message
        >>> try:
        ...     result = 1 / 0  # This will raise a ZeroDivisionError
        ... except ZeroDivisionError as e:
        ...     _print_failure_message(e, prefix="Error:")
        Error: division by zero.
        >>> try:
        ...     result = 1 / 0  # This will raise a ZeroDivisionError
        ... except ZeroDivisionError as e:
        ...     _print_failure_message(e, prefix="Error:", raise_error=True, verbose=False)
        Traceback (most recent call last):
          ...
            result = 1 / 0  # This will raise a ZeroDivisionError
                     ~~^~~
        ZeroDivisionError: division by zero
    """

    if verbose:
        msg = _format_exception_message(exception=e, prefix=prefix)
        if msg.strip():
            print(msg)

    if raise_error:
        if isinstance(e, BaseException):
            raise e  # Raise the passed exception object
        raise Exception(str(e))  # Fallback if e is just a message string

    return None


def _init_requests_session(url, max_retries=5, backoff_factor=0.1, retry_status='default',
                           **kwargs):
    # noinspection PyShadowingNames
    """
    Instantiates a `requests <https://docs.python-requests.org/en/latest/>`_ session
    with configurable retry behavior.

    :param url: A valid URL to establish the session.
    :type url: str
    :param max_retries: Maximum number of retry attempts; defaults to ``5``.
    :type max_retries: int
    :param backoff_factor: Backoff factor for exponential backoff in retries; defaults to ``0.1``.
    :type backoff_factor: float
    :param retry_status: HTTP status codes that trigger retries,
        derived from `urllib3.util.Retry()`_;
        defaults to ``[429, 500, 502, 503, 504]`` when ``retry_status='default'``.
    :param kwargs: [Optional] Additional parameters for the class `urllib3.util.Retry()`_.
    :return: A `requests.Session()`_ instance configured with the specified retry settings.
    :rtype: requests.Session

    .. _`requests`:
        https://docs.python-requests.org/en/latest/
    .. _`urllib3.util.Retry()`:
        https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry
    .. _`requests.Session()`:
        https://2.python-requests.org/en/master/api/#request-sessions

    **Examples**::

        >>> from pyhelpers._cache import _init_requests_session
        >>> url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> s = _init_requests_session(url)
        >>> type(s)
        requests.sessions.Session
    """

    codes_for_retries = [429, 500, 502, 503, 504] if retry_status == 'default' else retry_status
    kwargs.update({'backoff_factor': backoff_factor, 'status_forcelist': codes_for_retries})
    max_retries = urllib3.util.Retry(total=max_retries, **kwargs)

    session = requests.Session()

    # noinspection HttpUrlsUsage
    session.mount(
        prefix='https://' if url.startswith('https:') else 'http://',
        adapter=requests.adapters.HTTPAdapter(max_retries=max_retries))

    return session


def _check_url_scheme(url, allowed_schemes=None):
    """
    Checks if the scheme of a URL is allowed.

    :param url: A URL.
    :type url: str
    :param allowed_schemes: Safe URL schemes.
    :type allowed_schemes: list | set | None
    :return: The parsed URL.
    :rtype: urllib.parse.ParseResult

    **Examples**::

        >>> from pyhelpers._cache import _check_url_scheme
        >>> _check_url_scheme('https://github.com/mikeqfu/pyhelpers')
        ParseResult(scheme='https', netloc='github.com', path='/mikeqfu/pyhelpers', params='', q...
        >>> _check_url_scheme('httpx://github.com/mikeqfu/pyhelpers')
        Traceback (most recent call last):
            ...
        ValueError: Unknown/unsafe URL scheme: 'httpx'.
    """

    parsed_url = urllib.parse.urlparse(url)

    if allowed_schemes is None:
        schemes = {'https', 'http', 'ftp', 'file'}
    else:
        schemes = {allowed_schemes} if isinstance(allowed_schemes, str) else set(allowed_schemes)

    if parsed_url.scheme not in schemes:  # Check that the scheme is valid
        raise ValueError(f"Unknown/unsafe URL scheme: '{parsed_url.scheme}'.")

    return parsed_url


@functools.lru_cache(maxsize=1)
def _load_ansi_escape_codes():
    """
    Loads and filters ANSI escape codes from the package data file.

    The function accesses internal ``ansi-escape-codes.json`` using `importlib.resources`_.
    It filters out keys used for comments (keys starting with ``'_comment_'``).

    :return: A dictionary mapping color/style names (e.g. ``'red'``, ``'bold'``) to their
        full ANSI escape code strings (e.g. ``'\\u001b[31m'``).
        Returns an empty dictionary if the file is missing or invalid.
    :rtype: dict[str, str]

    .. note::

        Exceptions are caught internally; failures return an empty dict and
        print a warning to stderr.

    **Examples**::

        >>> from pyhelpers._cache import _load_ansi_escape_codes
        >>> ansi_escape_codes = _load_ansi_escape_codes()
        >>> ansi_escape_codes.get('red')
        '\\x1b[31m'
        >>> ansi_escape_codes.get('_comment_styles') is None
        True
    """

    try:
        data_path = importlib.resources.files(__package__ or __name__).joinpath(
            "data/ansi-escape-codes.json")

        raw_data = json.loads(data_path.read_text(encoding='utf-8'))

        return {k: v for k, v in raw_data.items() if not k.startswith('_comment_')}

    except Exception as e:  # Fallback
        # print(f"Warning: Failed to load ANSI escape codes. Error: {e}")
        logging.getLogger(__name__).warning(
            'Warning: Failed to load ANSI escape codes.\n  Error: %s', e)
        return {}


def _get_ansi_color_code(colors, show_valid_colors=False, concatenated=True, _spelling='color'):
    """
    Returns the ANSI escape code(s) for the given color name(s) and/or style(s).

    The function handles both single attribute requests and compound sequences
    (e.g. ``['red', 'blue']``) by concatenating the codes into a single escape sequence
    string when appropriate.

    :param colors: A single color/style name (str) or a sequence of names
        (e.g. ``'red'``, ``'bold'``, ``['red', 'bg_blue']``).
    :type colors: str | list[str] | tuple[str]
    :param show_valid_colors: If ``True``, returns a tuple containing the final
        output (string or list) and a set of all valid color/style names.
    :type show_valid_colors: bool
    :param concatenated: If ``True`` (default), multiple requested codes are
        concatenated into a single string (e.g. ``'\\u001b[31m\\u001b[1m'``).
        If ``False``, a list of individual escape code strings is returned
        (e.g. ``['\\u001b[31m', '\\u001b[1m']``).
    :type concatenated: bool
    :return: The ANSI escape code(s). This is a single string if
        ``concatenated=True``, a list of strings if ``concatenated=False``
        and multiple items were requested, or a tuple if ``show_valid_colors=True``.
    :rtype: str | list[str] | tuple[Union[str, list[str]], set[str]]

    :raises ValueError: If an invalid color or style name is provided.

    **Examples**::

        >>> from pyhelpers._cache import _get_ansi_color_code
        >>> _get_ansi_color_code('red')  # \\u001b[31m
        '\\x1b[31m'
        >>> _get_ansi_color_code(['red', 'blue'])  # \\u001b[31m\\u001b[34m
        '\\x1b[31m\\x1b[34m'
        >>> _get_ansi_color_code(['red', 'blue'], concatenated=False)
        >>> # ['\\u001b[31m', '\\u001b[34m']
        ['\\x1b[31m', '\\x1b[34m']
        >>> _get_ansi_color_code('invalid_color')
        Traceback (most recent call last):
            ...
        ValueError: 'invalid_color' is not a valid name.
        >>> _get_ansi_color_code('red', show_valid_colors=True)  # ('\\u001b[31m', ...
        ('\\x1b[31m', {'bg_black', 'bg_blue', 'bg_bright_black', 'bg_bright_blue', ...
    """

    # Handle single string input
    if isinstance(colors, str):
        names = [colors]  # Convert single string to list for uniform processing
    else:
        names = list(colors)

    ansi_escape_codes = _load_ansi_escape_codes()

    # Retrieve the raw numeric codes
    try:
        escape_codes = [ansi_escape_codes[x.lower()] for x in names]
    except KeyError as e:
        raise ValueError(f"'{e.args[0]}' is not a valid {str(_spelling).lower()} name.") from None

    # Create the final ANSI escape sequence
    if concatenated:  # Concatenate all retrieved codes into a single string
        final_code = "".join(escape_codes)
    else:  # Return the list of individual code strings
        final_code = escape_codes

    # If only one input was given, return the string itself, even if not concatenated
    if len(names) == 1 and not concatenated:
        final_code = escape_codes[0]

    valid_names = set(ansi_escape_codes.keys())

    return (final_code, valid_names) if show_valid_colors else final_code


def _transform_point_type(*pts, as_geom=True):
    """
    Transforms iterable data to geometric type or vice versa.

    :param pts: Iterable data representing points (e.g. list of lists/tuples).
    :type pts: list | tuple | shapely.geometry.Point
    :param as_geom: Whether to return points as `shapely.geometry.Point`_; defaults to ``True``.
    :type as_geom: bool
    :return: A sequence of points, including ``None`` if errors occur.
    :rtype: typing.Generator

    .. _`shapely.geometry.Point`: https://shapely.readthedocs.io/en/latest/manual.html#points

    **Examples**::

        >>> from pyhelpers._cache import example_dataframe, _transform_point_type
        >>> from shapely.geometry import Point
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> pt1 = example_df.loc['London'].values  # array([-0.1276474, 51.5073219])
        >>> pt2 = example_df.loc['Birmingham'].values  # array([-1.9026911, 52.4796992])
        >>> geom_points = _transform_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)
        >>> geom_points = _transform_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        [-0.1276474 51.5073219]
        [-1.9026911 52.4796992]
        >>> pt1, pt2 = map(lambda p: Point(p), (pt1, pt2))
        >>> geom_points = _transform_point_type(pt1, pt2)
        >>> for x in geom_points:
        ...     print(x)
        POINT (-0.1276474 51.5073219)
        POINT (-1.9026911 52.4796992)
        >>> geom_points = _transform_point_type(pt1, pt2, as_geom=False)
        >>> for x in geom_points:
        ...     print(x)
        (-0.1276474, 51.5073219)
        (-1.9026911, 52.4796992)
        >>> geom_points_ = _transform_point_type(Point([1, 2, 3]), as_geom=False)
        >>> for x in geom_points_:
        ...     print(x)
        (1.0, 2.0, 3.0)
    """

    for pt in pts:
        if isinstance(pt, shapely.geometry.Point):
            if not as_geom:
                if pt.has_z:
                    pt = (pt.x, pt.y, pt.z)
                else:
                    pt = (pt.x, pt.y)

        elif isinstance(pt, collections.abc.Iterable):
            assert len(list(pt)) <= 3
            if as_geom:
                pt = shapely.geometry.Point(pt)

        yield pt


def _vectorize_text(*texts):
    """
    Converts input texts into a bag-of-words vector representation.

    :param texts: Multiple text inputs as strings or lists of words.
    :type texts: str
    :return: Generator yielding word count vectors for each input.
    :rtype: typing.Generator

    **Examples**::

        >>> from pyhelpers._cache import _vectorize_text
        >>> vectors = list(_vectorize_text("Hello world!", "Hello, hello world."))
        >>> vectors  # "hello" appears twice in the second text
        [[1, 1], [2, 1]]
    """

    token_lists = [
        re.findall(r"[a-zA-Z0-9']+", text.lower().replace("-", " ")) if isinstance(text, str)
        else [] for text in texts
    ]

    if any(not tokens for tokens in token_lists):
        raise TypeError("Inputs must be strings or lists of words.")

    vocab = sorted(set().union(*token_lists))  # Ensure consistent word order

    # Generate word count vectors
    for tokens in token_lists:
        yield [tokens.count(word) for word in vocab]


def _remove_punctuation(text, normalize_whitespace=True, preserve_kebab_case=True,
                        preserve_snake_case=True, exclude=None):
    """
    Removes punctuation from textual data.

    :param text: The input text.
    :type text: str
    :param normalize_whitespace: Whether to collapse all whitespace into single spaces.
        Defaults to ``True``.
    :type normalize_whitespace: bool
    :param preserve_kebab_case: Whether to preserve hyphens in Kebab case (e.g., ``'kebab-case'``).
        Defaults to ``True``.
    :type preserve_kebab_case: bool
    :param preserve_snake_case: Whether to preserve underscores in Snake case
        (e.g. ``'snake_case'``). Defaults to ``True``.
    :param exclude: Punctuation marks to always keep, overriding other parameters.
        Defaults to ``None``.
    :type exclude: str | list | set | None
    :return: The processed text that is without punctuation (and optionally without whitespace).
    :rtype: str

    **Examples**::

        >>> from pyhelpers._cache import _remove_punctuation
        >>> _remove_punctuation('Hello, world!')
        'Hello world'
        >>> raw_text = '   How   are you? '
        >>> _remove_punctuation(raw_text, normalize_whitespace=True)
        'How are you'
        >>> _remove_punctuation(raw_text, normalize_whitespace=False)
        'How   are you'
        >>> _remove_punctuation('No-punctuation!', preserve_kebab_case=False)
        'No punctuation'
        >>> raw_text = 'Hello world!\tThis is a test. :-)'
        >>> _remove_punctuation(raw_text)
        'Hello world This is a test'
        >>> _remove_punctuation(raw_text, normalize_whitespace=False)
        'Hello world \tThis is a test'
        >>> raw_text = "The 'hyphen' is-cool; but underscores_are_not."
        >>> _remove_punctuation(raw_text)
        'The hyphen is-cool but underscores_are_not'
        >>> _remove_punctuation(raw_text, preserve_kebab_case=False, exclude=';')
        'The hyphen is cool; but underscores_are_not'
    """

    if not text:
        return ""

    text_str = str(text)

    # Ensure exclude is a set for O(1) lookup
    exclude_set = set(exclude) if exclude else set()

    if "-" not in exclude_set:
        if preserve_kebab_case:  # Only remove hyphens not surrounded by alphanumeric chars
            text_str = re.sub(r"(?<!\w)-|-(?!\w)", " ", text_str)
        else:
            text_str = text_str.replace("-", " ")

    if "_" not in exclude_set:
        if preserve_snake_case:
            text_str = re.sub(r"(?<!\w)_|_(?!\w)", " ", text_str)
        else:
            text_str = text_str.replace("_", " ")

    # General punctuation cleanup
    to_remove = set(string.punctuation) - exclude_set - {"-", "_"}

    if to_remove:  # Escaping ensures characters like '.' or '[' don't break the regex
        text_str = re.sub(f"[{re.escape(''.join(to_remove))}]", " ", text_str)

    if normalize_whitespace:
        # Collapses multiple spaces, tabs, and newlines into single spaces
        text_str = " ".join(text_str.split())

    return text_str.strip()  # Strip leading/trailing spaces
