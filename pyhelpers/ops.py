"""
Miscellaneous operations.
"""

import ast
import collections.abc
import copy
import datetime
import inspect
import itertools
import math
import os
import random
import re
import shutil
import socket
import urllib.parse

import fake_useragent
import fake_useragent.errors
import numpy as np
import pandas as pd
import requests
import requests.adapters
import urllib3.util.retry

""" == General use =========================================================================== """


def confirmed(prompt=None, confirmation_required=True, resp=False):
    """
    Type to confirm whether to proceed or not.

    See also
    [`OPS-C-1 <https://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/>`_].

    :param prompt: a message that prompts an response (Yes/No), defaults to ``None``
    :type prompt: str or None
    :param confirmation_required: whether to require users to confirm and proceed, defaults to ``True``
    :type confirmation_required: bool
    :param resp: default response, defaults to ``False``
    :type resp: bool
    :return: a response
    :rtype: bool

    **Example**::

        >>> from pyhelpers.ops import confirmed

        >>> if confirmed(prompt="Testing if the function works?", resp=True):
        ...     print("Passed.")
        Testing if the function works? [Yes]|No: yes
        Passed.
    """

    if confirmation_required:
        if prompt is None:
            prompt_ = "Confirmed? "
        else:
            prompt_ = copy.copy(prompt)

        if resp is True:  # meaning that default response is True
            prompt_ = "{} [{}]|{}: ".format(prompt_, "Yes", "No")
        else:
            prompt_ = "{} [{}]|{}: ".format(prompt_, "No", "Yes")

        ans = input(prompt_)
        if not ans:
            return resp

        if re.match('[Yy](es)?', ans):
            return True
        if re.match('[Nn](o)?', ans):
            return False

    else:
        return True


def get_obj_attr(obj, col_names=None):
    """
    Get main attributes of an object.

    :param obj: a object, e.g. a class
    :type obj: object
    :param col_names: a list of column names
    :type col_names: list
    :return: tabular data of the main attributes of the given object
    :rtype: pandas.DataFrame

    **Test**::

        >>> from pyhelpers import get_obj_attr, PostgreSQL

        >>> postgres = PostgreSQL('localhost', 5432, 'postgres', database_name='postgres')
        Password (postgres@localhost:5432): ***
        Connecting postgres:***@localhost:5432/postgres ... Successfully.

        >>> obj_attr = get_obj_attr(postgres)

        >>> obj_attr.head()
               Attribute                                              Value
        0        address               postgres:***@localhost:5432/postgres
        1        backend                                         postgresql
        2     connection  <sqlalchemy.pool.base._ConnectionFairy object ...
        3  database_info  {'drivername': 'postgresql+psycopg2', 'host': ...
        4  database_name                                           postgres

        >>> obj_attr.Attribute.to_list()
        ['address',
         'backend',
         'database_info',
         'database_name',
         'dialect',
         'driver',
         'engine',
         'host',
         'port',
         'url',
         'user']
    """

    if col_names is None:
        col_names = ['Attribute', 'Value']

    all_attrs = inspect.getmembers(obj, lambda x: not (inspect.isroutine(x)))

    attrs = [x for x in all_attrs if not re.match(r'^__?', x[0])]

    attrs_tbl = pd.DataFrame(attrs, columns=col_names)

    return attrs_tbl


def eval_dtype(str_val):
    """
    Convert a string to its intrinsic data type.

    :param str_val: a string-type variable
    :type str_val: str
    :return: converted value
    :rtype: any

    **Tests**::

        >>> from pyhelpers.ops import eval_dtype

        >>> val_1 = '1'
        >>> origin_val = eval_dtype(val_1)
        >>> origin_val
        1

        >>> val_2 = '1.1.1'
        >>> origin_val = eval_dtype(val_2)
        >>> origin_val
        '1.1.1'
    """

    try:
        val = ast.literal_eval(str_val)
    except (ValueError, SyntaxError):
        val = str_val

    return val


def gps_to_utc(gps_time):
    """
    Convert standard GPS time to UTC time.

    :param gps_time: standard GPS time
    :type gps_time: float
    :return: UTC time
    :rtype: datetime.datetime

    **Example**::

        >>> from pyhelpers.ops import gps_to_utc

        >>> utc_dt = gps_to_utc(gps_time=1271398985.7822514)

        >>> utc_dt
        datetime.datetime(2020, 4, 20, 6, 23, 5, 782251)
    """

    gps_from_utc = (datetime.datetime(1980, 1, 6) - datetime.datetime(1970, 1, 1)).total_seconds()

    utc_time = datetime.datetime.utcfromtimestamp(gps_time + gps_from_utc)

    return utc_time


""" == Basic data manipulation =============================================================== """


# Iterable

def split_list_by_size(lst, sub_len):
    """
    Split a list into (evenly sized) sub-lists.

    See also [`OPS-SLBS-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param sub_len: length of a sub-list
    :type sub_len: int
    :return: a sequence of ``sub_len``-sized sub-lists from ``lst``
    :rtype: typing.Generator[list]

    **Example**::

        >>> from pyhelpers.ops import split_list_by_size

        >>> lst_ = list(range(0, 10))
        >>> sub_lst_len = 3

        >>> lists = split_list_by_size(lst_, sub_lst_len)
        >>> list(lists)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """

    for i in range(0, len(lst), sub_len):
        yield lst[i:i + sub_len]


def split_list(lst, num_of_sub):
    """
    Split a list into a number of equally-sized sub-lists.

    See also [`OPS-SL-1 <https://stackoverflow.com/questions/312443/>`_].

    :param lst: a list of any
    :type lst: list
    :param num_of_sub: number of sub-lists
    :type num_of_sub: int
    :return: a total of ``num_of_sub`` sub-lists from ``lst``
    :rtype: typing.Generator[list]

    **Example**::

        >>> from pyhelpers.ops import split_list

        >>> lst_ = list(range(0, 10))
        >>> num_of_sub_lists = 3

        >>> lists = list(split_list(lst_, num_of_sub_lists))
        >>> list(lists)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """

    chunk_size = math.ceil(len(lst) / num_of_sub)
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def split_iterable(iterable, chunk_size):
    """
    Split a list into (evenly sized) chunks.

    See also [`OPS-SI-1 <https://stackoverflow.com/questions/24527006/>`_].

    :param iterable: iterable object
    :type iterable: typing.Iterable
    :param chunk_size: length of a chunk
    :type chunk_size: int
    :return: a sequence of equally-sized chunks from ``iterable``
    :rtype: typing.Generator[typing.Iterable]

    **Examples**::

        >>> from pyhelpers.ops import split_iterable
        >>> import pandas

        >>> lst = list(range(0, 10))
        >>> size_of_chunk = 3

        >>> for lst_ in split_iterable(lst, size_of_chunk): print(list(lst_))
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]

        >>> lst = pandas.Series(range(0, 20))
        >>> size_of_chunk = 5
        >>> for lst_ in split_iterable(lst, size_of_chunk): print(list(lst_))
        [0, 1, 2, 3, 4]
        [5, 6, 7, 8, 9]
        [10, 11, 12, 13, 14]
        [15, 16, 17, 18, 19]
    """

    iterator = iter(iterable)
    for x in iterator:
        yield itertools.chain([x], itertools.islice(iterator, chunk_size - 1))


def update_nested_dict(source_dict, updates):
    """
    Update a nested dictionary or similar mapping.

    See also [`OPS-UND-1 <https://stackoverflow.com/questions/3232943/>`_].

    :param source_dict: a dictionary that needs to be updated
    :type source_dict: dict
    :param updates: a dictionary with new data
    :type updates: dict
    :return: an updated dictionary
    :rtype: dict

    **Examples**::

        >>> from pyhelpers.ops import update_nested_dict

        >>> source_dict_ = {'key_1': 1}
        >>> updates_ = {'key_2': 2}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> source_dict_
        {'key_1': 1, 'key_2': 2}

        >>> source_dict_ = {'key': 'val_old'}
        >>> updates_ = {'key': 'val_new'}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> source_dict_
        {'key': 'val_new'}

        >>> source_dict_ = {'key': {'k1': 'v1_old', 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': 'v1_new'}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> source_dict_
        {'key': {'k1': 'v1_new', 'k2': 'v2'}}

        >>> source_dict_ = {'key': {'k1': {}, 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': 'v1'}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> source_dict_
        {'key': {'k1': 'v1', 'k2': 'v2'}}

        >>> source_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> updates_ = {'key': {'k1': {}}}
        >>> source_dict_ = update_nested_dict(source_dict_, updates_)
        >>> source_dict_
        {'key': {'k1': 'v1', 'k2': 'v2'}}
    """

    for key, val in updates.items():
        if isinstance(val, collections.abc.Mapping) or isinstance(val, dict):
            source_dict[key] = update_nested_dict(source_dict.get(key, {}), val)

        elif isinstance(val, list):
            source_dict[key] = (source_dict.get(key, []) + val)

        else:
            source_dict[key] = updates[key]

    return source_dict


def get_all_values_from_nested_dict(key, target_dict):
    """
    Get all values in a nested dictionary.

    See also
    [`OPS-GAVFND-1 <https://gist.github.com/douglasmiranda/5127251>`_] and
    [`OPS-GAVFND-2 <https://stackoverflow.com/questions/9807634/>`_].

    :param key: any that can be the key of a dictionary
    :type key: any
    :param target_dict: a (nested) dictionary
    :type target_dict: dict
    :return: all values of the ``key`` within the given ``target_dict``
    :rtype: typing.Generator[typing.Iterable]

    **Examples**::

        >>> from pyhelpers.ops import get_all_values_from_nested_dict

        >>> key_ = 'key'
        >>> target_dict_ = {'key': 'val'}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> list(val)
        [['val']]

        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': 'v2'}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> list(val)
        [['v1']]

        >>> key_ = 'k1'
        >>> target_dict_ = {'key': {'k1': ['v1', 'v1_1']}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> list(val)
        [['v1', 'v1_1']]

        >>> key_ = 'k2'
        >>> target_dict_ = {'key': {'k1': 'v1', 'k2': ['v2', 'v2_1']}}
        >>> val = get_all_values_from_nested_dict(key_, target_dict_)
        >>> list(val)
        [['v2', 'v2_1']]
    """

    for k, v in target_dict.items():
        if key == k:
            yield [v] if isinstance(v, str) else v

        elif isinstance(v, dict):
            for x in get_all_values_from_nested_dict(key, v):
                yield x

        elif isinstance(v, collections.abc.Iterable):
            for d in v:
                if isinstance(d, dict):
                    for y in get_all_values_from_nested_dict(key, d):
                        yield y


def remove_multiple_keys_from_dict(target_dict, *keys):
    """
    Remove multiple keys from a dictionary.

    :param target_dict: a dictionary
    :type target_dict: dict
    :param keys: (a sequence of) any that can be the key of a dictionary
    :type keys: any

    **Example**::

        >>> from pyhelpers.ops import remove_multiple_keys_from_dict

        >>> target_dict_ = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4', 'k5': 'v5'}

        >>> remove_multiple_keys_from_dict(target_dict_, 'k1', 'k3', 'k4')

        >>> target_dict_
        {'k2': 'v2', 'k5': 'v5'}
    """

    # assert isinstance(dictionary, dict)
    for k in keys:
        if k in target_dict.keys():
            target_dict.pop(k)


def merge_dicts(*dicts):
    """
    Merge multiple dictionaries.

    :param dicts: (one or) multiple dictionaries
    :type dicts: dict
    :return: a single dictionary containing all elements of the input
    :rtype: dict

    **Example**::

        >>> from pyhelpers.ops import merge_dicts

        >>> dict_a = {'a': 1}
        >>> dict_b = {'b': 2}
        >>> dict_c = {'c': 3}

        >>> merged_dict = merge_dicts(dict_a, dict_b, dict_c)
        >>> merged_dict
        {'a': 1, 'b': 2, 'c': 3}
    """

    super_dict = {}
    for d in dicts:
        super_dict.update(d)

    return super_dict


# Tabular data

def detect_nan_for_str_column(data_frame, column_names=None):
    """
    Detect if a str type column contains ``NaN`` when reading csv files.

    :param data_frame: a data frame to be examined
    :type data_frame: pandas.DataFrame
    :param column_names: a sequence of column names, if ``None`` (default), all columns
    :type column_names: None or collections.abc.Iterable
    :return: position index of the column that contains ``NaN``
    :rtype: typing.Generator[typing.Iterable]

    **Example**::

        >>> from pyhelpers.ops import detect_nan_for_str_column
        >>> import numpy
        >>> import pandas

        >>> df = pandas.DataFrame(numpy.resize(range(10), (10, 2)), columns=['a', 'b'])
        >>> df
           a  b
        0  0  1
        1  2  3
        2  4  5
        3  6  7
        4  8  9
        5  0  1
        6  2  3
        7  4  5
        8  6  7
        9  8  9

        >>> df.iloc[3, 1] = numpy.nan
        >>> df
           a    b
        0  0  1.0
        1  2  3.0
        2  4  5.0
        3  6  NaN
        4  8  9.0
        5  0  1.0
        6  2  3.0
        7  4  5.0
        8  6  7.0
        9  8  9.0

        >>> nan_col_pos = detect_nan_for_str_column(df, column_names=None)
        >>> list(nan_col_pos)
        [1]
    """

    if column_names is None:
        column_names = data_frame.columns

    for x in column_names:
        temp = [str(v) for v in data_frame[x].unique() if isinstance(v, str) or np.isnan(v)]
        if 'nan' in temp:
            yield data_frame.columns.get_loc(x)


def create_rotation_matrix(theta):
    """
    Create a rotation matrix (counterclockwise).

    :param theta: rotation angle (in radian)
    :type theta: int or float
    :return: a rotation matrix of shape (2, 2)
    :rtype: numpy.ndarray

    **Example**::

        >>> from pyhelpers.ops import create_rotation_matrix

        >>> rot_mat = create_rotation_matrix(theta=30)

        >>> rot_mat
        array([[-0.98803162,  0.15425145],
               [-0.15425145, -0.98803162]])
    """

    sin_theta, cos_theta = np.sin(theta), np.cos(theta)

    rotation_mat = np.array([[sin_theta, cos_theta], [-cos_theta, sin_theta]])

    return rotation_mat


def dict_to_dataframe(input_dict, k='key', v='value'):
    """
    Convert a dictionary to a data frame.

    :param input_dict: a dictionary to be converted to a data frame
    :type input_dict: dict
    :param k: column name for keys
    :type k: str
    :param v: column name for values
    :type v: str
    :return: a data frame converted from the ``input_dict``
    :rtype: pandas.DataFrame

    **Example**::

        >>> from pyhelpers.ops import dict_to_dataframe

        >>> input_dict_ = {'a': 1, 'b': 2}

        >>> df = dict_to_dataframe(input_dict_)
        >>> df
          key  value
        0   a      1
        1   b      2
    """

    dict_keys = list(input_dict.keys())
    dict_vals = list(input_dict.values())

    data_frame = pd.DataFrame({k: dict_keys, v: dict_vals})

    return data_frame


def parse_csr_matrix(path_to_csr, verbose=False, **kwargs):
    """
    Load in a compressed sparse row (CSR) or compressed row storage (CRS).

    :param path_to_csr: path where a CSR (e.g. .npz) file is saved
    :type path_to_csr: str
    :param verbose: whether to print relevant information in console as the function runs,
        defaults to ``False``
    :type verbose: bool or int
    :param kwargs: optional parameters of `numpy.load`_
    :return: a compressed sparse row
    :rtype: scipy.sparse.csr.csr_matrix

    .. _`numpy.load`: https://numpy.org/doc/stable/reference/generated/numpy.load

    **Example**::

        >>> from pyhelpers.ops import parse_csr_matrix
        >>> from pyhelpers.dir import cd
        >>> import numpy
        >>> import scipy.sparse

        >>> data_ = numpy.array([1, 2, 3, 4, 5, 6])
        >>> indices_ = numpy.array([0, 2, 2, 0, 1, 2])
        >>> indptr_ = numpy.array([0, 2, 3, 6])

        >>> csr_m = scipy.sparse.csr_matrix((data_, indices_, indptr_), shape=(3, 3))
        >>> csr_m
        <3x3 sparse matrix of type '<class 'numpy.int32'>'
            with 6 stored elements in Compressed Sparse Row format>

        >>> path_to_csr_npz = cd("tests\\data", "csr_mat.npz")
        >>> numpy.savez_compressed(path_to_csr_npz, indptr=csr_m.indptr,
        ...                        indices=csr_m.indices, data=csr_m.data,
        ...                        shape=csr_m.shape)

        >>> csr_mat_ = parse_csr_matrix(path_to_csr_npz, verbose=True)
        Loading "\\tests\\data\\csr_mat.npz" ... Done.

        >>> # .nnz gets the count of explicitly-stored values (non-zeros)
        >>> (csr_mat_ != csr_m).count_nonzero() == 0
        True

        >>> (csr_mat_ != csr_m).nnz == 0
        True
    """

    if verbose:
        print("Loading \"\\{}\"".format(os.path.relpath(path_to_csr)), end=" ... ")

    try:
        csr_loader = np.load(path_to_csr, **kwargs)
        data = csr_loader['data']
        indices = csr_loader['indices']
        indptr = csr_loader['indptr']
        shape = csr_loader['shape']

        import scipy.sparse
        csr_mat = scipy.sparse.csr_matrix((data, indices, indptr), shape)

        print("Done.") if verbose else ""

        return csr_mat

    except Exception as e:
        print("Failed. {}".format(e)) if verbose else ""


def swap_cols(array, c1, c2, as_list=False):
    """
    Swap positions of two columns in an array.

    :param array: an array
    :type array: numpy.ndarray
    :param c1: index of a column
    :type c1: int
    :param c2: index of another column
    :type c2: int
    :param as_list: whether to return a list
    :type as_list: bool
    :return: a new array/list in which the positions of the c1-th and c2-th columns are swapped
    :rtype: numpy.ndarray or list

    **Test**::

        >>> from pyhelpers.ops import swap_cols
        >>> import numpy

        >>> arr = numpy.array([[55.95615851, -2.96251228],
        ...                    [55.95705685, -2.96253458],
        ...                    [55.95706935, -2.96093324],
        ...                    [55.956171  , -2.96091098]])

        >>> new_arr = swap_cols(arr, c1=0, c2=1)
        >>> new_arr
        array([[-2.96251228, 55.95615851],
               [-2.96253458, 55.95705685],
               [-2.96093324, 55.95706935],
               [-2.96091098, 55.956171  ]])
    """

    array_ = array.copy()
    array_[:, c1], array_[:, c2] = array[:, c2], array[:, c1]

    if as_list:
        array_ = list(array_)

    return array_


def swap_rows(array, r1, r2, as_list=False):
    """
    Swap positions of two rows in an array.

    :param array: an array
    :type array: numpy.ndarray
    :param r1: index of a row
    :type r1: int
    :param r2: index of another row
    :type r2: int
    :param as_list: whether to return a list
    :type as_list: bool
    :return: a new array/list in which the positions of the r1-th and r2-th rows are swapped
    :rtype: numpy.ndarray or list

    **Test**::

        >>> from pyhelpers.ops import swap_rows
        >>> import numpy

        >>> arr = numpy.array([[55.95615851, -2.96251228],
        ...                    [55.95705685, -2.96253458],
        ...                    [55.95706935, -2.96093324],
        ...                    [55.956171  , -2.96091098]])

        >>> new_arr = swap_rows(arr, r1=0, r2=1)
        >>> new_arr
        array([[55.95705685, -2.96253458],
               [55.95615851, -2.96251228],
               [55.95706935, -2.96093324],
               [55.956171  , -2.96091098]])
    """

    array_ = array.copy()
    array_[r1, :], array_[r2, :] = array[r2, :], array[r1, :]

    if as_list:
        array_ = list(array_)

    return array_


""" == Basic computation ===================================================================== """


def get_extreme_outlier_bounds(num_dat, k=1.5):
    """
    Get upper and lower bounds for extreme outliers.

    :param num_dat: an array of numbers
    :type num_dat: array-like
    :param k: a scale coefficient associated with interquartile range, defaults to ``1.5``
    :type k: float, int
    :return: lower and upper bound
    :rtype: tuple

    **Example**::

        >>> from pyhelpers.ops import get_extreme_outlier_bounds
        >>> import pandas

        >>> data = pandas.DataFrame(range(100), columns=['col'])
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000

        >>> lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)
        >>> lo_bound, up_bound
        (0.0, 148.5)
    """

    q1, q3 = np.percentile(num_dat, 25), np.percentile(num_dat, 75)
    iqr = q3 - q1

    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr

    return lower_bound, upper_bound


def interquartile_range(num_dat):
    """
    Calculate interquartile range.

    This function may be an alternative to
    `scipy.stats.iqr <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.iqr.html>`_.

    :param num_dat: an array of numbers
    :type num_dat: numpy.ndarry or list or tuple
    :return: interquartile range of ``num_dat``
    :rtype: float

    **Example**::

        >>> from pyhelpers.ops import interquartile_range
        >>> import pandas

        >>> data = pandas.DataFrame(range(100), columns=['col'])
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000

        >>> iqr_ = interquartile_range(data)
        >>> iqr_
        49.5
    """

    iqr = np.subtract(*np.percentile(num_dat, [75, 25]))

    return iqr


def find_closest_date(date, lookup_dates, as_datetime=False, fmt='%Y-%m-%d %H:%M:%S.%f'):
    """
    Find the closest date of a given one from a list of dates.

    :param date: a date
    :type date: str or datetime.datetime
    :param lookup_dates: an array of dates
    :type lookup_dates: typing.Iterable
    :param as_datetime: whether to return a datetime.datetime-formatted date, defaults to ``False``
    :type as_datetime: bool
    :param fmt: datetime format, defaults to ``'%Y-%m-%d %H:%M:%S.%f'``
    :type fmt: str
    :return: the date that is closest to the given ``date``
    :rtype: str or datetime.datetime

    **Examples**::

        >>> from pyhelpers.ops import find_closest_date
        >>> import pandas

        >>> date_list = pandas.date_range('2019-01-02', '2019-12-31')
        >>> date_list
        DatetimeIndex(['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05',
                       '2019-01-06', '2019-01-07', '2019-01-08', '2019-01-09',
                       '2019-01-10', '2019-01-11',
                       ...
                       '2019-12-22', '2019-12-23', '2019-12-24', '2019-12-25',
                       '2019-12-26', '2019-12-27', '2019-12-28', '2019-12-29',
                       '2019-12-30', '2019-12-31'],
                      dtype='datetime64[ns]', length=364, freq='D')

        >>> date_ = '2019-01-01'
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=True)
        >>> print(closest_date_)  # Timestamp('2019-01-02 00:00:00', freq='D')
        2019-01-02 00:00:00

        >>> date_ = pandas.to_datetime('2019-01-01')
        >>> closest_date_ = find_closest_date(date_, date_list, as_datetime=False)
        >>> print(closest_date_)  # '2019-01-02 00:00:00.000000'
        2019-01-02 00:00:00.000000
    """

    closest_date = min(lookup_dates, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))

    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)

    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)

    return closest_date


""" == Graph plotting ======================================================================== """


def cmap_discretisation(cmap, n_colours):
    """
    Create a discrete colour ramp.

    See also [`OPS-CD-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. built-in `colormaps`_ accessible via `matplotlib.cm.get_cmap`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :return: a discrete colormap from (the continuous) ``cmap``
    :rtype: matplotlib.colors.LinearSegmentedColormap

    .. _`colormaps`: https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap`: https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap

    **Example**::

        >>> from pyhelpers.ops import cmap_discretisation
        >>> import matplotlib.cm
        >>> import matplotlib.pyplot as plt
        >>> import numpy

        >>> cm_accent = cmap_discretisation(matplotlib.cm.get_cmap('Accent'), n_colours=5)
        >>> cm_accent.name
        'Accent_5'

        >>> fig, ax = plt.subplots(figsize=(10, 2))

        >>> ax.imshow(numpy.resize(range(100), (5, 100)), cmap=cm_accent, interpolation='nearest')

        >>> plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    The exmaple is illustrated in :numref:`cmap-discretisation`:

    .. figure:: ../_images/cmap-discretisation.*
        :name: cmap-discretisation
        :align: center
        :width: 60%

        An example of discrete colour ramp, created by
        :py:func:`cmap_discretisation()<pyhelpers.ops.cmap_discretisation>`.
    """

    import matplotlib.cm
    import matplotlib.colors

    if isinstance(cmap, str):
        cmap = matplotlib.cm.get_cmap(cmap)

    colours_i = np.concatenate((np.linspace(0, 1., n_colours), (0., 0., 0., 0.)))
    colours_rgba = cmap(colours_i)
    indices = np.linspace(0, 1., n_colours + 1)
    c_dict = {}

    for ki, key in enumerate(('red', 'green', 'blue')):
        c_dict[key] = [
            (indices[x], colours_rgba[x - 1, ki], colours_rgba[x, ki]) for x in range(n_colours + 1)
        ]

    colour_map = matplotlib.colors.LinearSegmentedColormap(cmap.name + '_%d' % n_colours, c_dict, 1024)

    return colour_map


def colour_bar_index(cmap, n_colours, labels=None, **kwargs):
    """
    Create a colour bar.

    To stop making off-by-one errors. Takes a standard colour ramp, and discretizes it,
    then draws a colour bar with correctly aligned labels.

    See also [`OPS-CBI-1
    <https://sensitivecities.com/so-youd-like-to-make-a-map-using-python-EN.html#.WbpP0T6GNQB>`_].

    :param cmap: a colormap instance, e.g. built-in `colormaps`_ accessible via `matplotlib.cm.get_cmap`_
    :type cmap: matplotlib.colors.ListedColormap
    :param n_colours: number of colours
    :type n_colours: int
    :param labels: a list of labels for the colour bar, defaults to ``None``
    :type labels: list or None
    :param kwargs: optional parameters of `matplotlib.pyplot.colorbar`_
    :return: a colour bar object
    :rtype: matplotlib.colorbar.Colorbar

    .. _`colormaps`: https://matplotlib.org/tutorials/colors/colormaps.html
    .. _`matplotlib.cm.get_cmap`: https://matplotlib.org/api/cm_api.html#matplotlib.cm.get_cmap
    .. _`matplotlib.pyplot.colorbar`: https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    **Examples**::

        >>> from pyhelpers.ops import colour_bar_index
        >>> import matplotlib.pyplot as plt
        >>> import matplotlib.cm

        >>> plt.figure(figsize=(2, 6))

        >>> cbar = colour_bar_index(cmap=matplotlib.cm.get_cmap('Accent'), n_colours=5)

        >>> plt.xticks(fontsize=12)
        >>> plt.yticks(fontsize=12)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    The above example is illustrated in :numref:`colour-bar-index-1`:

    .. figure:: ../_images/colour-bar-index-1.*
        :name: colour-bar-index-1
        :align: center
        :width: 23%

        An example of colour bar with numerical index,
        created by :py:func:`colour_bar_index()<pyhelpers.ops.colour_bar_index>`.

    .. code-block:: python

        >>> plt.figure(figsize=(2, 6))

        >>> labels_ = list('abcde')
        >>> cbar = colour_bar_index(matplotlib.cm.get_cmap('Accent'), n_colours=5, labels=labels_)

        >>> plt.xticks(fontsize=12)
        >>> plt.yticks(fontsize=12)
        >>> cbar.ax.tick_params(labelsize=14)

        >>> # plt.axis('off')
        >>> plt.tight_layout()
        >>> plt.show()

    This second example is illustrated in :numref:`colour-bar-index-2`:

    .. figure:: ../_images/colour-bar-index-2.*
        :name: colour-bar-index-2
        :align: center
        :width: 23%

        An example of colour bar with textual index,
        created by :py:func:`colour_bar_index()<pyhelpers.ops.colour_bar_index>`.
    """

    import matplotlib.cm
    import matplotlib.pyplot

    cmap = cmap_discretisation(cmap, n_colours)

    mappable = matplotlib.cm.ScalarMappable(cmap=cmap)
    mappable.set_array(np.array([]))
    mappable.set_clim(-0.5, n_colours + 0.5)

    colour_bar = matplotlib.pyplot.colorbar(mappable, **kwargs)
    colour_bar.set_ticks(np.linspace(0, n_colours, n_colours))
    colour_bar.set_ticklabels(range(n_colours))

    if labels:
        colour_bar.set_ticklabels(labels)

    return colour_bar


""" == Web scraping ========================================================================== """


def is_network_connected():
    """
    Check whether the current machine can connect to the Internet.

    :return: whether the Internet connection is currently working
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_network_connected

        >>> is_network_connected()  # assuming the machine is currently connected to the Internet
        True
    """

    host_name = socket.gethostname()
    ip_address = socket.gethostbyname(host_name)

    return False if ip_address == "127.0.0.1" else True


def is_url_connectable(url):
    """
    Check whether the current machine can connect to a given URL.

    :param url: a URL
    :type url: str
    :return: whether the machine can currently connect to the given URL
    :rtype: bool

    **Examples**::

        >>> from pyhelpers.ops import is_url_connectable

        >>> url_0 = 'https://www.python.org/'
        >>> is_url_connectable(url_0)
        True

        >>> url_1 = 'https://www.python.org1/'
        >>> is_url_connectable(url_1)
        False
    """

    try:
        netloc = urllib.parse.urlparse(url).netloc
        host = socket.gethostbyname(netloc)
        s = socket.create_connection((host, 80))
        s.close()
        return True
    except (socket.gaierror, OSError):
        return False


def is_downloadable(url):
    """
    Check whether the url contain a downloadable resource.

    :param url: a valid URL
    :type url: str

    **Example**::

        >>> from pyhelpers.ops import is_downloadable

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> is_downloadable(logo_url)
        True

        >>> google_url = 'https://www.google.co.uk/'
        >>> is_downloadable(google_url)
        False
    """

    h = requests.head(url, allow_redirects=True)

    content_type = h.headers.get('content-type').lower()

    if content_type.startswith('text/html'):
        downloadable = False
    else:
        downloadable = True

    return downloadable


def instantiate_requests_session(url, max_retries=5, backoff_factor=0.1, retry_status='default',
                                 **kwargs):
    """
    Instantiate a requests session.

    :param url: a valid URL
    :type url: str
    :param max_retries: maximum number of retries, defaults to ``5``
    :type max_retries: int
    :param backoff_factor: ``backoff_factor`` of `urllib3.util.retry.Retry()`_, defaults to ``0.1``
    :type backoff_factor: float
    :param retry_status: a list of HTTP status codes that force to retry downloading,
        inherited from ``status_forcelist`` of `urllib3.util.retry.Retry()`_;
        when ``retry_status='default'``, the list defaults to ``[429, 500, 502, 503, 504]``
    :param kwargs: optional parameters (except ``backoff_factor`` and ``status_forcelist``)
        of `urllib3.util.retry.Retry()`_
    :return: a requests session
    :rtype: `requests.Session`_

    .. _urllib3.util.retry.Retry():
        https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.Retry
    .. _requests.Session:
        https://2.python-requests.org/en/master/api/#request-sessions

    **Example**::

        >>> from pyhelpers.ops import instantiate_requests_session

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'

        >>> s = instantiate_requests_session(logo_url)

        >>> type(s)
        requests.sessions.Session
    """

    if retry_status == 'default':
        codes_for_retries = [429, 500, 502, 503, 504]
    else:
        codes_for_retries = copy.copy(retry_status)

    retries = urllib3.util.retry.Retry(
        total=max_retries, backoff_factor=backoff_factor, status_forcelist=codes_for_retries,
        **kwargs)

    session = requests.Session()

    session.mount(
        prefix='https://' if url.startswith('https:') else 'http://',
        adapter=requests.adapters.HTTPAdapter(max_retries=retries))

    return session


def _fake_requests_headers(randomized=False, **kwargs):
    """
    Make a fake HTTP headers for `requests.get
    <https://requests.readthedocs.io/en/master/user/advanced/#request-and-response-objects>`_.

    :param randomized: whether to go for a random agent, defaults to ``False``
    :type randomized: bool
    :param kwargs: [optional] parameters used by `fake_useragent.UserAgent()`_
    :return: fake HTTP headers
    :rtype: dict

    .. _fake_useragent.UserAgent():
        https://github.com/hellysmile/fake-useragent/blob/master/fake_useragent/fake.py#L13

    **Examples**::

        >>> # noinspection PyProtectedMember
        >>> from pyhelpers.ops import _fake_requests_headers

        >>> fake_headers_1 = _fake_requests_headers()
        >>> fake_headers_1
        {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ch...

        >>> fake_headers_2 = _fake_requests_headers(randomized=True)
        >>> fake_headers_2  # a random one
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML ...

    .. note::

        ``fake_headers_1`` may also be different every time we run the examples.
    """

    try:
        fake_user_agent = fake_useragent.UserAgent(**kwargs)
        ua = fake_user_agent.random if randomized else fake_user_agent['google chrome']

    except fake_useragent.FakeUserAgentError:
        if len(kwargs) > 1:
            kwargs.update({'use_cache_server': False, 'verify_ssl': False})
        fake_user_agent = fake_useragent.UserAgent(**kwargs)

        if randomized:
            ua = random.choice(fake_user_agent.data_browsers['internetexplorer'])
        else:
            ua = fake_user_agent['Internet Explorer']

    fake_headers = {'User-Agent': ua}

    return fake_headers


def fake_requests_headers(randomized=False, **kwargs):
    """
    Make a fake HTTP headers for `requests.get
    <https://requests.readthedocs.io/en/master/user/advanced/#request-and-response-objects>`_.

    :param randomized: whether to go for a random agent, defaults to ``False``
    :type randomized: bool
    :param kwargs: [optional] parameters used by `fake_useragent.UserAgent()`_
    :return: fake HTTP headers
    :rtype: dict

    .. _fake_useragent.UserAgent():
        https://github.com/hellysmile/fake-useragent/blob/master/fake_useragent/fake.py#L13

    **Examples**::

        >>> from pyhelpers.ops import fake_requests_headers

        >>> fake_headers_1 = fake_requests_headers()
        >>> fake_headers_1
        {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ch...

        >>> fake_headers_2 = fake_requests_headers(randomized=True)
        >>> fake_headers_2  # a random one

        >>> fake_headers_2 == fake_headers_1
        False

    .. note::

        ``fake_headers_1`` may also be different every time we run the examples.
    """

    try:
        fake_headers = _fake_requests_headers(randomized=randomized, **kwargs)
    except IndexError:
        # Try again
        fake_headers = _fake_requests_headers(randomized=randomized, **kwargs)

    return fake_headers


def _download_with_tqdm(response, path_to_file):
    import tqdm

    file_size = int(response.headers.get('content-length'))  # Total size in bytes

    block_size = 1024 * 1024
    if file_size >= block_size:
        chunk_size, unit = block_size, 'MB'
    else:
        chunk_size, unit = 1024, 'KB'
    total_iter = file_size // chunk_size

    iterable = response.iter_content(chunk_size=chunk_size, decode_unicode=True)
    progress = tqdm.tqdm(iterable=iterable, total=total_iter, unit=unit, unit_scale=True)

    f = open(path_to_file, mode='wb')
    written = 0
    for dat in progress:
        if dat:
            try:
                f.write(dat)
            except TypeError:
                f.write(dat.encode())
            f.flush()
            progress.update(len(dat))
            progress.refresh()
            written = written + len(dat)

    progress.close()
    f.close()

    if file_size != 0 and written != file_size:
        print("ERROR! Something went wrong!")


def download_file_from_url(url, path_to_file, if_exists='replace', max_retries=5, random_header=True,
                           verbose=False, rsr_args=None, frh_args=None, **kwargs):
    """
    Download an object available at a valid URL.

    See also [`OPS-DFFU-1`_] and [`OPS-DFFU-2`_].

    .. _OPS-DFFU-1: https://stackoverflow.com/questions/37573483/
    .. _OPS-DFFU-2: https://stackoverflow.com/questions/15431044/

    :param url: valid URL to a web resource
    :type url: str
    :param path_to_file: a path where the downloaded object is saved as, or a filename
    :type path_to_file: str
    :param if_exists: given that the specified file already exists, options include
        ``'replace'`` (default, continuing to download the requested file and replace the existing one
        at the specified path) and ``'pass'`` (cancelling the download)
    :type if_exists: str
    :param max_retries: maximum number of retries, defaults to ``5``
    :type max_retries: int
    :param random_header: whether to go for a random agent, defaults to ``True``
    :type random_header: bool
    :param verbose: whether to print relevant information in console, defaults to ``False``
    :type verbose: bool or int
    :param rsr_args: optional parameters used by
        :py:func:`requests_session_response()<pyhelpers.ops.requests_session_response>`,
        defaults to ``None``
    :type rsr_args: dict or None
    :param frh_args: optional parameters used by
        :py:func:`fake_requests_headers()<pyhelpers.ops.fake_requests_headers>`, defaults to ``None``
    :type frh_args: dict or None
    :param kwargs: optional parameters of `requests.Session.get()`_

    .. _requests.Session.get():
        https://docs.python-requests.org/en/master/_modules/requests/sessions/#Session.get

    **Example**::

        >>> from pyhelpers.ops import download_file_from_url
        >>> from pyhelpers.dir import cd
        >>> from PIL import Image

        >>> logo_url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
        >>> path_to_img = cd("tests", "images", "python-logo.png")

        >>> download_file_from_url(logo_url, path_to_img)

        >>> img = Image.open(path_to_img)
        >>> img.show()  # as illustrated below

    .. figure:: ../_images/python-logo.*
        :name: python-logo
        :align: center
        :width: 65%

        The Python Logo.

    .. only:: html

        |

    .. note::

        - When setting ``verbose`` to be ``True`` (or ``1``), the function relies on `tqdm`_,
          which is not an essential dependency for installing `pyhelpers`_>=1.2.15.
          You may need to install `tqdm`_ before proceeding with ``verbose=True`` (or ``verbose=1``).

        .. _tqdm: https://pypi.org/project/tqdm/
        .. _pyhelpers: https://pypi.org/project/pyhelpers/
    """

    # url = 'https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
    # path_to_file = cd("tests", "images", "python-logo.png")
    # max_retries = 5
    # random_header = True
    # verbose = True
    # fh_args = None

    path_to_dir = os.path.dirname(path_to_file)
    if path_to_dir == "":
        path_to_file_ = os.path.join(os.getcwd(), path_to_file)
        path_to_dir = os.path.dirname(path_to_file_)
    else:
        path_to_file_ = copy.copy(path_to_file)

    if os.path.exists(path_to_file_) and if_exists != 'replace':
        if verbose:
            print(f"The destination already has a file named \"{os.path.basename(path_to_file_)}\". "
                  f"The download is cancelled.")

    else:
        if rsr_args is None:
            rsr_args = {}
        session = instantiate_requests_session(url=url, max_retries=max_retries, **rsr_args)

        if frh_args is None:
            frh_args = {}
        try:
            fake_headers = fake_requests_headers(randomized=random_header, **frh_args)
        except IndexError:  # Try again
            fake_headers = fake_requests_headers(randomized=random_header, **frh_args)

        # Streaming, so we can iterate over the response
        response = session.get(url, stream=True, headers=fake_headers, **kwargs)

        if not os.path.exists(path_to_dir):
            os.makedirs(path_to_dir)

        if verbose:
            _download_with_tqdm(response=response, path_to_file=path_to_file_)

        else:
            f = open(file=path_to_file_, mode='wb')
            shutil.copyfileobj(response.raw, f)
            f.close()

            if os.stat(path=path_to_file_).st_size == 0:
                print("ERROR! Something went wrong! Check if the URL is downloadable.")

        response.close()
