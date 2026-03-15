"""
Utilities for loading data of various formats.
"""

import bz2
import csv
import gzip
import inspect
import logging
import lzma
import operator
import pathlib
import pickle  # nosec
import warnings

import numpy as np
import pandas as pd

from .utils import _check_loading_path, _is_parquet_geospatial, _resolve_json_engine, _set_index, \
    suppress_gpkg_warnings
from .._cache import _lazy_check_dependencies, _print_failure_message


def load_pickle(path_to_file, verbose=False, prt_kwargs=None, raise_error=False, **kwargs):
    """
    Loads data from a `Pickle`_ file.

    The function is intended for use with trusted data sources only.

    :param path_to_file: Path where the pickle file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `pickle.load()`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: typing.Any

    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`pickle.load()`: https://docs.python.org/3/library/pickle.html#pickle.load

    .. note::

        - Ensure that ``path_to_file`` comes from a trusted source to avoid deserialization
          vulnerabilities.
        - Example data can be referred to the function :func:`~pyhelpers.store.svr.save_pickle`.

    **Examples**::

        >>> from pyhelpers.store import load_pickle
        >>> from pyhelpers.dirs import cd
        >>> pickle_pathname = cd("tests", "data", "dat.pickle")
        >>> pickle_dat = load_pickle(pickle_pathname, verbose=True)
        Loading "./tests/data/dat.pickle" ... Done.
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        path_to_file_ = str(path_to_file).lower()

        if path_to_file_.endswith((".pkl.gz", ".pickle.gz")):
            with gzip.open(path_to_file, mode='rb') as f:
                data = pickle.load(f, **kwargs)  # nosec
        elif path_to_file_.endswith((".pkl.xz", ".pkl.lzma", ".pickle.xz", ".pickle.lzma")):
            with lzma.open(path_to_file, mode='rb') as f:
                data = pickle.load(f, **kwargs)  # nosec
        elif path_to_file_.endswith((".pkl.bz2", ".pickle.bz2")):
            with bz2.BZ2File(path_to_file, mode='rb') as f:
                data = pickle.load(f, **kwargs)  # nosec
        else:
            with open(file=path_to_file, mode='rb') as f:
                data = pickle.load(f, **kwargs)  # nosec

        if verbose:
            print("Done.")

        return data

    except ModuleNotFoundError:
        data = pd.read_pickle(path_to_file)  # nosec

        if verbose:
            print("Done.")

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def load_csv(path_to_file, delimiter=',', header=0, index_col=None, verbose=False, prt_kwargs=None,
             raise_error=False, **kwargs):
    """
    Loads data from a `CSV`_ file.

    :param path_to_file: Pathname of the `CSV`_ file.
    :type path_to_file: str | os.PathLike
    :param delimiter: Delimiter used between values in the data file; defaults to ``','``.
    :type delimiter: str
    :param header: Index number of the row(s) used as column names; defaults to ``0``.
    :type header: int | typing.List[int] | None
    :param index_col: Index number of the column(s) to use as the row labels of the dataframe;
        defaults to ``None``.
    :type index_col: str | int | list | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `csv.reader()`_ or `pandas.read_csv()`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: pandas.DataFrame | None

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`csv.reader()`: https://docs.python.org/3/library/pickle.html#pickle.load
    .. _`pandas.read_csv()`: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

    .. note::

        Example data can be referred to in the function
        :func:`~pyhelpers.store.save_spreadsheet`.

    **Examples**::

        >>> from pyhelpers.store import load_csv
        >>> from pyhelpers.dirs import cd
        >>> csv_pathname = cd("tests", "data", "dat.csv")
        >>> csv_dat = load_csv(csv_pathname, index_col=0, verbose=True)
        Loading "./tests/data/dat.csv" ... Done.
        >>> csv_dat
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185
        >>> csv_pathname = cd("tests", "data", "dat.txt")
        >>> csv_dat = load_csv(csv_pathname, index_col=0, verbose=True)
        Loading "./tests/data/dat.txt" ... Done.
        >>> csv_dat
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185
        >>> csv_dat = load_csv(csv_pathname, header=[0, 1], verbose=True)
        Loading "./tests/data/dat.txt" ... Done.
        >>> csv_dat
                 City Easting Northing
               London  530034   180381
        0  Birmingham  406689   286822
        1  Manchester  383819   398052
        2       Leeds  582044   152953
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        with open(path_to_file, mode='r') as csv_file:
            csv_data_ = csv.reader(csv_file, delimiter=delimiter, **kwargs)
            csv_rows = [row for row in csv_data_]

        if header is not None:
            col_names = operator.itemgetter(
                *[header] if isinstance(header, int) else header)(csv_rows)  # noqa
            dat = [x for x in csv_rows if (x not in col_names and x != col_names)]
            data = pd.DataFrame(data=dat, columns=list(col_names))
        else:
            data = pd.DataFrame(csv_rows)

        data = _set_index(data, index_col=index_col)

        if verbose:
            print("Done.")

        return data

    except TypeError:
        try:
            kwargs.update({'index_col': index_col})
            data = pd.read_csv(path_to_file, **kwargs)
            if verbose:
                print("Done.")
            return data
        except Exception as e:
            _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def load_spreadsheets(path_to_file, as_dict=True, verbose=False, prt_kwargs=None, raise_error=False,
                      **kwargs):
    """
    Loads one or multiple sheets from a `Microsoft Excel`_ or an `OpenDocument`_ format file.

    :param path_to_file: Path where the spreadsheet file is saved.
    :type path_to_file: str | os.PathLike
    :param as_dict: Whether to return the retrieved data as a dictionary; defaults to ``True``.
    :type as_dict: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param prt_kwargs: [Optional] Additional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param kwargs: [Optional] Additional parameters for the method `pandas.ExcelFile.parse()`_.
    :return: Data of all worksheets in the file from the specified pathname ``path_to_file``.
    :rtype: list | dict | None

    .. _`Microsoft Excel`:
        https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`OpenDocument`:
        https://en.wikipedia.org/wiki/OpenDocument
    .. _`pandas.ExcelFile.parse()`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelFile.parse.html

    .. note::

         - Example data can be referred to in the functions
           :func:`~pyhelpers.store.save_multiple_spreadsheets` and
           :func:`~pyhelpers.store.save_spreadsheet`.

    **Examples**::

        >>> from pyhelpers.store import load_spreadsheets
        >>> from pyhelpers.dirs import cd
        >>> dat_dir = cd("tests", "data")
        >>> path_to_xlsx = cd(dat_dir, "dat.ods")
        >>> wb_data = load_spreadsheets(path_to_xlsx, verbose=True, index_col=0)
        Loading "./tests/data/dat.ods" ...
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
        Loading "./tests/data/dat.xlsx" ...
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

    invalid_kwargs = [
        k for k in kwargs if k not in inspect.signature(pd.ExcelFile.parse).parameters]
    if len(invalid_kwargs) > 0:
        if len(invalid_kwargs) == 1:
            be, arg_, invalid_kwargs = "is an", "argument", f"'{invalid_kwargs[0]}'"
        else:
            be, arg_ = "are", "arguments"
        msg = f"{invalid_kwargs} {be} invalid keyword {arg_} for this function."
        if raise_error:
            raise ValueError(msg)
        if verbose:
            print(msg)

    _check_loading_path(
        path_to_file=path_to_file, verbose=verbose, print_end=" ... \n", **(prt_kwargs or {}))

    with pd.ExcelFile(path_to_file) as excel_file_reader:
        sheet_names = excel_file_reader.sheet_names
        data = []

        for sheet_name in sheet_names:
            if verbose:
                print(f"  '{sheet_name}'.", end=" ... ")

            try:
                sheet_dat = excel_file_reader.parse(sheet_name, **kwargs)
                if verbose:
                    print("Done.")
            except Exception as e:
                sheet_dat = None
                _print_failure_message(
                    e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)

            data.append(sheet_dat)

    if as_dict:
        data = dict(zip(sheet_names, data))

    return data


@_resolve_json_engine
def load_json(path_to_file, engine=None, verbose=False, prt_kwargs=None, raise_error=False,
              **kwargs):
    """
    Loads data from a `JSON`_ file.

    :param path_to_file: Path where the JSON file is saved.
    :type path_to_file: str | os.PathLike
    :param engine: An open-source Python package for JSON serialization;
        valid options include ``None`` (default, for the built-in `json module`_),
        ``'ujson'`` (for `UltraJSON`_), ``'orjson'`` (for `orjson`_) and
        ``'rapidjson'`` (for `python-rapidjson`_); defaults to ``None``.
    :type engine: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `json.load()`_ (if ``engine=None``),
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

        - Example data can be referred to in the function :func:`~pyhelpers.store.save_json`.

    **Examples**::

        >>> from pyhelpers.store import load_json
        >>> from pyhelpers.dirs import cd
        >>> json_path = cd("tests", "data", "dat.json")
        >>> json_dat = load_json(json_path, verbose=True)
        Loading "./tests/data/dat.json" ... Done.
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}
    """

    json_mod = kwargs.pop('json_mod')

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        if engine == 'orjson':
            with open(path_to_file, mode='rb') as json_in:
                data = json_mod.loads(json_in.read(), **kwargs)

        else:
            with open(path_to_file, mode='r') as json_in:
                data = json_mod.load(json_in, **kwargs)

        if verbose:
            print("Done.")

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies('joblib')
def load_joblib(path_to_file, verbose=False, prt_kwargs=None, raise_error=False, **kwargs):
    """
    Loads data from a `Joblib`_ file.

    :param path_to_file: Path where the `Joblib`_ file is saved.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in the console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] addtional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] addtional parameters for the function `joblib.load()`_.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: typing.Any

    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`joblib.load()`: https://joblib.readthedocs.io/en/latest/generated/joblib.load.html

    .. note::

        - Example data can be referred to in the function :func:`~pyhelpers.store.save_joblib`.

    **Examples**::

        >>> from pyhelpers.store import load_joblib
        >>> from pyhelpers.dirs import cd
        >>> joblib_pathname = cd("tests", "data", "dat.joblib")
        >>> joblib_dat = load_joblib(joblib_pathname, verbose=True)
        Loading "./tests/data/dat.joblib" ... Done.
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

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        data = joblib.load(filename=path_to_file, **kwargs)  # noqa

        if verbose:
            print("Done.")

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def load_feather(path_to_file, index_col=None, verbose=False, prt_kwargs=None, raise_error=False,
                 **kwargs):
    """
    Loads a dataframe from a `Feather`_ file.

    :param path_to_file: Path where the feather file is saved.
    :type path_to_file: str | os.PathLike
    :param index_col: Index number or name of the column(s) to use as the row labels of the dataframe;
        defaults to ``None``.
    :type index_col: str | int | list | None
    :param verbose: Whether to print relevant information in the console; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `pandas.read_feather()`_:

        - ``columns``: Sequence of column names to read. If ``None``, all columns are read.
        - ``use_threads``: Whether to parallelize reading using multiple threads;
          defaults to ``True``.

    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: pandas.DataFrame

    .. _`Feather`:
        https://arrow.apache.org/docs/python/feather.html
    .. _`pandas.read_feather()`:
        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_feather.html

    .. note::

        - Example data can be referred to in the function :func:`~pyhelpers.store.save_feather`.

    **Examples**::

        >>> from pyhelpers.store import load_feather
        >>> from pyhelpers.dirs import cd
        >>> feather_path = cd("tests", "data", "dat.feather")
        >>> feather_dat = load_feather(feather_path, index_col=0, verbose=True)
        Loading "./tests/data/dat.feather" ... Done.
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        data = pd.read_feather(path_to_file, **kwargs)

        data = _set_index(data, index_col=index_col)

        if verbose:
            print("Done.")

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def _load_parquet(path_to_file, is_geospatial, engine, gpd_module, **kwargs):
    """
    Attempts to load data using the preferred high-level library (Pandas/GeoPandas).
    Handles specific edge cases for the 'fastparquet' engine.
    """

    actual_engine = engine or 'auto'
    warn_message = ""

    if is_geospatial:
        return gpd_module.read_parquet(path_to_file, **kwargs), warn_message

    data = pd.read_parquet(path_to_file, engine=actual_engine, **kwargs)

    # Fix for potential 'fastparquet' issue where index is loaded as a column with nulls
    if actual_engine == 'fastparquet' and data.index.get_level_values(0).isnull().all():
        index_name = data.index.name

        if index_name in data.columns:
            data = data.set_index(index_name)
        else:
            # If the index cannot be resolved
            warn_message = (
                f"`engine='fastparquet'` failed to decode the index '{index_name}'; "
                f"retried and resolved using `pyarrow`.")
            kwargs_copy = kwargs.copy()
            kwargs_copy['engine'] = 'pyarrow'
            data = pd.read_parquet(path_to_file, **kwargs_copy)

    return data, warn_message


def _load_parquet_fallback(path_to_file, pq_module, kwargs):
    """
    Last-resort loader using PyArrow directly.
    Returns a DataFrame if possible, otherwise a PyArrow Table.
    """

    # Remove 'engine' from kwargs as read_table doesn't accept it
    fallback_kwargs = kwargs.copy()
    fallback_kwargs.pop('engine', None)

    table = pq_module.read_table(path_to_file, **fallback_kwargs)
    try:
        return table.to_pandas()
    except Exception:  # noqa
        return table


@_lazy_check_dependencies(pa='pyarrow', pq='pyarrow.parquet', gpd='geopandas')
def load_parquet(path_to_file, engine=None, verbose=False, prt_kwargs=None, raise_error=False,
                 **kwargs):
    """
    Loads data from a `Parquet`_ file.

    This function provides a flexible interface for loading Parquet files.
    It uses ``pandas.read_parquet`` or ``geopandas.read_parquet``. If the specified engine is
    invalid or unavailable, it falls back to ``pyarrow.parquet.read_table``.

    :param path_to_file: Path where the Parquet file is saved.
    :type path_to_file: str | os.PathLike
    :param engine: Parquet library to use; options are ``None`` (default), ``'auto'``,
        ``'pyarrow'`` or ``'fastparquet'``.
    :type engine: str | None
    :param verbose: Whether to print progress information; defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise exceptions; if ``False`` (default),
        errors are captured and printed via a failure message if ``verbose=True``.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for `pandas.read_parquet()`_,
        `geopandas.read_parquet()`_ or `pyarrow.parquet.read_table()`_.
    :return: Data retrieved from the specified path.
    :rtype: pandas.DataFrame | geopandas.GeoDataFrame | pyarrow.Table

    .. _`Parquet`: https://arrow.apache.org/docs/python/parquet.html
    .. _`pandas.read_parquet()`:
        https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html
    .. _`geopandas.read_parquet()`:
        https://geopandas.org/en/stable/docs/reference/api/geopandas.read_parquet.html
    .. _`pyarrow.parquet.read_table()`:
        https://arrow.apache.org/docs/python/generated/pyarrow.parquet.read_table.html

    .. note::
        If the primary loaders fail (e.g. due to an invalid ``engine``), the function
        falls back to PyArrow and attempts to convert the resulting table back to a
        DataFrame. If conversion fails, a ``pyarrow.Table`` is returned.

    **Examples**::

        >>> from pyhelpers.store import load_parquet
        >>> from pyhelpers.dirs import cd
        >>> parquet_pathname = cd("tests", "data", "dat.parquet")
        >>> parquet_dat1 = load_parquet(parquet_pathname, verbose=True)
        Loading "./tests/data/dat.parquet" ... Done.
        >>> parquet_dat1
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> # Load with a specific engine
        >>> parquet_dat2 = load_parquet(parquet_pathname, engine='fastparquet', verbose=True)
        Loading "./tests/data/dat.parquet" ... Done.
        /pyhelpers/store/loaders.py:679: UserWarning: `engine='fastparquet'` failed to decode t...
        >>> parquet_dat2.equals(parquet_dat1)
        True
        >>> # Trigger fallback by providing an invalid engine
        >>> parquet_dat = load_parquet(parquet_pathname, engine='invalid', verbose=True)
        Loading "./tests/data/dat.parquet" ... Done.
        /pyhelpers/store/loaders.py:677: UserWarning: Primary loader failed (engine must be one...

    .. seealso::
        - Example data can be referred to in the function :func:`~pyhelpers.store.save_parquet`.
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        is_geospatial = _is_parquet_geospatial(path_to_file, pq)  # noqa

        try:
            # Try the high-level loaders (includes the internal fastparquet fix)
            data, warn_message = _load_parquet(
                path_to_file=path_to_file,
                is_geospatial=is_geospatial,
                engine=engine,
                gpd_module=gpd,  # noqa
                **kwargs
            )

        except Exception as e:
            warn_message = f"Primary loader failed ({e}). Falling back to PyArrow."

            data = _load_parquet_fallback(
                path_to_file=path_to_file,
                pq_module=pq,  # noqa
                kwargs=kwargs
            )  # noqa

            if not isinstance(data, (pd.DataFrame, gpd.GeoDataFrame)):  # noqa
                warn_message += "\nDataFrame conversion also failed. Returning a `pyarrow.Table`."

        if verbose:
            print("Done.")
            if warn_message:
                warnings.warn(warn_message, UserWarning)

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies('fiona', 'shapely', gpd='geopandas')
def _read_gpkg_file(filepath, engine='geopandas', suppress_warnings=True, target_crs=None,
                    **kwargs):
    """
    Internal helper to read a single layer from a GeoPackage using a specified engine.

    :param filepath: Path to the GeoPackage file.
    :type filepath: str | pathlib.Path
    :param engine: The parsing engine (``'geopandas'``/``'gpd'`` or ``'fiona'``).
    :type engine: str
    :param suppress_warnings: Whether to ignore non-critical OGR warnings.
    :type suppress_warnings: bool
    :param target_crs: Optional CRS to reproject the data into (e.g. 'EPSG:27700').
    :type target_crs: Any | None
    :param kwargs: Arguments passed to ``geopandas.read_file`` or ``fiona.open``.
    :return: A cleaned and downcast GeoDataFrame.
    :rtype: geopandas.GeoDataFrame
    """

    if not isinstance(engine, str):
        raise TypeError(f"Invalid engine type: {type(engine).__name__}. `engine` must be a string.")

    engine_ = engine.lower()
    if engine_ not in {'geopandas', 'gpd', 'fiona'}:
        raise ValueError(f"Invalid engine: '{engine}'. Choose 'geopandas' or 'fiona'.")

    if engine_ in {'geopandas', 'gpd'}:
        if suppress_warnings:
            with suppress_gpkg_warnings():
                gdf = gpd.read_file(filepath, **kwargs)  # noqa
        else:
            gdf = gpd.read_file(filepath, **kwargs)  # noqa

    elif engine_ == 'fiona':
        features = []

        # noinspection PyUnresolvedReferences
        with fiona.open(filepath, **kwargs) as f:
            crs = f.crs
            features = [
                {
                    'type': 'Feature',
                    'properties': dict(feat['properties']),
                    'geometry': shapely.geometry.shape(feat['geometry'])  # noqa
                }
                for feat in f
            ]

        gdf = gpd.GeoDataFrame.from_features(features, crs=crs)  # noqa
        cols = [c for c in gdf.columns if c != 'geometry']
        gdf = gdf[cols + ['geometry']]

    if target_crs and gdf.crs is not None:
        # Use equals() to compare the underlying projection parameters
        if not gdf.crs.equals(target_crs):
            gdf = gdf.to_crs(crs=target_crs)

    data = gdf.fillna(pd.NA).convert_dtypes()

    return data


def _load_geopackage(path_to_file, engine='geopandas', target_crs=None, suppress_warnings=True,
                     verbose=False, **kwargs):
    """
    Reads a GeoPackage file and returns data for all layers.

    If the GeoPackage contains multiple layers, returns a dictionary of GeoDataFrames.
    If it contains a single layer, returns a single GeoDataFrame.

    :param path_to_file: Path to the GeoPackage (.gpkg) file.
    :type path_to_file: str | pathlib.Path
    :param engine: Valid options include ``'geopandas'``, ``'gpd'``, and ``'fiona'``.
    :type engine: str
    :param target_crs: Optional CRS for reprojection.
    :type target_crs: Any | None
    :param suppress_warnings: Whether to hide underlying OGR or engine warnings.
        Defaults to ``True``.
    :type suppress_warnings: bool
    :param verbose: Whether to print progress or layer information. Defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: Additional parameters passed to `geopandas.read_file` or `fiona.open`,
        depending on ``engine`` (e.g. ``bbox``, ``rows``, or ``where``).
    :return: A GeoDataFrame (single layer), or a dictionary mapping layer names to GeoDataFrames,
        or ``None`` if no valid layers found.
    :rtype: geopandas.GeoDataFrame | dict[str, geopandas.GeoDataFrame] | None

    :raises TypeError: If ``engine`` is not a string.
    :raises ValueError: If ``engine`` is not one of the supported options.
    """

    # Retrieve all layer names available in the GeoPackage
    with suppress_gpkg_warnings():
        layers_info = gpd.list_layers(path_to_file)  # noqa
        all_layers = layers_info['name'].tolist()

    # OGR sometimes exposes these as layers if the file is slightly malformed
    internal_layers = {
        'gpkg_contents',
        'gpkg_geometry_columns',
        'gpkg_spatial_ref_sys',
        'gpkg_tile_matrix',
        'gpkg_tile_matrix_set',
        'gpkg_extensions',
        'sqlite_sequence',
        'spatial_ref_sys',
    }
    # Filter out known SQLite/GPKG system or internal metadata layers
    valid_layers = [lyr for lyr in all_layers if lyr.lower() not in internal_layers]

    # Define metadata parameters to pass to the helper
    common_params = dict(
        filepath=path_to_file,
        engine=engine,
        target_crs=target_crs,
        suppress_warnings=suppress_warnings,
        verbose=verbose
    )

    if len(valid_layers) > 1:  # Load each layer into a dictionary
        data = {
            lyr: _read_gpkg_file(layer=lyr, **common_params, **kwargs)
            for lyr in valid_layers
        }
    elif len(valid_layers) == 1:  # Load the single layer directly (layer=None or first in list)
        kwargs['layer'] = valid_layers[0]
        data = _read_gpkg_file(**common_params, **kwargs)
    else:  # No layers found
        data = None

    return data


def load_geopackage(path_to_file, engine='geopandas', target_crs=None, suppress_warnings=True,
                    verbose=False, prt_kwargs=None, raise_error=False, **kwargs):
    """
    Loads data from a GeoPackage file with support for multi-layer datasets.

    :param path_to_file: Path to the GeoPackage file.
    :type path_to_file: str | pathlib.Path
    :param engine: The parsing engine to use (``'geopandas'`` or ``'fiona'``).
        Defaults to ``'geopandas'``.
    :type engine: str
    :param target_crs: Optional CRS for reprojection.
    :type target_crs: Any | None
    :param suppress_warnings: If ``True``, silences common OGR 'Measured Geometry' warnings.
    :type suppress_warnings: bool
    :param verbose: If ``True``, prints the loading status and feature counts.
    :type verbose: bool | int
    :param prt_kwargs: Optional dictionary of keyword arguments for the internal
        path check printer (e.g., ``prefix``, ``suffix``).
    :type prt_kwargs: dict | None
    :param raise_error: If ``True``, re-raises any caught exceptions during loading.
        If ``False``, prints a failure message and returns ``None``.
    :type raise_error: bool
    :param kwargs: Additional arguments passed to the engine (e.g., ``layer``, ``bbox``, ``rows``).
    :return: A GeoDataFrame for single-layer files, or a dictionary of
        {layer_name: GeoDataFrame} for multi-layer files.
    :rtype: geopandas.GeoDataFrame | dict[str, geopandas.GeoDataFrame] | None

    **Examples**::

        >>> from pyhelpers.store import load_geopackage
        >>> from pyhelpers.dirs import cd
        >>> gpkg_pathname = cd("tests/data", "dat.gpkg")
        >>> gpkg_dat = load_geopackage(gpkg_pathname, verbose=True)
        Loading "./tests/data/dat.gpkg" ... Done.
        >>> gpkg_dat
                 City  Longitude   Latitude                   geometry
        0      London  -0.127647  51.507322  POINT (-0.12765 51.50732)
        1  Birmingham  -1.902691  52.479699   POINT (-1.90269 52.4797)
        2  Manchester  -2.245115  53.479489  POINT (-2.24511 53.47949)
        3       Leeds  -1.543794  53.797418  POINT (-1.54379 53.79742)
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        data = _load_geopackage(
            path_to_file=path_to_file,
            engine=engine,
            target_crs=target_crs,
            suppress_warnings=suppress_warnings,
            verbose=verbose,
            **kwargs
        )

        if verbose:
            print("Done.")

        return data

    except Exception as e:
        _print_failure_message(e=e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


@_lazy_check_dependencies(sp='scipy.sparse')
def load_csr_matrix(path_to_file, verbose=False, prt_kwargs=None, raise_error=False, **kwargs):
    # noinspection PyShadowingNames
    """
    Loads in a compressed sparse row (CSR) or compressed row storage (CRS).

    :param path_to_file: Path to the CSR file (e.g. with extension ".npz").
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console as the function runs;
        defaults to ``False``.
    :type verbose: bool | int
    :param prt_kwargs: [Optional] Additional parameters for
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for the function `numpy.load()`_.
    :return: A compressed sparse row.
    :rtype: scipy.sparse.csr.csr_matrix

    .. _`numpy.load()`: https://numpy.org/doc/stable/reference/generated/numpy.load

    **Examples**::

        >>> from pyhelpers.store import load_csr_matrix
        >>> from pyhelpers.dirs import cd
        >>> from scipy.sparse import csr_matrix
        >>> data = [1, 2, 3, 4, 5, 6]
        >>> indices = [0, 2, 2, 0, 1, 2]
        >>> indptr = [0, 2, 3, 6]
        >>> csr_mat = csr_matrix((data, indices, indptr), shape=(3, 3))
        >>> csr_mat
        <3x3 sparse matrix of type '<class 'numpy.int32'>'
            with 6 stored elements in Compressed Sparse Row format>
        >>> path_to_csr_npz = cd("tests", "data", "csr_mat.npz")
        >>> csr_mat_ = load_csr_matrix(path_to_csr_npz, verbose=True)
        Loading "./tests/data/csr_mat.npz" ... Done.
        >>> # .nnz gets the count of explicitly-stored values (non-zeros)
        >>> (csr_mat != csr_mat_).count_nonzero() == 0
        np.True_
        >>> (csr_mat != csr_mat_).nnz == 0
        True
    """

    _check_loading_path(path_to_file=path_to_file, verbose=verbose, **(prt_kwargs or {}))

    try:
        csr_loader = np.load(path_to_file, **kwargs)

        data = csr_loader['data']
        indices = csr_loader['indices']
        indptr = csr_loader['indptr']
        shape = csr_loader['shape']

        csr_mat = sp.csr_matrix((data, indices, indptr), shape)  # noqa

        if verbose:
            print("Done.")

        return csr_mat

    except Exception as e:
        _print_failure_message(e, prefix="Failed.", verbose=verbose, raise_error=raise_error)


def load_data(path_to_file, verbose=False, warn_err=True, prt_kwargs=None, raise_error=False,
              **kwargs):
    """
    Loads data from a file.

    :param path_to_file: Pathname of the file; supported formats include
        `Pickle`_, `CSV`_, `Microsoft Excel`_ spreadsheet, `JSON`_, `Joblib`_, `Feather`_ and
        `Parquet`_.
    :type path_to_file: str | os.PathLike
    :param verbose: Whether to print relevant information in console as the function runs;
        defaults to ``False``.
    :type verbose: bool | int
    :param warn_err: Whether to show a warning message if an unknown error occurs;
        defaults to ``True``.
    :type warn_err: bool
    :param prt_kwargs: [Optional] Additional parameters for the function
        :func:`pyhelpers.store._check_loading_path`; defaults to ``None``.
    :type prt_kwargs: dict | None
    :param raise_error: Whether to raise the provided exception;
        if ``raise_error=False`` (default), the error will be suppressed.
    :type raise_error: bool
    :param kwargs: [Optional] Additional parameters for one of the following functions:
        :func:`~pyhelpers.store.load_pickle`,
        :func:`~pyhelpers.store.load_csv`,
        :func:`~pyhelpers.store.load_spreadsheets`,
        :func:`~pyhelpers.store.load_json`,
        :func:`~pyhelpers.store.load_joblib`,
        :func:`~pyhelpers.store.load_feather`, or
        :func:`~pyhelpers.store.load_parquet`.
    :return: Data retrieved from the specified path ``path_to_file``.
    :rtype: typing.Any

    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`Pickle`: https://docs.python.org/3/library/pickle.html
    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`JSON`: https://www.json.org/json-en.html
    .. _`Joblib`: https://pypi.org/project/joblib/
    .. _`Feather`: https://arrow.apache.org/docs/python/feather.html
    .. _`Parquet`: https://arrow.apache.org/docs/python/parquet.html

    .. note::

        - Example data can be referred to in the function :func:`~pyhelpers.store.save_data`.

    **Examples**::

        >>> from pyhelpers.store import load_data
        >>> from pyhelpers.dirs import cd
        >>> data_dir = cd("tests", "data")
        >>> dat_pathname = cd(data_dir, "dat.pickle")
        >>> pickle_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "./tests/data/dat.pickle" ... Done.
        >>> pickle_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> dat_pathname = cd(data_dir, "dat.csv")
        >>> csv_dat = load_data(path_to_file=dat_pathname, index_col=0, verbose=True)
        Loading "./tests/data/dat.csv" ... Done.
        >>> csv_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> dat_pathname = cd(data_dir, "dat.json")
        >>> json_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "./tests/data/dat.json" ... Done.
        >>> json_dat
        {'London': {'Longitude': -0.1276474, 'Latitude': 51.5073219},
         'Birmingham': {'Longitude': -1.9026911, 'Latitude': 52.4796992},
         'Manchester': {'Longitude': -2.2451148, 'Latitude': 53.4794892},
         'Leeds': {'Longitude': -1.5437941, 'Latitude': 53.7974185}}
        >>> dat_pathname = cd(data_dir, "dat.feather")
        >>> feather_dat = load_data(path_to_file=dat_pathname, index_col=0, verbose=True)
        Loading "./tests/data/dat.feather" ... Done.
        >>> feather_dat
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> dat_pathname = cd(data_dir, "dat.joblib")
        >>> joblib_dat = load_data(path_to_file=dat_pathname, verbose=True)
        Loading "./tests/data/dat.joblib" ... Done.
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

    load_params = {
        'path_to_file': path_to_file,
        'verbose': verbose,
        'prt_kwargs': prt_kwargs,
        'raise_error': raise_error,
        **kwargs
    }

    ext = "".join(pathlib.Path(path_to_file).suffixes).lower()

    if ext.endswith(('.pickle', '.pickle.bz2', '.pickle.gz', '.pickle.lzma', '.pickle.xz',
                     '.pkl', '.pkl.bz2', '.pkl.gz', '.pkl.lzma', '.pkl.xz')):
        return load_pickle(**load_params)

    if ext.endswith((".csv", ".txt")):
        return load_csv(**load_params)

    if ext.endswith((".xlsx", ".xls", ".ods")):
        return load_spreadsheets(**load_params)

    if ext.endswith(".json"):
        return load_json(**load_params)

    if ext.endswith((".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma")):
        return load_joblib(**load_params)

    if ext.endswith((".fea", ".feather")):
        return load_feather(**load_params)

    if ext.endswith((".parquet", ".geoparquet")):
        return load_parquet(**load_params)

    if ext.endswith((".gpkg", ".geopackage")):
        return load_geopackage(**load_params)

    if ext.endswith(".npz"):
        return load_csr_matrix(**load_params)

    if warn_err:
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        logging.warning(
            f'\n  The file format/extension "{ext}" is not recognized by `load_data()`.')

    return None
