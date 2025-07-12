"""
Utilities for saving data in various formats.
"""

import bz2
import copy
import gzip
import logging
import lzma
import os
import pathlib
import pickle  # nosec
import subprocess  # nosec
import sys

import pandas as pd

from .utils import _autofit_column_width, _check_saving_path
from .._cache import _check_dependencies, _check_file_pathname, _confirmed, \
    _lazy_check_dependencies, _print_failure_message
from ..ops.web import is_url


def save_pickle(data, path_to_file, verbose=False, raise_error=False, **kwargs):
    """
    Saves data to a `pickle <https://docs.python.org/3/library/pickle.html>`_ file.

    :param data: Data to be saved, compatible with the built-in `pickle.dump()`_ function.
    :type data: typing.Any
    :param path_to_file: Path where the `Pickle`_ file will be saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
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

    _check_saving_path(path_to_file, verbose=verbose, ret_info=True)

    try:
        path_to_file_ = str(path_to_file).lower()

        if path_to_file_.endswith((".pkl.gz", ".pickle.gz")):
            with gzip.open(path_to_file, mode='wb') as pickle_out:
                pickle.dump(data, pickle_out, **kwargs)  # noqa
        elif path_to_file_.endswith((".pkl.xz", ".pkl.lzma", ".pickle.xz", ".pickle.lzma")):
            with lzma.open(path_to_file, mode='wb') as pickle_out:
                pickle.dump(data, pickle_out, **kwargs)  # noqa
        elif path_to_file_.endswith((".pkl.bz2", ".pickle.bz2")):
            with bz2.BZ2File(path_to_file, mode='wb') as pickle_out:
                pickle.dump(data, pickle_out, **kwargs)  # noqa
        else:
            with open(path_to_file, mode='wb') as pickle_out:
                pickle.dump(data, pickle_out, **kwargs)  # noqa

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies('openpyxl', 'odf')
def save_spreadsheet(data, path_to_file, sheet_name="Sheet1", index=False, engine=None,
                     delimiter=',', autofit_column_width=True, writer_kwargs=None,
                     verbose=False, raise_error=False, **kwargs):
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

    _, filename = _check_saving_path(path_to_file=path_to_file, verbose=verbose, ret_info=True)
    _, ext = os.path.splitext(filename)

    valid_extensions = {".txt", ".csv", ".xlsx", ".xls", ".ods", ".odt"}
    if raise_error:
        assert ext in valid_extensions, f"File extension must be one of {valid_extensions}."

    try:  # to save the data
        if ext in {".csv", ".txt", ".odt"}:  # a .csv file
            kwargs.update({'path_or_buf': path_to_file, 'sep': delimiter, 'index': index})
            data.to_csv(**kwargs)

        else:
            if writer_kwargs is None:
                writer_kwargs = {'path': path_to_file}
            else:
                writer_kwargs.update({'path': path_to_file})

            if ext.startswith(".xls"):  # a .xlsx file or a .xls file
                _ = _check_dependencies('openpyxl')
                writer_kwargs.update({'engine': 'openpyxl'})
            elif ext == ".ods":
                _ = _check_dependencies('odf')
                writer_kwargs.update({'engine': 'odf'})  # kwargs.update({'engine': None})
            else:
                writer_kwargs.update({'engine': engine})

            with pd.ExcelWriter(**writer_kwargs) as writer:
                kwargs.update({'excel_writer': writer, 'index': index, 'sheet_name': sheet_name})
                data.to_excel(**kwargs)

                if autofit_column_width:
                    _autofit_column_width(writer, writer_kwargs, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def _save_spreadsheets(data, sheet_names, cur_sheet_names, writer, if_sheet_exists,
                       autofit_column_width, writer_kwargs, verbose, raise_error, **kwargs):
    for sheet_data, sheet_name in zip(data, sheet_names):
        # sheet_data, sheet_name = spreadsheets_data[0], sheet_names[0]
        if verbose:
            print(f"\t'{sheet_name}'", end=" ... ")

        if sheet_name in cur_sheet_names:
            if if_sheet_exists is None:
                if_sheet_exists_ = input("This sheet already exists; [pass]|new|replace: ")
            else:
                assert if_sheet_exists in {'error', 'new', 'replace', 'overlay'}, \
                    "Invalid option for `if_sheet_exists`."
                if_sheet_exists_ = copy.copy(if_sheet_exists)

            if if_sheet_exists_ != 'pass':
                writer._if_sheet_exists = if_sheet_exists_

        try:
            kwargs.update({'excel_writer': writer, 'sheet_name': sheet_name})
            sheet_data.to_excel(**kwargs)

            if autofit_column_width:
                _autofit_column_width(writer, writer_kwargs, **kwargs)

            if writer._if_sheet_exists == 'new':
                new_sheet_name = [x for x in writer.sheets if x not in cur_sheet_names][0]
                prefix = "\t\t" if if_sheet_exists is None else ""
                add_msg = f"{prefix}saved as '{new_sheet_name}' ... Done."
            else:
                add_msg = "Done."

            if verbose:
                print(add_msg)

            cur_sheet_names = list(writer.sheets.keys())

        except Exception as e:
            _print_failure_message(
                e=e, prefix=f'Failed. Sheet name "{sheet_name}":', verbose=verbose,
                raise_error=raise_error)


def save_spreadsheets(data, path_to_file, sheet_names, mode='w', if_sheet_exists=None,
                      autofit_column_width=True, writer_kwargs=None, verbose=False,
                      raise_error=False, **kwargs):
    """
    Saves multiple dataframes to a multi-sheet `Microsoft Excel`_ or `OpenDocument`_ format file.

    The file extension can be ``.xlsx`` (or ``.xls``) for `Microsoft Excel`_ files or
    ``.ods`` for `OpenDocument`_ files.

    :param data: Sequence of dataframes to be saved as sheets in the workbook.
    :type data: list | tuple | iterable
    :param path_to_file: File path where the spreadsheet will be saved.
    :type path_to_file: str | os.PathLike
    :param sheet_names: Names of all sheets in the workbook.
    :type sheet_names: list | tuple | iterable
    :param mode: Mode for writing to the spreadsheet file:

        - `'w'` (default): Write mode, creates a new file or overwrites existing.
        - `'a'`: Append mode, adds sheets to an existing file (not supported for `OpenDocument`_).

    :type mode: str
    :param if_sheet_exists: Behaviour when trying to write to an existing sheet;
        defaults to ``None``; see also the parameter ``if_sheet_exists`` of `pandas.ExcelWriter()`_.
    :type if_sheet_exists: None | str
    :param autofit_column_width: Whether to autofit column width; defaults to ``True``.
    :type autofit_column_width: bool
    :param writer_kwargs: [Optional] Additional parameters for the class `pandas.ExcelWriter()`_.
    :type writer_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_excel()`_.

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
        >>> dat1 = example_dataframe()  # Get an example dataframe
        >>> dat1
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> dat2 = dat1.T
        >>> dat2
        City          London  Birmingham  Manchester      Leeds
        Longitude  -0.127647   -1.902691   -2.245115  -1.543794
        Latitude   51.507322   52.479699   53.479489  53.797418
        >>> dat = [dat1, dat2]
        >>> sheets = ['TestSheet1', 'TestSheet2']
        >>> pathname = cd("tests", "data", "dat.ods")
        >>> save_spreadsheets(dat, pathname, sheets, verbose=True)
        Saving "dat.ods" to "./tests/data/" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.
        >>> pathname = cd("tests", "data", "dat.xlsx")
        >>> save_spreadsheets(dat, pathname, sheets, verbose=True)
        Saving "dat.xlsx" to "./tests/data/" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.
        >>> save_spreadsheets(dat, pathname, sheets, mode='a', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
            'TestSheet1' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet11' ... Done.
            'TestSheet2' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet21' ... Done.
        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='replace', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.
        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='new', verbose=True)
        Updating "dat.xlsx" at "./tests/data/" ...
            'TestSheet1' ... saved as 'TestSheet12' ... Done.
            'TestSheet2' ... saved as 'TestSheet22' ... Done.
    """

    assert path_to_file.endswith((".xlsx", ".xls", ".ods")), "File must be an Excel or ODS file."

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    if os.path.isfile(path_to_file) and mode == 'a':
        with pd.ExcelFile(path_to_file) as f:
            cur_sheet_names = f.sheet_names
    else:
        cur_sheet_names = []
        if mode == 'a':
            pd.DataFrame().to_excel(path_to_file, sheet_name=sheet_names[0])

    engine = 'openpyxl' if path_to_file.endswith((".xlsx", ".xls")) else 'odf'

    if writer_kwargs is None:
        writer_kwargs = {}
    writer_kwargs.update(
        {'path': path_to_file, 'engine': engine, 'mode': mode, 'if_sheet_exists': if_sheet_exists})

    with pd.ExcelWriter(**writer_kwargs) as writer:
        if verbose:
            print("")

        _save_spreadsheets(
            data=data, sheet_names=sheet_names, cur_sheet_names=cur_sheet_names, writer=writer,
            if_sheet_exists=if_sheet_exists, autofit_column_width=autofit_column_width,
            writer_kwargs=writer_kwargs, verbose=verbose, raise_error=raise_error, **kwargs)


def save_json(data, path_to_file, engine=None, verbose=False, raise_error=False, **kwargs):
    """
    Saves data to a `JSON <https://www.json.org/json-en.html>`_ file.

    :param data: Data to be serialised and
        saved as a `JSON <https://www.json.org/json-en.html>`_ file.
    :type data: typing.Any
    :param path_to_file: File path
        where the `JSON <https://www.json.org/json-en.html>`_ file will be saved.
    :type path_to_file: str | os.PathLike
    :param engine: Serialisation engine:

        - ``None`` (default): Use the built-in
          `json module <https://docs.python.org/3/library/json.html>`_.
        - ``'ujson'``: Use `UltraJSON`_ for faster serialisation.
        - ``'orjson'``: Use `orjson`_ for faster and more efficient serialisation.
        - ``'rapidjson'``: Use `python-rapidjson`_ for fast and efficient serialisation.

    :type engine: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
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

    if engine is not None:
        valid_engines = {'ujson', 'orjson', 'rapidjson'}
        assert engine in valid_engines, f"`engine` must be on one of {valid_engines}."
        mod = _check_dependencies(engine)
    else:
        mod = sys.modules.get('json')

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        if engine == 'orjson':
            with open(path_to_file, mode='wb') as json_out:
                json_out.write(mod.dumps(data, **kwargs))

        else:
            with open(path_to_file, mode='w') as json_out:
                mod.dump(data, json_out, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_joblib(data, path_to_file, verbose=False, raise_error=False, **kwargs):
    """
    Saves data to a `Joblib <https://pypi.org/project/joblib/>`_ file.

    :param data: The data to be serialised and saved using `joblib.dump()`_.
    :type data: typing.Any
    :param path_to_file: The file path where the Joblib file will be saved.
    :type path_to_file: str | os.PathLike
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the `joblib.dump()`_ function.

    .. _`joblib.dump()`: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html

    **Examples**::

        >>> from pyhelpers.store import save_joblib
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy as np
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
        >>> np.random.seed(0)
        >>> joblib_dat = np.random.rand(100, 100)
        >>> joblib_dat
        array([[0.5488135 , 0.71518937, 0.60276338, ..., 0.02010755, 0.82894003,
                0.00469548],
               [0.67781654, 0.27000797, 0.73519402, ..., 0.25435648, 0.05802916,
                0.43441663],
               [0.31179588, 0.69634349, 0.37775184, ..., 0.86219152, 0.97291949,
                0.96083466],
               ...,
               [0.89111234, 0.26867428, 0.84028499, ..., 0.5736796 , 0.73729114,
                0.22519844],
               [0.26969792, 0.73882539, 0.80714479, ..., 0.94836806, 0.88130699,
                0.1419334 ],
               [0.88498232, 0.19701397, 0.56861333, ..., 0.75842952, 0.02378743,
                0.81357508]])
        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Updating "dat.joblib" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_joblib`.
    """

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        joblib = _check_dependencies('joblib')

        joblib.dump(value=data, filename=path_to_file, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_feather(data, path_to_file, index=False, verbose=False, raise_error=False, **kwargs):
    """
    Saves a dataframe to a `Feather <https://arrow.apache.org/docs/python/feather.html>`_ file.

    :param data: The dataframe to be saved as a Feather-formatted file.
    :type data: pandas.DataFrame
    :param path_to_file: The path where the Feather file will be saved.
    :type path_to_file: str | os.PathLike
    :param index: Whether to include the index as a column; defaults to ``False``.
    :type index: bool
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the method `pandas.DataFrame.to_feather()`_.

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
        >>> feather_pathname = cd("tests\\data", "dat.feather")
        >>> save_feather(feather_dat, feather_pathname, verbose=True)
        Saving "dat.feather" to "./tests/data/" ... Done.
        >>> save_feather(feather_dat, feather_pathname, index=True, verbose=True)
        Updating "dat.feather" in "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`pyhelpers.store.load_feather`.
    """

    # assert isinstance(data, pd.DataFrame)

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        if list(data.index) != range(len(data)) or index is True:
            data.reset_index().to_feather(path_to_file, **kwargs)
        else:
            data.to_feather(path_to_file, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def save_svg_as_emf(path_to_svg, path_to_emf, inkscape_exe=None, verbose=False, raise_error=False):
    # noinspection PyShadowingNames
    """
    Saves a `SVG <https://en.wikipedia.org/wiki/Scalable_Vector_Graphics>`_ file (.svg) as
    a `EMF <https://en.wikipedia.org/wiki/Windows_Metafile#EMF>`_ file (.emf).

    :param path_to_svg: The path where the SVG file is located.
    :type path_to_svg: str
    :param path_to_emf: The path where the EMF file will be saved.
    :type path_to_emf: str
    :param inkscape_exe: The path to the executable "*inkscape.exe*";
        if ``inkscape_exe=None`` (default), the default installation path will be used, e.g.
        (on Windows) "*C:\\\\Program Files\\\\Inkscape\\\\bin\\\\inkscape.exe*" or
        "*C:\\\\Program Files\\\\Inkscape\\\\inkscape.exe*".
    :type inkscape_exe: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool

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

    The above exmaple is illustrated in :numref:`store-save_fig-demo-1`:

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
    optional_pathnames = {
        exe_name,
        f"{exe_name}.exe"
        f"C:/Program Files/Inkscape/{exe_name}.exe",
        f"C:/Program Files/Inkscape/bin/{exe_name}.exe",
    }
    inkscape_exists, inkscape_exe_ = _check_file_pathname(
        name=exe_name, options=optional_pathnames, target=inkscape_exe)

    abs_svg_path, abs_emf_path = map(pathlib.Path, (path_to_svg, path_to_emf))
    assert abs_svg_path.suffix.lower() == ".svg"

    if inkscape_exists:
        _check_saving_path(abs_emf_path, verbose=verbose)

        ret_code = 1

        try:
            abs_emf_path.parent.mkdir(exist_ok=True)

            result = subprocess.run(
                [inkscape_exe_, '-z', path_to_svg, '--export-filename', path_to_emf],
                # [inkscape_exe_, '-z', path_to_svg, '-M', path_to_emf],  # Old
                check=True,
            )  # nosec
            ret_code = result.returncode

        except Exception as e:
            _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

        if verbose and ret_code == 0:
            print("Done.")

    else:
        if raise_error:
            raise FileNotFoundError(
                '"Inkscape" (https://inkscape.org) is required to '
                'convert a SVG file to an EMF file; however, it is not found on this device.'
                '\nInstall it and then try again.')


def save_fig(path_to_file, dpi=None, verbose=False, conv_svg_to_emf=False, raise_error=False,
             **kwargs):
    """
    Saves a figure object to a file in a supported format.

    This function utilises the `matplotlib.pyplot.savefig()`_ function and
    optionally `Inkscape`_ for SVG to EMF conversion.

    :param path_to_file: The path where the figure file will be saved.
    :type path_to_file: str | os.PathLike
    :param dpi: Resolution in dots per inch;
        when ``dpi=None`` (default), it takes the value of ``rcParams['savefig.dpi']``.
    :type dpi: int | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `matplotlib.pyplot.savefig()`_.

    .. _`matplotlib.pyplot.savefig()`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
    .. _`Inkscape`:
        https://inkscape.org

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

    The above exmaple is illustrated in :numref:`store-save_fig-demo-2`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-2
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_fig`.

    .. code-block:: python

        >>> img_dir = cd("tests", "images")
        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> save_fig(svg_file_pathname, verbose=True)
        Saving "store-save_fig-demo.png" in "./tests/images/" ... Done.
        >>> save_fig(svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        Updating "store-save_fig-demo.svg" in "./tests/images/" ... Done.
        Saving "store-save_fig-demo.emf" to "./tests/images/" ... Done.
        >>> plt.close()
    """

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        mpl_plt = _check_dependencies('matplotlib.pyplot')
        mpl_plt.savefig(path_to_file, dpi=dpi, **kwargs)
        if verbose:
            print("Done.")
    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    file_ext = pathlib.Path(path_to_file).suffix
    if file_ext == ".svg" and conv_svg_to_emf:
        save_svg_as_emf(
            path_to_file, path_to_file.replace(file_ext, ".emf"), verbose=verbose,
            raise_error=raise_error)


def save_figure(data, path_to_file, verbose=False, conv_svg_to_emf=False, raise_error=False,
                **kwargs):
    # noinspection PyShadowingNames
    """
    Saves a figure object to a file in a supported format (with the figure object specified).

    This function serves an alternative to the :func:`~pyhelpers.store.save_fig` function.

    :param data: The figure object to be saved.
    :type data: matplotlib.Figure | seaborn.FacetGrid
    :param path_to_file: The path where the figure file will be saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param conv_svg_to_emf: Whether to convert a .svg file to a .emf file; defaults to ``False``.
    :type conv_svg_to_emf: bool
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `matplotlib.pyplot.savefig()`_.

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

    The above exmaple is illustrated in :numref:`store-save_figure-demo-3`:

    .. figure:: ../_images/store-save_figure-demo.*
        :name: store-save_figure-demo-3
        :align: center
        :width: 75%

        An example figure created for the function :func:`~pyhelpers.store.save_figure`.

    .. code-block:: python

        >>> img_dir = cd("tests", "images")
        >>> svg_file_pathname = cd(img_dir, "store-save_figure-demo.svg")
        >>> save_figure(fig, svg_file_pathname, verbose=True)
        Saving "store-save_figure-demo.png" in "./tests/images/" ... Done.
        >>> # save_figure(fig, "docs/source/_images/store-save_figure-demo.svg", verbose=True)
        >>> # save_figure(fig, "docs/source/_images/store-save_figure-demo.pdf", verbose=True)
        >>> save_figure(fig, svg_file_pathname, verbose=True, conv_svg_to_emf=True)
        Updating "store-save_figure-demo.svg" in "./tests/images/" ... Done.
        Saving "store-save_figure-demo.emf" to "./tests/images/" ... Done.
        >>> plt.close()
    """

    assert 'savefig' in dir(data), \
        ("The `fig` object does not have attribute `.savefig`. \n"
         "Check `fig`, or try `save_fig()` instead.")

    _check_saving_path(path_to_file, verbose=verbose, ret_info=False)

    try:
        data.savefig(path_to_file, **kwargs)
        if verbose:
            print("Done.")
    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    if conv_svg_to_emf:
        file_ext = pathlib.Path(path_to_file).suffix
        if file_ext != ".svg":
            kwargs.update({'conv_svg_to_emf': False, 'raise_error': raise_error})
            save_figure(data, path_to_file.replace(file_ext, ".svg"), **kwargs)

        save_svg_as_emf(
            path_to_file, path_to_file.replace(file_ext, ".emf"), verbose=verbose,
            raise_error=raise_error)


def save_html_as_pdf(data, path_to_file, if_exists='replace', page_size='A4', zoom=1.0,
                     encoding='UTF-8', wkhtmltopdf_options=None, wkhtmltopdf_path=None,
                     verbose=False, raise_error=False, **kwargs):
    """
    Saves a web page as a `PDF <https://en.wikipedia.org/wiki/PDF>`_ file
    using `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param data: The URL of a web page or the pathname of an HTML file.
    :type data: str
    :param path_to_file: The path where the PDF file will be saved.
    :type path_to_file: str
    :param if_exists: Action to take if the .pdf file already exists;
        options are ``'replace'`` (default), ``'pass'`` and ``'append'``.
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
        "*C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe*" (on Windows).
    :type wkhtmltopdf_path: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `pdfkit.from_url()`_.

    .. _`wkhtmltopdf options`: https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    .. _`pdfkit`: https://pypi.org/project/pdfkit/
    .. _`pdfkit.from_url()`: https://pypi.org/project/pdfkit/

    **Examples**::

        >>> from pyhelpers.store import save_html_as_pdf
        >>> from pyhelpers.dirs import cd
        >>> import subprocess
        >>> pdf_pathname = cd("tests", "documents", "pyhelpers.pdf")
        >>> web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
        >>> save_html_as_pdf(web_page_url, pdf_pathname)
        >>> # Open the PDF file using the system's default application
        >>> subprocess.Popen(pdf_pathname, shell=True)
        >>> # Close the PDF file (if opened with Foxit Reader)
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

    if os.path.isfile(path_to_file) and if_exists == 'pass':
        return None

    else:
        exe_name = "wkhtmltopdf"
        optional_pathnames = {
            exe_name,
            f"{exe_name}.exe"
            f"C:/Program Files/wkhtmltopdf/{exe_name}.exe",
            f"C:/Program Files/wkhtmltopdf/bin/{exe_name}.exe",
        }
        wkhtmltopdf_exists, wkhtmltopdf_exe = _check_file_pathname(
            name=exe_name, options=optional_pathnames, target=wkhtmltopdf_path)

        if wkhtmltopdf_exists:
            pdfkit = _check_dependencies('pdfkit')

            if os.path.dirname(path_to_file):
                os.makedirs(os.path.dirname(path_to_file), exist_ok=True)

            verbose_, print_end = (True, " ... \n") if verbose == 2 else (False, " ... ")

            _check_saving_path(
                path_to_file=path_to_file, verbose=verbose, print_end=print_end, ret_info=False)

            options = {
                'enable-local-file-access': None,
                'page-size': page_size,
                'zoom': str(float(zoom)),
                'encoding': encoding,
                # 'margin-top': '0',
                # 'margin-right': '0',
                # 'margin-left': '0',
                # 'margin-bottom': '0',
            }
            if isinstance(wkhtmltopdf_options, dict):
                options.update(wkhtmltopdf_options)
            configuration = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_exe)
            kwargs.update({'configuration': configuration, 'options': options, 'verbose': verbose_})

            try:
                if is_url(data):
                    status = pdfkit.from_url(data, path_to_file, **kwargs)
                elif os.path.isfile(data):
                    status = pdfkit.from_file(data, path_to_file, **kwargs)
                else:
                    status = None

                if verbose:
                    if not status:
                        print("Failed. Check if the URL is available.")
                    elif not verbose_:
                        print("Done.")

            except Exception as e:
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

        else:
            print('"wkhtmltopdf" (https://wkhtmltopdf.org/) is required to run this function; '
                  'however, it is not found on this device.\nInstall it and then try again.')

            return None


def save_data(data, path_to_file, err_warning=True, confirmation_required=True, raise_error=False,
              **kwargs):
    """
    Saves data to a file in a specific format.

    :param data: The data to be saved, which can be:

        - a file in `Pickle`_, `CSV`_, `Microsoft Excel`_, `JSON`_, `Joblib`_ or `Feather`_ format;
        - a URL of a web page or an `HTML file`_;
        - an image file in a `Matplotlib`_-supported format.

    :type data: typing.Any
    :param path_to_file: The path of the file where the ``data`` will be stored.
    :type path_to_file: str | os.PathLike
    :param err_warning: Whether to display a warning message if an unknown error occurs;
        defaults to ``True``.
    :type err_warning: bool
    :param confirmation_required: Whether user confirmation is required to proceed;
        defaults to ``True``.
    :type confirmation_required: bool
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
        :func:`~pyhelpers.store.save_figure` or
        :func:`~pyhelpers.store.save_web_page_as_pdf`.

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
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
        >>> dat = example_dataframe()
        >>> dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> # Save the data to files different formats:
        >>> dat_pathname = cd(data_dir, "dat.pickle")
        >>> save_data(dat, dat_pathname, verbose=True)
        Saving "dat.pickle" to "./tests/data/" ... Done.
        >>> dat_pathname = cd(data_dir, "dat.csv")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.csv" to "./tests/data/" ... Done.
        >>> dat_pathname = cd(data_dir, "dat.xlsx")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "./tests/data/" ... Done.
        >>> dat_pathname = cd(data_dir, "dat.txt")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.txt" to "./tests/data/" ... Done.
        >>> dat_pathname = cd(data_dir, "dat.feather")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.feather" to "./tests/data/" ... Done.
        >>> # Convert `dat` to JSON format
        >>> import json
        >>> dat_ = json.loads(dat.to_json(orient='index'))
        >>> dat_
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}
        >>> dat_pathname = cd(data_dir, "dat.json")
        >>> save_data(dat_, dat_pathname, indent=4, verbose=True)
        Saving "dat.json" to "./tests/data/" ... Done.

    .. seealso::

        - Examples for the function :func:`~pyhelpers.store.load_data`.
    """

    path_to_file_ = str(path_to_file).lower()

    kwargs.update({'data': data, 'path_to_file': path_to_file, 'raise_error': raise_error})

    if path_to_file_.endswith(
            (".pkl", ".pickle",
             ".pkl.gz", ".pkl.xz", ".pkl.lzma", ".pkl.bz2",
             ".pickle.gz", ".pickle.xz", ".pickle.lzma", ".pickle.bz2")):
        save_pickle(**kwargs)

    elif path_to_file_.endswith((".csv", ".xlsx", ".xls", ".txt")):
        # noinspection PyBroadException
        try:
            save_spreadsheet(**kwargs)
        except Exception:
            save_spreadsheets(**kwargs)

    elif path_to_file_.endswith(".json"):
        save_json(**kwargs)

    elif path_to_file_.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        save_joblib(**kwargs)

    elif path_to_file_.endswith((".fea", ".feather")):
        save_feather(**kwargs)

    elif (path_to_file_.endswith(".pdf") and
          all(x not in data.__class__.__module__ for x in {'seaborn', 'matplotlib'})):
        # noinspection PyBroadException
        save_html_as_pdf(**kwargs)

    elif path_to_file_.endswith(
            ('.eps', '.jpeg', '.jpg', '.pdf', '.pgf', '.png', '.ps',
             '.raw', '.rgba', '.svg', '.svgz', '.tif', '.tiff')):
        # noinspection PyBroadException
        try:
            save_figure(**kwargs)
        except Exception:
            save_fig(path_to_file=path_to_file, **kwargs)

    else:
        if err_warning:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(
                "\n\tThe specified file format (extension) is not recognisable by "
                "`pyhelpers.store.save_data`.")

        if _confirmed("To save the data as a pickle file\n?", confirmation_required):
            save_pickle(**kwargs)
