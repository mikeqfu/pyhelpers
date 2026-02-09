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

from .utils import _check_loading_path, _resolve_json_engine, _set_index
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
        is_geospatial = False

        try:  # Check Parquet metadata for 'geo' key
            parquet_meta = pq.read_metadata(path_to_file)  # noqa
            if parquet_meta.metadata and b'geo' in parquet_meta.metadata:
                is_geospatial = True
        except Exception:  # noqa
            # Fallback to extension check if metadata is unreadable/corrupt
            file_ext = "".join(pathlib.Path(path_to_file).suffixes).lower()
            is_geospatial = (file_ext == ".geoparquet")

        warn_message = ""
        try:
            actual_engine = engine or 'auto'

            if is_geospatial:
                data = gpd.read_parquet(path_to_file, **kwargs)  # noqa
            else:
                data = pd.read_parquet(path_to_file, engine=actual_engine, **kwargs)

            if actual_engine == 'fastparquet' and not is_geospatial:
                if data.index.get_level_values(0).isnull().all():
                    index_name = data.index.name

                    if index_name and index_name in data.columns:  # Check edge cases
                        data.set_index(index_name, inplace=True)
                    else:  # Fallback to pyarrow
                        warn_message = \
                            (f"`engine='fastparquet'` failed to decode the index "
                             f"'{index_name}'; retried and resolved using `pyarrow`.")
                        kwargs['engine'] = 'pyarrow'
                        data = pd.read_parquet(path_to_file, **kwargs)

        except Exception as e:
            warn_message = f"Primary loader failed ({e}). Falling back to PyArrow."

            pq_kwargs = kwargs.copy()
            pq_kwargs.pop('engine', None)
            data = pq.read_table(path_to_file, **pq_kwargs)  # noqa

            try:
                data = data.to_pandas()
            except Exception:  # noqa
                warn_message += "\nDataFrame conversion also failed. Returning a `pyarrow.Table`."

        if verbose:
            print("Done.")
            if warn_message:
                warnings.warn(warn_message, UserWarning)

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

    ext = "".join(pathlib.Path(path_to_file).suffixes).lower()

    kwargs.update(
        {'path_to_file': path_to_file,
         'verbose': verbose,
         'prt_kwargs': prt_kwargs,
         'raise_error': raise_error}
    )

    if ext in {'.pickle', '.pickle.bz2', '.pickle.gz', '.pickle.lzma', '.pickle.xz',
               '.pkl', '.pkl.bz2', '.pkl.gz', '.pkl.lzma', '.pkl.xz'}:
        return load_pickle(**kwargs)

    if ext in {".csv", ".txt"}:
        return load_csv(**kwargs)

    if ext in {".xlsx", ".xls", ".ods"}:
        return load_spreadsheets(**kwargs)

    if ext == ".json":
        return load_json(**kwargs)

    if ext in {".joblib", ".sav", ".z", ".gz", ".bz2", ".xz", ".lzma"}:
        return load_joblib(**kwargs)

    if ext in {".fea", ".feather"}:
        return load_feather(**kwargs)

    if ext == ".npz":
        return load_csr_matrix(**kwargs)

    if ext in {".parquet", ".geoparquet"}:
        return load_parquet(**kwargs)

    if warn_err:
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        logging.warning(
            "\n  The specified file format (extension) is not recognisable by `load_data()`.")

    return None
