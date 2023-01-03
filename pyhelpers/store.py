"""Saving, loading and other relevant operations of file-like objects."""

import copy
import csv
import io
import operator
import os
import pathlib
import pickle
import platform
import subprocess
import sys
import tempfile
import warnings
import zipfile

import pandas as pd
import pkg_resources

from ._cache import _check_dependency, _check_rel_pathname
from .ops import confirmed, find_executable, is_url


def _check_path_to_file(path_to_file, verbose=False, verbose_end=" ... ", ret_info=False):
    """
    Check about a specified file pathname.

    :param path_to_file: path where a file is saved
    :type path_to_file: str or pathlib.Path
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param verbose_end: a string passed to ``end`` for ``print``, defaults to ``" ... "``
    :type verbose_end: str
    :param ret_info: whether to return the file path information, defaults to ``False``
    :type ret_info: bool
    :return: a relative path and a filename (if ``ret_info=True``)
    :rtype: tuple

    **Tests**::

        >>> from pyhelpers.store import _check_path_to_file
        >>> from pyhelpers.dirs import cd

        >>> file_path = cd()
        >>> try:
        ...     _check_path_to_file(file_path, verbose=True)
        ... except AssertionError as e:
        ...     print(e)
        The input for `path_to_file` may not be a file path.

        >>> file_path = cd("pyhelpers.pdf")
        >>> _check_path_to_file(file_path, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" ... Passed.

        >>> file_path = cd("tests\\documents", "pyhelpers.pdf")
        >>> _check_path_to_file(file_path, verbose=True)
        >>> print("Passed.")
        Saving "pyhelpers.pdf" to "tests\\" ... Passed.
    """

    abs_path_to_file = pathlib.Path(path_to_file).absolute()
    assert not abs_path_to_file.is_dir(), "The input for `path_to_file` may not be a file path."

    filename = pathlib.Path(abs_path_to_file).name if abs_path_to_file.suffix else ""

    try:
        rel_path = pathlib.Path(os.path.relpath(abs_path_to_file.parent))

        if rel_path == rel_path.parent:
            rel_path = abs_path_to_file.parent
            msg_fmt = "{} \"{}\""
        else:
            msg_fmt = "{} \"{}\" {} \"{}\\\""
            # The specified path exists?
            os.makedirs(abs_path_to_file.parent, exist_ok=True)

    except ValueError:
        if verbose == 2:
            warn_msg = "Warning: \"{}\" is outside the current working directory".format(
                str(abs_path_to_file.parent))
            print(warn_msg)

        rel_path = abs_path_to_file.parent
        msg_fmt = "{} \"{}\""

    if verbose:
        if os.path.exists(abs_path_to_file):
            status_msg, prep = "Updating", "at"
        else:
            status_msg, prep = "Saving", "to"

        if verbose_end:
            verbose_end_ = verbose_end
        else:
            verbose_end_ = "\n"

        if rel_path == rel_path.parent:
            print(msg_fmt.format(status_msg, filename), end=verbose_end_)
        else:
            print(msg_fmt.format(status_msg, filename, prep, rel_path), end=verbose_end_)

    if ret_info:
        return rel_path, filename


def _check_loading_path(path_to_file, verbose=False, verbose_end=" ... "):
    """
    Check about loading a file from a specified pathname.

    :param path_to_file: path where a file is saved
    :type path_to_file: str or pathlib.Path
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param verbose_end: a string passed to ``end`` for ``print``, defaults to ``" ... "``
    :type verbose_end: str

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers.dirs import cd

        >>> file_path = cd("test_func.py")
        >>> _check_loading_path(file_path, verbose=True)
        >>> print("Passed.")
        Loading "test_func.py" ... Passed.
    """

    if verbose:
        rel_pathname = _check_rel_pathname(path_to_file)
        print("Loading \"{}\"".format(rel_pathname), end=verbose_end)


def _check_exe_pathname(exe_name, exe_pathname, possible_pathnames):
    """
    Check about a specified executable file pathname.

    :param exe_name: name of an executable file
    :type exe_name: str
    :param exe_pathname: pathname of an executable file
    :type exe_pathname: str or None
    :param possible_pathnames: a number of possible pathnames of the executable file
    :type possible_pathnames: list or set
    :return: whether the specified executable file exists and its pathname
    :rtype: typing.Tuple[bool, str]

    **Tests**::

        >>> from pyhelpers.store import _check_exe_pathname
        >>> import os

        >>> possibilities = ["C:\\Python39\\python.exe", "C:\\Program Files\\Python39\\python.exe"]

        >>> python_exists, path_to_exe = _check_exe_pathname("python.exe", None, possibilities)
        >>> python_exists
        True
        >>> os.path.basename(path_to_exe)
        'python.exe'
    """

    if exe_pathname is None:
        exe_exists, exe_pathname_ = find_executable(app_name=exe_name, possibilities=possible_pathnames)
    else:
        exe_exists, exe_pathname_ = os.path.exists(exe_pathname), copy.copy(exe_pathname)

    return exe_exists, exe_pathname_


def _set_index(df, index=None):
    """
    Set index of a dataframe.

    :param df: any dataframe
    :type df: pandas.DataFrame
    :param index: column index or a list of column indices, defaults to ``None``;
        when ``index=None``, set the first column to be the index if the column name is an empty string
    :type index: int or list or None
    :return: an updated dataframe
    :rtype: pandas.DataFrame

    **Tests**::

        >>> from pyhelpers.store import _set_index
        >>> from pyhelpers._cache import example_dataframe

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

        >>> example_df_ = _set_index(example_df, index=0)
        >>> example_df_
                    Latitude
        Longitude
        -0.127647  51.507322
        -1.902691  52.479699
        -2.245115  53.479489
        -1.543794  53.797418

        >>> example_df.iloc[:, 0].to_list() == example_df_.index.to_list()
        True
    """

    data = df.copy()

    if index is None:
        idx_col = df.columns[0]
        if idx_col == '':
            data = df.set_index(idx_col)
            data.index.name = None

    else:
        idx_keys_ = [index] if isinstance(index, (int, list)) else copy.copy(index)
        idx_keys = [df.columns[x] if isinstance(x, int) else x for x in idx_keys_]
        data = df.set_index(keys=idx_keys)

    return data


# ==================================================================================================
# Save data
# ==================================================================================================


# Pickle files

def save_pickle(pickle_data, path_to_pickle, verbose=False, **kwargs):
    """
    Save data to a `Pickle <https://docs.python.org/3/library/pickle.html>`_ file.

    :param pickle_data: data that could be dumped by the built-in module `pickle.dump`_
    :type pickle_data: any
    :param path_to_pickle: path where a pickle file is saved
    :type path_to_pickle: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pickle.dump`_

    .. _`pickle.dump`: https://docs.python.org/3/library/pickle.html#pickle.dump

    **Examples**::

        >>> from pyhelpers.store import save_pickle
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe

        >>> pickle_dat = 1

        >>> pickle_pathname = cd("tests\\data", "dat.pickle")
        >>> save_pickle(pickle_dat, pickle_pathname, verbose=True)
        Saving "dat.pickle" to "tests\\data\\" ... Done.

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
        Updating "dat.pickle" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_pickle`.
    """

    _check_path_to_file(path_to_pickle, verbose=verbose, ret_info=False)

    try:
        pickle_out = open(path_to_pickle, mode='wb')
        pickle.dump(pickle_data, pickle_out, **kwargs)
        pickle_out.close()

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")


# Spreadsheets

def save_spreadsheet(spreadsheet_data, path_to_spreadsheet, index=False, engine=None, delimiter=',',
                     verbose=False, **kwargs):
    """
    Save data to a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ or
    an `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`_ file.

    The file extension can be `".txt"`, `".csv"`, `".xlsx"` or `".xls"`;
    engines can include: `xlsxwriter`_ (for .xlsx) and `openpyxl`_ (for .xlsx/.xlsm).

    :param spreadsheet_data: data that could be saved as a spreadsheet
        (e.g. with a file extension ".xlsx" or ".csv")
    :type spreadsheet_data: pandas.DataFrame
    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str] or None
    :param index: whether to include the index as a column, defaults to ``False``
    :type index: bool
    :param engine: options include ``'openpyxl'`` for latest Excel file formats,
        ``'xlrd'`` for .xls ``'odf'`` for OpenDocument file formats (.odf, .ods, .odt), and
        ``'pyxlsb'`` for Binary Excel files; defaults to ``None``
    :type engine: str or None
    :param delimiter: separator for saving a `".xlsx"` (or `".xls"`) file as a `".csv"` file,
        defaults to ``','``
    :type delimiter: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_excel`_ or `pandas.DataFrame.to_csv`_

    .. _`xlsxwriter`: https://pypi.org/project/XlsxWriter/
    .. _`openpyxl`: https://pypi.org/project/openpyxl/
    .. _`pandas.DataFrame.to_excel`:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
    .. _`pandas.DataFrame.to_csv`:
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

        >>> spreadsheet_pathname = cd("tests\\data", "dat.csv")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.csv" to "tests\\data\\" ... Done.

        >>> spreadsheet_pathname = cd("tests\\data", "dat.xlsx")
        >>> save_spreadsheet(spreadsheet_dat, spreadsheet_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ... Done.
    """

    _, spreadsheet_filename = _check_path_to_file(
        path_to_file=path_to_spreadsheet, verbose=verbose, ret_info=True)

    try:  # to save the data
        if spreadsheet_filename.endswith(".xlsx"):  # a .xlsx file
            spreadsheet_data.to_excel(
                excel_writer=path_to_spreadsheet, index=index, engine=engine, **kwargs)

        elif spreadsheet_filename.endswith(".xls"):  # a .xls file
            if engine is None or engine == 'xlwt':
                engine = 'openpyxl'
            spreadsheet_data.to_excel(
                excel_writer=path_to_spreadsheet, index=index, engine=engine, **kwargs)

        elif spreadsheet_filename.endswith((".csv", ".txt")):  # a .csv file
            spreadsheet_data.to_csv(
                path_or_buf=path_to_spreadsheet, index=index, sep=delimiter, **kwargs)

        else:
            raise AssertionError('File extension must be ".txt", ".csv", ".xlsx" or ".xls"')

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e.args[0]}")


def save_spreadsheets(spreadsheets_data, path_to_spreadsheet, sheet_names, mode='w',
                      if_sheet_exists=None, verbose=False, **kwargs):
    """
    Save data to a multi-sheet `Microsoft Excel`_ file.

    The file extension can be `".xlsx"` or `".xls"`.

    :param spreadsheets_data: a sequence of pandas.DataFrame
    :type spreadsheets_data: list or tuple or iterable
    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str]
    :param sheet_names: all sheet names of an Excel workbook
    :type sheet_names: list or tuple or iterable
    :param mode: mode to write to an Excel file; ``'w'`` (default) for 'write' and ``'a'`` for 'append'
    :type mode: str
    :param if_sheet_exists: indicate the behaviour when trying to write to an existing sheet;
        see also the parameter ``if_sheet_exists`` of `pandas.ExcelWriter`_
    :type if_sheet_exists: None or str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_excel`_

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`pandas.ExcelWriter`:
        https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    .. _`pandas.DataFrame.to_excel`:
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
        >>> pathname = cd("tests\\data", "dat.xlsx")

        >>> save_spreadsheets(dat, pathname, sheets, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, mode='a', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet11' ... Done.
            'TestSheet2' ... This sheet already exists; [pass]|new|replace: new
                saved as 'TestSheet21' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='replace', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... Done.
            'TestSheet2' ... Done.

        >>> save_spreadsheets(dat, pathname, sheets, 'a', if_sheet_exists='new', verbose=True)
        Updating "dat.xlsx" at "tests\\data\\" ...
            'TestSheet1' ... saved as 'TestSheet12' ... Done.
            'TestSheet2' ... saved as 'TestSheet22' ... Done.
    """

    assert path_to_spreadsheet.endswith((".xlsx", ".xls"))

    _check_path_to_file(path_to_spreadsheet, verbose=verbose, ret_info=False)

    if os.path.isfile(path_to_spreadsheet) and mode == 'a':
        with pd.ExcelFile(path_or_buffer=path_to_spreadsheet) as f:
            cur_sheet_names = f.sheet_names
    else:
        cur_sheet_names = []

    engine = 'openpyxl' if mode == 'a' else None
    writer = pd.ExcelWriter(path=path_to_spreadsheet, engine=engine, mode=mode)

    if verbose:
        print("")

    for sheet_data, sheet_name in zip(spreadsheets_data, sheet_names):
        # sheet_data, sheet_name = spreadsheets_data[0], sheet_names[0]
        if verbose:
            print("\t'{}'".format(sheet_name), end=" ... ")

        if sheet_name in cur_sheet_names:
            if if_sheet_exists is None:
                if_sheet_exists_ = input("This sheet already exists; [pass]|new|replace: ")
            else:
                assert if_sheet_exists in {'error', 'new', 'replace', 'overlay'}
                if_sheet_exists_ = copy.copy(if_sheet_exists)

            if if_sheet_exists_ != 'pass':
                writer._if_sheet_exists = if_sheet_exists_

        try:
            sheet_data.to_excel(excel_writer=writer, sheet_name=sheet_name, **kwargs)

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
            print(f"Failed. {e}")

    writer.close()


# JSON files

def save_json(json_data, path_to_json, engine=None, verbose=False, **kwargs):
    """
    Save data to a `JSON <https://www.json.org/json-en.html>`_ file.

    :param json_data: data that could be dumped by as a JSON file
    :type json_data: any json data
    :param path_to_json: path where a json file is saved
    :type path_to_json: str or os.PathLike[str]
    :param engine: an open-source module used for JSON serialization, options include
        ``None`` (default, for the built-in `json module`_), ``'ujson'`` (for `UltraJSON`_),
        ``'orjson'`` (for `orjson`_) and ``'rapidjson'`` (for `python-rapidjson`_)
    :type engine: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `json.dump()`_ (if ``engine=None``),
        `orjson.dumps()`_ (if ``engine='orjson'``), `ujson.dump()`_ (if ``engine='ujson'``) or
        `rapidjson.dump()`_ (if ``engine='rapidjson'``)

    .. _`json module`: https://docs.python.org/3/library/json.html
    .. _`UltraJSON`: https://pypi.org/project/ujson/
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`orjson.dumps()`: https://github.com/ijl/orjson#serialize
    .. _`ujson.dump()`: https://github.com/ultrajson/ultrajson#encoder-options
    .. _`rapidjson.dump()`: https://python-rapidjson.readthedocs.io/en/latest/dump.html
    .. _`json.dump()`: https://docs.python.org/3/library/json.html#json.dump

    **Examples**::

        >>> from pyhelpers.store import save_json
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import json

        >>> json_pathname = cd("tests\\data", "dat.json")

        >>> json_dat = {'a': 1, 'b': 2, 'c': 3, 'd': ['a', 'b', 'c']}
        >>> save_json(json_dat, json_pathname, indent=4, verbose=True)
        Saving "dat.json" to "tests\\data\\" ... Done.

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
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='orjson', verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='ujson', indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

        >>> save_json(json_dat, json_pathname, engine='rapidjson', indent=4, verbose=True)
        Updating "dat.json" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_json`.
    """

    if engine is not None:
        valid_engines = {'ujson', 'orjson', 'rapidjson'}
        assert engine in valid_engines, f"`engine` must be on one of {valid_engines}"
        mod = _check_dependency(name=engine)
    else:
        mod = sys.modules.get('json')

    _check_path_to_file(path_to_json, verbose=verbose, ret_info=False)

    try:
        if engine == 'orjson':
            with open(path_to_json, mode='wb') as json_out:
                json_out.write(mod.dumps(json_data, **kwargs))

        else:
            with open(path_to_json, mode='w') as json_out:
                mod.dump(json_data, json_out, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")


# Joblib

def save_joblib(joblib_data, path_to_joblib, verbose=False, **kwargs):
    """
    Save data to a `Joblib <https://pypi.org/project/joblib/>`_ file.

    :param joblib_data: data that could be dumped by `joblib.dump`_
    :type joblib_data: any
    :param path_to_joblib: path where a pickle file is saved
    :type path_to_joblib: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `joblib.dump`_

    .. _`joblib.dump`: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html

    **Examples**::

        >>> from pyhelpers.store import save_joblib
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers._cache import example_dataframe
        >>> import numpy as np

        >>> joblib_pathname = cd("tests\\data", "dat.joblib")

        >>> # Example 1:
        >>> joblib_dat = example_dataframe().to_numpy()
        >>> joblib_dat
        array([[-0.1276474, 51.5073219],
               [-1.9026911, 52.4796992],
               [-2.2451148, 53.4794892],
               [-1.5437941, 53.7974185]])

        >>> save_joblib(joblib_dat, joblib_pathname, verbose=True)
        Saving "dat.joblib" to "tests\\data\\" ... Done.

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
        Updating "dat.joblib" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_joblib`.
    """

    _check_path_to_file(path_to_joblib, verbose=verbose, ret_info=False)

    try:
        joblib_ = _check_dependency(name='joblib')

        joblib_.dump(value=joblib_data, filename=path_to_joblib, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")


# Feather files

def save_feather(feather_data, path_to_feather, index=False, verbose=False, **kwargs):
    """
    Save a dataframe to a `Feather <https://arrow.apache.org/docs/python/feather.html>`_ file.

    :param feather_data: a dataframe to be saved as a feather-formatted file
    :type feather_data: pandas.DataFrame
    :param path_to_feather: path where a feather file is saved
    :type path_to_feather: str or os.PathLike[str]
    :param index: whether to include the index as a column, defaults to ``False``
    :type index: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.DataFrame.to_feather`_

    .. _`pandas.DataFrame.to_feather`:
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
        Saving "dat.feather" to "tests\\data\\" ... Done.

        >>> save_feather(feather_dat, feather_pathname, index=True, verbose=True)
        Updating "dat.feather" at "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_feather`.
    """

    assert isinstance(feather_data, pd.DataFrame)

    _check_path_to_file(path_to_feather, verbose=verbose, ret_info=False)

    try:
        if list(feather_data.index) != range(len(feather_data)) or index is True:
            feather_data.reset_index().to_feather(path_to_feather, **kwargs)
        else:
            feather_data.to_feather(path_to_feather, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")


# Images

def save_svg_as_emf(path_to_svg, path_to_emf, verbose=False, inkscape_exe=None, **kwargs):
    """
    Save a `SVG <https://en.wikipedia.org/wiki/Scalable_Vector_Graphics>`_ file (.svg) as
    a `EMF <https://en.wikipedia.org/wiki/Windows_Metafile#EMF>`_ file (.emf).

    :param path_to_svg: path where a .svg file is saved
    :type path_to_svg: str
    :param path_to_emf: path where a .emf file is saved
    :type path_to_emf: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param inkscape_exe: absolute path to 'inkscape.exe', defaults to ``None``;
        when ``inkscape_exe=None``, use the default installation path, e.g. (on Windows)
        "*C:\\\\Program Files\\\\Inkscape\\\\bin\\\\inkscape.exe*"
        or "*C:\\\\Program Files\\\\Inkscape\\\\inkscape.exe*"
    :type inkscape_exe: str or None
    :param kwargs: [optional] parameters of `subprocess.run`_

    .. _`subprocess.run`:
        https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import save_svg_as_emf
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`store-save_fig-demo-1`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-1
        :align: center
        :width: 75%

        An example figure created for the function :py:func:`~pyhelpers.store.save_svg_as_emf`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> plt.savefig(svg_file_pathname)  # Save the figure as a .svg file

        >>> emf_file_pathname = cd(img_dir, "store-save_fig-demo.emf")
        >>> save_svg_as_emf(svg_file_pathname, emf_file_pathname, verbose=True)
        Saving the .svg file as "tests\\images\\store-save_fig-demo.emf" ... Done.

        >>> plt.close()
    """

    exe_name = "inkscape.exe"
    possible_exe_pathnames = {
        exe_name,
        f"C:\\Program Files\\Inkscape\\{exe_name}",
        f"C:\\Program Files\\Inkscape\\bin\\{exe_name}",
    }
    inkscape_exists, inkscape_exe_ = _check_exe_pathname(exe_name, inkscape_exe, possible_exe_pathnames)

    abs_svg_path, abs_emf_path = map(pathlib.Path, (path_to_svg, path_to_emf))
    assert abs_svg_path.suffix.lower() == ".svg"

    if inkscape_exists:
        # if verbose:
        #     if abs_emf_path.exists():
        #         msg = f"Updating \"{abs_emf_path.name}\" at " \
        #               f"\"{os.path.relpath(abs_emf_path.parent)}\\\""
        #     else:
        #         msg = f"Saving the {abs_svg_path.suffix} file as \"{os.path.relpath(abs_emf_path)}\""
        #     print(msg, end=" ... ")
        _check_path_to_file(abs_emf_path, verbose=verbose)

        try:
            abs_emf_path.parent.mkdir(exist_ok=True)

            command_args = [inkscape_exe_, '-z', path_to_svg, '-M', path_to_emf]
            rslt = subprocess.run(command_args, **kwargs)
            ret_code = rslt.returncode

            if ret_code != 0:
                command_args = [inkscape_exe_, '-z', path_to_svg, '--export-filename', path_to_emf]
                rslt = subprocess.run(command_args, **kwargs)
                ret_code = rslt.returncode

            if verbose:
                if ret_code == 0:
                    print("Done.")
                else:
                    print("Failed.", end=" ")

        except Exception as e:
            print(e)

    else:
        if verbose:
            print(
                "\"Inkscape\" (https://inkscape.org) is required to convert a SVG file to an EMF file;"
                " however, it is not found on this device.\nInstall it and then try again.")


def save_fig(path_to_fig_file, dpi=None, verbose=False, conv_svg_to_emf=False, **kwargs):
    """
    Save a figure object to a file of a supported file format.

    This function relies on `matplotlib.pyplot.savefig`_ (and `Inkscape`_).

    :param path_to_fig_file: path where a figure file is saved
    :type path_to_fig_file: str or os.PathLike[str]
    :param dpi: the resolution in dots per inch; if ``None`` (default), use ``rcParams['savefig.dpi']``
    :type dpi: int or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param conv_svg_to_emf: whether to convert a .svg file to a .emf file, defaults to ``False``
    :type conv_svg_to_emf: bool
    :param kwargs: [optional] parameters of `matplotlib.pyplot.savefig`_

    .. _`matplotlib.pyplot.savefig`:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
    .. _`Inkscape`: https://inkscape.org

    **Examples**::

        >>> from pyhelpers.store import save_fig
        >>> from pyhelpers.dirs import cd
        >>> from pyhelpers.settings import mpl_preferences
        >>> import matplotlib.pyplot as plt

        >>> mpl_preferences()

        >>> x, y = (1, 1), (2, 2)

        >>> plt.figure()
        >>> plt.plot([x[0], y[0]], [x[1], y[1]])
        >>> plt.show()

    The above exmaple is illustrated in :numref:`store-save_fig-demo-2`:

    .. figure:: ../_images/store-save_fig-demo.*
        :name: store-save_fig-demo-2
        :align: center
        :width: 75%

        An example figure created for the function :py:func:`~pyhelpers.store.save_fig`.

    .. code-block:: python

        >>> img_dir = cd("tests\\images")

        >>> png_file_pathname = cd(img_dir, "store-save_fig-demo.png")
        >>> save_fig(png_file_pathname, dpi=600, verbose=True)
        Saving "store-save_fig-demo.png" to "tests\\images\\" ... Done.

        >>> svg_file_pathname = cd(img_dir, "store-save_fig-demo.svg")
        >>> save_fig(svg_file_pathname, dpi=600, verbose=True, conv_svg_to_emf=True)
        Saving "store-save_fig-demo.svg" to "tests\\images\\" ... Done.
        Saving the .svg file as "tests\\images\\store-save_fig-demo.emf" ... Done.

        >>> plt.close()
    """

    _check_path_to_file(path_to_fig_file, verbose=verbose, ret_info=False)

    file_ext = pathlib.Path(path_to_fig_file).suffix

    try:
        mpl_plt = _check_dependency(name='matplotlib.pyplot')

        mpl_plt.savefig(path_to_fig_file, dpi=dpi, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")

    if file_ext == ".svg" and conv_svg_to_emf:
        save_svg_as_emf(path_to_fig_file, path_to_fig_file.replace(file_ext, ".emf"), verbose=verbose)


# Web page

def save_web_page_as_pdf(web_page, path_to_pdf, page_size='A4', zoom=1.0, encoding='UTF-8',
                         verbose=False, wkhtmltopdf_exe=None, **kwargs):
    """
    Save a web page as a `PDF <https://en.wikipedia.org/wiki/PDF>`_ file
    by `wkhtmltopdf <https://wkhtmltopdf.org/>`_.

    :param web_page: URL of a web page or pathname of an HTML file
    :type web_page: str
    :param path_to_pdf: path where a .pdf is saved
    :type path_to_pdf: str
    :param page_size: page size, defaults to ``'A4'``
    :type page_size: str
    :param zoom: a parameter to zoom in/out, defaults to ``1.0``
    :type zoom: float
    :param encoding: encoding format defaults to ``'UTF-8'``
    :type encoding: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool
    :param wkhtmltopdf_exe: absolute path to 'wkhtmltopdf.exe', defaults to ``None``;
        when ``wkhtmltopdf_exe=None``, use the default installation path, e.g. (on Windows)
        "*C:\\\\Program Files\\\\wkhtmltopdf\\\\bin\\\\wkhtmltopdf.exe*"

    :type wkhtmltopdf_exe: str or None
    :param kwargs: [optional] parameters of `pdfkit.from_url <https://pypi.org/project/pdfkit/>`_

    **Examples**::

        >>> from pyhelpers.store import save_web_page_as_pdf
        >>> from pyhelpers.dirs import cd
        >>> import subprocess

        >>> pdf_pathname = cd("tests\\documents", "pyhelpers.pdf")

        >>> web_page_url = 'https://pyhelpers.readthedocs.io/en/latest/'
        >>> save_web_page_as_pdf(web_page_url, pdf_pathname)

        >>> # Open the PDF file using the system's default application
        >>> subprocess.Popen(pdf_pathname, shell=True)

        >>> web_page_file = cd("docs\\build\\html\\index.html")
        >>> save_web_page_as_pdf(web_page_file, pdf_pathname, verbose=True)
        Updating "pyhelpers.pdf" at "tests\\documents\\" ...
        Loading pages (1/6)
        Counting pages (2/6)
        Resolving links (4/6)
        Loading headers and footers (5/6)
        Printing pages (6/6)
        Done
        >>> subprocess.Popen(pdf_pathname, shell=True)
    """

    exe_name = "wkhtmltopdf.exe"
    possible_exe_pathnames = {exe_name, f"C:\\Program Files\\wkhtmltopdf\\bin\\{exe_name}"}
    wkhtmltopdf_exists, wkhtmltopdf_exe_ = _check_exe_pathname(
        exe_name, exe_pathname=wkhtmltopdf_exe, possible_pathnames=possible_exe_pathnames)

    if wkhtmltopdf_exists:
        pdfkit_ = _check_dependency(name='pdfkit')

        pdfkit_configuration = pdfkit_.configuration(wkhtmltopdf=wkhtmltopdf_exe_)

        try:
            _check_path_to_file(
                path_to_file=path_to_pdf, verbose=verbose, verbose_end=" ... \n", ret_info=False)

            wkhtmltopdf_options = {
                'enable-local-file-access': None,
                'page-size': page_size,
                'zoom': str(float(zoom)),
                'encoding': encoding,
                # 'margin-top': '0',
                # 'margin-right': '0',
                # 'margin-left': '0',
                # 'margin-bottom': '0',
            }

            os.makedirs(os.path.dirname(path_to_pdf), exist_ok=True)

            if os.path.isfile(path_to_pdf):
                os.remove(path_to_pdf)

            kwargs.update({'configuration': pdfkit_configuration, 'options': wkhtmltopdf_options})

            if os.path.isfile(web_page):
                status = pdfkit_.from_file(web_page, path_to_pdf, verbose=verbose, **kwargs)
            elif is_url(web_page):
                status = pdfkit_.from_url(web_page, path_to_pdf, verbose=verbose, **kwargs)
            else:
                status = None

            if verbose and not status:
                print("Failed. Check if the URL is available.")

        except Exception as e:
            print(f"Failed. {e}")

    else:
        print("\"wkhtmltopdf\" (https://wkhtmltopdf.org/) is required to run this function; "
              "however, it is not found on this device.\nInstall it and then try again.")


# A comprehensive function

def save_data(data, path_to_file, err_warning=True, confirmation_required=True, **kwargs):
    """
    Save data to a file of a specific format.

    :param data: data that could be saved to
        a file of `Pickle`_, `CSV`_, `Microsoft Excel`_, `JSON`_, `Joblib`_ or `Feather`_ format;
        a URL of a web page or an `HTML file`_; or an image file of a `Matplotlib`-supported format
    :type data: any
    :param path_to_file: pathname of a file that stores the ``data``
    :type path_to_file: str or os.PathLike[str]
    :param err_warning: whether to show a warning message if any unknown error occurs,
        defaults to ``True``
    :type err_warning: bool
    :param confirmation_required: whether to require users to confirm and proceed, defaults to ``True``
    :type confirmation_required: bool
    :param kwargs: [optional] parameters of one of the following functions:
        :py:func:`~pyhelpers.store.save_pickle`,
        :py:func:`~pyhelpers.store.save_spreadsheet`,
        :py:func:`~pyhelpers.store.save_json`,
        :py:func:`~pyhelpers.store.save_joblib`,
        :py:func:`~pyhelpers.store.save_feather`,
        :py:func:`~pyhelpers.store.save_fig` or
        :py:func:`~pyhelpers.store.save_web_page_as_pdf`

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

        >>> data_dir = cd("tests\\data")

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
        Saving "dat.pickle" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.csv")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.csv" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.xlsx")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.xlsx" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.txt")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.txt" to "tests\\data\\" ... Done.

        >>> dat_pathname = cd(data_dir, "dat.feather")
        >>> save_data(dat, dat_pathname, index=True, verbose=True)
        Saving "dat.feather" to "tests\\data\\" ... Done.

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
        Saving "dat.json" to "tests\\data\\" ... Done.

    .. seealso::

        - Examples for the function :py:func:`pyhelpers.store.load_data`.
    """

    path_to_file_ = path_to_file.lower()

    if path_to_file_.endswith((".pkl", ".pickle")):
        save_pickle(data, path_to_pickle=path_to_file, **kwargs)

    elif path_to_file_.endswith((".csv", ".xlsx", ".xls", ".txt")):
        save_spreadsheet(data, path_to_spreadsheet=path_to_file, **kwargs)

    elif path_to_file_.endswith(".json"):
        save_json(data, path_to_json=path_to_file, **kwargs)

    elif path_to_file_.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        save_joblib(data, path_to_joblib=path_to_file, **kwargs)

    elif path_to_file_.endswith((".fea", ".feather")):
        save_feather(data, path_to_feather=path_to_file, **kwargs)

    elif path_to_file_.endswith(".pdf"):
        if is_url(data) or os.path.isfile(data):
            save_web_page_as_pdf(data, path_to_pdf=path_to_file_, **kwargs)

    elif path_to_file_.endswith(
            ('.eps', '.jpeg', '.jpg', '.pdf', '.pgf', '.png', '.ps',
             '.raw', '.rgba', '.svg', '.svgz', '.tif', '.tiff')):
        save_fig(path_to_fig_file=path_to_file, **kwargs)

    else:
        if err_warning:
            warnings.warn(
                "The specified file format (extension) is not recognisable by "
                "`pyhelpers.store.save_data`.")

        if confirmed("To save the data as a pickle file\n?", confirmation_required):
            save_pickle(data, path_to_pickle=path_to_file, **kwargs)


# ==================================================================================================
# Load data
# ==================================================================================================


def load_pickle(path_to_pickle, verbose=False, **kwargs):
    """
    Load data from a `Pickle`_ file.

    :param path_to_pickle: path where a pickle file is saved
    :type path_to_pickle: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pickle.load`_
    :return: data retrieved from the specified path ``path_to_pickle``
    :rtype: any

    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`pickle.load`: https://docs.python.org/3/library/pickle.html#pickle.load

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_pickle`.

    **Examples**::

        >>> from pyhelpers.store import load_pickle
        >>> from pyhelpers.dirs import cd

        >>> pickle_pathname = cd("tests\\data", "dat.pickle")
        >>> pickle_dat = load_pickle(pickle_pathname, verbose=True)
        Loading "tests\\data\\dat.pickle" ... Done.
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    _check_loading_path(path_to_file=path_to_pickle, verbose=verbose)

    try:
        with open(file=path_to_pickle, mode='rb') as pickle_in:
            pickle_data = pickle.load(pickle_in, **kwargs)

        if verbose:
            print("Done.")

        return pickle_data

    except Exception as e:
        print(f"Failed. {e}")


def load_csv(path_to_csv, delimiter=',', header=0, index=None, verbose=False, **kwargs):
    """
    Load data from a `CSV`_ file.

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values

    :param path_to_csv: path where a `CSV`_ file is saved
    :type path_to_csv: str or os.PathLike[str]
    :param delimiter: delimiter used between values in the data file, defaults to ``','``
    :type delimiter: str
    :param header: index number of the rows used as column names, defaults to ``0``
    :type header: int or typing.List[int] or None
    :param index: index number of the column(s) to use as the row labels of the dataframe,
        defaults to ``None``
    :type index: str or int or list or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `csv.reader()`_ or `pandas.read_csv()`_
    :return: data retrieved from the specified path ``path_to_csv``
    :rtype: pandas.DataFrame or None

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`csv.reader()`: https://docs.python.org/3/library/pickle.html#pickle.load
    .. _`pandas.read_csv()`: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_spreadsheet`.

    **Examples**::

        >>> from pyhelpers.store import load_csv
        >>> from pyhelpers.dirs import cd

        >>> csv_pathname = cd("tests\\data", "dat.csv")
        >>> csv_dat = load_csv(csv_pathname, index=0, verbose=True)
        Loading "tests\\data\\dat.csv" ... Done.
        >>> csv_dat
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185

        >>> csv_pathname = cd("tests\\data", "dat.txt")
        >>> csv_dat = load_csv(csv_pathname, index=0, verbose=True)
        Loading "tests\\data\\dat.txt" ... Done.
        >>> csv_dat
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185

        >>> csv_dat = load_csv(csv_pathname, header=[0, 1], verbose=True)
        Loading "tests\\data\\dat.txt" ... Done.
        >>> csv_dat
                 City Easting Northing
               London  530034   180381
        0  Birmingham  406689   286822
        1  Manchester  383819   398052
        2       Leeds  582044   152953
    """

    _check_loading_path(path_to_file=path_to_csv, verbose=verbose)

    try:
        with open(path_to_csv, mode='r') as csv_file:
            csv_data_ = csv.reader(csv_file, delimiter=delimiter, **kwargs)
            csv_rows = [row for row in csv_data_]

        if header is not None:
            col_names = operator.itemgetter(*[header] if isinstance(header, int) else header)(csv_rows)
            dat = [x for x in csv_rows if (x not in col_names and x != col_names)]
            csv_data = pd.DataFrame(data=dat, columns=list(col_names))
        else:
            csv_data = pd.DataFrame(csv_rows)

        csv_data = _set_index(csv_data, index=index)

        if verbose:
            print("Done.")

        return csv_data

    except TypeError:
        csv_data = pd.read_csv(path_to_csv, index_col=index, **kwargs)

        return csv_data

    except Exception as e:
        print(f"Failed. {e}")


def load_spreadsheets(path_to_spreadsheet, as_dict=True, verbose=False, **kwargs):
    """
    Load multiple sheets of an `Microsoft Excel`_ file.

    :param path_to_spreadsheet: path where a spreadsheet is saved
    :type path_to_spreadsheet: str or os.PathLike[str]
    :param as_dict: whether to return the retrieved data as a dictionary type, defaults to ``True``
    :type as_dict: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.ExcelFile.parse`_
    :return: all worksheet in an Excel workbook from the specified file path ``path_to_spreadsheet``
    :rtype: list or dict

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`pandas.ExcelFile.parse`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelFile.parse.html

    .. note::

        - Example data can be referred to the functions
          :py:func:`pyhelpers.store.save_multiple_spreadsheets` and
          :py:func:`pyhelpers.store.save_spreadsheet`.

    **Examples**::

        >>> from pyhelpers.store import load_spreadsheets
        >>> from pyhelpers.dirs import cd

        >>> dat_dir = cd("tests\\data")
        >>> path_to_xlsx = cd(dat_dir, "dat.xlsx")

        >>> wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        Loading "tests\\data\\dat.xlsx" ...
            'TestSheet1'. ... Done.
            'TestSheet2'. ... Done.
            'TestSheet11'. ... Done.
            'TestSheet21'. ... Done.
        >>> list(wb_data.keys())
        ['TestSheet1', 'TestSheet2', 'TestSheet11', 'TestSheet21']

        >>> wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        >>> type(wb_data)
        list
        >>> len(wb_data)
        4
        >>> wb_data[0]
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    _check_loading_path(path_to_file=path_to_spreadsheet, verbose=verbose, verbose_end=" ... \n")

    excel_file_reader = pd.ExcelFile(path_to_spreadsheet)

    sheet_names = excel_file_reader.sheet_names
    workbook_dat = []

    for sheet_name in sheet_names:
        if verbose:
            print("\t'{}'.".format(sheet_name), end=" ... ")

        try:
            sheet_dat = excel_file_reader.parse(sheet_name, **kwargs)
            if verbose:
                print("Done.")

        except Exception as e:
            sheet_dat = None
            print(f"Failed. {e}")

        workbook_dat.append(sheet_dat)

    excel_file_reader.close()

    if as_dict:
        workbook_data = dict(zip(sheet_names, workbook_dat))
    else:
        workbook_data = workbook_dat

    return workbook_data


def load_json(path_to_json, engine=None, verbose=False, **kwargs):
    """
    Load data from a `JSON`_ file.

    :param path_to_json: path where a json file is saved
    :type path_to_json: str or os.PathLike[str]
    :param engine: an open-source Python package for JSON serialization, options include
        ``None`` (default, for the built-in `json module`_), ``'ujson'`` (for `UltraJSON`_),
        ``'orjson'`` (for `orjson`_) and ``'rapidjson'`` (for `python-rapidjson`_)
    :type engine: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `json.load()`_ (if ``engine=None``),
        `orjson.loads()`_ (if ``engine='orjson'``), `ujson.load()`_ (if ``engine='ujson'``) or
        `rapidjson.load()`_ (if ``engine='rapidjson'``)
    :return: data retrieved from the specified path ``path_to_json``
    :rtype: dict

    .. _`JSON`: https://www.json.org/json-en.html
    .. _`json module`: https://docs.python.org/3/library/json.html
    .. _`UltraJSON`: https://pypi.org/project/ujson/
    .. _`orjson`: https://pypi.org/project/orjson/
    .. _`python-rapidjson`: https://pypi.org/project/python-rapidjson
    .. _`orjson.loads()`: https://github.com/ijl/orjson#deserialize
    .. _`ujson.load()`: https://github.com/ultrajson/ultrajson/blob/main/python/JSONtoObj.c
    .. _`rapidjson.load()`: https://docs.python.org/3/library/functions.html#open
    .. _`json.load()`: https://docs.python.org/3/library/json.html#json.load

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_json`.

    **Examples**::

        >>> from pyhelpers.store import load_json
        >>> from pyhelpers.dirs import cd

        >>> json_path = cd("tests\\data", "dat.json")
        >>> json_dat = load_json(json_path, verbose=True)
        Loading "tests\\data\\dat.json" ... Done.
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}
    """

    if engine is not None:
        valid_engines = {'ujson', 'orjson', 'rapidjson'}
        assert engine in valid_engines, f"`engine` must be on one of {valid_engines}"
        mod = _check_dependency(name=engine)
    else:
        mod = sys.modules.get('json')

    _check_loading_path(path_to_file=path_to_json, verbose=verbose)

    try:
        if engine == 'orjson':
            with open(path_to_json, mode='rb') as json_in:
                json_data = mod.loads(json_in.read(), **kwargs)

        else:
            with open(path_to_json, mode='r') as json_in:
                json_data = mod.load(json_in, **kwargs)

        if verbose:
            print("Done.")

        return json_data

    except Exception as e:
        print(f"Failed. {e}")


def load_joblib(path_to_joblib, verbose=False, **kwargs):
    """
    Load data from a `joblib`_ file.

    :param path_to_joblib: path where a joblib file is saved
    :type path_to_joblib: str or os.PathLike[str]
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `joblib.load`_
    :return: data retrieved from the specified path ``path_to_joblib``
    :rtype: any

    .. _`joblib`: https://pypi.org/project/joblib/
    .. _`joblib.load`: https://joblib.readthedocs.io/en/latest/generated/joblib.load.html

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_joblib`.

    **Examples**::

        >>> from pyhelpers.store import load_joblib
        >>> from pyhelpers.dirs import cd

        >>> joblib_pathname = cd("tests\\data", "dat.joblib")
        >>> joblib_dat = load_joblib(joblib_pathname, verbose=True)
        Loading "tests\\data\\dat.joblib" ... Done.
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
    """

    joblib_ = _check_dependency(name='joblib')

    _check_loading_path(path_to_file=path_to_joblib, verbose=verbose)

    try:
        joblib_data = joblib_.load(filename=path_to_joblib, **kwargs)

        if verbose:
            print("Done.")

        return joblib_data

    except Exception as e:
        print(f"Failed. {e}")


def load_feather(path_to_feather, verbose=False, index=None, **kwargs):
    """
    Load a dataframe from a `Feather`_ file.

    :param path_to_feather: path where a feather file is saved
    :type path_to_feather: str or os.PathLike[str]
    :param index: index number of the column(s) to use as the row labels of the dataframe,
        defaults to ``None``
    :type index: str or int or list or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `pandas.read_feather`_

        * columns: a sequence of column names, if ``None``, all columns
        * use_threads: whether to parallelize reading using multiple threads, defaults to ``True``

    :return: data retrieved from the specified path ``path_to_feather``
    :rtype: pandas.DataFrame

    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`pandas.read_feather`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_feather.html

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_feather`.

    **Examples**::

        >>> from pyhelpers.store import load_feather
        >>> from pyhelpers.dirs import cd

        >>> feather_path = cd("tests\\data", "dat.feather")
        >>> feather_dat = load_feather(feather_path, index=0, verbose=True)
        Loading "tests\\data\\dat.feather" ... Done.
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    _check_loading_path(path_to_file=path_to_feather, verbose=verbose)

    try:
        feather_data = pd.read_feather(path_to_feather, **kwargs)

        feather_data = _set_index(feather_data, index=index)

        # if isinstance(feather_data, pd.DataFrame):
        #     col_0 = feather_data.columns[0]
        #
        #     if col_0.startswith('level_') and all(feather_data[col_0] == range(feather_data.shape[0])):
        #         del feather_data[col_0]
        #
        #     if feather_data.columns[0] == 'index':
        #         feather_data.set_index('index', inplace=True)
        #         # feather_data = feather_data.rename_axis(None, axis=1)
        #         feather_data.index.name = None

        if verbose:
            print("Done.")

        return feather_data

    except Exception as e:
        print(f"Failed. {e}")


def load_data(path_to_file, err_warning=True, **kwargs):
    """
    Load data from a file.

    :param path_to_file: pathname of a file;
        supported file formats include
        `Pickle`_, `CSV`_, `Microsoft Excel`_ spreadsheet, `JSON`_, `Joblib`_ and `Feather`_
    :type path_to_file: str or os.PathLike[str]
    :param err_warning: whether to show a warning message if any unknown error occurs, 
        defaults to ``True``
    :type err_warning: bool
    :param kwargs: [optional] parameters of one of the following functions:
        :py:func:`~pyhelpers.store.load_pickle`,
        :py:func:`~pyhelpers.store.load_csv`,
        :py:func:`~pyhelpers.store.load_multiple_spreadsheets`,
        :py:func:`~pyhelpers.store.load_json`,
        :py:func:`~pyhelpers.store.load_joblib` or
        :py:func:`~pyhelpers.store.load_feather`
    :return: loaded data
    :rtype: any

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html

    .. note::

        - Example data can be referred to the function :py:func:`pyhelpers.store.save_data`.

    **Examples**::

        >>> from pyhelpers.store import load_data
        >>> from pyhelpers.dirs import cd

        >>> data_dir = cd("tests\\data")

        >>> dat_pathname = cd(data_dir, "dat.pickle")
        >>> pickle_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "tests\\data\\dat.pickle" ... Done.
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> dat_pathname = cd(data_dir, "dat.csv")
        >>> csv_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
        Loading "tests\\data\\dat.csv" ... Done.
        >>> csv_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> dat_pathname = cd(data_dir, "dat.json")
        >>> json_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "tests\\data\\dat.json" ... Done.
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}

        >>> dat_pathname = cd(data_dir, "dat.feather")
        >>> feather_dat = load_data(path_to_file=dat_pathname, index=0, verbose=True)
        Loading "tests\\data\\dat.feather" ... Done.
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> dat_pathname = cd(data_dir, "dat.joblib")
        >>> joblib_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "tests\\data\\dat.joblib" ... Done.
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
    """

    path_to_file_ = path_to_file.lower()

    if path_to_file_.endswith((".pkl", ".pickle")):
        data = load_pickle(path_to_file, **kwargs)

    elif path_to_file_.endswith((".csv", ".txt")):
        data = load_csv(path_to_file, **kwargs)

    elif path_to_file_.endswith((".xlsx", ".xls")):
        data = load_spreadsheets(path_to_file, **kwargs)

    elif path_to_file_.endswith(".json"):
        data = load_json(path_to_file, **kwargs)

    elif path_to_file_.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        data = load_joblib(path_to_file, **kwargs)

    elif path_to_file_.endswith((".fea", ".feather")):
        data = load_feather(path_to_file, **kwargs)

    else:
        data = None

        if err_warning:
            warnings.warn(
                "The specified file format (extension) is not recognisable by "
                "`pyhelpers.store.load_data`.")

    return data


# ==================================================================================================
# Uncompress data
# ==================================================================================================


def unzip(path_to_zip_file, out_dir=None, verbose=False, **kwargs):
    """
    Extract data from a `zipped (compressed)
    <https://support.microsoft.com/en-gb/help/14200/windows-compress-uncompress-zip-files>`_ file.

    :param path_to_zip_file: path where a Zip file is saved
    :type path_to_zip_file: str
    :param out_dir: path to a directory where the extracted data is saved, defaults to ``None``
    :type out_dir: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `zipfile.ZipFile.extractall`_

    .. _`zipfile.ZipFile.extractall`:
        https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.extractall

    **Examples**::

        >>> from pyhelpers.store import unzip
        >>> from pyhelpers.dirs import cd, delete_dir

        >>> zip_file_path = cd("tests\\data", "zipped.zip")

        >>> unzip(path_to_zip_file=zip_file_path, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> unzip(path_to_zip_file=zip_file_path, out_dir=output_dir, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped_alt\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Delete the directories "tests\\data\\zipped\\" and "tests\\data\\zipped_alt\\"
        >>> delete_dir([cd("tests\\data\\zipped"), output_dir], verbose=True)
        To delete the following directories:
            "tests\\data\\zipped\\" (Not empty)
            "tests\\data\\zipped_alt\\" (Not empty)
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    if out_dir is None:
        out_dir = os.path.splitext(path_to_zip_file)[0]

    if not os.path.exists(out_dir):
        os.makedirs(name=out_dir)

    if verbose:
        rel_path = os.path.relpath(path=path_to_zip_file)
        out_dir_ = os.path.relpath(path=out_dir) + ("\\" if not out_dir.endswith("\\") else "")
        print("Extracting \"{}\" to \"{}\"".format(rel_path, out_dir_), end=" ... ")

    try:
        with zipfile.ZipFile(file=path_to_zip_file) as zf:
            zf.extractall(path=out_dir, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        print(f"Failed. {e}")


def seven_zip(path_to_zip_file, out_dir=None, mode='aoa', verbose=False, seven_zip_exe=None, **kwargs):
    """
    Extract data from a compressed file by using `7-Zip <https://www.7-zip.org/>`_.

    :param path_to_zip_file: path where a compressed file is saved
    :type path_to_zip_file: str
    :param out_dir: path to a directory where the extracted data is saved, defaults to ``None``
    :type out_dir: str or None
    :param mode: defaults to ``'aoa'``
    :type mode: str
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param seven_zip_exe: absolute path to '7z.exe', defaults to ``None``;
        when ``seven_zip_exe=None``, use the default installation path, e.g. (on Windows)
        "*C:\\\\Program Files\\\\7-Zip\\\\7z.exe*"
    :type seven_zip_exe: str or None
    :param kwargs: [optional] parameters of `subprocess.run`_

    .. _`subprocess.run`: https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import seven_zip
        >>> from pyhelpers.dirs import cd, delete_dir

        >>> zip_file_pathname = cd("tests\\data", "zipped.zip")

        >>> seven_zip(path_to_zip_file=zip_file_pathname, verbose=True)
        7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06

        Scanning the drive for archives:
        1 file, 158 bytes (1 KiB)

        Extracting archive: \\tests\\data\\zipped.zip
        --
        Path = \\tests\\data\\zipped.zip
        Type = zip
        Physical Size = 158

        Everything is Ok

        Size:       4
        Compressed: 158

        Done.

        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> seven_zip(path_to_zip_file=zip_file_pathname, out_dir=output_dir, verbose=False)

        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Extract a .7z file
        >>> zip_file_path = cd("tests\\data", "zipped.7z")
        >>> seven_zip(path_to_zip_file=zip_file_path, out_dir=output_dir)

        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test

        >>> # Delete the directories "tests\\data\\zipped\\" and "tests\\data\\zipped_alt\\"
        >>> delete_dir([cd("tests\\data\\zipped"), output_dir], verbose=True)
        To delete the following directories:
            "tests\\data\\zipped\\" (Not empty)
            "tests\\data\\zipped_alt\\" (Not empty)
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    exe_name = "7z.exe"
    possible_exe_pathnames = {exe_name, "C:\\Program Files\\7-Zip\\7z.exe"}
    seven_zip_exists, seven_zip_exe_ = _check_exe_pathname(
        exe_name, exe_pathname=seven_zip_exe, possible_pathnames=possible_exe_pathnames)

    if seven_zip_exists:
        if out_dir is None:
            out_dir = os.path.splitext(path_to_zip_file)[0]

        try:
            # subprocess.run(
            #     '"{}" x "{}" -o"{}" -{}'.format(seven_zip_exe_, path_to_zip_file, out_dir, mode),
            #     **kwargs)
            command_args = [seven_zip_exe_, 'x', path_to_zip_file, '-o' + out_dir, '-' + mode]
            if not verbose:
                command_args += ['-bso0', '-bsp0']

            rslt = subprocess.run(command_args, **kwargs)

            if verbose:
                print("\nDone." if rslt.returncode == 0 else "\nFailed.")

        except Exception as e:
            if verbose:
                print("An error occurred: {}.".format(e))

    else:
        print("\"7-Zip\" (https://www.7-zip.org/) is required to run this function; "
              "however, it is not found on this device.\nInstall it and then try again.")


# ==================================================================================================
# Convert data
# ==================================================================================================


def markdown_to_rst(path_to_md, path_to_rst, engine=None, pandoc_exe=None, verbose=False, **kwargs):
    """
    Convert a `Markdown <https://daringfireball.net/projects/markdown/>`_ file (.md)
    to a `reStructuredText <https://docutils.readthedocs.io/en/sphinx-docs/user/rst/quickstart.html>`_
    (.rst) file.

    This function relies on
    `Pandoc <https://pandoc.org/>`_ or `pypandoc <https://github.com/bebraw/pypandoc>`_.

    :param path_to_md: path where a markdown file is saved
    :type path_to_md: str
    :param path_to_rst: path where a reStructuredText file is saved
    :type path_to_rst: str
    :param engine: engine/module used for performing the conversion, defaults to ``None``;
        an alternative option is ``'pypandoc'``
    :type engine: None or str
    :param pandoc_exe: absolute path to the executable "pandoc.exe", defaults to ``None``;
        when ``pandoc_exe=None``, use the default installation path, e.g. (on Windows)
        "*C:\\\\Program Files\\\\Pandoc\\\\pandoc.exe*"
    :type pandoc_exe: str or None
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of `subprocess.run`_ (when ``engine=None``) or
        `pypandoc.convert_file`_ (when ``engine='pypandoc'``)

    .. _`subprocess.run`: https://docs.python.org/3/library/subprocess.html#subprocess.run
    .. _`pypandoc.convert_file`: https://github.com/NicklasTegner/pypandoc#usage

    **Examples**::

        >>> from pyhelpers.store import markdown_to_rst
        >>> from pyhelpers.dirs import cd

        >>> dat_dir = cd("tests\\documents")

        >>> path_to_md_file = cd(dat_dir, "readme.md")
        >>> path_to_rst_file = cd(dat_dir, "readme.rst")

        >>> markdown_to_rst(path_to_md_file, path_to_rst_file, verbose=True)
        Converting "tests\\data\\markdown.md" to "tests\\data\\markdown.rst" ... Done.
    """

    exe_name = "pandoc.exe"
    possible_exe_pathnames = {exe_name, f"C:\\Program Files\\Pandoc\\{exe_name}"}
    pandoc_exists, pandoc_exe_ = _check_exe_pathname(exe_name, pandoc_exe, possible_exe_pathnames)

    abs_md_path, abs_rst_path = pathlib.Path(path_to_md), pathlib.Path(path_to_rst)
    # assert abs_md_path.suffix == ".md" and abs_rst_path.suffix == ".rst"

    if verbose:
        rel_md_path, rel_rst_path = map(
            lambda x: pathlib.Path(os.path.relpath(x)), (abs_md_path, abs_rst_path))

        if not os.path.exists(abs_rst_path):
            msg = "Converting \"{}\" to \"{}\"".format(rel_md_path, rel_rst_path)
        else:
            msg = "Updating \"{}\" at \"{}\\\"".format(rel_rst_path.name, rel_rst_path.parent)
        print(msg, end=" ... ")

    try:
        if engine is None:
            if pandoc_exists:
                # subprocess.run(
                #     f'"{pandoc_exe_}" "{abs_md_path}" -f markdown -t rst -s -o "{abs_rst_path}"')
                command_args = [
                    pandoc_exe_, abs_md_path, '-f', 'markdown', '-t', 'rst', '-s', '-o', abs_rst_path]
                rslt = subprocess.run(command_args, **kwargs)
                ret_code = rslt.returncode

            else:
                ret_code = -1

        else:
            py_pandoc = _check_dependency(name='pypandoc')

            rslt = py_pandoc.convert_file(
                str(abs_md_path), 'rst', outputfile=str(abs_rst_path), **kwargs)

            ret_code = 0 if rslt == '' else -2

        if verbose:
            if ret_code == 0:
                print("Done.")
            elif ret_code == -1:
                print(
                    "Failed."
                    "\n\"Pandoc\" is required to proceed with `engine=None`; "
                    "however, it is not found on this device."
                    "\nInstall it (https://pandoc.org/) and then try again; "
                    "or, try instead `engine='pypandoc'`")
            else:
                print("Failed.")

    except Exception as e:
        print("An error occurred: {}".format(e))


def _xlsx_to_csv(xlsx_pathname, csv_pathname_, sheet_name='1', vbscript=None, **kwargs):
    """
    Convert Microsoft Excel spreadsheet (in the format .xlsx/.xls) to a CSV file
    using VBScript.

    Reference: https://stackoverflow.com/questions/1858195/.

    :param xlsx_pathname: pathname of an Excel spreadsheet (in the format of .xlsx)
    :type xlsx_pathname: str
    :param csv_pathname_: pathname of a CSV format file;
    :type csv_pathname_: str or None
    :param sheet_name: name of the target worksheet in the given Excel file, defaults to ``'1'``
    :type sheet_name: str
    :param vbscript: pathname of a VB script used for converting .xlsx/.xls to .csv, defaults to ``None``
    :type vbscript: str or None
    :param kwargs: [optional] parameters of the function `subprocess.run`_
    :return: code for the result of running the VBScript
    :rtype: int

    .. _`subprocess.run`: https://docs.python.org/3/library/subprocess.html#subprocess.run
    """

    command_args = ["cscript.exe", "//Nologo", vbscript, xlsx_pathname, csv_pathname_, sheet_name]
    if platform.system() == 'Linux':
        command_args = ["wine"] + command_args

    rslt = subprocess.run(command_args, **kwargs)
    ret_code = rslt.returncode

    return ret_code


def xlsx_to_csv(xlsx_pathname, csv_pathname=None, engine=None, if_exists='replace', vbscript=None,
                sheet_name='1', ret_null=False, verbose=False, **kwargs):
    """
    Convert Microsoft Excel spreadsheet (in the format .xlsx/.xls) to a CSV file.

    See also [`STORE-XTC-1 <https://stackoverflow.com/questions/1858195/>`_].

    :param xlsx_pathname: pathname of an Excel spreadsheet (in the format of .xlsx)
    :type xlsx_pathname: str
    :param csv_pathname: pathname of a CSV format file;
        when ``csv_pathname=None`` (default),
        the target CSV file is generated as a `tempfile.NamedTemporaryFile`_;
        when ``csv_pathname=""``,
        the target CSV file is generated at the same directory where the source Excel spreadsheet is;
        otherwise, it could also be a specific pathname
    :type csv_pathname: str or None
    :param engine: engine used for converting .xlsx/.xls to .csv;
        when ``engine=None`` (default), a Microsoft VBScript (Visual Basic Script) is used;
        when ``engine='xlsx2csv'``, the function would rely on `xlsx2csv`_
    :type engine: str or None
    :param if_exists: how to proceed if the target ``csv_pathname`` exists, defaults to ``'replace'``
    :type if_exists: str
    :param vbscript: pathname of a VB script used for converting .xlsx/.xls to .csv, defaults to ``None``
    :type vbscript: str or None
    :param sheet_name: name of the target worksheet in the given Excel file, defaults to ``'1'``
    :type sheet_name: str
    :param ret_null: whether to return something depending on the specified ``engine``,
        defaults to ``False``
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param kwargs: [optional] parameters of the function `subprocess.run`_
    :return: the pathname of the generated CSV file or None, when ``engine=None``;
        `io.StringIO`_ buffer, when ``engine='xlsx2csv'``
    :rtype: str or _io.StringIO or None

    .. _`tempfile.NamedTemporaryFile`:
        https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    .. _`xlsx2csv`: https://github.com/dilshod/xlsx2csv
    .. _`io.StringIO`: https://docs.python.org/3/library/io.html#io.StringIO
    .. _`subprocess.run`: https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import xlsx_to_csv, load_csv
        >>> from pyhelpers.dirs import cd
        >>> import os

        >>> path_to_test_xlsx = cd("tests\\data", "dat.xlsx")

        >>> path_to_temp_csv = xlsx_to_csv(path_to_test_xlsx, verbose=True)
        Converting "tests\\data\\dat.xlsx" to a (temporary) CSV file ... Done.
        >>> os.path.isfile(path_to_temp_csv)
        True
        >>> data = load_csv(path_to_temp_csv, index=0)
        >>> data
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185

        >>> # Set `engine='xlsx2csv'`
        >>> temp_csv_buffer = xlsx_to_csv(path_to_test_xlsx, engine='xlsx2csv', verbose=True)
        Converting "tests\\data\\dat.xlsx" to a (temporary) CSV file ... Done.
        >>> # import pandas as pd; data_ = pandas.read_csv(io_buffer, index_col=0)
        >>> data_ = load_csv(temp_csv_buffer, index=0)
        >>> data_
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> data.astype('float16').equals(data_.astype('float16'))
        True

        >>> # Remove the temporary CSV file
        >>> os.remove(path_to_temp_csv)
    """

    if verbose:
        try:
            rel_path = os.path.relpath(xlsx_pathname)
        except ValueError:
            rel_path = copy.copy(xlsx_pathname)

        print(f"Converting \"{rel_path}\" to a (temporary) CSV file", end=" ... ")

    if engine is None:
        if vbscript is None:
            vbscript = pkg_resources.resource_filename(__name__, "data/xlsx2csv.vbs")

        if csv_pathname is None:
            temp_file = tempfile.NamedTemporaryFile()
            csv_pathname_ = temp_file.name + ".csv"
        elif csv_pathname == "":
            csv_pathname_ = xlsx_pathname.replace(".xlsx", ".csv")
        else:
            csv_pathname_ = copy.copy(csv_pathname)

        if os.path.exists(csv_pathname_):
            if if_exists == 'replace':
                os.remove(csv_pathname_)
            elif if_exists == 'pass':
                return csv_pathname_

        ret_code = _xlsx_to_csv(
            xlsx_pathname=xlsx_pathname, csv_pathname_=csv_pathname_, sheet_name=sheet_name,
            vbscript=vbscript, **kwargs)

        if verbose:
            print("Done." if ret_code == 0 else "Failed.")

        if not ret_null and ret_code == 0:
            return csv_pathname_

    elif engine == 'xlsx2csv':
        xlsx2csv = _check_dependency(name='xlsx2csv')

        buffer = io.StringIO()
        try:
            xlsx2csv.Xlsx2csv(
                xlsxfile=xlsx_pathname, sheet_name=sheet_name, outputencoding="utf-8").convert(buffer)
            buffer.seek(0)

            if verbose:
                print("Done.")

            return buffer

        except Exception as e:
            print(f"Failed. {e}")
            buffer.close()
