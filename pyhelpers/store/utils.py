"""
Utilities that support the main submodules of :mod:`~pyhelpers.store`.
"""

import contextlib
import functools
import inspect
import logging
import os
import pathlib
import sys
import warnings

from .._cache import _add_slashes, _check_dependencies, _check_relative_pathname


def _print_wrapped_string(message, filename, end, print_wrap_limit=100, **kwargs):
    """
    Prints a string, splitting it into two lines if it exceeds the threshold, with the second half
    being indented based on the initial indentation level.

    :param message: The string to print.
    :type message: str
    :param filename: The filename to be included in the string.
    :type filename: str
    :param end:
    :param print_wrap_limit: The maximum length before splitting.
    :type print_wrap_limit: int | None
    """

    if print_wrap_limit:
        stripped_text = message.lstrip()  # Remove leading spaces for accurate tab count
        leading_indentation = len(message) - len(stripped_text)

        if len(stripped_text) <= print_wrap_limit:
            print(message, end=end, **kwargs)

        else:
            # Find a suitable split point (preferably at a space)
            split_index = message.find(f'"{filename}"') + len(f'"{filename}"')
            if message[split_index] == " ":
                split_index += 1  # Move to space if it exists

            first_part = message[:split_index].rstrip()  # Trim trailing spaces
            second_part = message[split_index:].lstrip()  # Trim leading spaces

            # Print first part as is, plus " ... "
            print(first_part + " ... ", **kwargs)

            # Print second part with increased indentation (original + 1 extra double spaces)
            indent_str = " " * (leading_indentation + 2)
            print(f"{indent_str}{second_part}", end=end, **kwargs)

    else:
        print(message, end=end, **kwargs)


def _check_saving_path(path_to_file, verbose=False, print_prefix="", state_verb="Saving",
                       state_prep="to", print_suffix="", print_end=" ... ", print_wrap_limit=None,
                       belated=False, ret_info=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Verifies a specified file path before saving.

    :param path_to_file: Path where the file will be saved.
    :type path_to_file: str | pathlib.Path
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Text prefixed to the default print message; defaults to ``""``.
    :type print_prefix: str
    :param state_verb: Verb indicating the action being performed, e.g. *saving* or *updating*;
        defaults to ``"Saving"``.
    :type state_verb: str
    :param state_prep: Preposition associated with ``state_verb``; defaults to ``"to"``.
    :type state_prep: str
    :param print_suffix: Text suffixed to the default print message; defaults to ``""``.
    :type print_suffix: str
    :param print_end: String passed to the ``end`` parameter of ``print``; defaults to ``" ... "``.
    :type print_end: str
    :param print_wrap_limit: Maximum length of the string before splitting into two lines;
        defaults to ``None``, which disables splitting. If the string exceeds this value,
        e.g. ``100``, it will be split at (before) ``state_prep`` to improve readability
        when printed.
    :type print_wrap_limit: int | None
    :param ret_info: Whether to return file path information; defaults to ``False``.
    :type ret_info: bool
    :return: A tuple containing the relative path and, if ``ret_info=True``, the filename.
    :rtype: tuple

    **Tests**::

        >>> from pyhelpers.store import _check_saving_path
        >>> from pyhelpers.dirs import cd
        >>> path_to_file = cd()
        >>> _check_saving_path(path_to_file, verbose=True)
        Traceback (most recent call last):
            ...
        ValueError: The input for '<path_to_file>' may not be a file path.
        >>> path_to_file = "pyhelpers.txt"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" ... Passed.
        >>> path_to_file = cd("tests", "documents", "pyhelpers.txt")
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" to "./tests/documents/" ... Passed.
        >>> _check_saving_path(path_to_file, verbose=True, print_wrap_limit=10); print("Passed.")
        Saving "pyhelpers.txt" ...
          to "./tests/documents/" ... Passed.
        >>> path_to_file = "C:\\Windows\\pyhelpers.txt"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" to "C:/Windows/" ... Passed.
        >>> path_to_file = "C:\\pyhelpers.txt"
        >>> _check_saving_path(path_to_file, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" to "C:/" ... Passed.
    """

    file_path = pathlib.Path(path_to_file).resolve()
    cwd = pathlib.Path.cwd()

    if file_path.is_dir():
        raise ValueError(f"The input for '{path_to_file}' may not be a file path.")

    try:
        # Attempt to get path relative to current working directory
        rel_dir_path = file_path.parent.relative_to(cwd)
    except ValueError:  # If outside CWD (common on Linux mounts or different Windows drives)
        if verbose == 2:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(
                f'\n  "{file_path.parent}" is outside the current working directory.')
        rel_dir_path = file_path.parent

    # Ensure the directory exists
    rel_dir_path.mkdir(parents=True, exist_ok=True)

    filename = file_path.name if file_path.suffix else ""

    if verbose:
        # Flip verb to 'Updating' if file exists, unless 'belated' is flagged
        if os.path.isfile(file_path) and not belated:
            state_verb, state_prep = "Updating", "in"

        prt_end = print_end or "\n"

        # Cross-platform check: Is the file in the CWD or its immediate root?
        # On Linux, .anchor is '/', on Windows it is 'C:\\'
        is_internal = file_path.is_relative_to(cwd)

        # If the directory is effectively the "base" or on the same local drive/anchor
        if (rel_dir_path == rel_dir_path.parent or rel_dir_path == file_path.parent) and \
                (file_path.anchor == cwd.anchor):
            message = f'{print_prefix}{state_verb} "{filename}"{print_suffix}'
            print(message, end=prt_end, **kwargs)
        else:
            # Use relative path if internal, otherwise absolute
            display_path = rel_dir_path if is_internal else file_path.parent
            message = (f'{print_prefix}{state_verb} "{filename}" '
                       f'{state_prep} {_add_slashes(display_path)}{print_suffix}')

            _print_wrapped_string(
                message=message, filename=filename, end=prt_end, print_wrap_limit=print_wrap_limit,
                **kwargs)

    if ret_info:
        file_ext = "".join(file_path.suffixes).lower()
        return file_path, rel_dir_path, file_ext

    return None


def _autofit_column_width(writer, writer_kwargs, **kwargs):
    """
    Adjusts the column widths in an Excel spreadsheet based on the content length.

    This function is specifically designed for *openpyxl* engine when working with *Pandas*
    `ExcelWriter`_. It iterates through each column of the specified sheet and calculates
    the maximum length of the content. It then adjusts the column width to accommodate the
    longest content plus some padding.

    :param writer: ExcelWriter object used to write data into Excel file.
    :type writer: pandas.ExcelWriter
    :param writer_kwargs: Keyword arguments passed to the `ExcelWriter`_, including the engine.
    :type writer_kwargs: dict
    :param kwargs: [Optional] Additional parameters.

    .. _ExcelWriter:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html

    .. note::

        - This function assumes that *openpyxl* engine is used
          (i.e. ``writer_kwargs['engine'] == 'openpyxl'``).
        - It modifies the column dimensions directly in the ``pandas.ExcelWriter`` object.

    .. seealso::

        - For more information on *openpyxl*, refer to the official documentation:
          https://openpyxl.readthedocs.io/en/stable/
    """

    if 'sheet_name' in kwargs and writer_kwargs['engine'] == 'openpyxl':
        # Reference: https://stackoverflow.com/questions/39529662/
        ws = writer.sheets[kwargs.get('sheet_name')]
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            ws.column_dimensions[column_letter].width = (max_length + 2) * 1.1


def _check_loading_path(path_to_file, verbose=False, print_prefix="", state_verb="Loading",
                        print_suffix="", print_end=" ... ", ret_info=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Checks the status of loading a file from a specified path.

    :param path_to_file: Path where the file is located.
    :type path_to_file: str | bytes | pathlib.Path
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Prefix added to the default printing message; defaults to ``""``.
    :type print_prefix: str
    :param state_verb: Action verb indicating *loading* or *reading* a file;
        defaults to ``"Loading"``.
    :type state_verb: str
    :param print_suffix: Suffix added to the default printing message; defaults to ``""``.
    :type print_suffix: str
    :param print_end: String passed to ``end`` parameter for ``print()``; defaults to ``" ... "``.
    :type print_end: str
    :param ret_info: Whether to return file path information; defaults to ``False``.
    :type ret_info: bool

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers._cache import _check_relative_pathname
        >>> from pyhelpers.dirs import cd
        >>> from pathlib import Path
        >>> path_to_file = cd("test_func.py")
        >>> _check_loading_path(path_to_file, verbose=True); print("Passed.")
        Loading "./test_func.py" ... Passed.
        >>> file_path, rel_dir_path = _check_loading_path(path_to_file, ret_info=True)
        >>> _check_relative_pathname(file_path)
        'test_func.py'
        >>> _check_relative_pathname(rel_dir_path)
        '.'
        >>> path_to_file = Path("C:\\Windows\\pyhelpers.pkg")
        >>> _check_loading_path(path_to_file, verbose=True); print("Passed.")
        Loading "C:/Windows/pyhelpers.pkg" ... Passed.
        >>> file_path, rel_dir_path = _check_loading_path(path_to_file, ret_info=True)
        >>> _check_relative_pathname(file_path)
        'C:/Windows/pyhelpers.pkg'
        >>> _check_relative_pathname(rel_dir_path)
        'C:/Windows'
    """

    rel_dir_path = _check_relative_pathname(path_to_file)

    if verbose:
        prt_msg = f'{print_prefix}{state_verb} {_add_slashes(rel_dir_path)}{print_suffix}'
        print(prt_msg, end=print_end, **kwargs)

    if ret_info:
        file_path = pathlib.Path(path_to_file).resolve()
        return file_path, pathlib.Path(rel_dir_path).parent

    return None


def _set_index(data, index_col=None):
    """
    Sets the index of a dataframe using column names or integer positions.

    :param data: The dataframe to update.
    :type data: pandas.DataFrame
    :param index_col: Column name(s) or integer index/indices to set as the index.
        If ``None`` (default), the function sets the first column as the index
        only if its name is an empty string (``''``) or starts with ``'Unnamed:'``.
    :type index_col: str | int | list | None
    :return: The dataframe with the updated index.
    :rtype: pandas.DataFrame

    **Tests**::

        >>> from pyhelpers.store import _set_index
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy as np
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> example_df.equals(_set_index(example_df))
        True
        >>> example_df_1 = _set_index(example_df, index_col=0)
        >>> example_df_1
                    Latitude
        Longitude
        -0.127647  51.507322
        -1.902691  52.479699
        -2.245115  53.479489
        -1.543794  53.797418
        >>> example_df.iloc[:, 0].to_list() == example_df_1.index.to_list()
        True
        >>> example_df_2 = example_df.copy()
        >>> example_df_2.index.name = ''
        >>> example_df_2.reset_index(inplace=True)
        >>> example_df_2 = _set_index(example_df_2, index_col=None)
        >>> np.array_equal(example_df_2.values, example_df.values)
        True
    """

    dat = data.copy()

    if index_col is None:
        # Check if the first column looks like a saved index (empty name or 'Unnamed: 0')
        first_col = dat.columns[0]
        if str(first_col) == '' or str(first_col).startswith('Unnamed:'):
            dat = dat.set_index(first_col)
            dat.index.name = None

    else:
        # Normalize to list (handles scalars and iterables)
        if isinstance(index_col, (str, int)):
            idx_keys_raw = [index_col]
        else:
            idx_keys_raw = list(index_col)

        # Resolve integers and validate existence
        idx_keys = []
        for x in idx_keys_raw:
            # Resolve integer positions to names
            if isinstance(x, int):
                if x >= len(dat.columns):
                    raise IndexError(f"Column index {x} is out of bounds.")
                col_name = dat.columns[x]
            else:
                col_name = x

            # Validate existence
            if col_name not in dat.columns:
                if col_name == dat.index.name:
                    continue  # Already the index, skip
                raise KeyError(f"Column '{col_name}' not found in DataFrame.")

            # Prevent duplication (the fix)
            if col_name not in idx_keys:
                idx_keys.append(col_name)

        # Set the index, only if valid columns are found
        if idx_keys:
            dat = dat.set_index(keys=idx_keys)

    return dat


def _resolve_json_engine(func):
    """
    Decorator to dynamically resolve and inject a JSON engine module.

    This decorator inspects the ``engine`` argument of the decorated function.
    It validates the engine selection, ensures the required dependency is
    available via :func:`~pyhelpers._cache._check_dependencies`, and injects
    the resulting module into the function's keyword arguments as ``json_mod``.

    :param func: The function to be decorated.
    :type func: callable
    :return: A wrapped version of the function with ``json_mod`` injected.
    :rtype: callable

    .. note::

        - Supported engines include: ``'ujson'``, ``'orjson'``, and ``'rapidjson'``.
        - If ``engine=None``, the standard library
          `json <https://docs.python.org/3/library/json.html>`_ module is used.
        - The decorated function must be able to accept ``json_mod`` via its
          ``**kwargs`` or have a specific parameter named ``json_mod``.

    **Example**::

        >>> from pyhelpers.store.utils import _resolve_json_engine

        >>> @_resolve_json_engine
        ... def load_my_json(path, engine=None, **kwargs):
        ...     json_mod = kwargs.pop('json_mod')
        ...     print(f"Using engine: {json_mod.__name__}")

        >>> load_my_json("data.json", engine='ujson')
        Using engine: ujson
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Bind args and kwargs to the function's signature
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)

        # Extract 'engine' from bound arguments or get the default value
        engine = bound_args.arguments.get('engine', sig.parameters['engine'].default)

        # Handle cases where default is inspect.Parameter.empty
        if engine is inspect.Parameter.empty:
            engine = None

        # Resolve the module
        if engine is not None:
            valid_engines = {'ujson', 'orjson', 'rapidjson'}
            if engine not in valid_engines:
                raise ValueError(f"`engine` must be one of {valid_engines}")
            kwargs['json_mod'] = _check_dependencies(engine)
        else:
            kwargs['json_mod'] = sys.modules.get('json') or __import__('json')

        return func(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def suppress_gpkg_warnings():
    # noinspection PyShadowingNames
    """
    A context manager to suppress common GeoPackage (GPKG) and geometric warnings.

    This utility silences recurring "noise" from the GIS stack (GDAL, pyogrio and Fiona) that
    does not impact data integrity but clutters the console. Specifically, it handles:

    1. ``Measured (M) geometry`` warnings: Silences the UserWarning emitted when
       GEOS strips M-coordinates (linear referencing) from 4D geometries.
    2. ``VERBOSE`` driver warnings: Silences the RuntimeWarning emitted when
       the GPKG driver receives a ``'VERBOSE'`` open option it does not support.

    **Examples**::

        >>> from pyhelpers.store.utils import suppress_gpkg_warnings
        >>> import geopandas as gpd
        >>> # Suppose this would normally produce a warning:
        >>> with suppress_gpkg_warnings():  # With warning suppression:
        ...     df = gpd.read_file("data_with_m_coords.gpkg")
        >>> # Outside the context, warnings behave normally

    .. note::

        The suppression only applies to:

        - This uses ``warnings.catch_warnings`` to ensure that warning filters are restored to
          their original state once the context is exited.
        - Only specific messages are filtered; other unrelated ``UserWarnings`` or
          ``RuntimeWarnings`` will still be displayed.
        - Warnings originating from the ``'pyogrio'`` module
    """

    with warnings.catch_warnings():
        # Handle Measured M coordinate stripping
        warnings.filterwarnings(
            action='ignore',
            message=r".*Measured \(M\) geometry types are not supported.*",
            category=UserWarning,
            # module='pyogrio'
        )

        # Handle GDAL/GPKG driver 'VERBOSE' chatter
        warnings.filterwarnings(
            action='ignore',
            message=".*driver GPKG does not support open option VERBOSE.*",
            category=RuntimeWarning,
            # module='pyogrio'
        )

        yield
