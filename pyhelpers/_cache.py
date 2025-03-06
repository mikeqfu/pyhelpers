"""
Cached functions and constants.
"""

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

# import name: (package/module name, install name)
_OPTIONAL_DEPENDENCY = json.loads(
    pkgutil.get_data(__name__, "data/optional-dependency.json").decode())


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


def _check_relative_pathname(pathname):
    """
    Checks if the pathname is relative to the current working directory.

    This function returns a relative pathname of the input ``pathname`` to the current working
    directory if ``pathname`` is within the current working directory;
    otherwise, it returns a copy of the input.

    :param pathname: Pathname (of a file or directory).
    :type pathname: str | bytes | pathlib.Path
    :return: A location relative to the current working directory
        if ``pathname`` is within the current working directory; otherwise, a copy of ``pathname``.
    :rtype: str

    **Tests**::

        >>> from pyhelpers._cache import _check_relative_pathname
        >>> from pyhelpers.dirs import cd
        >>> _check_relative_pathname(".")
        '.'
        >>> _check_relative_pathname(cd())
        '.'
        >>> _check_relative_pathname("C:\\Program Files")
        'C:\\Program Files'
        >>> _check_relative_pathname(pathname="C:/Windows")
        'C:/Windows'
    """

    try:
        rel_path = os.path.relpath(pathname)
    except ValueError:
        rel_path = copy.copy(pathname)

    if not isinstance(rel_path, str):
        rel_path = str(rel_path, encoding='utf-8')

    return rel_path


def _add_slashes(pathname):
    """
    Adds leading and/or trailing slashes to a given pathname for formatting or display purposes.

    :param pathname: The pathname of a file or directory.
    :type pathname: str | bytes | os.PathLike
    :return: A formatted pathname with added slashes.
    :rtype: str

    **Examples**::

        >>> from pyhelpers._cache import _add_slashes
        >>> _add_slashes("pyhelpers\\data")
        '".\\pyhelpers\\data\\"'
        >>> _add_slashes("pyhelpers\\data\\pyhelpers.dat")
        '".\\pyhelpers\\data\\pyhelpers.dat"'
        >>> _add_slashes("C:\\Windows")
        '"C:\\Windows\\"'
    """

    # Normalise path separators for consistency
    path = os.path.normpath(pathname.decode() if isinstance(pathname, bytes) else pathname)

    # Add a leading slash if necessary
    if not path.startswith((os.path.sep, ".")) and not os.path.isabs(path):
        # For Windows, add './' or '.\' depending on the system separator
        path = f".{os.path.sep}{path}"

    has_trailing_sep = path.endswith(os.path.sep)
    is_file_like = os.path.splitext(path)[1] != ''

    if not has_trailing_sep and not is_file_like:  # Add a trailing slash
        path = path + os.path.sep

    return f'"{path}"'


def _check_file_pathname(name, options=None, target=None):
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
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(
        ...     python_exe, target=possible_paths[0])
        >>> python_exe_exists
        False
        >>> python_exe_exists, path_to_python_exe = _check_file_pathname(
        ...     python_exe, target=possible_paths[1])
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
        >>> _check_url_scheme('http://github.com/mikeqfu/pyhelpers')
        Traceback (most recent call last):
            ...
        ValueError: Unsafe URL scheme: 'http'.
    """

    parsed_url = urllib.parse.urlparse(url)

    if allowed_schemes is None:
        allowed_schemes_ = {'https', 'http', 'ftp', 'file'}
    else:
        allowed_schemes_ = {allowed_schemes} if isinstance(allowed_schemes, str) \
            else set(allowed_schemes)

    # Check that the scheme is either 'http' or 'https'
    if parsed_url.scheme not in allowed_schemes_:
        raise ValueError(f"Unsafe URL scheme: '{parsed_url.scheme}'.")

    return parsed_url


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


_USER_AGENT_STRINGS = json.loads(
    pkgutil.get_data(__name__, "data/user-agent-strings.json").decode())

_ENGLISH_NUMERALS = json.loads(
    pkgutil.get_data(__name__, "data/english-numerals.json").decode())

_ANSI_ESCAPE_CODES = json.loads(
    pkgutil.get_data(__name__, "data/ansi-escape-codes.json").decode())
