"""
Utilities that support the main submodules of :mod:`~pyhelpers.store`.
"""

import contextlib
import functools
import inspect
import logging
import sys
import textwrap
import warnings
from pathlib import Path

from .._cache import _add_slashes, _check_dependencies, _check_relative_pathname, _normalize_pathname


@functools.lru_cache(maxsize=8)
def _get_indent_str(indent=None):
    """
    Returns a standardized indentation string.

    :param indent: Number of spaces (int) or a literal prefix string; defaults to ``None``.
    :type indent: int | str | None
    :return: Indentation string.
    :rtype: str
    """

    # Handle integer input (common case: indent=2, 4, etc.)
    if isinstance(indent, int):
        return " " * max(0, indent)

    # Handle string input or None (common case: indent="\t" or indent=None)
    return str(indent) if indent is not None else ""


def _print_wrapped_string(message, indent=None, base_indent="  ", end=" ... ", wrap_limit=100,
                          **kwargs):
    # noinspection PyShadowingNames
    """
    Prints a message, wrapping it into multiple lines if it exceeds a length threshold.

    This function uses ``textwrap.TextWrapper`` to break long strings (e.g. file paths)
    into multiple lines while maintaining a clear visual hierarchy through indentation
    and continuation markers (``...``).

    :param message: The full string/message to be printed.
    :type message: str
    :param indent: Base indentation level for the first line; can be an integer (number of spaces),
        a literal string, or ``None`` (no indentation); defaults to ``None``.
    :type indent: int | str | None
    :param base_indent: Default indentation prepended from the second line if ``indent`` is a str;
        defaults to ``"  "``.
    :type base_indent: str
    :param end: String to append to the end of the final line; defaults to ``" ... "``.
    :type end: str
    :param wrap_limit: Maximum character width for a single line before wrapping occurs.
        If ``None``, wrapping is disabled; defaults to ``100``.
    :type wrap_limit: int | None
    :param kwargs: Additional keyword arguments passed to the built-in ``print()`` function.
    :return: None
    :rtype: None

    **Examples**::

        >>> from pyhelpers.store.utils import _print_wrapped_string
        >>> message = 'Saving "data.bin" to "C:/Users/Admin/Documents/Projects/Output/"'
        >>> # Example of multi-line wrapping with default settings
        >>> _print_wrapped_string(message, wrap_limit=60)
        Saving "data.bin" ...
          to "C:/Users/Admin/Documents/Projects/Output/" ...
        >>> # Example with integer indentation and custom end
        >>> _print_wrapped_string(message, indent=2, wrap_limit=50); print("Done.")
          Saving "data.bin" ...
            to "C:/Users/Admin/Documents/Projects/Output/" ... Done.
    """

    initial_indent = _get_indent_str(indent)  # The initial indent is for the first line

    if isinstance(indent, int):  # The subsequent indent is for lines 2, 3, ..., N
        subsequent_indent = _get_indent_str(indent + 2)
    else:  # If indent is a string or None, prepend the base_indent
        subsequent_indent = base_indent + initial_indent

    # Check if wrapping is necessary
    if not wrap_limit or (len(initial_indent) + len(message)) <= wrap_limit:
        print(f"{initial_indent}{message}", end=end, **kwargs)
        return

    line1_content, line2_content = None, None
    msg = message.lstrip()
    for prep in [" in ", " on ", " at ", " for ", " with ", " by ", " to ", " from ", " into "]:
        if prep in msg:
            parts = msg.split(prep, 1)
            line1_content = parts[0]
            line2_content = f"{prep.lstrip()}{parts[1]}"
            break

    if line1_content and line2_content:
        print(f"{initial_indent}{line1_content} ...", **kwargs)

        wrapper = textwrap.TextWrapper(
            width=wrap_limit,
            initial_indent=subsequent_indent,
            subsequent_indent=subsequent_indent,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False
        )

        path_lines = wrapper.wrap(line2_content)

        for i, line in enumerate(path_lines):
            print(line, end=end if i == len(path_lines) - 1 else " ...\n", **kwargs)

    else:
        wrapper = textwrap.TextWrapper(
            width=wrap_limit,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_long_words=False
        )
        lines = wrapper.wrap(message)
        for i, line in enumerate(lines):
            print(line, end=end if i == len(lines) - 1 else " ...\n", **kwargs)


def _check_saving_path(path, verbose=False, msg_prefix="", state_verb="Saving", state_prep="to",
                       msg_suffix="", end=" ... ", skip_updating_state=False, indent=None,
                       msg_wrap_limit=None, return_info=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Verifies a file path before saving, creates directories, and manages console output.

    :param path: Destination file path.
    :type path: str | pathlib.Path | os.PathLike
    :param verbose: Whether to print relevant information to the console;
        ``2`` enables CWD boundary warnings; defaults to ``False``.
    :type verbose: bool | int
    :param msg_prefix: Text prefixed to the default print message; defaults to ``""``.
    :type msg_prefix: str
    :param state_verb: Verb indicating the action being performed, e.g. *saving* or *updating*;
        defaults to ``"Saving"``.
    :type state_verb: str
    :param state_prep: Preposition associated with ``state_verb``; defaults to ``"to"``.
    :type state_prep: str
    :param msg_suffix: Text suffixed to the default print message; defaults to ``""``.
    :type msg_suffix: str
    :param end: String passed to the ``end`` parameter of ``print``; defaults to ``" ... "``.
    :type end: str
    :param skip_updating_state: If ``True``, ``state_verb`` does not flip to ``"Updating"``;
        defaults to ``False``.
    :type skip_updating_state: bool
    :param indent: Indentation level; defaults to ``None``.
    :type indent: int | str | None
    :param msg_wrap_limit: Threshold for multi-line wrapping;
        If the string exceeds this value (e.g. ``100``), it will be split at (before)
        ``state_prep`` to improve readability when being printed.
        If ``None`` (default), the printed string is in a single line.
    :type msg_wrap_limit: int | None
    :param return_info: Whether to return file path information; defaults to ``False``.
    :type return_info: bool
    :return: A tuple containing the absolute path, the relative directory path, and the extension.
    :rtype: tuple

    **Tests**::

        >>> from pyhelpers.store import _check_saving_path
        >>> from pyhelpers.dirs import cd
        >>> path = cd()
        >>> _check_saving_path(path, verbose=True)
        Traceback (most recent call last):
          ...
            raise ValueError(f"The input '{path}' appears to be a directory, not a file path.")
        ValueError: The input '<path>' appears to be a directory, not a file path.
        >>> path = "pyhelpers.txt"
        >>> _check_saving_path(path, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" ... Passed.
        >>> path = cd("tests", "documents", "pyhelpers.txt")
        >>> _check_saving_path(path, verbose=True); print("Passed.")
        Saving "pyhelpers.txt" to "./tests/documents/" ... Passed.
        >>> _check_saving_path(path, verbose=True, msg_wrap_limit=40); print("Passed.")
        Saving "pyhelpers.txt" ...
          to "./tests/documents/" ... Passed.
        >>> path = "C:\\Windows\\pyhelpers.txt"
        >>> _check_saving_path(path, verbose=2); print("Passed.")
        Saving "pyhelpers.txt" to "C:/Windows/" ... Passed.
          Warning: "C:/Windows/pyhelpers.txt" is outside the current working directory.
        >>> path = "C:\\pyhelpers.txt"
        >>> _check_saving_path(path, verbose=2); print("Passed.")
        Saving "pyhelpers.txt" to "C:/" ... Passed.
          Warning: "C:/pyhelpers.txt" is outside the current working directory.
        >>> _check_saving_path(path, verbose=2, indent=4, msg_wrap_limit=30); print("Passed.")
            Saving "pyhelpers.txt" to "C:/" ... Passed.
              Warning: "C:/pyhelpers.txt" is outside the current working directory.
    """

    file_path = Path(path).resolve()

    if file_path.is_dir():  # Guard against directory-only paths
        raise ValueError(f'The input "{path}" appears to be a directory, not a file path.')

    # Determine display path (relative vs absolute)
    try:
        # Attempt to get path relative to current working directory
        rel_dir = file_path.parent.relative_to(Path.cwd())
    except ValueError:  # If outside CWD (common on Linux mounts or different Windows drives)
        rel_dir = file_path.parent

    # Ensure the parent directory exists before proceeding
    rel_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        filename = file_path.name if file_path.suffix else ""

        # Flip verb to 'Updating' if file exists, unless 'skip_updating_state' is flagged
        if file_path.is_file() and not skip_updating_state:
            state_verb, state_prep = "Updating", "in"

        # Build message
        indent_str = _get_indent_str(indent)
        base_msg = f'{indent_str}{msg_prefix}{state_verb} "{filename}"'

        if rel_dir == Path('.') or rel_dir == Path(''):
            msg = f'{base_msg}{msg_suffix}'
        else:
            msg = f'{base_msg} {state_prep} {_add_slashes(rel_dir)}{msg_suffix}'

        # Print message
        kwargs['flush'] = True
        if msg_wrap_limit and len(msg) > msg_wrap_limit:
            _print_wrapped_string(
                message=msg, indent=indent, end=end, wrap_limit=msg_wrap_limit, **kwargs)
        else:
            print(msg, end=end, **kwargs)

        if verbose == 2:
            logging.getLogger(__name__).warning(
                f'  {indent_str}Warning: "{_normalize_pathname(file_path)}" '
                f'is outside the current working directory.')

    if return_info:
        file_ext = "".join(file_path.suffixes).lower()
        # Returns (absolute path, relative dir, file extension)
        return file_path, rel_dir, file_ext

    return None


def _autofit_column_width(excel_writer, writer_kwargs, sheet_name):
    """
    Adjusts the column widths in an Excel spreadsheet based on the content length.

    This function is specifically designed for *openpyxl* engine when working with *Pandas*
    `ExcelWriter`_. It iterates through each column of the specified sheet and calculates
    the maximum length of the content. It then adjusts the column width to accommodate the
    longest content plus some padding.

    :param excel_writer: ``pandas.ExcelWriter`` object used to write data into Excel file.
    :type excel_writer: pandas.ExcelWriter
    :param writer_kwargs: A dict of keyword arguments passed to the `pandas.ExcelWriter`_,
        including the ``'engine'``.
    :type writer_kwargs: dict
    :param sheet_name: The name of the sheet to adjust.
    :type sheet_name: str

    .. _ExcelWriter:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html

    .. note::

        - This function assumes that *openpyxl* engine is used
          (i.e. ``writer_kwargs['engine'] == 'openpyxl'``).
        - It modifies the column dimensions directly in the ``pandas.ExcelWriter`` object.

    .. seealso::

        - For more information on *openpyxl*, refer to the official documentation:
          https://openpyxl.readthedocs.io/en/stable/
        - Reference: [`STORE-U-ACW-1 <https://stackoverflow.com/questions/39529662/>`_]
    """

    kwargs = writer_kwargs or {}
    engine = kwargs.get('engine')

    if engine == 'openpyxl' and sheet_name in excel_writer.sheets:
        ws = excel_writer.sheets[sheet_name]

        for column in ws.columns:
            # column[0] is the header cell
            column_letter = column[0].column_letter

            # Use a list comprehension to get lengths of all lines in all cells
            max_length = 0
            for cell in column:
                if cell.value is not None:
                    # Handle multiline text by taking the longest line
                    lines = str(cell.value).split('\n')
                    current_max = max(len(line) for line in lines)
                    if current_max > max_length:
                        max_length = current_max

            # If the column is empty, max_length stays 0; use a minimum floor
            adjusted_width = (max_length + 2) * 1.05
            ws.column_dimensions[column_letter].width = max(adjusted_width, 8.0)


def _check_loading_path(path, verbose=False, msg_prefix="", state_verb="Loading", msg_suffix="",
                        end=" ... ", indent=None, return_info=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Verifies a file path for loading and prints status to the console.

    :param path_to_file: Path to the target file.
    :type path_to_file: str | bytes | pathlib.Path
    :param verbose: Whether to print status; defaults to ``False``.
    :type verbose: bool | int
    :param msg_prefix: Text prepended to the message; defaults to ``""``.
    :type msg_prefix: str
    :param state_verb: Action verb; defaults to ``"Loading"``.
    :type state_verb: str
    :param msg_suffix: Text appended to the message; defaults to ``""``.
    :type msg_suffix: str
    :param end: Print end character; defaults to ``" ... "``.
    :type end: str
    :param indent: Indentation level; defaults to ``None``.
    :type indent: int | str | None
    :param return_info: If ``True``, returns path metadata; defaults to ``False``.
    :type return_info: bool
    :return: (Absolute path, Parent directory, Extension) if ``return_info`` else ``None``.
    :rtype: tuple | None

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers._cache import _check_relative_pathname
        >>> from pyhelpers.dirs import cd
        >>> from pathlib import Path
        >>> path_to_file = cd("test_func.py")
        >>> _check_loading_path(path, verbose=True); print("Passed.")
        Loading "./test_func.py" ... Passed.
        >>> file_path, rel_dir, file_ext = _check_loading_path(path, return_info=True)
        >>> _check_relative_pathname(file_path)
        'test_func.py'
        >>> _check_relative_pathname(rel_dir)
        '.'
        >>> file_ext
        '.py'
        >>> path_to_file = Path("C:\\Windows\\pyhelpers.pkg")
        >>> _check_loading_path(path, verbose=True); print("Passed.")
        Loading "C:/Windows/pyhelpers.pkg" ... Passed.
        >>> file_path, rel_dir, file_ext = _check_loading_path(path, return_info=True)
        >>> _check_relative_pathname(file_path)
        'C:/Windows/pyhelpers.pkg'
        >>> _check_relative_pathname(rel_dir)
        'C:/Windows'
        >>> file_ext
        '.pkg'
    """

    rel_dir = _check_relative_pathname(path)

    if verbose:
        indent_str = _get_indent_str(indent)
        prt_msg = f'{indent_str}{msg_prefix}{state_verb} {_add_slashes(rel_dir)}{msg_suffix}'

        print(prt_msg, end=end, **kwargs)

    if return_info:
        file_path = Path(path).resolve()
        file_ext = "".join(file_path.suffixes).lower()
        return file_path, Path(rel_dir).parent, file_ext

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


def _is_parquet_geospatial(path, pq_module):
    """
    Detects if a file is GeoParquet via metadata or extension.
    """

    try:
        parquet_meta = pq_module.read_metadata(path)
        return bool(parquet_meta.metadata and b'geo' in parquet_meta.metadata)
    except Exception:  # noqa
        file_ext = "".join(Path(path).suffixes).lower()
        return bool(file_ext == ".geoparquet")


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
