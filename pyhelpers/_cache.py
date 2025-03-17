"""
Cached functions and constants.
"""

import collections.abc
import copy
import importlib
import importlib.util
import json
import os
import pkgutil
import re
import shutil
import sys
import urllib.parse

import requests.adapters
import shapely.geometry
import urllib3


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

    pd = _check_dependency(name='pandas')

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


# import name: (package/module name, install name)
_OPTIONAL_DEPENDENCY = json.loads(
    pkgutil.get_data(__name__, "data/optional-dependency.json").decode())


def _check_dependency(name, package=None):
    """
    Imports an optional dependency package/module.

    Attempts to import the module specified by ``name`` as an optional dependency.
    If ``package`` is provided, attempts to import ``name`` from within ``package``.

    :param name: Name of the package/module as an optional dependency of pyhelpers.
    :type name: str
    :param package: Name of the package that contains ``name``; defaults to ``None``.
    :type package: str | None
    :return: Imported module object.
    :rtype: module

    **Tests**::

        >>> from pyhelpers._cache import _check_dependency
        >>> psycopg2_ = _check_dependency(name='psycopg2')
        >>> psycopg2_.__name__
        'psycopg2'
        >>> pyodbc_ = _check_dependency(name='pyodbc')
        >>> pyodbc_.__name__
        'pyodbc'
        >>> sqlalchemy_dialects = _check_dependency(name='dialects', package='sqlalchemy')
        >>> sqlalchemy_dialects.__name__
        'sqlalchemy.dialects'
        >>> gdal_ = _check_dependency(name='gdal', package='osgeo')
        >>> gdal_.__name__
        'osgeo.gdal'
    """

    import_name = name.replace('-', '_')

    if package is None:
        pkg_name = import_name.split('.', 1)[0] if '.' in import_name else None
    else:
        pkg_name = package.replace('-', '_')
        import_name = f'{pkg_name}.{import_name}'

    if import_name in sys.modules:  # The optional dependency has already been imported
        return sys.modules.get(import_name)

    if importlib.util.find_spec(name=import_name, package=pkg_name):
        return importlib.import_module(name=import_name, package=pkg_name)

    # Check `_OPTIONAL_DEPENDENCY` mapping
    if name.startswith('osgeo') or 'gdal' in import_name:
        package_name, install_name = 'GDAL', 'gdal'
    elif import_name in _OPTIONAL_DEPENDENCY:
        package_name, install_name = _OPTIONAL_DEPENDENCY.get(import_name)
    else:
        package_name, install_name = name, name.split('.')[0]

    raise ModuleNotFoundError(
        f"Missing optional dependency '{package_name}'. "
        f"Use `pip` or `conda` to install it, e.g. `pip install {install_name}`.")


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

        if resp is True:  # meaning that default response is True
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

    else:
        return True


def _normalize_pathname(pathname, sep="/", add_slash=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Converts a pathname to a consistent file path format for cross-platform compatibility.

    This function formats a file (or an OS-specific) path to ensure compatibility across
    Windows and Ubuntu (and other Unix-like systems).

    :param pathname: A pathname.
    :type pathname: str | bytes | pathlib.Path | os.PathLike
    :param sep: File path separator used by the operating system; defaults to ``"/"``
        (forward slash) for both Windows and Ubuntu (and other Unix-like systems).
    :type sep: str
    :param add_slash:  If ``True``, adds a leading slash (and, if appropriate, a trailing slash)
        to the returned pathname; defaults to ``False``.
    :type add_slash: bool
    :return: Pathname of a consistent file path format.
    :rtype: str

    **Examples**::

        >>> from pyhelpers._cache import _normalize_pathname
        >>> import os
        >>> import pathlib
        >>> _normalize_pathname("tests\\data\\dat.csv")
        'tests/data/dat.csv'
        >>> _normalize_pathname("tests\\data\\dat.csv", add_slash=True)
        './tests/data/dat.csv'
        >>> _normalize_pathname("tests//data/dat.csv")
        'tests/data/dat.csv'
        >>> pathname = pathlib.Path("tests\\data/dat.csv")
        >>> _normalize_pathname(pathname, sep=os.path.sep)  # On Windows
        'tests\\data\\dat.csv'
        >>> _normalize_pathname(pathname, sep=os.path.sep, add_slash=True)  # On Windows
        '.\\tests\\data\\dat.csv'
    """

    pathname_ = pathname.decode(**kwargs) if isinstance(pathname, bytes) else str(pathname)

    pathname_ = _add_slashes(pathname_, surrounded_by='') if add_slash else pathname_

    return re.sub(r"[\\/]+", re.escape(sep), pathname_)


def _add_slashes(pathname, normalized=True, surrounded_by='"'):
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

    # Normalise path separators for consistency
    path = os.path.normpath(pathname.decode() if isinstance(pathname, bytes) else pathname)

    # Add a leading slash
    if not path.startswith((os.path.sep, ".")) and not os.path.isabs(path):
        path = f".{os.path.sep}{path}"

    has_trailing_sep = path.endswith(os.path.sep)
    is_file_like = os.path.splitext(path)[1] != ''

    if not has_trailing_sep and not is_file_like:  # Add a trailing slash
        path = path + os.path.sep

    if normalized:
        path = _normalize_pathname(path)

    s = surrounded_by or ""

    return f'{s}{path}{s}'


def _check_relative_pathname(pathname, normalized=True):
    """
    Checks if the pathname is relative to the current working directory.

    This function returns a relative pathname of the input ``pathname`` to the current working
    directory if ``pathname`` is within the current working directory;
    otherwise, it returns a copy of the input.

    :param pathname: Pathname (of a file or directory).
    :type pathname: str | bytes | pathlib.Path
    :param normalized: Whether to normalize the returned pathname; defaults to ``True``.
    :type normalized: bool
    :return: A location relative to the current working directory
        if ``pathname`` is within the current working directory; otherwise, a copy of ``pathname``.
    :rtype: str

    **Tests**::

        >>> from pyhelpers._cache import _check_relative_pathname
        >>> from pyhelpers.dirs import cd
        >>> _check_relative_pathname(pathname=".")
        '.'
        >>> _check_relative_pathname(pathname=cd())
        '.'
        >>> _check_relative_pathname(pathname="C:/Windows")
        'C:/Windows'
        >>> _check_relative_pathname(pathname="C:\\Program Files", normalized=False)
        'C:\\Program Files'
    """

    if isinstance(pathname, (bytes, bytearray)):
        pathname_ = str(pathname, encoding='utf-8')
    else:
        pathname_ = str(pathname)

    abs_pathname = os.path.abspath(pathname_)
    abs_cwd = os.getcwd()

    if os.name == "nt":  # Handle different drive letters on Windows
        if os.path.splitdrive(abs_pathname)[0] != os.path.splitdrive(abs_cwd)[0]:
            # Return absolute path if drives differ
            return _normalize_pathname(abs_pathname) if normalized else abs_pathname

    # Check if the pathname is inside the current working directory
    if os.path.commonpath([abs_pathname, abs_cwd]) == abs_cwd:
        try:
            rel_path = os.path.relpath(pathname_)
        except ValueError:
            rel_path = copy.copy(pathname_)

    else:
        rel_path = abs_pathname  # Return original absolute path if outside CWD

    return _normalize_pathname(rel_path) if normalized else rel_path


def _check_file_pathname(name, options=None, target=None):
    # noinspection PyShadowingNames
    """
    Checks the pathname of a specified file given its name or filename.

    This function determines whether the specified executable file exists and returns its pathname.

    :param name: Name or filename of the executable file.
    :type name: str
    :param options: Possible pathnames or directories to search for ``name``; defaults to ``None``.
    :type options: list | set | None
    :param target: Specific pathname that may already be known; defaults to ``None``.
    :type target: str | None
    :return: Tuple containing a boolean indicating if the file exists and its pathname.
    :rtype: tuple[bool, str]

    **Tests**::

        >>> from pyhelpers._cache import _check_file_pathname
        >>> import os
        >>> import sys
        >>> python_exe = "python.exe"
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe)
        >>> python_exe_exists
        True
        >>> possible_paths = [os.path.dirname(sys.executable), sys.executable]
        >>> target = possible_paths[0]
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=target)
        >>> python_exe_exists
        False
        >>> target = possible_paths[1]
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(python_exe, target=target)
        >>> python_exe_exists
        True
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(possible_paths[1])
        >>> python_exe_exists
        True
        >>> text_exe = "pyhelpers.exe"  # This file does not actually exist
        >>> test_exe_exists, path_to_test_exe = _check_file_pathname(text_exe, possible_paths)
        >>> test_exe_exists
        False
        >>> os.path.relpath(path_to_test_exe)
        'pyhelpers.exe'
    """

    if target:
        if os.path.isfile(target) and os.path.splitext(name)[0] in os.path.basename(target):
            file_exists, file_pathname = True, target
        else:
            file_exists, file_pathname = False, None

    else:
        file_pathname = copy.copy(name)

        if os.path.isfile(file_pathname):
            file_exists = True

        else:
            file_exists = False
            alt_pathnames = [shutil.which(file_pathname)]

            if options:
                alt_pathnames = list(options) + alt_pathnames

            for x in [x_ for x_ in alt_pathnames if x_]:
                file_pathname_ = os.path.join(x, file_pathname) if os.path.isdir(x) else x

                if os.path.isfile(file_pathname_) and file_pathname in file_pathname_:
                    file_exists, file_pathname = True, file_pathname_
                    break

    return file_exists, file_pathname


def _format_error_message(e=None, prefix=""):
    """
    Formats an error message.

    This function formats an error message by combining ``message`` and ``e`` (if provided).
    If ``e`` is provided and is a string, it appends ``e`` to ``message``.
    If ``e`` is an ``Exception`` or its subclass, it includes the exception's message
    in the final output.

    :param e: An error message, exception, or any subclass of ``Exception``; defaults to ``None``.
    :type e: Exception | BaseException | str | None
    :param prefix: The base text to prepend to ``e``; defaults to ``""``.
    :type prefix: str
    :return: A formatted error message.
    :rtype: str

    **Tests**::

        >>> from pyhelpers._cache import _format_error_message
        >>> _format_error_message("test")
        'test.'
        >>> _format_error_message("test", prefix="Failed.")
        'Failed. test.'
    """

    if e:
        e_ = f"{e}".strip()
        error_message = e_ + "." if not e_.endswith((".", "!", "?")) else e_
    else:
        error_message = ""

    if prefix:
        error_message = prefix + " " + error_message

    return error_message


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
    :return: None
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
        ZeroDivisionError: division by zero
    """

    error_message = _format_error_message(e=e, prefix=prefix)

    if verbose:
        print(error_message)

    if raise_error:
        raise e


_USER_AGENT_STRINGS = json.loads(
    pkgutil.get_data(__name__, "data/user-agent-strings.json").decode())


def _init_requests_session(url, max_retries=5, backoff_factor=0.1, retry_status='default',
                           **kwargs):
    # noinspection PyShadowingNames
    """
    Instantiates a `requests <https://docs.python-requests.org/en/latest/>`_ session
    with configurable retry behaviour.

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


_ANSI_ESCAPE_CODES = json.loads(
    pkgutil.get_data(__name__, "data/ansi-escape-codes.json").decode())


def _get_ansi_colour_code(colours, show_valid_colours=False):
    """
    Returns the ANSI escape code(s) for the given colour name(s).

    :param colours: A single colour name (str) or a sequence of colour names
        (e.g. 'red', ['red', 'green']).
    :type colours: str | list[str] | tuple[str]
    :param show_valid_colours: If ``True``, returns a tuple containing the ANSI code(s) and
        a set of valid colour names.
    :type show_valid_colours: bool
    :return: The ANSI escape code(s) for the given colour(s), or an error message
        if an invalid colour is provided.
    :rtype: str | list[str] | tuple[str | list[str], set[str]]

    **Examples**::

        >>> from pyhelpers._cache import _get_ansi_colour_code
        >>> _get_ansi_colour_code('red')
        '\\033[31m'
        >>> _get_ansi_colour_code(['red', 'blue'])
        ['\\033[31m', '\\033[34m']
        >>> _get_ansi_colour_code('invalid_colour')
        Traceback (most recent call last):
            ...
        ValueError: 'invalid_colour' is not a valid colour name.
        >>> _get_ansi_colour_code('red', show_valid_colours=True)
        ('\\033[31m', {'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', ...})
    """

    if isinstance(colours, str):
        colours = [colours]  # Convert single string to list for uniform processing

    try:
        color_codes = [_ANSI_ESCAPE_CODES[x.lower()] for x in colours]
    except KeyError as e:
        raise ValueError(f"'{e.args[0]}' is not a valid colour name.") from None

    if len(color_codes) == 1:
        color_codes = color_codes[0]  # Return a single string instead of a list

    return (color_codes, set(_ANSI_ESCAPE_CODES)) if show_valid_colours else color_codes


_ENGLISH_NUMERALS = json.loads(
    pkgutil.get_data(__name__, "data/english-numerals.json").decode())


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


def _vectorize_text(*text):
    """
    Converts input texts into a bag-of-words vector representation.

    :param text: Multiple text inputs as strings or lists of words.
    :type text: str
    :return: Generator yielding word count vectors for each input.
    :rtype: typing.Generator

    **Examples**::

        >>> from pyhelpers._cache import _vectorize_text
        >>> vectors = list(_vectorize_text("Hello world!", "Hello, hello world."))
        >>> vectors  # "hello" appears twice in the second text
        [[1, 1], [2, 1]]
    """

    text_ = [
        re.findall(r"[a-zA-Z0-9'-]+", x.lower()) if isinstance(x, str)
        else [x_.lower() for x_ in x] if isinstance(x, list)
        else None
        for x in text
    ]
    if None in text_:
        raise TypeError("Inputs must be strings or lists of words.")

    doc_words = sorted(set().union(*text_))  # Ensure consistent word order

    # Generate word count vectors
    for x in text_:
        yield [x.count(word) for word in doc_words]


def _remove_punctuation(text, rm_whitespace=True, preserve_hyphenated=True):
    """
    Removes punctuation from textual data.

    :param text: The input text from which punctuation will be removed.
    :type text: str
    :param rm_whitespace: Whether to remove whitespace characters as well; defaults to ``True``.
    :type rm_whitespace: bool
    :param preserve_hyphenated: Whether to preserve hyphenated words; defaults to ``True``.
    :type preserve_hyphenated: bool
    :return: The input text without punctuation (and optionally without whitespace).
    :rtype: str

    **Examples**::

        >>> from pyhelpers._cache import _remove_punctuation
        >>> _remove_punctuation('Hello, world!')
        'Hello world'
        >>> raw_text = '   How   are you? '
        >>> _remove_punctuation(raw_text)
        'How are you'
        >>> _remove_punctuation(raw_text, rm_whitespace=False)
        'How   are you'
        >>> _remove_punctuation('No-punctuation!', preserve_hyphenated=False)
        'No punctuation'
        >>> raw_text = 'Hello world!\tThis is a test. :-)'
        >>> _remove_punctuation(raw_text)
        'Hello world This is a test'
        >>> _remove_punctuation(raw_text, rm_whitespace=False)
        'Hello world \tThis is a test'
    """

    if preserve_hyphenated:  # Remove hyphens only if not between words
        text_ = re.sub(r'(?<!\w)-|-(?!\w)', ' ', text)  # Remove isolated hyphens only
        text_ = re.sub(r'[^\w\s-]', ' ', text_)  # Remove punctuation except hyphens
    else:
        text_ = re.sub(r'[^\w\s]', ' ', text)  # Remove all hyphens completely

    # Strip leading/trailing spaces
    text_ = text_.strip()

    # Normalize whitespace by collapsing multiple spaces
    if rm_whitespace:
        text_ = ' '.join(text_.split())

    return text_
