"""
Load data.
"""

import copy
import csv
import logging
import operator
import pickle
import sys

import pandas as pd

from .._cache import _check_dependency, _check_rel_pathname, _print_failure_msg


def _check_loading_path(path_to_file, verbose=False, print_prefix="", state_verb="Loading",
                        print_suffix="", print_end=" ... "):
    # noinspection PyShadowingNames
    """
    Check about loading a file from a specified pathname.

    :param path_to_file: Path where a file is saved.
    :type path_to_file: str | bytes | pathlib.Path
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param print_prefix: Something prefixed to the default printing message; defaults to ``""`.
    :type print_prefix: str
    :param state_verb: Normally a word indicating either "loading" or "reading" a file;
        defaults to ``"Loading"``.
    :type state_verb: str
    :param print_suffix: Something suffixed to the default printing message; defaults to ``""`.
    :type print_suffix: str
    :param print_end: A string passed to ``end`` for ``print()``; defaults to ``" ... "``.
    :type print_end: str

    **Tests**::

        >>> from pyhelpers.store import _check_loading_path
        >>> from pyhelpers.dirs import cd

        >>> path_to_file = cd("test_func.py")
        >>> _check_loading_path(path_to_file, verbose=True)
        >>> print("Passed.")
        Loading "test_func.py" ... Passed.
    """

    if verbose:
        rel_pathname = _check_rel_pathname(path_to_file)
        print(f'{print_prefix}{state_verb} "{rel_pathname}"{print_suffix}', end=print_end)


def _set_index(data, index=None):
    """
    Set index of a dataframe.

    :param data: A dataframe.
    :type data: pandas.DataFrame
    :param index: Column index or a list of column indices; defaults to ``None``.
        When ``index=None``, set the first column to be the index
        if the column name is an empty string.
    :type index: int | list | None
    :return: An updated dataframe.
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
        >>> example_df_1 = _set_index(example_df, index=0)
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
        >>> example_df_2 = _set_index(example_df_2, index=None)
        >>> np.array_equal(example_df_2.values, example_df.values)
        True
    """

    data_ = data.copy()

    if index is None:
        idx_col = data.columns[0]
        if idx_col == '':
            data_ = data.set_index(idx_col)
            data_.index.name = None

    else:
        idx_keys_ = [index] if isinstance(index, (int, list)) else copy.copy(index)
        idx_keys = [data.columns[x] if isinstance(x, int) else x for x in idx_keys_]
        data_ = data.set_index(keys=idx_keys)

    return data_


def load_pickle(path_to_file, verbose=False, prt_kwargs=None, **kwargs):
    """
    Load data from a `Pickle`_ file.

    :param path_to_file: Path where a pickle file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `pickle.load`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: Any

    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`pickle.load`: https://docs.python.org/3/library/pickle.html#pickle.load

    .. note::

        - Example data can be referred to the function :func:`pyhelpers.store.save_pickle`.

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

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **prt_kwargs)

    try:
        try:
            with open(file=path_to_file, mode='rb') as pickle_in:
                pickle_data = pickle.load(pickle_in, **kwargs)
        except ModuleNotFoundError:
            pickle_data = pd.read_pickle(path_to_file)

        if verbose:
            print("Done.")

        return pickle_data

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def load_csv(path_to_file, delimiter=',', header=0, index=None, verbose=False, prt_kwargs=None,
             **kwargs):
    """
    Load data from a `CSV`_ file.

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values

    :param path_to_file: Pathname of a `CSV`_ file.
    :type path_to_file: str | os.PathLike
    :param delimiter: Delimiter used between values in the data file; defaults to ``','``
    :type delimiter: str
    :param header: Index number of the rows used as column names; defaults to ``0``.
    :type header: int | typing.List[int] | None
    :param index: Index number of the column(s) to use as the row labels of the dataframe,
        defaults to ``None``.
    :type index: str | int | list | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `csv.reader()`_ or `pandas.read_csv()`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: pandas.DataFrame | None

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`csv.reader()`: https://docs.python.org/3/library/pickle.html#pickle.load
    .. _`pandas.read_csv()`: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

    .. note::

        - Example data can be referred to the function :func:`pyhelpers.store.save_spreadsheet`.

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

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **prt_kwargs)

    try:
        with open(path_to_file, mode='r') as csv_file:
            csv_data_ = csv.reader(csv_file, delimiter=delimiter, **kwargs)
            csv_rows = [row for row in csv_data_]

        if header is not None:
            col_names = operator.itemgetter(
                *[header] if isinstance(header, int) else header)(csv_rows)
            dat = [x for x in csv_rows if (x not in col_names and x != col_names)]
            csv_data = pd.DataFrame(data=dat, columns=list(col_names))
        else:
            csv_data = pd.DataFrame(csv_rows)

        csv_data = _set_index(csv_data, index=index)

        if verbose:
            print("Done.")

        return csv_data

    except TypeError:
        csv_data = pd.read_csv(path_to_file, index_col=index, **kwargs)

        return csv_data

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def load_spreadsheets(path_to_file, as_dict=True, verbose=False, prt_kwargs=None, **kwargs):
    """
    Load multiple sheets of an `Microsoft Excel`_ or an `OpenDocument`_ format file.

    :param path_to_file: Path where a spreadsheet is saved.
    :type path_to_file: str | os.PathLike
    :param as_dict: Whether to return the retrieved data as a dictionary type; defaults to ``True``.
    :type as_dict: bool
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `pandas.ExcelFile.parse`_
    :return: Data of all worksheets in the file from the specified pathname ``path_to_file``.
    :rtype: list | dict

    .. _`Microsoft Excel`:
        https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`OpenDocument`:
        https://en.wikipedia.org/wiki/OpenDocument
    .. _`pandas.ExcelFile.parse`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelFile.parse.html

    .. note::

         - Example data can be referred to the functions
           :func:`pyhelpers.store.save_multiple_spreadsheets` and
           :func:`pyhelpers.store.save_spreadsheet`.

    **Examples**::

        >>> from pyhelpers.store import load_spreadsheets
        >>> from pyhelpers.dirs import cd

        >>> dat_dir = cd("tests\\data")

        >>> path_to_xlsx = cd(dat_dir, "dat.ods")
        >>> wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        Loading "tests\\data\\dat.ods" ...
            'TestSheet1'. ... Done.
            'TestSheet2'. ... Done.
        >>> list(wb_data.keys())
        ['TestSheet1', 'TestSheet2']
        >>> wb_data['TestSheet1']
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> path_to_xlsx = cd(dat_dir, "dat.xlsx")
        >>> wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        Loading "tests\\data\\dat.xlsx" ...
            'TestSheet1'. ... Done.
            'TestSheet2'. ... Done.
            'TestSheet11'. ... Done.
            'TestSheet21'. ... Done.
            'TestSheet12'. ... Done.
            'TestSheet22'. ... Done.
        >>> list(wb_data.keys())
        ['TestSheet1',
         'TestSheet2',
         'TestSheet11',
         'TestSheet21',
         'TestSheet12',
         'TestSheet22']

        >>> wb_data = load_spreadsheets(path_to_xlsx, as_dict=False, index_col=0)
        >>> type(wb_data)
        list
        >>> len(wb_data)
        6
        >>> wb_data[0]
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(
        path_to_file=path_to_file, verbose=verbose, print_end=" ... \n", **prt_kwargs)

    with pd.ExcelFile(path_to_file) as excel_file_reader:
        sheet_names = excel_file_reader.sheet_names
        workbook_dat = []

        for sheet_name in sheet_names:
            if verbose:
                print(f"\t'{sheet_name}'.", end=" ... ")
            try:
                sheet_dat = excel_file_reader.parse(sheet_name, **kwargs)
                if verbose:
                    print("Done.")
            except Exception as e:
                sheet_dat = None
                _print_failure_msg(e=e, msg="Failed.")

            workbook_dat.append(sheet_dat)

    if as_dict:
        workbook_data = dict(zip(sheet_names, workbook_dat))
    else:
        workbook_data = workbook_dat

    return workbook_data


def load_json(path_to_file, engine=None, verbose=False, prt_kwargs=None, **kwargs):
    """
    Load data from a `JSON`_ file.

    :param path_to_file: Path where a JSON file is saved.
    :type path_to_file: str | os.PathLike
    :param engine: An open-source Python package for JSON serialization; valid options include
        ``None`` (default, for the built-in `json module`_), ``'ujson'`` (for `UltraJSON`_),
        ``'orjson'`` (for `orjson`_) and ``'rapidjson'`` (for `python-rapidjson`_).
    :type engine: str | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `json.load()`_ (if ``engine=None``),
        `orjson.loads()`_ (if ``engine='orjson'``), `ujson.load()`_ (if ``engine='ujson'``) or
        `rapidjson.load()`_ (if ``engine='rapidjson'``).
    :return: Data retrieved from the specified path ``path_to_file``.
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

        - Example data can be referred to the function :func:`pyhelpers.store.save_json`.

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

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **prt_kwargs)

    try:
        if engine == 'orjson':
            with open(path_to_file, mode='rb') as json_in:
                json_data = mod.loads(json_in.read(), **kwargs)

        else:
            with open(path_to_file, mode='r') as json_in:
                json_data = mod.load(json_in, **kwargs)

        if verbose:
            print("Done.")

        return json_data

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def load_joblib(path_to_file, verbose=False, prt_kwargs=None, **kwargs):
    """
    Load data from a `joblib`_ file.

    :param path_to_file: Path where a joblib file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `joblib.load`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: Any

    .. _`joblib`: https://pypi.org/project/joblib/
    .. _`joblib.load`: https://joblib.readthedocs.io/en/latest/generated/joblib.load.html

    .. note::

        - Example data can be referred to the function :func:`pyhelpers.store.save_joblib`.

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

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **prt_kwargs)

    try:
        joblib_data = joblib_.load(filename=path_to_file, **kwargs)

        if verbose:
            print("Done.")

        return joblib_data

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def load_feather(path_to_file, index=None, verbose=False, prt_kwargs=None, **kwargs):
    """
    Load a dataframe from a `Feather`_ file.

    :param path_to_file: Path where a feather file is saved.
    :type path_to_file: str | os.PathLike
    :param index: Index number of the column(s) to use as the row labels of the dataframe;
        defaults to ``None``.
    :type index: str | int | list | None
    :param verbose: Whether to print relevant information in console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of `pandas.read_feather`_:

        * columns: a sequence of column names, if ``None``, all columns
        * use_threads: whether to parallelize reading using multiple threads; defaults to ``True``

    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: pandas.DataFrame

    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`pandas.read_feather`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_feather.html

    .. note::

        - Example data can be referred to the function :func:`pyhelpers.store.save_feather`.

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

    if prt_kwargs is None:
        prt_kwargs = {}
    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **prt_kwargs)

    try:
        feather_data = pd.read_feather(path_to_file, **kwargs)

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
        _print_failure_msg(e=e, msg="Failed.")


def load_data(path_to_file, err_warning=True, prt_kwargs=None, **kwargs):
    """
    Load data from a file.

    :param path_to_file: Pathname of a file;
        supported file formats include
        `Pickle`_, `CSV`_, `Microsoft Excel`_ spreadsheet, `JSON`_, `Joblib`_ and `Feather`_.
    :type path_to_file: str | os.PathLike
    :param err_warning: Whether to show a warning message if any unknown error occurs;
        defaults to ``True``.
    :type err_warning: bool
    :param prt_kwargs: [Optional] parameters of :func:`pyhelpers.store.ldr.__check_loading_path`;
        defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] parameters of one of the following functions:
        :func:`~pyhelpers.store.load_pickle`,
        :func:`~pyhelpers.store.load_csv`,
        :func:`~pyhelpers.store.load_multiple_spreadsheets`,
        :func:`~pyhelpers.store.load_json`,
        :func:`~pyhelpers.store.load_joblib` or
        :func:`~pyhelpers.store.load_feather`.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: Any

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html

    .. note::

        - Example data can be referred to the function :func:`pyhelpers.store.save_data`.

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

    path_to_file_ = str(path_to_file).lower()

    kwargs.update({'path_to_file': path_to_file, 'prt_kwargs': prt_kwargs})

    if path_to_file_.endswith((".pkl", ".pickle")):
        data = load_pickle(**kwargs)

    elif path_to_file_.endswith((".csv", ".txt")):
        data = load_csv(**kwargs)

    elif path_to_file_.endswith((".xlsx", ".xls")):
        data = load_spreadsheets(**kwargs)

    elif path_to_file_.endswith(".json"):
        data = load_json(**kwargs)

    elif path_to_file_.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        data = load_joblib(**kwargs)

    elif path_to_file_.endswith((".fea", ".feather")):
        data = load_feather(**kwargs)

    else:
        data = None

        if err_warning:
            logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            logging.warning(
                "\n\tThe specified file format (extension) is not recognisable by "
                "`pyhelpers.store.load_data()`.")

    return data
