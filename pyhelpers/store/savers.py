"""
Utilities for saving data in various formats.
"""

import bz2
import copy
import functools
import gzip
import logging
import lzma
import pathlib
import pickle  # nosec
import subprocess  # nosec

import pandas as pd

from .utils import _autofit_column_width, _check_saving_path, _resolve_json_engine
from .._cache import _check_file_pathname, _lazy_check_dependencies, \
    _print_failure_message
from ..ops.general import is_visual_object
from ..ops.web import is_url


def save_pickle(data, path_to_file, verbose=False, print_kwargs=None, raise_error=False, **kwargs):
    """
    Saves data to a `pickle <https://docs.python.org/3/library/pickle.html>`_ file.

    :param data: Data to be saved, compatible with the built-in `pickle.dump()`_ function.
    :type data: typing.Any
    :param path_to_file: Path where the `Pickle`_ file will be saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `pickle.dump()`_.

    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`pickle.dump()`: https://docs.python.org/3/library/pickle.html#pickle.dump

    **Examples**::

        >>> from pyhelpers.store import save_pickle
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> pickle_dat = 1
        >>> pickle_pathname = cd("tests", "data", "dat.pickle")
        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Saving "dat.pickle" to "./tests/data/" ... Done.
        >>> # Get an example dataframe
        >>> pickle_dat = example_dataframe()
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Updating "dat.pickle" in "./tests/data/" ... Done.

    .. tip::

        - The file path is validated before saving. Ensure the directory exists and is writable.
        - Supported compression formats: ``.gz`` (gzip), ``.xz`` (LZMA compression) and
          ``.bz2`` (bzip2).
        - Other extensions are saved as uncompressed files.
        - Compression format is determined by the file extension. Ensure the extension matches
          the desired format.

    .. seealso::

        - Examples for the function :func:`~pyhelpers.store.load_pickle`.
    """

    file_path, _, ext = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    try:
        if ext.endswith((".pkl.gz", ".pickle.gz")):
            with gzip.open(file_path, mode='wb') as f:
                pickle.dump(data, f, **kwargs)  # noqa
        elif ext.endswith((".pkl.xz", ".pkl.lzma", ".pickle.xz", ".pickle.lzma")):
            with lzma.open(file_path, mode='wb') as f:
                pickle.dump(data, f, **kwargs)  # noqa
        elif ext.endswith((".pkl.bz2", ".pickle.bz2")):
            with bz2.BZ2File(file_path, mode='wb') as f:
                pickle.dump(data, f, **kwargs)  # noqa
        else:
            with open(file_path, mode='wb') as f:
                pickle.dump(data, f, **kwargs)  # noqa

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies('openpyxl', 'odf')
def save_spreadsheet(data, path_to_file, sheet_name="Sheet1", index=False, engine=None,
                     delimiter=',', autofit_column_width=True, writer_kwargs=None,
                     verbose=False, print_kwargs=None, raise_error=False, **kwargs):
    """
    Saves data to a spreadsheet file format
    (e.g. `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_,
    `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`_ or
    `OpenDocument <https://en.wikipedia.org/wiki/OpenDocument>`_).

    The file format is determined by the extension of ``path_to_file``, which can be
    ``".txt"``, ``".csv"``, ``".xlsx"`` or ``".xls"``. The saving engine may use `xlsxwriter`_,
    `openpyxl`_ or `odfpy`_.

    :param data: Data to be saved as a spreadsheet.
    :type data: pandas.DataFrame
    :param path_to_file: File path where the spreadsheet will be saved.
    :type path_to_file: str | os.PathLike[str] | None
    :param sheet_name: Name of the sheet where the data will be saved; defaults to ``"Sheet1"``.
    :type sheet_name: str
    :param index: Whether to include the dataframe index as a column; defaults to ``False``.
    :type index: bool
    :param engine: Engine to use for saving:

        - ``'openpyxl'`` or ``'xlsxwriter'`` for `Microsoft Excel`_ formats such as
          ``.xlsx`` or ``.xls``.
        - ``'odf'`` for `OpenDocument`_ format ``.ods``.

    :type engine: str | None
    :param delimiter: Separator for ``".csv"``, ``".txt"`` or ``".odt"`` file formats;
        defaults to ``','``.
    :type delimiter: str
    :param autofit_column_width: Whether to autofit column width; defaults to ``True``.
    :type autofit_column_width: bool
    :param writer_kwargs: [Optional] Additional parameters for the class `pandas.ExcelWriter()`_.
    :type writer_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_excel()`_
        or `pandas.DataFrame.to_csv()`_.

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`OpenDocument`: https://en.wikipedia.org/wiki/OpenDocument
    .. _`xlsxwriter`: https://pypi.org/project/XlsxWriter/
    .. _`openpyxl`: https://pypi.org/project/openpyxl/
    .. _`odfpy`: https://pypi.org/project/odfpy/
    .. _`pandas.ExcelWriter()`:
        https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    .. _`pandas.DataFrame.to_excel()`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
    .. _`pandas.DataFrame.to_csv()`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

    **Examples**::

        >>> from pyhelpers.store import save_spreadsheet
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> # Get an example dataframe
        >>> spreadsheet_dat = example_dataframe()
        >>> spreadsheet_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> spreadsheet_pathname = cd("tests", "data", "dat.csv")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.csv" to "./tests/data/" ... Done.
        >>> spreadsheet_pathname = cd("tests", "data", "dat.xlsx")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "./tests/data/" ... Done.
        >>> spreadsheet_pathname = cd("tests", "data", "dat.ods")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.ods" to "./tests/data/" ... Done.
    """

    file_path, _, ext = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    valid_extensions = {".txt", ".csv", ".xlsx", ".xls", ".ods", ".odt"}
    if raise_error:
        assert ext in valid_extensions, f"File extension must be one of {valid_extensions}."

    try:
        if ext.endswith((".csv", ".txt", ".odt")):  # Handle CSV/Text formats
            csv_kwargs = {
                'path_or_buf': file_path,
                'sep': delimiter,
                'index': index,
                **kwargs  # User overrides defaults
            }
            data.to_csv(**csv_kwargs)

        else:  # Handle Excel/Spreadsheet formats
            # Determine the engine based on extension
            if ext.endswith((".xls", ".xlsx")):
                engine_ = 'openpyxl'
            elif ext == ".ods":
                engine_ = 'odf'
            else:
                engine_ = engine

            # Prepare Writer arguments
            writer_base = writer_kwargs or {}
            final_writer_kwargs = {
                'path': file_path,
                'engine': engine_,
                **writer_base
            }

            with pd.ExcelWriter(**final_writer_kwargs) as writer:
                excel_kwargs = {
                    'excel_writer': writer,
                    'index': index,
                    'sheet_name': sheet_name,
                    **kwargs
                }
                data.to_excel(**excel_kwargs)

                if autofit_column_width:
                    # Pass the final dictionaries to avoid re-calculation
                    _autofit_column_width(
                        excel_writer=writer, writer_kwargs=final_writer_kwargs,
                        sheet_name=sheet_name)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def _save_spreadsheets(data, sheet_names, cur_sheet_names, excel_writer, if_sheet_exists,
                       autofit_column_width=True, writer_kwargs=None, verbose=False, indent=None,
                       raise_error=True, **kwargs):
    """
    Helper function to iterate through the list of DataFrames and save each one to a sheet
    in the provided ExcelWriter object, handling existing sheets, autofitting and error suppression.

    :param data: Sequence of pandas DataFrames to be saved.
    :type data: list[pandas.DataFrame]
    :param sheet_names: Names corresponding to the DataFrames in ``data``.
    :type sheet_names: list[str]
    :param cur_sheet_names: List of sheet names currently existing in the workbook
        (used for ``'a'`` mode).
    :type cur_sheet_names: list[str]
    :param excel_writer: The pandas.ExcelWriter object used for writing to the file.
    :type excel_writer: pandas.ExcelWriter
    :param if_sheet_exists: Behavior when writing to an existing sheet (None for prompt).
    :type if_sheet_exists: None | str
    :param autofit_column_width: Whether to autofit column width after saving the sheet.
    :type autofit_column_width: bool
    :param writer_kwargs: Arguments originally passed to pandas.ExcelWriter
        (needed for autofit helper).
    :type writer_kwargs: dict | None
    :param verbose: Whether to print progress messages.
    :type verbose: bool | int
    :param indent: Base indentation level; if an integer, represents spaces.
        Sub-messages are automatically indented further.
    :type indent: int | str | None
    :param raise_error: Whether to raise an error if sheet writing fails.
    :type raise_error: bool
    :param kwargs: Additional arguments for ``pandas.DataFrame.to_excel()``
        (e.g. ``index``, ``header``, ``startrow``).
    :return: None
    :rtype: None

    .. note::

        If ``autofit_column_width=True``, the function ensures the sheet is
        processed post-save. If ``if_sheet_exists='new'``, the autofit targets
        the newly generated unique sheet name.
    """

    # Resolve indentation hierarchy for printing
    base_indent = " " * indent if isinstance(indent, int) else (indent or "")
    sheet_indent = f"  {base_indent}"  # Level 1: Primary task detail
    detail_indent = f"  {sheet_indent}"  # Level 2: Footnotes/renaming info

    # Ensure a mutable list of current sheet names to update if 'new' is used
    cur_sheet_names_list = list(cur_sheet_names)
    writer_kwargs_ = writer_kwargs or {}

    for sheet_data, sheet_name in zip(data, sheet_names):
        # Reset to the default behavior for the current sheet to be processed:
        # This is the behavior set by the ExcelWriter instantiation in the caller.
        excel_writer._if_sheet_exists = if_sheet_exists or 'error'

        if verbose:
            print(f"{sheet_indent}'{sheet_name}'", end=" ... ")

        if sheet_name in cur_sheet_names_list:
            if if_sheet_exists is None:  # Use a local variable for the user choice
                user_choice = input("This sheet already exists; [pass]|new|replace: ")
            else:  # Use a local variable for the chosen action
                valid_options = {'error', 'new', 'replace', 'overlay', 'pass'}
                if if_sheet_exists not in {'error', 'new', 'replace', 'overlay', 'pass'}:
                    raise ValueError(f"`if_sheet_exists` must be one of {valid_options}.")
                user_choice = copy.copy(if_sheet_exists)

            if user_choice != 'pass':  # Set the writer's internal state for pandas to use
                excel_writer._if_sheet_exists = user_choice
            else:
                if verbose:
                    print("Skipped.")
                continue  # Skip this sheet entirely

        try:
            common_args = {'excel_writer': excel_writer, 'sheet_name': sheet_name}
            sheet_data.to_excel(**(kwargs | common_args))

            # Check the state of the writer after to_excel to see if a new sheet was created
            if excel_writer._if_sheet_exists == 'new':
                # actual_sheet_name = [
                #     x for x in excel_writer.sheets if x not in cur_sheet_names_list][0]
                actual_sheet_name = list(excel_writer.sheets.keys())[-1]
                prefix = f"{detail_indent}" if if_sheet_exists is None else ""
                add_msg = f"{prefix}saved as '{actual_sheet_name}' ... Done."
                # Update the list of existing sheets
                cur_sheet_names_list = list(excel_writer.sheets.keys())
            else:
                actual_sheet_name = sheet_name
                add_msg = "Done."

            if autofit_column_width:
                _autofit_column_width(
                    excel_writer=excel_writer, writer_kwargs=writer_kwargs_,
                    sheet_name=actual_sheet_name)

            if verbose:
                print(add_msg)

        except Exception as e:
            _print_failure_message(
                e=e, prefix=f'{sheet_indent}Failed. Sheet name "{sheet_name}":', verbose=verbose,
                raise_error=raise_error)

    return None


def save_spreadsheets(data, path_to_file, sheet_names, mode='w', if_sheet_exists=None,
                      autofit_column_width=True, writer_kwargs=None, verbose=False,
                      print_kwargs=None, raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Saves multiple dataframes to a multi-sheet `Microsoft Excel`_ (.xlsx, .xls) or
    `OpenDocument`_ (.ods) format file.

    The function wraps ``pandas.ExcelWriter`` and ``pandas.DataFrame.to_excel``, adding features
    like error suppression, progress output, column autofit and interactive handling
    of existing sheets in append mode.

    :param data: Sequence of pandas DataFrames to be saved as sheets in the workbook.
    :type data: list[pandas.DataFrame] | tuple[pandas.DataFrame] | iterable[pandas.DataFrame]
    :param path_to_file: File path where the spreadsheet will be saved. Must end with
        ``.xlsx``, ``.xls`` or ``.ods``.
    :type path_to_file: str | os.PathLike
    :param sheet_names: Names of all sheets in the workbook. Must match the length of `data`.
    :type sheet_names: list[str] | tuple[str] | iterable[str]
    :param mode: Mode for writing to the spreadsheet file:

        - ``'w'`` (default): Write mode. Creates a new file or overwrites existing.
        - ``'a'``: Append mode. Adds sheets to an existing file. **Note:** Not supported for
          OpenDocument (``.ods``) files; a write operation will be performed instead.

    :type mode: str
    :param if_sheet_exists: Behavior when trying to write a sheet that already exists:

        - ``None`` (default): Prompts the user for action: ``[pass]|new|replace``.
        - ``'error'``: Raises a ValueError (pandas default).
        - ``'new'``: Creates a new sheet with an incremented name (e.g. 'Sheet11').
        - ``'replace'``: Overwrites the existing sheet.
        - ``'overlay'``: Writes data on top of existing data (only available with ``openpyxl``).
        - ``'pass'``: Skips saving the sheet.

    :type if_sheet_exists: None | str
    :param autofit_column_width: Whether to adjust column width to fit content automatically;
        defaults to ``True``. Requires the ``openpyxl`` or ``odfpy`` engine.
    :type autofit_column_width: bool
    :param writer_kwargs: [Optional] Additional parameters for the class `pandas.ExcelWriter()`_,
        such as `date_format` or `datetime_format`; defaults to ``None``.
    :type writer_kwargs: dict | None
    :param verbose: Whether to print relevant information and sheet saving progress to the console;
        defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the exception if saving a specific sheet fails;
        if ``raise_error=False`` (default), the error will be suppressed, and the process
        will continue with the next sheet.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_excel()`_,
        e.g. ``index=False``, ``header=True``.

    :return: ``None``. The function's main effect is the side effect of saving the file.
    :rtype: None

    :raises AssertionError: If `path_to_file` does not end with a supported file extension
        (``.xlsx``, ``.xls``, ``.ods``).
    :raises ValueError: If an invalid option is provided for ``if_sheet_exists`` when not ``None``.
    :raises Exception: Any exception raised during saving if ``raise_error=True``.

    .. _`Microsoft Excel`:
        https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`OpenDocument`:
        https://en.wikipedia.org/wiki/OpenDocument
    .. _`pandas.ExcelWriter()`:
        https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    .. _`pandas.DataFrame.to_excel()`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html

    **Examples**::

        >>> from pyhelpers.store import save_spreadsheets
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> data1 = example_dataframe()  # Get an example dataframe
        >>> data1
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> data2 = data1.T
        >>> data2
        City          London  Birmingham  Manchester      Leeds
        Longitude  -0.127647   -1.902691   -2.245115  -1.543794
        Latitude   51.507322   52.479699   53.479489  53.797418
        >>> data = [data1, data2]
        >>> sheet_names = ['TestSheet1', 'TestSheet2']
        >>> # Save to ODS format (write mode)
        >>> path_to_file = cd("tests", "data", "dat.ods")
        >>> save_spreadsheets(
        ...     data, path_to_file=path_to_file, sheet_names=sheet_names, verbose=True)
        Saving "dat.ods" to "./tests/data/" ...
          'TestSheet1' ... Done.
          'TestSheet2' ... Done.
        >>> # Save to XLSX format (append mode with interactive prompt)
        >>> path_to_file = cd("tests", "data", "dat.xlsx")
        >>> save_spreadsheets(
        ...     data, path_to_file=path_to_file, sheet_names=sheet_names, verbose=True)
        Saving "dat.xlsx" to "./tests/data/" ...
          'TestSheet1' ... Done.
          'TestSheet2' ... Done.
        >>> save_spreadsheets(
        ...     data, path_to_file=path_to_file, sheet_names=sheet_names, mode='a', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
          'TestSheet1' ... This sheet already exists; [pass]|new|replace: new
            saved as 'TestSheet11' ... Done.
          'TestSheet2' ... This sheet already exists; [pass]|new|replace: new
            saved as 'TestSheet21' ... Done.
        >>> # Save with automatic replacement
        >>> save_spreadsheets(
        ...     data, path_to_file=path_to_file, sheet_names=sheet_names, mode='a',
        ...     if_sheet_exists='replace', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
          'TestSheet1' ... Done.
          'TestSheet2' ... Done.
        >>> save_spreadsheets(
        ...     data, path_to_file=path_to_file, sheet_names=sheet_names, mode='a',
        ...     if_sheet_exists='new', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
          'TestSheet1' ... saved as 'TestSheet12' ... Done.
          'TestSheet2' ... saved as 'TestSheet22' ... Done.
    """

    file_path = pathlib.Path(path_to_file).resolve()

    supported_ext_set = {".xlsx", ".xls", ".ods"}
    if file_path.suffix not in supported_ext_set:
        raise ValueError(
            f"Unsupported file format '{file_path.suffix}'. Must be one of {supported_ext_set}")

    _check_saving_path(file_path, verbose=verbose, **(print_kwargs or {}))

    if file_path.is_file() and mode == 'a':
        with pd.ExcelFile(file_path) as f:
            cur_sheet_names = f.sheet_names
    else:
        cur_sheet_names = []
        if mode == 'a':
            pd.DataFrame().to_excel(file_path, sheet_name=sheet_names[0])

    engine = 'openpyxl' if str(path_to_file).endswith((".xlsx", ".xls")) else 'odf'

    write_args = writer_kwargs or {}
    write_args.update(
        {'path': path_to_file, 'engine': engine, 'mode': mode, 'if_sheet_exists': if_sheet_exists})

    with pd.ExcelWriter(**write_args) as writer:
        if verbose:
            print("")
        _save_spreadsheets(
            data=data, sheet_names=sheet_names, cur_sheet_names=cur_sheet_names,
            excel_writer=writer, if_sheet_exists=if_sheet_exists,
            autofit_column_width=autofit_column_width, writer_kwargs=write_args,
            verbose=verbose, raise_error=raise_error,
            **kwargs
        )


@_resolve_json_engine
def save_json(data, path_to_file, engine=None, verbose=False, print_kwargs=None, raise_error=False,
              **kwargs):
    """
    Saves data to a `JSON <https://www.json.org/json-en.html>`_ file.

    :param data: Data to be serialized and
        saved as a `JSON <https://www.json.org/json-en.html>`_ file.
    :type data: typing.Any
    :param path_to_file: File path
        where the `JSON <https://www.json.org/json-en.html>`_ file will be saved.
    :type path_to_file: str | os.PathLike
    :param engine: Serialisation engine:

        - ``None`` (default): Use the built-in
          `json module <https://docs.python.org/3/library/json.html>`_.
        - ``'ujson'``: Use `UltraJSON`_ for faster serialization.
        - ``'orjson'``: Use `orjson`_ for faster and more efficient serialization.
        - ``'rapidjson'``: Use `python-rapidjson`_ for fast and efficient serialization.

    :type engine: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for one of the following functions:

        - `json.dump()`_ (if ``engine=None``)
        - `orjson.dumps()`_ (if ``engine='orjson'``)
        - `ujson.dump()`_ (if ``engine='ujson'``)
        - `rapidjson.dump()`_ (if ``engine='rapidjson'``)

    .. _`UltraJSON`: https://pypi.org/project/ujson/
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`json.dump()`: https://docs.python.org/3/library/json.html#json.dump
    .. _`orjson.dumps()`: https://github.com/ijl/orjson#serialize
    .. _`ujson.dump()`: https://github.com/ultrajson/ultrajson#encoder-options
    .. _`rapidjson.dump()`: https://python-rapidjson.readthedocs.io/en/latest/dump.html

    **Examples**::

        >>> from pyhelpers.store import save_json
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import json
        >>> json_pathname = cd("tests", "data", "dat.json")
        >>> json_dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Saving "dat.json" to "./tests/data/" ... Done.
        >>> # Get an example dataframe
        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> # Convert the dataframe to JSON format
        >>> json_dat = json.loads(example_df.to_json(orient='index'))
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}
        >>> # Use built-in json module
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Updating "dat.json" in "./tests/data/" ... Done.
        >>> save_json(json_dat, json_pathname, engine='orjson', verbose=True)
        Updating "dat.json" in "./tests/data/" ... Done.
        >>> save_json(json_dat, json_pathname, engine='ujson', indent=4, verbose=True)
        Updating "dat.json" in "./tests/data/" ... Done.
        >>> save_json(json_dat, json_pathname, engine='rapidjson', indent=4, verbose=True)
        Updating "dat.json" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`~pyhelpers.store.load_json`.
    """

    json_mod = kwargs.pop('json_mod')

    _check_saving_path(path_to_file, verbose=verbose, **(print_kwargs or {}))

    try:
        if engine == 'orjson':
            with open(path_to_file, mode='wb') as f:
                f.write(json_mod.dumps(data, **kwargs))
        else:
            with open(path_to_file, mode='w') as f:
                json_mod.dump(data, f, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies('joblib')
def save_joblib(data, path_to_file, verbose=False, print_kwargs=None, raise_error=False, **kwargs):
    """
    Saves data to a `Joblib <https://pypi.org/project/joblib/>`_ file.

    :param data: The data to be serialized and saved using `joblib.dump()`_.
    :type data: typing.Any
    :param path_to_file: The file path where the Joblib file will be saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the `joblib.dump()`_ function.

    .. _`joblib.dump()`: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html

    **Examples**::

        >>> from pyhelpers.store import save_joblib
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> joblib_pathname = cd("tests", "data", "dat.joblib")
        >>> # Example 1:
        >>> joblib_dat = example_dataframe().to_numpy()
        >>> joblib_dat
        array([[-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])
        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Saving "dat.joblib" to "./tests/data/" ... Done.
        >>> # Example 2:
        >>> import numpy as np
        >>> from sklearn.linear_model import LinearRegression
        >>> np.random.seed(0)
        >>> x = example_dataframe().to_numpy()
        >>> y = np.random.rand(*x.shape)
        >>> reg = LinearRegression().fit(x, y)
        >>> reg
        LinearRegression()
        >>> save_joblib(reg, joblib_pathname, verbose=True)
        Updating "dat.joblib" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_joblib`.
    """

    file_path, _, _ = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    try:
        joblib.dump(data, file_path, **kwargs)  # noqa

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_feather(data, path_to_file, index=True, verbose=False, print_kwargs=None,
                 raise_error=False, **kwargs):
    """
    Saves a dataframe to a `Feather <https://arrow.apache.org/docs/python/feather.html>`_ file.

    .. note::

        The Feather format may require the index to be the default integer index.
        If the index is not a standard range, or if ``index=True``, it will be
        automatically reset and saved as a column.

    :param data: The dataframe to be saved.
    :type data: pandas.DataFrame
    :param path_to_file: The path where the Feather file will be saved.
    :type path_to_file: str | pathlib.Path
    :param index: Whether to include the index as a column.
        If ``None``, the index is included only if it is not the default range;
        defaults to ``True``.
    :type index: bool | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise an exception if saving fails; defaults to ``False``.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `pandas.DataFrame.to_feather()`_.

    .. _`pandas.DataFrame.to_feather()`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_feather.html

    **Examples**::

        >>> from pyhelpers.store import save_feather
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> feather_dat = example_dataframe()  # Get an example dataframe
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> feather_pathname = cd("tests/data", "dat.feather")
        >>> save_feather(feather_dat, feather_pathname, verbose=True)
        Saving "dat.feather" to "./tests/data/" ... Done.
        >>> save_feather(feather_dat, feather_pathname, index=True, verbose=True)
        Updating "dat.feather" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_feather`.
    """

    file_path, _, _ = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    try:
        # Check if index is the default integer range [0, 1, ..., n-1]
        is_default_index = (list(data.index) == list(range(len(data))) and data.index.name is None)

        # Decide whether to reset (keep as column), drop, or leave as is
        if index is True or (index is None and not is_default_index):
            data.reset_index().to_feather(file_path, **kwargs)
        elif index is False and not is_default_index:
            # Discard the non-default index
            data.reset_index(drop=True).to_feather(file_path, **kwargs)
        else:
            data.to_feather(file_path, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies(pa='pyarrow', pq='pyarrow_parquet')
def save_parquet(data, path_to_file, engine=None, verbose=False, print_kwargs=None,
                 raise_error=False, **kwargs):
    """
    Saves a dataframe to a `Parquet <https://arrow.apache.org/docs/python/parquet.html>`_ file.

    This function supports saving via Pandas/GeoPandas (default) or directly using the
    PyArrow engine.

    :param data: The dataframe to be saved.
    :type data: pandas.DataFrame | geopandas.GeoDataFrame | pyarrow.Table
    :param path_to_file: The destination path for the Parquet file.
    :type path_to_file: str | os.PathLike
    :param engine: Parquet library to use; options are ``None``, ``'auto'``,
        ``'pyarrow'`` or ``'fastparquet'``; when ``engine=None``, it defaults to ``'auto'``
        if ``data`` is ``pandas.DataFrame``.
    :type engine: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to re-raise exceptions encountered during saving;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `pandas.DataFrame.to_parquet()`_,
        `geopandas.GeoDataFrame.to_parquet()`_ or `pyarrow.parquet.write_table()`_.

    .. _`pandas.DataFrame.to_parquet()`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html
    .. _`geopandas.GeoDataFrame.to_parquet()`:
        https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_parquet.html
    .. _`pyarrow.parquet.write_table()`:
        https://arrow.apache.org/docs/python/generated/pyarrow.parquet.write_table.html

    **Examples**::

        >>> from pyhelpers.store import save_parquet
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import pyarrow as pa
        >>> parquet_dat = example_dataframe()  # Get an example dataframe
        >>> parquet_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> parquet_pathname = cd("tests/data", "dat.parquet")
        >>> save_parquet(parquet_dat, parquet_pathname, verbose=True)
        Saving "dat.parquet" to "./tests/data/" ... Done.
        >>> # Save using an explicit engine (e.g. 'pyarrow')
        >>> save_parquet(parquet_dat, parquet_pathname, engine='pyarrow', verbose=True)
        Updating "dat.parquet" in "./tests/data/" ... Done.
        >>> # Save a PyArrow Table directly
        >>> parquet_tbl = pa.Table.from_pandas(parquet_dat)
        >>> parquet_tbl
        pyarrow.Table
        Longitude: double
        Latitude: double
        City: string
        ----
        Longitude: [[-0.1276474,-1.9026911,-2.2451148,-1.5437941]]
        Latitude: [[51.5073219,52.4796992,53.4794892,53.7974185]]
        City: [["London","Birmingham","Manchester","Leeds"]]
        >>> save_parquet(parquet_tbl, parquet_pathname, verbose=True)
        Updating "dat.parquet" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_parquet`.
    """

    file_path, _, _ = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    try:
        # Only use direct pyarrow writer if data is already an Arrow Table
        if isinstance(data, pa.Table):  # noqa
            # engine is ignored here
            pq.write_table(data, file_path, **kwargs)  # noqa

        elif all(hasattr(data, a) for a in {'has_sindex', 'geometry', 'to_parquet'}):  # GeoDataFrame
            # noinspection PyUnresolvedReferences
            data.to_parquet(file_path, engine=engine, **kwargs)

        elif hasattr(data, 'to_parquet'):  # Standard Pandas DataFrame
            data.to_parquet(file_path, engine='auto' if engine is None else engine, **kwargs)

        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_geopackage(data, path_to_file, driver='GPKG', layer_name=None, mode='w', verbose=False,
                    print_kwargs=None, raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Saves a GeoDataFrame or a dictionary of GeoDataFrames to a GeoPackage file.

    This function handles both single-layer and multi-layer datasets. It uses
    a file-level reset for 'w' mode to prevent SQLite 'ghost layer' artifacts.

    :param data: Spatial data to save.
    :type data: geopandas.GeoDataFrame | dict[str, geopandas.GeoDataFrame]
    :param path_to_file: Destination path for the ``.gpkg`` file.
    :type path_to_file: str | pathlib.Path
    :param driver: OGR driver to use. Defaults to ``'GPKG'``.
    :type driver: str
    :param layer_name: Name for the layer (used if data is a GeoDataFrame).
        Defaults to filename stem.
    :type layer_name: str | None
    :param mode: File write mode:

        - ``'w'`` (default): Overwrite. Deletes existing file and writes fresh.
        - ``'a'``: Append. Adds layers to existing file.

    :type mode: str
    :param verbose: If ``True``, prints status messages. Defaults to ``False``.
    :type verbose: bool
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: If ``True``, re-raises exceptions. Defaults to ``False``.
    :type raise_error: bool
    :param kwargs: Additional arguments passed to ``geopandas.to_file``.

    **Examples**::

        >>> from pyhelpers.store import save_geopackage
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import shapely
        >>> import geopandas as gpd
        >>> gpkg_dat_ = example_dataframe()  # Get an example dataframe
        >>> gpkg_dat = gpkg_dat_.copy()
        >>> gpkg_dat['geometry'] = gpkg_dat_.apply(
        ...     lambda x: shapely.geometry.Point([x.Longitude, x.Latitude]), axis=1)
        >>> gpkg_dat = gpd.GeoDataFrame(gpkg_dat, crs=4326)
        >>> gpkg_pathname = cd("tests/data", "dat.gpkg")
        >>> save_geopackage(gpkg_dat, gpkg_pathname, verbose=True)
        Saving "dat.gpkg" to "./tests/data/" ... Done.
    """

    file_path, _, _ = _check_saving_path(
        path=path_to_file, verbose=verbose, return_info=True, **(print_kwargs or {}))

    # Handle file-level overwrite to ensure a clean SQLite container
    if mode == 'w' and file_path.is_file():
        file_path.unlink()

    try:
        if isinstance(data, dict):
            for i, (lyr_name, gpkg_dat) in enumerate(data.items()):
                # Save each dict entry as a separate layer to the multi-layer GeoPackage
                kwargs.update({'mode': 'a' if (i > 0 or mode == 'a') else 'w', 'layer': lyr_name})
                gpkg_dat.to_file(file_path, driver=driver, **kwargs)
        else:
            kwargs.update(dict(layer=layer_name or file_path.stem))
            data.to_file(file_path, mode=mode, driver=driver, **kwargs)  # noqa

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_svg_as_emf(path_to_svg, path_to_emf, inkscape_exe=None, verbose=False, print_kwargs=None,
                    raise_error=False):
    # noinspection PyShadowingNames
    """
    Saves a `SVG <https://en.wikipedia.org/wiki/Scalable_Vector_Graphics>`_ file (.svg) as
    a `EMF <https://en.wikipedia.org/wiki/Windows_Metafile#EMF>`_ file (.emf)
    using `Inkscape <https://inkscape.org/>`_.

    :param path_to_svg: The path to the source SVG file.
    :type path_to_svg: str | os.PathLike
    :param path_to_emf: The path where the EMF file will be saved.
    :type path_to_emf: str | os.PathLike
    :param inkscape_exe: The path to the Inkscape executable.
        If ``inkscape_exe=None`` (default), uses the standard installation path.
    :type inkscape_exe: str | None
    :param verbose: Whether to print progress to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise FileNotFoundError if the Inkscape executable is not found;
        defaults to ``False``.
    :type raise_error: bool
    :param print_kwargs: [Optional] Additional parameters passed to
        `pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None

    **Examples**::

        >>> from pyhelpers.store import save_svg_as_emf
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> mpl_preferences(backend='TkAgg')
        >>> import matplotlib.pyplot as plt
        >>> x, y = (1, 1), (2, 2)
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot()
        >>> ax.plot([x[0], y[0]], [x[1], y[1]])
        >>> # from pyhelpers.store import save_figure
        >>> # save_figure(fig, "docs/source/_images/store-save_fig-demo.pdf", verbose=True)
        >>> fig.show()

    The above example is illustrated in :numref:`store-save_fig-demo-1`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-1
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_svg_as_emf`.

    .. code-block:: python

        >>> img_dir = cd("tests", "images")
        >>> path_to_svg = cd(img_dir, "store-save_fig-demo.svg")
        >>> fig.savefig(path_to_svg)  # Save the figure as a .svg file
        >>> path_to_emf = cd(img_dir, "store-save_fig-demo.emf")
        >>> save_svg_as_emf(path_to_svg, path_to_emf, verbose=True)
        Saving "store-save_fig-demo.emf" to "./tests/images/" ... Done.
        >>> plt.close()
    """

    exe_name = "inkscape"

    # Comprehensive list of standard installation paths across OSs
    optional_pathnames = {
        exe_name,
        f"{exe_name}.exe",
        # Windows standard locations
        f"C:/Program Files/Inkscape/bin/{exe_name}.exe",
        f"C:/Program Files/Inkscape/{exe_name}.exe",
        # Linux / macOS standard locations
        f"/usr/bin/{exe_name}",
        f"/usr/local/bin/{exe_name}",
        f"/bin/{exe_name}",
        "/Applications/Inkscape.app/Contents/MacOS/inkscape",
    }

    inkscape_exists, inkscape_exe_ = _check_file_pathname(
        name=exe_name, options=optional_pathnames, target=inkscape_exe)

    if not inkscape_exists and raise_error:
        raise FileNotFoundError(
            '"Inkscape" (https://inkscape.org) is required to convert SVG to EMF, '
            'but was not found.\n'
            '  Install "Inkscape" or provide a valid path.')

    svg_file_path = pathlib.Path(path_to_svg).resolve()
    emf_file_path = pathlib.Path(path_to_emf).resolve()

    # Validate extensions (Essential for subprocess reliability)
    if svg_file_path.suffix.lower() != '.svg':
        raise ValueError(f"Source file must be .svg, got '{svg_file_path.suffix}'")
    if emf_file_path.suffix.lower() != '.emf':
        raise ValueError(f"Target file must be .emf, got '{emf_file_path.suffix}'")

    _check_saving_path(emf_file_path, verbose=verbose, **(print_kwargs or {}))

    ret_code = 1
    try:
        # Inkscape CLI: -z is for older versions; --export-filename is for 1.0+
        # nosec: inkscape_exe_ is validated by _check_file_pathname
        result = subprocess.run(
            [str(inkscape_exe_), str(svg_file_path), '--export-filename', str(emf_file_path)],
            check=True,
            capture_output=True,
            text=True
        )  # nosec
        ret_code = result.returncode

    except Exception as e:
        _print_failure_message(e, prefix="Failed. Error:", verbose=verbose, raise_error=raise_error)

    if verbose and ret_code == 0:
        print("Done.")

    return None


def _convert_svg_to_emf(conv_svg_to_emf, func, file_ext, file_path, common_args, print_kwargs=None,
                        **kwargs):
    if conv_svg_to_emf:
        if file_ext == ".svg":
            svg_path = file_path
        else:
            svg_path = file_path.with_suffix(".svg")
            kwargs.update({'conv_svg_to_emf': False} | common_args)
            func(path_to_file=svg_path, **kwargs)

        emf_path = svg_path.with_suffix(".emf")
        save_svg_as_emf(
            path_to_svg=svg_path, path_to_emf=emf_path, print_kwargs=print_kwargs, **common_args)


@_lazy_check_dependencies(plt='matplotlib.pyplot')
def save_fig(path_to_file, dpi=None, conv_svg_to_emf=False, verbose=False, print_kwargs=None,
             raise_error=False, **kwargs):
    """
    Saves a figure object to a file in a supported format.

    This function utilizes the `matplotlib.pyplot.savefig()`_ function and
    optionally `Inkscape`_ for SVG to EMF conversion.

    :param path_to_file: The path where the figure file will be saved.
    :type path_to_file: str | os.PathLike
    :param dpi: Resolution in dots per inch;
        when ``dpi=None`` (default), it takes the value of ``rcParams['savefig.dpi']``.
    :type dpi: int | None
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters passed to `matplotlib.pyplot.savefig()`_.

    .. _`matplotlib.pyplot.savefig()`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
    .. _`Inkscape`: https://inkscape.org

    **Examples**::

        >>> from pyhelpers.store import save_fig
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> mpl_preferences(backend='TkAgg')
        >>> import matplotlib.pyplot as plt
        >>> x, y = (1, 1), (2, 2)
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot()
        >>> ax.plot([x[0], y[0]], [x[1], y[1]])
        >>> fig.show()

    The above example is illustrated in :numref:`store-save_fig-demo-2`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-2
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_fig`.

    .. code-block:: python

        >>> img_dir = cd("tests", "images")
        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> save_fig(svg_file_pathname, verbose=True)
        [Figure 1] Saving "store-save_fig-demo.png" in "./tests/images/" ... Done.
        >>> save_fig(svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        [Figure 1] Updating "store-save_fig-demo.svg" in "./tests/images/" ... Done.
        [Figure 1] Saving "store-save_fig-demo.emf" to "./tests/images/" ... Done.
        >>> plt.close()
    """

    # Check if an active figure exists
    if not plt.get_fignums() and raise_error:  # noqa
        raise RuntimeError("No active figure found to save.")

    # Identify the specific figure being saved
    current_fig = plt.gcf()  # noqa
    fig_id = current_fig.get_label() or f"Figure {current_fig.number}"

    print_kwargs_ = print_kwargs or {'msg_prefix': f"[{fig_id}] "}
    file_path, _, file_ext = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **print_kwargs_)
    common_args = {'verbose': verbose, 'raise_error': raise_error}

    try:
        plt.savefig(file_path, dpi=dpi, **kwargs)  # noqa
        if verbose:
            print("Done.")
    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", **common_args)

    _convert_svg_to_emf(
        conv_svg_to_emf=conv_svg_to_emf,
        func=save_fig,
        file_ext=file_ext,
        file_path=file_path,
        common_args=common_args,
        print_kwargs=print_kwargs,
        **kwargs
    )


def save_figure(data, path_to_file, conv_svg_to_emf=False, verbose=False, print_kwargs=None,
                raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Saves a figure object to a file in a supported format (with the figure object specified).

    This function serves an alternative to the :func:`~pyhelpers.store.save_fig` function.

    :param data: The figure object to be saved.
    :type data: matplotlib.Figure | seaborn.FacetGrid
    :param path_to_file: The path where the figure file will be saved.
    :type path_to_file: str | os.PathLike
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters passed to `matplotlib.pyplot.savefig()`_.

    .. _`matplotlib.pyplot.savefig()`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html

    **Examples**::

        >>> from pyhelpers.store import save_figure
        >>> from pyhelpers.dirs import cd
        >>> import numpy as np
        >>> from pyhelpers.settings import mpl_preferences
        >>> mpl_preferences(backend='TkAgg')
        >>> import matplotlib.pyplot as plt
        >>> x = np.linspace(-5, 5)
        >>> y = 1 / (1 + np.exp(-x))
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot()
        >>> ax.plot(x, y)
        >>> fig.show()

    The above example is illustrated in :numref:`store-save_figure-demo-3`:

    .. figure:: ../_images/store-save_figure-demo.*
        :name: store-save_figure-demo-3
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_figure`.

    .. code-block:: python

        >>> img_dir = cd("tests", "images")
        >>> svg_file_pathname = cd(img_dir, "store-save_figure-demo.svg")
        >>> save_figure(fig, svg_file_pathname, verbose=True)
        [Figure 1] Saving "store-save_figure-demo.png" in "./tests/images/" ... Done.
        >>> # save_figure(fig, "docs/source/_images/store-save_figure-demo.svg", verbose=True)
        >>> # save_figure(fig, "docs/source/_images/store-save_figure-demo.pdf", verbose=True)
        >>> save_figure(fig, svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        [Figure 1] Updating "store-save_figure-demo.svg" in "./tests/images/" ... Done.
        [Figure 1] Saving "store-save_figure-demo.emf" to "./tests/images/" ... Done.
        >>> plt.close()
    """

    if not hasattr(data, 'savefig') and raise_error:
        raise AttributeError(
            "The input `data` does not have attribute `.savefig`."
            "\n  Check `data`, or try `save_fig()` instead.")

    fig_id = data.get_label() or f"Figure {data.number}"

    print_kwargs_ = print_kwargs or {'msg_prefix': f"[{fig_id}] "}
    file_path, _, file_ext = _check_saving_path(
        path_to_file, verbose=verbose, return_info=True, **print_kwargs_)
    common_args = {'verbose': verbose, 'raise_error': raise_error}

    try:
        data.savefig(file_path, **kwargs)
        if verbose:
            print("Done.")
    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", **common_args)

    # EMF conversion
    _convert_svg_to_emf(
        conv_svg_to_emf=conv_svg_to_emf,
        func=save_figure,
        file_ext=file_ext,
        file_path=file_path,
        common_args=common_args,
        print_kwargs=print_kwargs,
        data=data, **kwargs
    )


@_lazy_check_dependencies('pdfkit')
def save_html_as_pdf(data, path_to_file, if_exists='replace', page_size='A4', zoom=1.0,
                     encoding='UTF-8', wkhtmltopdf_options=None, wkhtmltopdf_path=None,
                     verbose=False, print_kwargs=None, raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Saves a web page as a `PDF <https://en.wikipedia.org/wiki/PDF>`_ file
    using `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param data: The URL of a web page or the pathname of an HTML file.
    :type data: str | os.PathLike
    :param path_to_file: The path where the PDF file will be saved.
    :type path_to_file: str | os.PathLike
    :param if_exists: Action to take if the .pdf file already exists;
        options are ``'replace'`` (default) and ``'pass'``.
    :type if_exists: str
    :param page_size: The page size; defaults to ``'A4'``.
    :type page_size: str
    :param zoom: Magnification for zooming in/out; defaults to ``1.0``.
    :type zoom: float
    :param encoding: The encoding format; defaults to ``'UTF-8'``.
    :type encoding: str
    :param wkhtmltopdf_options: Options for `wkhtmltopdf`_; defaults to ``None``.
        Refer to the description of `pdfkit`_ project for more details.
    :type wkhtmltopdf_options: dict | None
    :param wkhtmltopdf_path: The path to "*wkhtmltopdf.exe*";
        when ``wkhtmltopdf_path=None`` (default), the default installation path will be used, e.g.
        "*C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe*" (on Windows).
    :param wkhtmltopdf_path: The path to the wkhtmltopdf executable;
        if ``None`` (default), searches standard installation paths.
    :type wkhtmltopdf_path: str | None
    :param verbose: Whether to print progress to the console; defaults to ``False``.
        Set ``verbose=2`` to see full output from wkhtmltopdf.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param raise_error: Whether to raise exceptions on failure; defaults to ``False``.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `pdfkit.from_url()`_ or
        `pdfkit.from_file()`_.

    .. _`wkhtmltopdf options`: https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    .. _`pdfkit`: https://pypi.org/project/pdfkit/
    .. _`pdfkit.from_url()`: https://pypi.org/project/pdfkit/
    .. _`pdfkit.from_file()`: https://pypi.org/project/pdfkit/

    **Examples**::

        >>> from pyhelpers.store import save_html_as_pdf
        >>> from pyhelpers.dirs import cd
        >>> import subprocess
        >>> pdf_pathname = cd("tests", "documents", "pyhelpers.pdf")
        >>> web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
        >>> save_html_as_pdf(web_page_url, pdf_pathname)
        >>> subprocess.Popen(pdf_pathname, shell=True)  # Open the PDF file
        >>> # Close the PDF file (if opened with Foxit Reader)
        >>> # subprocess.call("taskkill /f /im FoxitPDFReader.exe", shell=True)
        >>> wkhtmltopdf_options = {'margin-top': '0', 'orientation': 'Landscape'}
        >>> # Using custom options for margins and orientation
        >>> save_html_as_pdf(
        ...     web_page_url, pdf_pathname, wkhtmltopdf_options=wkhtmltopdf_options, verbose=True)
        >>> subprocess.Popen(pdf_pathname, shell=True)
        >>> # subprocess.call("taskkill /f /im FoxitPDFReader.exe", shell=True)
        >>> web_page_file = cd("docs", "build", "html", "index.html")
        >>> save_html_as_pdf(web_page_file, pdf_pathname, verbose=2)
        Updating "pyhelpers.pdf" in "./tests/documents/" ...
        Loading pages (1/6)
        Counting pages (2/6)
        Resolving links (4/6)
        Loading headers and footers (5/6)
        Printing pages (6/6)
        Done
        >>> subprocess.Popen(pdf_pathname, shell=True)
        >>> # subprocess.call("taskkill /f /im FoxitPDFReader.exe", shell=True)
        >>> save_html_as_pdf(web_page_file, pdf_pathname, verbose=True)
        Updating "pyhelpers.pdf" in "./tests/documents/" ... Done.
        >>> subprocess.Popen(pdf_pathname, shell=True)
        >>> # subprocess.call("taskkill /f /im FoxitPDFReader.exe", shell=True)
    """

    file_path = pathlib.Path(path_to_file).resolve()

    if file_path.is_file() and if_exists == 'pass':
        return None

    exe_name = "wkhtmltopdf"
    optional_pathnames = {
        exe_name,
        f"{exe_name}.exe",
        f"C:/Program Files/wkhtmltopdf/bin/{exe_name}.exe",
        f"C:/Program Files/wkhtmltopdf/{exe_name}.exe",
        f"/usr/bin/{exe_name}",
        f"/usr/local/bin/{exe_name}",
    }

    wkhtmltopdf_exists, wkhtmltopdf_exe = _check_file_pathname(
        name=exe_name, options=optional_pathnames, target=wkhtmltopdf_path)

    if not wkhtmltopdf_exists and raise_error:
        raise FileNotFoundError(
            '"wkhtmltopdf" (https://wkhtmltopdf.org/) is required to run this function, '
            'but was not found.\n  Install "wkhtmltopdf" and then try again.')

    # Handle verbosity levels
    verbose_level = 2 if verbose == 2 else (1 if verbose else 0)
    print_end = " ... \n" if verbose_level == 2 else " ... "

    print_kwargs_ = print_kwargs or {}
    print_kwargs_['end'] = print_end
    _check_saving_path(path=path_to_file, verbose=verbose, **print_kwargs_)

    # Base options
    options = {
        'enable-local-file-access': None,  # Crucial for modern versions to load local CSS/images
        'page-size': page_size,
        'zoom': str(float(zoom)),
        'encoding': encoding,
        # 'margin-top': '0',
        # 'margin-right': '0',
        # 'margin-left': '0',
        # 'margin-bottom': '0',
    }
    extra_options = wkhtmltopdf_options or {}
    options.update(extra_options)

    # Prepare pdfkit configuration
    configuration = pdfkit.configuration(wkhtmltopdf=str(wkhtmltopdf_exe))  # noqa
    # pdfkit internal verbose is a bool; verbose_level 2 shows wkhtmltopdf internal progress
    pdfkit_verbose = True if verbose_level == 2 else False

    kwargs.update({'configuration': configuration, 'options': options, 'verbose': pdfkit_verbose})

    try:
        if is_url(data):
            status = pdfkit.from_url(data, path_to_file, **kwargs)  # noqa
        else:
            data_path = pathlib.Path(data)
            if data_path.is_file():
                status = pdfkit.from_file(str(data_path), str(file_path), **kwargs)  # noqa
            else:
                status = False
                if verbose:
                    print("Failed. Input is not a valid URL or file.")

        if status and verbose and verbose_level != 2:
            print("Done.")

    except Exception as e:
        _print_failure_message(
            e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@functools.lru_cache(maxsize=64)
def get_save_func(file_ext):
    """
    Finds the appropriate saver function based on a file extension.

    This function uses an LRU cache to ensure that once an extension is mapped
    to a saver function, subsequent lookups are nearly instantaneous (``O(1)``).

    :param file_ext: The file extension string (e.g. ``".pickle.gz"`` or ``".parquet"``).
    :type file_ext: str
    :return: The saver function if a match is found; otherwise, ``None``.
    :rtype: typing.Callable | None

    .. note::

        **Logic**: The mapping follows a specific order where nested extensions
        (e.g. ``".pkl.gz"``) are prioritized over general compression extensions (e.g. ``".gz"``)
        to ensure the specialized saver is selected.

    **Examples**::

        >>> from pyhelpers.store import get_save_func
        >>> get_save_func(".parquet").__name__
        'save_parquet'
        >>> get_save_func(".pkl.gz").__name__
        'save_pickle'
        >>> get_save_func(".gz").__name__
        'save_joblib'
    """

    _mapping = {
        (".pickle", ".pickle.bz2", ".pickle.gz", ".pickle.gzip", ".pickle.lzma", ".pickle.xz",
         ".pkl", ".pkl.bz2", ".pkl.gz", ".pkl.gzip", ".pkl.lzma", ".pkl.xz"): save_pickle,
        (".csv", ".xlsx", ".xls", ".txt", ".ods"): save_spreadsheets,
        (".json",): save_json,
        (".fea", ".feather"): save_feather,
        (".parquet", ".geoparquet"): save_parquet,
        (".gpkg", ".geopackage"): save_geopackage,
        (".pdf",): save_html_as_pdf,
        (".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma"): save_joblib,
        (".eps", ".jpeg", ".jpg", ".pgf", ".png", ".ps",
         ".raw", ".rgba", ".svg", ".svgz", ".tif", ".tiff"): save_figure,
    }

    return next((func for ext, func in _mapping.items() if file_ext.endswith(ext)), None)


def save_data(data, path_to_file, verbose=False, print_kwargs=None, show_warning=True,
              raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Saves data to a file in a specific format.

    :param data: The data to be saved, which can be:

        - a file in `Pickle`_, `CSV`_, `Microsoft Excel`_, `JSON`_, `Joblib`_, `Feather`_ or
          `Parquet`_ format;
        - a URL of a web page or an `HTML file`_;
        - an image file in a `Matplotlib`_-supported format.

    :type data: typing.Any
    :param path_to_file: The path of the file where the ``data`` will be stored.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param print_kwargs: [Optional] Additional parameters passed to
        :func:`pyhelpers.store._check_saving_path()`. Defaults to ``None``.
    :type print_kwargs: dict | None
    :param show_warning: Whether to display a warning message if an unknown error occurs;
        defaults to ``True``.
    :type show_warning: bool
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for one of the following functions:
        :func:`~pyhelpers.store.save_pickle`,
        :func:`~pyhelpers.store.save_spreadsheet`,
        :func:`~pyhelpers.store.save_spreadsheets`,
        :func:`~pyhelpers.store.save_json`,
        :func:`~pyhelpers.store.save_joblib`,
        :func:`~pyhelpers.store.save_feather`,
        :func:`~pyhelpers.store.save_parquet`,
        :func:`~pyhelpers.store.save_geopackage`,
        :func:`~pyhelpers.store.save_figure` or
        :func:`~pyhelpers.store.save_web_page_as_pdf`.

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`Parquet`: https://arrow.apache.org/docs/python/parquet.html
    .. _`HTML file`: https://fileinfo.com/extension/html
    .. _`Matplotlib`:
        https://matplotlib.org/stable/api/backend_bases_api.html#
        matplotlib.backend_bases.FigureCanvasBase.get_supported_filetypes

    **Examples**::

        >>> from pyhelpers.store import save_data
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> data_dir = cd("tests", "data")
        >>> # Get an example dataframe
        >>> data = example_dataframe()
        >>> data
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> # Save the data to files different formats:
        >>> path_to_file = cd(data_dir, "dat.pickle")
        >>> save_data(data, path_to_file, verbose=True)
        Saving "dat.pickle" in "./tests/data/" ... Done.
        >>> path_to_file = cd(data_dir, "dat.csv")
        >>> save_data(data, path_to_file, verbose=True, index=True)
        Saving "dat.csv" in "./tests/data/" ... Done.
        >>> path_to_file = cd(data_dir, "dat.xlsx")
        >>> save_data(data, path_to_file, verbose=True, index=True)
        Saving "dat.xlsx" in "./tests/data/" ... Done.
        >>> path_to_file = cd(data_dir, "dat.txt")
        >>> save_data(data, path_to_file, verbose=True, index=True)
        Saving "dat.txt" in "./tests/data/" ... Done.
        >>> path_to_file = cd(data_dir, "dat.feather")
        >>> save_data(data, path_to_file, verbose=True, index=True)
        Saving "dat.feather" in "./tests/data/" ... Done.
        >>> path_to_file = cd(data_dir, "dat.parquet")
        >>> save_data(data, path_to_file, verbose=True)
        Saving "dat.parquet" in "./tests/data/" ... Done.
        >>> data = data.T.to_dict()  # Convert `dat` to JSON format
        >>> path_to_file = cd(data_dir, "dat.json")
        >>> save_data(data, path_to_file, verbose=True, indent=4)
        Saving "dat.json" to "./tests/data/" ... Done.

    .. seealso::

        - Examples for :func:`~pyhelpers.store.load_data`.
    """

    file_ext = "".join(pathlib.Path(path_to_file).suffixes).lower()

    save_params = {
        'data': data,
        'path_to_file': path_to_file,
        'verbose': verbose,
        'print_kwargs': print_kwargs,
        'raise_error': raise_error,
        **kwargs
    }

    if file_ext.endswith((".csv", ".xlsx", ".xls", ".txt", ".ods")):
        try:
            save_spreadsheet(**save_params)
        except Exception:  # noqa
            save_spreadsheets(**save_params)

    elif file_ext.endswith(".pdf"):
        if is_visual_object(data):
            save_figure(**save_params)
        else:
            save_html_as_pdf(**save_params)

    else:
        save_func = get_save_func(file_ext)

        if save_func is not None:
            save_func(**save_params)

        else:
            if show_warning:
                logging.getLogger(__name__).warning(
                    'Warning: The file format/extension "%s" is not recognized by `save_data()`.',
                    file_ext)
